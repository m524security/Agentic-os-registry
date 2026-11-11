"""One-command work (understand, execute, loop, journal, resume) and compact sessions, through the real CLI code and adapter."""
import json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'brain'), str(ROOT / 'tests')]
import agent_cli  # noqa: E402
from test_adapter import Local, serve, BEHAVIOR, CALLS  # noqa: E402

class Work(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.server, cls.url = serve(Local)
    @classmethod
    def tearDownClass(cls): cls.server.shutdown(); cls.server.server_close()
    def setUp(self):
        BEHAVIOR.update(mode='good', n=0); CALLS.clear()
        self.tmp = Path(tempfile.mkdtemp()); agent_cli.RUNS = self.tmp / 'runs'; agent_cli.SESSIONS = self.tmp / 'sessions'
        self.env = {'LLM_PROVIDER': 'lmstudio', 'LLM_BASE_URL': self.url + '/v1', 'LLM_MODEL': 'x:2b'}

    def test_work_completes_and_saves_a_brief(self):
        out = agent_cli.work('AGENT-420', 'write the docs for the CLI', env=self.env)
        self.assertEqual((out['status'], out['text'], out['turns']), ('completed', 'built', 1)); self.assertEqual(out['tokens'], 133)
        brief = Path(out['brief']).read_text(encoding='utf-8'); self.assertIn('ASKED: write the docs for the CLI', brief); self.assertIn('DONE: t1', brief)

    def test_a_partial_answer_loops_with_what_is_left(self):
        BEHAVIOR['mode'] = 'partial_then_good'
        out = agent_cli.work('AGENT-420', 'write the docs for the CLI', max_turns=3, env=self.env)
        self.assertEqual((out['status'], out['turns'], out['text']), ('completed', 2, 'parser and tests'))
        second = [c for c in CALLS if c[0].endswith('completions')][1][1]['messages'][1]['content']
        self.assertIn('add the tests', second); self.assertIn('wrote the parser', second)

    def test_an_unavailable_model_stops_cleanly_and_resumes_later(self):
        BEHAVIOR['mode'] = 'unavailable'
        out = agent_cli.work('AGENT-420', 'write the docs for the CLI', env=self.env)
        self.assertEqual(out['status'], 'blocked'); self.assertIn('unavailable', out['reason'])
        self.assertIn('LEFT: t1', Path(out['brief']).read_text(encoding='utf-8'))
        BEHAVIOR['mode'] = 'good'
        done = agent_cli.work(None, None, env=self.env, resume=out['state'])
        self.assertEqual((done['status'], done['text']), ('completed', 'built'))

    def test_work_needs_an_agent_and_reports_ambiguity(self):
        self.assertEqual(agent_cli.work('web-research', 'x', env=self.env)['status'], 'blocked')
        self.assertEqual(agent_cli.work('zzzz qqqq', 'x', env=self.env)['status'], 'needs_selection')

class Sessions(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.server, cls.url = serve(Local)
    @classmethod
    def tearDownClass(cls): cls.server.shutdown(); cls.server.server_close()
    def test_a_session_carries_a_compact_record_forward(self):
        BEHAVIOR.update(mode='good', n=0); CALLS.clear()
        tmp = Path(tempfile.mkdtemp()); agent_cli.SESSIONS = tmp
        env = {'LLM_PROVIDER': 'ollama', 'LLM_BASE_URL': self.url, 'LLM_MODEL': 'x:2b'}
        agent_cli.ask('AGENT-433', 'first question about running offline', env=env, session='demo')
        agent_cli.ask('AGENT-433', 'second question', env=env, session='demo')
        sent = [c for c in CALLS if c[0] == '/api/chat'][1][1]['messages'][1]['content']
        self.assertIn('Earlier in this session', sent); self.assertIn('first question about running offline', sent); self.assertTrue(sent.endswith('Now: second question'))
        self.assertEqual(len(json.loads((tmp / 'demo.json').read_text(encoding='utf-8'))['turns']), 2)

    def test_session_records_stay_small(self):
        turns = [{'q': 'q' * 300, 'a': 'a' * 500} for _ in range(8)]
        self.assertLessEqual(len(agent_cli._session_brief(turns)), 1500)

if __name__ == '__main__':
    unittest.main()
