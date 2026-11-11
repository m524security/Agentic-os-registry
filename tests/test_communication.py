"""Agent-to-agent communication: handoffs, shared facts and compact context, always mediated by the controller."""
import json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'brain'))
import runtime  # noqa: E402

VERIFIER = 'AGENT-111'

def response(aid, **kw):
    r = {'agent_id': aid, 'status': 'completed', 'result': 'done', 'evidence': ['checked'], 'assumptions': [], 'limitations': [], 'next_action': None}
    r.update(kw); return r

class Script:
    """Scripted adapter: execute responses are looked up by task id; verification passes unless the task id is listed."""
    def __init__(self, execute=None, fail_verify=()):
        self.execute, self.fail_verify, self.calls = execute or {}, set(fail_verify), []
    def invoke(self, envelope, timeout):
        self.calls.append(envelope); tid = envelope['task']['id']; aid = envelope['agent_id']
        if envelope['mode'] == 'verify': return response(aid, verdict='fail' if tid in self.fail_verify else 'pass')
        return response(aid, **self.execute.get(tid, {}))
    def executed(self): return [c['task']['id'] for c in self.calls if c['mode'] == 'execute']

def task(tid, aid, deps=(), caps=()):
    return {'id': tid, 'objective': 'objective of ' + tid, 'agent_id': aid, 'depends_on': list(deps), 'acceptance_criteria': ['done'], 'required_capabilities': list(caps), 'verify': True}

def handoff(**kw):
    h = {'to': 'AGENT-063', 'objective': 'read the attached paper and extract its method', 'acceptance_criteria': ['method summarized'], 'reason': 'outside my role'}
    h.update(kw); return h

