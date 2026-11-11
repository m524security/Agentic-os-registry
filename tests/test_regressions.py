"""Regression tests for defects found in the bug hunt. Each test names the defect it guards."""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'brain'), str(ROOT / 'tests'), str(ROOT / 'examples')]
import agent_cli, claude_code_pack, runtime  # noqa: E402
from test_adapter import Local, serve, run_adapter, envelope, BEHAVIOR, CALLS  # noqa: E402

class Regressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.server, cls.url = serve(Local)
    @classmethod
    def tearDownClass(cls): cls.server.shutdown(); cls.server.server_close()
    def setUp(self): BEHAVIOR.update(mode='good', n=0); CALLS.clear()

    def test_install_into_the_registry_itself_does_not_crash(self):
        out = claude_code_pack.install('project', str(ROOT))
        self.assertEqual(out['files_copied'], 0)

    def test_build_keeps_unrelated_files_in_dest(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'settings.local.json').write_text('{}'); claude_code_pack.build(d)
            self.assertTrue((Path(d) / 'settings.local.json').exists())

    def test_mcp_only_on_browser_agents(self):
        for f in (ROOT / '.claude/agents').rglob('*.md'):
            text = f.read_text(encoding='utf-8')
            if 'mcpServers:' in text: self.assertIn('browser-automation', text, f.name)
        self.assertNotIn('@latest', (ROOT / 'scripts/claude_code_pack.py').read_text(encoding='utf-8'))

    def test_adapters_are_version_pinned(self):
        for f in (ROOT / 'browser/adapters').glob('*.json'): self.assertNotIn('@latest', f.read_text(encoding='utf-8'), f.name)

    def test_commands_resolve_from_any_directory(self):
        here = os.getcwd(); self.addCleanup(os.chdir, here)
        with tempfile.TemporaryDirectory() as elsewhere:
            os.chdir(elsewhere); cmd = runtime.resolve_command(['python3', 'examples/llm_adapter.py'])
        self.assertEqual(cmd[0], sys.executable); self.assertTrue(os.path.isabs(cmd[1]) and os.path.isfile(cmd[1]))
        with tempfile.TemporaryDirectory() as d:
            p = subprocess.run([sys.executable, str(ROOT / 'brain/runtime.py'), 'plan', 'Review accessibility', '--config', str(ROOT / 'examples/runtime-config.live.json'),
                                '--out', str(Path(d) / 'p.json')], cwd=d, capture_output=True, text=True,
                               env={**os.environ, 'LLM_PROVIDER': 'lmstudio', 'LLM_BASE_URL': self.url + '/v1', 'LLM_MODEL': 'x:2b'}, timeout=60)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_non_ascii_survives_a_non_utf8_locale(self):
        with tempfile.TemporaryDirectory() as d:
            script = Path(d) / 'm.py'
            script.write_text('import json,sys\nsys.stdout.buffer.write(json.dumps({"status":"completed","result":"caf\\u00e9 \\u2014 \\u2713","evidence":["x"]},ensure_ascii=False).encode("utf-8"))\n', encoding='utf-8')
            p = run_adapter(envelope(), LLM_PROVIDER='command', LLM_COMMAND=json.dumps([sys.executable, str(script)]), LC_ALL='C', PYTHONUTF8='0')
        self.assertEqual(json.loads(p.stdout)['result'], 'caf\u00e9 \u2014 \u2713')

    def test_several_installed_models_are_not_guessed(self):
        BEHAVIOR['mode'] = 'multi_models'
        out = json.loads(run_adapter(envelope(), LLM_PROVIDER='ollama', LLM_BASE_URL=self.url).stdout)
        self.assertIn('missing_model', out['result']); self.assertIn('llama3:8b', out['limitations'][0])
        self.assertEqual([c for c in CALLS if c[0] == '/api/chat'], [])

    def test_embedding_models_are_skipped_when_detecting(self):
        out = json.loads(run_adapter(envelope(), LLM_PROVIDER='ollama', LLM_BASE_URL=self.url).stdout)
        self.assertEqual((out['status'], CALLS[-1][1]['model']), ('completed', 'gemma2:2b'))

    def test_slow_server_is_reported_as_timeout_not_network_error(self):
        BEHAVIOR['mode'] = 'slow'
        out = json.loads(run_adapter(envelope(), LLM_PROVIDER='lmstudio', LLM_BASE_URL=self.url + '/v1', LLM_MODEL='m', LLM_TIMEOUT='1').stdout)
        self.assertIn('timeout', out['result']); self.assertIn('LLM_TIMEOUT', out['limitations'][0])

    def test_hosted_openai_without_key_fails_before_any_request(self):
        out = json.loads(run_adapter(envelope(), LLM_PROVIDER='openai').stdout)
        self.assertIn('missing_key', out['result'])

    def test_ask_with_web_but_no_search_backend_says_so(self):
        out = agent_cli.ask('web-research', 'latest node', web=True, env={'LLM_PROVIDER': 'lmstudio', 'LLM_BASE_URL': self.url + '/v1', 'LLM_MODEL': 'x:2b'})
        self.assertEqual(out['status'], 'ok'); self.assertTrue(any('SEARCH_URL' in n for n in out['notes']))

    def test_bad_inputs_fail_cleanly_without_tracebacks(self):
        d = tempfile.mkdtemp()
        for args in (['scripts/agent_cli.py', 'lean-audit', 'nonexistent'], ['scripts/agent_cli.py', 'install-claude-code', '--dest', '/proc/nope/x'],
                     ['brain/runtime.py', 'run', '--plan', d + '/missing.json', '--config', 'examples/runtime-config.json', '--state', d + '/s.json']):
            p = subprocess.run([sys.executable, str(ROOT / args[0])] + args[1:], cwd=ROOT, capture_output=True, text=True, timeout=60)
            self.assertNotIn('Traceback', p.stderr, args); self.assertEqual(p.returncode, 2, args)

    def test_malformed_adapter_requests_fail_with_a_named_error_not_a_traceback(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith(('LLM_', 'ANTHROPIC', 'OPENAI'))}; env.update(LLM_PROVIDER='command', LLM_COMMAND='["true"]')
        for text in ['', 'not json', '[]', 'null', '{}', '{"mode":"execute"}', '{"mode":"nope","agent_id":"A"}', '{"mode":"execute","agent_id":"A","task":5}',
                     '{"mode":"execute","agent_id":"A","task":{},"granted_capabilities":"web_fetch"}', '{"mode":"ask","agent_id":"A"}', '{"mode":"plan","agent_id":"A","goal":5}']:
            p = subprocess.run([sys.executable, str(ROOT / 'examples/llm_adapter.py')], input=text, capture_output=True, text=True, env=env, timeout=60)
            self.assertNotIn('Traceback', p.stderr, text); self.assertIn('bad_request', p.stdout, text)

    def test_a_closed_pipe_does_not_print_a_traceback(self):
        for args in (['scripts/agent_cli.py', 'list'], ['brain/runtime.py', 'route', 'review accessibility']):
            p = subprocess.Popen([sys.executable, str(ROOT / args[0])] + args[1:], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=ROOT)
            p.stdout.read(10); p.stdout.close(); err = p.stderr.read().decode(); p.wait(); self.assertNotIn('Traceback', err)

    def test_every_manifest_and_adapter_file_reads_as_utf8(self):
        for f in list(ROOT.rglob('*.md')) + list(ROOT.rglob('*.json')):
            if '__pycache__' in f.parts: continue
            f.read_text(encoding='utf-8')

