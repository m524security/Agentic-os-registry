import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(root, *args):
    return subprocess.run([sys.executable, str(Path(root) / args[0])] + list(args[1:]), cwd=root, capture_output=True, text=True, timeout=300)

class Catalog(unittest.TestCase):
    def test_nothing_derived_is_out_of_date(self):
        p = run(ROOT, 'scripts/build_all.py', '--check'); self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_readme_and_directory_list_every_agent_with_what_it_does(self):
        readme = (ROOT / 'README.md').read_text(encoding='utf-8'); doc = (ROOT / 'docs/AGENTS.md').read_text(encoding='utf-8')
        for f in (ROOT / 'agents').glob('*/AGENT-*/manifest.json'):
            m = json.loads(f.read_text(encoding='utf-8'))
            self.assertIn('| %s | %s | ' % (m['id'], m['name']), readme, m['id'])
            self.assertIn(m['specialist_focus'].replace('|', '/'), doc, m['id'])
        self.assertFalse('\nplaceholder\n' in readme)

    def test_registry_files_agree_with_manifests(self):
        agents = json.loads((ROOT / 'registry/agents.json').read_text(encoding='utf-8'))
        for a in agents:
            m = json.loads(next((ROOT / 'agents').glob('*/%s/manifest.json' % a['id'])).read_text(encoding='utf-8'))
            self.assertEqual((a['name'], a['purpose'], a['status']), (m['name'], m['mission'], m['status']))
            self.assertNotIn('Loaded or instantiated only when', a['purpose'])

class AddAgent(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / 'repo'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('__pycache__', '.git'))
        self.spec = {'id': 'AGENT-435', 'name': 'Release Notes Agent', 'category': 'software-engineering', 'group': 'Software Engineering / Dev',
                     'mission': 'Write accurate release notes from merged changes', 'method': 'Group merged changes by user impact and verify each entry against its change',
                     'gate': 'Every note maps to a merged change and no merged user-facing change is missing',
                     'focus': 'Release notes: lead with user impact, link each entry to its change, put breaking changes and migrations first and never describe unverified behavior.',
                     'capabilities': ['repository_read', 'scoped_file_edit'], 'skills': ['clear-communication'], 'aliases': ['release notes', 'changelog']}

    def add(self, spec):
        path = self.tmp / 'spec.json'; path.write_text(json.dumps(spec), encoding='utf-8'); return run(self.root, 'scripts/add_agent.py', str(path))

    def test_a_new_agent_is_fully_integrated(self):
        p = self.add(self.spec); self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertTrue((self.root / 'agents/software-engineering/AGENT-435/system-prompt.md').is_file())
        self.assertIn('| AGENT-435 | Release Notes Agent |', (self.root / 'README.md').read_text(encoding='utf-8'))
        self.assertTrue(list((self.root / '.claude/agents').rglob('agent-435-*.md')))
        self.assertEqual(run(self.root, 'scripts/build_all.py', '--check').returncode, 0)
        self.assertEqual(run(self.root, 'scripts/agent_cli.py', 'validate').returncode, 0)
        prompt = (self.root / 'agents/software-engineering/AGENT-435/system-prompt.md').read_text(encoding='utf-8')
        self.assertIn(self.spec['focus'], prompt); self.assertIn('What a master of this field knows', prompt)

    def test_bad_specs_are_rejected_without_changing_anything(self):
        before = (self.root / 'registry/agents.json').read_bytes()
        for change in ({'id': 'AGENT-027'}, {'skills': ['no-such-skill']}, {'group': 'Nope'}, {'focus': 'too short.'}, {'name': 'Coding Agent'}, {'id': 'X-1'}):
            p = self.add({**self.spec, **change}); self.assertEqual(p.returncode, 2, change)
        self.assertEqual((self.root / 'registry/agents.json').read_bytes(), before)
        self.assertFalse((self.root / 'agents/software-engineering/AGENT-435').exists())

if __name__ == '__main__':
    unittest.main()