class Communication(unittest.TestCase):
    def run_plan(self, adapter, plan_tasks, **config):
        cfg = {'allowed_agents': ['*'], 'granted_capabilities': ['web_fetch'], 'timeout_seconds': 5, 'verifier_agent_id': VERIFIER}
        cfg.update(config); d = tempfile.mkdtemp(); path = str(Path(d) / 's.json')
        state = runtime.Brain(runtime.Catalog(), adapter, cfg).run({'goal': 'g', 'tasks': plan_tasks}, path)
        return state, json.loads(Path(path).read_text(encoding='utf-8'))

    def test_a_handoff_runs_the_target_before_dependents_and_flows_into_their_context(self):
        script = Script({'t1': {'handoffs': [handoff(inputs={'url': 'https://example.org/p.pdf'})]}})
        state, saved = self.run_plan(script, [task('t1', 'AGENT-420'), task('t2', 'AGENT-433', ['t1'])])
        self.assertEqual(script.executed(), ['t1', 't1-h1', 't2']); self.assertEqual(state['outcome'], 'adapter_reported_and_verified')
        child = next(c for c in script.calls if c['task']['id'] == 't1-h1' and c['mode'] == 'execute')
        self.assertEqual((child['agent_id'], child['context']['requested_by']), ('AGENT-063', 't1')); self.assertIn('t1', child['context']['dependencies'])
        self.assertIn('example.org', child['context']['inputs'])
        last = next(c for c in script.calls if c['task']['id'] == 't2' and c['mode'] == 'execute')
        self.assertEqual(set(last['context']['dependencies']), {'t1', 't1-h1'})
        self.assertEqual(saved['messages'][0]['status'], 'queued'); self.assertEqual(saved['extra_deps'], {'t2': ['t1-h1']})

    def test_context_packets_are_compact_but_the_full_output_is_kept(self):
        big = {'result': 'x' * 5000, 'evidence': ['e' * 500] * 10, 'limitations': ['l' * 400] * 5}
        script = Script({'t1': big}); state, _ = self.run_plan(script, [task('t1', 'AGENT-420'), task('t2', 'AGENT-433', ['t1'])])
        packet = next(c for c in script.calls if c['task']['id'] == 't2' and c['mode'] == 'execute')['context']['dependencies']['t1']
        self.assertLessEqual(len(packet['summary']), 1500); self.assertEqual(len(packet['evidence']), 3); self.assertTrue(all(len(e) <= 200 for e in packet['evidence']))
        self.assertEqual(len(packet['limitations']), 2); self.assertEqual(len(state['tasks']['t1']['output']['result']), 5000)

    def test_published_facts_reach_later_tasks_but_only_after_verification(self):
        publish = [{'key': 'api_base', 'value': 'https://api.example.org'}, {'key': 'bad key!', 'value': 'x'}, {'key': 'n', 'value': {'nested': 1}}]
        script = Script({'t1': {'publish': publish}}); state, saved = self.run_plan(script, [task('t1', 'AGENT-420'), task('t2', 'AGENT-433', ['t1'])])
        board = next(c for c in script.calls if c['task']['id'] == 't2' and c['mode'] == 'execute')['context']['blackboard']
        self.assertEqual(list(board), ['api_base']); self.assertEqual(board['api_base']['from'], 'AGENT-420')
        script = Script({'t1': {'publish': publish, 'handoffs': [handoff()]}}, fail_verify={'t1'})
        state, saved = self.run_plan(script, [task('t1', 'AGENT-420')])
        self.assertEqual((saved['blackboard'], saved['dynamic'], saved['messages']), ({}, [], []))  # an unverified result communicates nothing

    def test_bad_handoffs_are_rejected_with_a_reason_and_never_run(self):
        bad = [handoff(to='AGENT-999'), handoff(to='AGENT-000'), handoff(to='AGENT-420'), handoff(acceptance_criteria=[]), handoff(required_capabilities=['browser_control']),
               handoff(objective=''), 'not an object']
        script = Script({'t1': {'handoffs': bad}}); state, saved = self.run_plan(script, [task('t1', 'AGENT-420')])
        reasons = [m['reason'] for m in saved['messages']]
        self.assertEqual(len(reasons), 7); self.assertTrue(all(m['status'] == 'rejected' for m in saved['messages']))
        for fragment in ('unknown or executive', 'executive', 'itself', 'acceptance_criteria', 'widen capabilities', 'objective', 'must be an object'):
            self.assertTrue(any(fragment in r for r in reasons), fragment)
        self.assertEqual(script.executed(), ['t1']); self.assertEqual(state['status'], 'completed')

    def test_limits_duplicates_depth_and_host_allowlist(self):
        many = [handoff(objective='task number %d' % i) for i in range(5)]
        script = Script({'t1': {'handoffs': many + [handoff(objective='task number 0')]}}); state, saved = self.run_plan(script, [task('t1', 'AGENT-420')])
        self.assertEqual(sum(m['status'] == 'queued' for m in saved['messages']), 3)
        self.assertTrue(any('too many' in m['reason'] for m in saved['messages']))
        script = Script({'t1': {'handoffs': [handoff()]}, 't1-h1': {'handoffs': [handoff(to='AGENT-433', objective='one level deeper')]}})
        state, saved = self.run_plan(script, [task('t1', 'AGENT-420')], max_handoff_depth=1)
        self.assertEqual([m['status'] for m in saved['messages']], ['queued', 'rejected']); self.assertIn('depth', saved['messages'][1]['reason'])
        script = Script({'t1': {'handoffs': [handoff()]}}); state, saved = self.run_plan(script, [task('t1', 'AGENT-420')], allowed_agents=['AGENT-420', VERIFIER])
        self.assertIn('not enabled', saved['messages'][0]['reason'])

    def test_routing_is_used_when_no_target_is_named(self):
        script = Script({'t1': {'handoffs': [handoff(to=None, objective='translate the ui strings')]}})
        state, saved = self.run_plan(script, [task('t1', 'AGENT-420')])
        self.assertEqual(state['tasks']['t1-h1']['agent_id'], 'AGENT-421')

    def test_a_failed_handoff_blocks_whatever_waited_for_it(self):
        script = Script({'t1': {'handoffs': [handoff()]}}, fail_verify={'t1-h1'})
        state, _ = self.run_plan(script, [task('t1', 'AGENT-420'), task('t2', 'AGENT-433', ['t1'])])
        self.assertEqual((state['tasks']['t1-h1']['status'], state['tasks']['t2']['status']), ('failed', 'blocked')); self.assertEqual(state['outcome'], 'incomplete')

    def test_context_size_settings_are_validated(self):
        for bad in ({'context_chars': 5}, {'max_handoff_depth': 99}, {'max_handoffs_per_task': 'x'}, {'max_iterations': 0}):
            with self.assertRaises(runtime.BrainError): runtime.Brain(runtime.Catalog(), Script(), {'allowed_agents': ['*'], **bad})

if __name__ == '__main__':
    unittest.main()
