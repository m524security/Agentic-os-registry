import json, os, sys, tempfile, unittest, threading
from http.server import HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'brain'), str(ROOT / 'tests')]
import agent_cli, claude_code_pack, runtime  # noqa: E402
from test_adapter import Mock, Local, serve, BEHAVIOR  # noqa: E402

class CliPackTests(unittest.TestCase):
    def test_explicit_targets_are_exact_and_final(self):
        self.assertEqual(agent_cli.resolve_target('agent-046')['method'], 'exact-id')
        self.assertEqual(agent_cli.resolve_target('/web-research')['kind'], 'skill')
        self.assertEqual(agent_cli.resolve_target('agent-426-web-crawl-agent')['id'], 'AGENT-426')

    def test_ambiguous_target_is_not_guessed(self):
        self.assertEqual(agent_cli.resolve_target('zzzz qqqq')['kind'], 'ambiguous')

    def test_every_agent_found_by_name_and_mission(self):
        cat = runtime.Catalog(); wrong = []
        for aid, row in cat.rows.items():
            if aid == 'AGENT-000': continue
            try:
                if cat.resolve({'objective': row['name'] + ' ' + row['mission']})[0] != aid: wrong.append(aid)
            except runtime.BrainError: wrong.append(aid)
        self.assertEqual(wrong, [])

    def test_claude_code_pack_in_sync_and_valid(self):
        out = claude_code_pack.check()
        self.assertEqual(out['status'], 'passed', out['problems'])
        self.assertEqual(out['agents'], len(runtime.Catalog().rows))
        self.assertLess(out['approx_description_tokens'], 15000)

    def test_web_agents_have_web_tools(self):
        text = (ROOT / '.claude/agents/research-science').rglob('agent-427*')
        body = next(iter(text)).read_text()
        self.assertIn('WebSearch', body); self.assertIn('WebFetch', body)
        self.assertIn('playwright', (ROOT / '.claude/agents/computer-tools/agent-428-browser-automation-operator.md').read_text())

    def test_install_never_overwrites_different_files(self):
        with tempfile.TemporaryDirectory() as d:
            claude_code_pack.install('project', d)
            f = next((Path(d) / '.claude/skills').rglob('SKILL.md')); f.write_text('mine')
            out = claude_code_pack.install('project', d)
            self.assertEqual(f.read_text(), 'mine'); self.assertEqual(out['skipped_count'], 1)

    def test_ask_calls_live_adapter(self):
        server = HTTPServer(('127.0.0.1', 0), Mock); threading.Thread(target=server.serve_forever, daemon=True).start()
        os.environ.update(ANTHROPIC_API_KEY='good-key', ANTHROPIC_BASE_URL='http://127.0.0.1:%d' % server.server_port)
        self.addCleanup(lambda: [os.environ.pop(k) for k in ('ANTHROPIC_API_KEY', 'ANTHROPIC_BASE_URL')]); self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        out = agent_cli.ask('AGENT-427', 'find x', web=True)
        self.assertEqual(out['status'], 'ok'); self.assertEqual(out['sources'], ['https://example.org/a'])
        self.assertEqual(agent_cli.ask('web-research', 'find x')['resolved']['kind'], 'skill')

    def test_ask_works_with_a_local_model_and_provider_flags(self):
        server, url = serve(Local); self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        for k in ('ANTHROPIC_API_KEY', 'ANTHROPIC_BASE_URL'): os.environ.pop(k, None)
        out = agent_cli.ask('AGENT-433', 'how do I run this offline?', env={'LLM_PROVIDER': 'ollama', 'LLM_BASE_URL': url, 'LLM_MODEL': 'qwen2.5:1.5b'})
        self.assertEqual((out['status'], out['text'], out['profile']), ('ok', 'ANSWER', 'tiny'))
        bad = agent_cli.ask('AGENT-433', 'x', env={'LLM_PROVIDER': 'ollama', 'LLM_BASE_URL': 'http://127.0.0.1:9', 'LLM_MODEL': 'm'})
        self.assertEqual(bad['status'], 'blocked'); self.assertIn('network_error', bad['reason'])

if __name__ == '__main__':
    unittest.main()