class DeclaredSkills(unittest.TestCase):
    """A declared skill module that is unavailable must stop the run before the agent is called."""
    def copy_tree(self):
        import shutil
        d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, d, True)
        for part in ('registry', 'agents', 'skills'): shutil.copytree(ROOT / part, d / part)
        return d

    def run_with(self, root):
        calls = []
        class Spy:
            def invoke(self, envelope, timeout): calls.append(envelope); raise AssertionError('adapter must not be called')
        cfg = {'allowed_agents': ['*'], 'granted_capabilities': [], 'timeout_seconds': 5, 'verifier_agent_id': 'AGENT-111'}
        plan = {'goal': 'g', 'tasks': [{'id': 't1', 'objective': 'write docs', 'agent_id': 'AGENT-420', 'depends_on': [], 'acceptance_criteria': ['done'], 'required_capabilities': [], 'verify': True}]}
        state = runtime.Brain(runtime.Catalog(root), Spy(), cfg).run(plan, str(root / 's.json'))
        return state, calls

    def test_missing_skill_file_blocks_the_task_before_any_call(self):
        root = self.copy_tree(); (root / 'skills/what-why-required/SKILL.md').unlink() if False else None
        manifest = next((root / 'agents').glob('*/AGENT-420/manifest.json')); m = json.loads(manifest.read_text(encoding='utf-8'))
        missing = m['skill_modules'][-1]; (root / missing).unlink()
        state, calls = self.run_with(root)
        self.assertEqual(calls, []); self.assertEqual(state['status'], 'blocked'); self.assertIn('missing', state['tasks']['t1']['reason'])
        self.assertIn(missing, state['tasks']['t1']['reason'])
        self.assertEqual((state['activation_count'], state['inflight']), (0, None))  # not misreported as an interrupted call

    def test_empty_or_escaping_skill_paths_are_rejected(self):
        root = self.copy_tree(); cat = runtime.Catalog(root)
        manifest = next((root / 'agents').glob('*/AGENT-420/manifest.json')); m = json.loads(manifest.read_text(encoding='utf-8'))
        (root / m['skill_modules'][0]).write_text('  \n')
        with self.assertRaises(runtime.BrainError): cat.skills('AGENT-420')
        m['skill_modules'] = ['../outside.md']; manifest.write_text(json.dumps(m), encoding='utf-8')
        with self.assertRaises(runtime.BrainError): cat.skills('AGENT-420')

    def test_agent_cli_ask_reports_a_missing_skill_instead_of_continuing(self):
        out = agent_cli.ask('AGENT-420', 'x', extra_skills=['no-such-skill'], env={'LLM_PROVIDER': 'command', 'LLM_COMMAND': '["true"]'})
        self.assertEqual(out['status'], 'blocked'); self.assertIn('no-such-skill', out['reason'])

if __name__ == '__main__':
    unittest.main()
