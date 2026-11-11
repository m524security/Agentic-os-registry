import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'brain'))
from runtime import Brain, BrainError, Catalog, DemoAdapter, SubprocessAdapter, validate_plan

def task(tid='a', aid='AGENT-031', deps=None, objective='Debug a parser failure'):
    return {'id':tid,'agent_id':aid,'objective':objective,'depends_on':deps or [],'acceptance_criteria':['Observed check passes'],'required_capabilities':[],'verify':True}
def plan(*tasks): return {'goal':'Test controlled scheduling','tasks':list(tasks)}

class Recording(DemoAdapter):
    def __init__(self, change=None): self.calls=[];self.change=change
    def invoke(self, envelope, timeout):
        self.calls.append(envelope)
        result=super().invoke(envelope,timeout)
        return self.change(envelope,result) if self.change else result

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'state.json'
        self.cat=Catalog();self.config={'allowed_agents':['*'],'granted_capabilities':[]}
    def tearDown(self): self.tmp.cleanup()
    def run_brain(self,p,adapter=None,config=None):
        return Brain(self.cat,adapter or Recording(),config or self.config,True).run(p,self.path)
    def test_on_demand_dependency_order_and_verifier(self):
        a=Recording();seen=[];original=self.cat.prompt
        self.cat.prompt=lambda aid:(seen.append(aid) or original(aid))
        s=self.run_brain(plan(task('second','AGENT-420',['first']),task('first')),a)
        self.assertEqual(s['status'],'completed')
        self.assertEqual([c['task']['id'] for c in a.calls],['first','first','second','second'])
        self.assertEqual(seen,['AGENT-031','AGENT-111','AGENT-420','AGENT-111'])
        self.assertEqual(set(a.calls[2]['context']['dependencies']),{'first'})
    def test_router_common_tasks(self):
        for text,expected in [('Debug a failing test','AGENT-031'),('Review accessibility keyboard navigation','AGENT-409'),('Optimize GPU CUDA kernels','AGENT-415'),('Design backup restore procedures','AGENT-423')]:
            self.assertEqual(self.cat.resolve({'objective':text})[0],expected)
    def test_unmatched_task_is_not_forced(self):
        with self.assertRaises(BrainError):self.cat.resolve({'objective':'qzxv wxyk'})
    def test_ambiguous_task_is_not_forced(self):
        self.cat.rank=lambda text:[{'agent_id':'AGENT-031','score':20},{'agent_id':'AGENT-032','score':19}]
        with self.assertRaises(BrainError):self.cat.resolve({'objective':'ambiguous'})
    def test_cycle_rejected(self):
        with self.assertRaises(BrainError):validate_plan(plan(task('a',deps=['b']),task('b',deps=['a'])),self.cat)
    def test_unknown_dependency_rejected(self):
        with self.assertRaises(BrainError):validate_plan(plan(task(deps=['missing'])),self.cat)
    def test_recursive_brain_assignment_rejected(self):
        with self.assertRaises(BrainError):validate_plan(plan(task(aid='AGENT-000')),self.cat)
    def test_missing_binding_blocks(self):
        s=self.run_brain(plan(task()),SubprocessAdapter(self.config));self.assertEqual(s['status'],'blocked')
    def test_missing_verifier_binding_blocks_before_activation(self):
        adapter=SubprocessAdapter(dict(self.config,agent_commands={'AGENT-031':[sys.executable,str(ROOT/'examples/adapter_stub.py')]}))
        s=self.run_brain(plan(task()),adapter)
        self.assertEqual(s['activation_count'],0)
        self.assertIsNone(s['inflight'])
    def test_crash_between_response_and_checkpoint_requires_reconciliation(self):
        p=plan(task());b=Brain(self.cat,Recording(),self.config,True);b.run(p,self.path)
        s=json.loads(self.path.read_text());s['tasks']['a']['status']='running';self.path.write_text(json.dumps(s))
        with self.assertRaises(BrainError):b.run(p,self.path,True)
    def test_denied_agent_never_invoked(self):
        a=Recording();s=self.run_brain(plan(task()),a,dict(self.config,allowed_agents=[]))
        self.assertEqual(s['status'],'blocked');self.assertEqual(a.calls,[])
    def test_denied_capability_never_invoked(self):
        t=task();t['required_capabilities']=['file.write'];a=Recording();s=self.run_brain(plan(t),a)
        self.assertEqual(s['status'],'blocked');self.assertEqual(a.calls,[])
    def test_missing_verifier_permission_blocks_before_mutation(self):
        a=Recording();s=self.run_brain(plan(task()),a,dict(self.config,allowed_agents=['AGENT-031']))
        self.assertEqual(a.calls,[]);self.assertEqual(s['status'],'blocked')
    def test_failure_blocks_dependents(self):
        def fail(e,r):r['status']='failed';return r
        a=Recording(fail);s=self.run_brain(plan(task(),task('b',deps=['a'])),a)
        self.assertEqual(s['tasks']['b']['status'],'blocked');self.assertEqual(len(a.calls),1)
    def test_verification_failure_does_not_replay(self):
        def fail(e,r):
            if e['mode']=='verify':r['verdict']='fail'
            return r
        a=Recording(fail);s=self.run_brain(plan(task(),task('b',deps=['a'])),a)
        self.assertEqual(s['tasks']['a']['status'],'failed');self.assertEqual(len(a.calls),2)
    def test_false_success_rejected(self):
        def empty(e,r):r['evidence']=[];return r
        s=self.run_brain(plan(task()),Recording(empty));self.assertEqual(s['status'],'blocked')
    def test_wrong_agent_response_rejected(self):
        def wrong(e,r):r['agent_id']='AGENT-999';return r
        s=self.run_brain(plan(task()),Recording(wrong));self.assertEqual(s['status'],'blocked')
    def test_resume_completed_work_does_not_reexecute(self):
        a=Recording();p=plan(task());b=Brain(self.cat,a,self.config,True);b.run(p,self.path);b.run(p,self.path,True)
        self.assertEqual(len(a.calls),2)
    def test_resume_changed_plan_rejected(self):
        b=Brain(self.cat,Recording(),self.config,True);b.run(plan(task()),self.path)
        with self.assertRaises(BrainError):b.run(plan(task(objective='changed')),self.path,True)
    def test_interrupted_invocation_not_replayed(self):
        class Crash(Recording):
            def invoke(self,e,t):raise BrainError('uncertain effect')
        b=Brain(self.cat,Crash(),self.config,True);p=plan(task());b.run(p,self.path)
        with self.assertRaises(BrainError):b.run(p,self.path,True)
    def test_unverified_requires_host_opt_in(self):
        t=task();t['verify']=False;a=Recording();self.run_brain(plan(t),a);self.assertEqual(a.calls,[])
    def test_real_subprocess_protocol_and_literal_task_data(self):
        adapter=SubprocessAdapter(dict(self.config,default_command=[sys.executable,str(ROOT/'examples/adapter_stub.py')]))
        s=self.run_brain(plan(task(objective='text $(touch SHOULD_NOT_EXIST)')),adapter)
        self.assertEqual(s['status'],'blocked');self.assertFalse((ROOT/'SHOULD_NOT_EXIST').exists())
    def test_subprocess_timeout(self):
        slow=Path(self.tmp.name)/'slow.py';slow.write_text('import time\ntime.sleep(5)\n')
        adapter=SubprocessAdapter(dict(self.config,default_command=[sys.executable,str(slow)]))
        with self.assertRaises(BrainError):adapter.invoke({'agent_id':'AGENT-031','mode':'execute'},0.05)
    def test_malformed_subprocess_output(self):
        bad=Path(self.tmp.name)/'bad.py';bad.write_text('print("not json")\n')
        adapter=SubprocessAdapter(dict(self.config,default_command=[sys.executable,str(bad)]))
        with self.assertRaises(BrainError):adapter.invoke({'agent_id':'AGENT-031','mode':'execute'},1)
    def test_shell_command_string_rejected(self):
        with self.assertRaises(BrainError):SubprocessAdapter({'default_command':'echo unsafe'})

if __name__=='__main__':unittest.main(verbosity=2)
