"""The execute -> check -> loop cycle, the compact journal and resuming from what is left."""
import json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'brain'))
import runtime  # noqa: E402

def reply(aid, **kw):
    r = {'agent_id': aid, 'status': 'completed', 'result': 'done', 'evidence': ['checked'], 'assumptions': [], 'limitations': [], 'next_action': None}
    r.update(kw); return r

class Seq:
    """Adapter whose execute and verify answers come from per-task queues; the last answer repeats. Optionally reports token usage."""
    def __init__(self, execute=None, verify=None, usage=None):
        self.execute, self.verify, self.usage, self.calls = execute or {}, verify or {}, usage, []
    def invoke(self, envelope, timeout):
        self.calls.append(envelope); tid, aid, mode = envelope['task']['id'], envelope['agent_id'], envelope['mode']
        queue = (self.verify if mode == 'verify' else self.execute).get(tid, [{}])
        step = sum(1 for c in self.calls[:-1] if c['task']['id'] == tid and c['mode'] == mode)
        item = dict(queue[min(step, len(queue) - 1)])
        if mode == 'verify': item.setdefault('verdict', 'pass')
        out = reply(aid, **item)
        if self.usage: out['usage'] = dict(self.usage)
        return out
    def sequence(self): return [(c['task']['id'], c['mode']) for c in self.calls]

def task(tid, deps=(), verify=True, aid='AGENT-420'):
    return {'id': tid, 'objective': 'objective of ' + tid, 'agent_id': aid, 'depends_on': list(deps), 'acceptance_criteria': ['criterion of ' + tid], 'required_capabilities': [], 'verify': verify}

def run(adapter, tasks, path=None, resume=False, **config):
    cfg = {'allowed_agents': ['*'], 'granted_capabilities': [], 'timeout_seconds': 5, 'verifier_agent_id': 'AGENT-111'}; cfg.update(config)
    path = path or str(Path(tempfile.mkdtemp()) / 's.json')
    return runtime.Brain(runtime.Catalog(), adapter, cfg).run({'goal': 'ship the feature', 'tasks': tasks}, path, resume=resume), path

class Loop(unittest.TestCase):
    def test_a_partial_result_is_continued_from_what_is_left_not_restarted(self):
        a = Seq({'t1': [{'status': 'partial', 'result': 'wrote the parser', 'next_action': 'add the tests'}, {'result': 'parser and tests'}]})
        state, _ = run(a, [task('t1')], max_iterations=3)
        self.assertEqual(a.sequence(), [('t1', 'execute'), ('t1', 'execute'), ('t1', 'verify')]); self.assertEqual(state['tasks']['t1']['attempts'], 2)
        previous = a.calls[1]['context']['previous']
        self.assertEqual((previous['status'], previous['done'], previous['left'], previous['attempt']), ('partial', 'wrote the parser', 'add the tests', 2))
        self.assertEqual(state['outcome'], 'adapter_reported_and_verified')

    def test_a_rejected_verification_loops_with_the_verifiers_reason(self):
        a = Seq(verify={'t1': [{'verdict': 'fail', 'result': 'criterion 2 has no test'}, {}]})
        state, _ = run(a, [task('t1')], max_iterations=2)
        self.assertEqual(a.sequence(), [('t1', 'execute'), ('t1', 'verify'), ('t1', 'execute'), ('t1', 'verify')])
        self.assertIn('criterion 2 has no test', a.calls[2]['context']['previous']['why']); self.assertEqual(state['tasks']['t1']['status'], 'completed')

    def test_no_loop_by_default_and_blocked_is_never_retried(self):
        a = Seq({'t1': [{'status': 'partial'}]}); state, _ = run(a, [task('t1')]); self.assertEqual((len(a.calls), state['tasks']['t1']['status']), (1, 'blocked'))
        a = Seq({'t1': [{'status': 'blocked', 'result': 'needs a credential'}]}); state, _ = run(a, [task('t1')], max_iterations=5); self.assertEqual(len(a.calls), 1)

    def test_the_loop_stops_at_its_iteration_limit(self):
        a = Seq({'t1': [{'status': 'partial'}]}); state, _ = run(a, [task('t1')], max_iterations=3)
        self.assertEqual((len(a.calls), state['tasks']['t1']['status'], len(state['tasks']['t1']['history'])), (3, 'blocked', 3))

class Resume(unittest.TestCase):
    def test_work_stopped_by_an_unavailable_model_resumes_from_what_is_left(self):
        class Flaky(Seq):
            """The model is unreachable for t2's first call, then recovers."""
            def __init__(self): super().__init__(); self.down = {('t2', 'execute')}
            def invoke(self, envelope, timeout):
                key = (envelope['task']['id'], envelope['mode'])
                if key in self.down:
                    self.down.discard(key); self.calls.append(envelope)
                    return reply(envelope['agent_id'], status='blocked', result='Model call failed: rate_limited', evidence=[], retryable=True, **({'verdict': 'fail'} if key[1] == 'verify' else {}))
                return super().invoke(envelope, timeout)
        a = Flaky(); plan = [task('t1'), task('t2', ['t1']), task('t3', ['t2'])]
        state, path = run(a, plan)
        self.assertEqual((state['tasks']['t1']['status'], state['tasks']['t2']['status'], state['tasks']['t3']['status']), ('completed', 'blocked', 'blocked'))
        self.assertTrue(state['tasks']['t2']['resumable']); self.assertEqual(state['outcome'], 'incomplete')
        brief = Path(path).with_name('s.brief.md').read_text(encoding='utf-8')
        self.assertIn('ASKED: ship the feature', brief); self.assertIn('DONE: t1', brief); self.assertIn('LEFT: t2', brief); self.assertIn('do not redo', brief)
        before = len(a.calls)
        state, _ = run(a, plan, path=path, resume=True)
        resumed = [(c['task']['id'], c['mode']) for c in a.calls[before:]]
        self.assertEqual(state['outcome'], 'adapter_reported_and_verified'); self.assertNotIn(('t1', 'execute'), resumed)
        self.assertEqual(resumed.count(('t2', 'execute')), 1)

    def test_a_verification_cut_short_is_resumed_without_redoing_the_finished_work(self):
        class Flaky(Seq):
            def __init__(self): super().__init__(); self.down = {('t1', 'verify')}
            def invoke(self, envelope, timeout):
                key = (envelope['task']['id'], envelope['mode'])
                if key in self.down:
                    self.down.discard(key); self.calls.append(envelope)
                    return reply(envelope['agent_id'], status='blocked', result='Model call failed: timeout', evidence=[], verdict='fail', retryable=True)
                return super().invoke(envelope, timeout)
        a = Flaky(); state, path = run(a, [task('t1')]); self.assertEqual(state['tasks']['t1']['status'], 'blocked')
        state, _ = run(a, [task('t1')], path=path, resume=True)
        self.assertEqual([(c['task']['id'], c['mode']) for c in a.calls], [('t1', 'execute'), ('t1', 'verify'), ('t1', 'verify')])
        self.assertEqual(state['tasks']['t1']['status'], 'completed')

    def test_a_temporary_model_failure_is_retried_inside_the_loop(self):
        class Flaky(Seq):
            def __init__(self): super().__init__(); self.first = True
            def invoke(self, envelope, timeout):
                if envelope['mode'] == 'execute' and self.first:
                    self.first = False; self.calls.append(envelope)
                    return reply(envelope['agent_id'], status='blocked', result='Model call failed: network_error', evidence=[], retryable=True)
                return super().invoke(envelope, timeout)
        a = Flaky(); state, _ = run(a, [task('t1')], max_iterations=2)
        self.assertEqual(state['tasks']['t1']['status'], 'completed'); self.assertEqual(state['tasks']['t1']['attempts'], 2)

    def test_token_use_is_recorded_from_reports_or_estimated(self):
        a = Seq(usage={'in': 400, 'out': 100}); state, _ = run(a, [task('t1')])
        self.assertEqual((state['usage']['in'], state['usage']['out'], state['usage']['estimated_calls']), (800, 200, 0))
        a = Seq(); state, _ = run(a, [task('t1')]); self.assertEqual(state['usage']['estimated_calls'], 2); self.assertGreater(state['usage']['in'], 0)

    def test_resume_still_refuses_a_changed_plan(self):
        a = Seq(); _, path = run(a, [task('t1')])
        with self.assertRaises(runtime.BrainError): run(a, [task('t1'), task('t2')], path=path, resume=True)

class Journal(unittest.TestCase):
    def test_the_brief_is_short_complete_and_bounded(self):
        tasks = [task('t%d' % i, ['t%d' % (i - 1)] if i else []) for i in range(40)]
        a = Seq({'t%d' % i: [{'result': 'r' * 300}] for i in range(40)}); state, path = run(a, tasks)
        j = json.loads(Path(path).with_name('s.journal.json').read_text(encoding='utf-8')); self.assertEqual(len(j['done']), 40)
        self.assertLessEqual(len(runtime.render_brief(j)), 1800); self.assertNotIn('NEXT', runtime.render_brief(j))
        j['left'] = [{'task': 't40', 'agent': 'A', 'objective': 'finish', 'status': 'pending', 'next': None}]
        self.assertIn('NEXT: continue with t40', runtime.render_brief(j))

    def test_stuck_work_is_recorded_with_why(self):
        a = Seq({'t1': [{'status': 'blocked', 'result': 'needs a key', 'next_action': 'provide the API key'}]}); state, path = run(a, [task('t1'), task('t2', ['t1'])])
        brief = Path(path).with_name('s.brief.md').read_text(encoding='utf-8')
        self.assertIn('STUCK: t1: Specialist returned blocked', brief); self.assertIn('provide the API key', brief); self.assertIn('LEFT:', brief)

if __name__ == '__main__':
    unittest.main()
