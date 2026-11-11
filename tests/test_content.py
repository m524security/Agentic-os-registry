"""Checks on the written content of every prompt, expertise pack and skill."""
import json, re, subprocess, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ['Identity and expertise standard', 'How you work', 'Task intake', 'Tools, authority and information handling', 'Response contract', 'Your role and mission',
            'Specialization focus', 'Field expertise', 'Specialist operating procedure', 'Required completion evidence']

def manifests():
    for f in sorted((ROOT / 'agents').glob('*/AGENT-*/manifest.json')):
        yield f, json.loads(f.read_text(encoding='utf-8'))

class Prompts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exp = json.loads((ROOT / 'registry/expertise.json').read_text(encoding='utf-8'))

    def test_every_prompt_has_the_full_structure_in_order(self):
        for f, m in manifests():
            text = (f.parent / 'system-prompt.md').read_text(encoding='utf-8')
            heads = re.findall(r'^## (.+)$', text, re.M)
            expected = SECTIONS + (['Executive activation protocol'] if m['id'] == 'AGENT-000' else [])
            self.assertEqual(heads, expected, m['id'])

    def test_every_prompt_carries_its_own_focus_and_its_groups_expertise(self):
        for f, m in manifests():
            text = (f.parent / 'system-prompt.md').read_text(encoding='utf-8'); pack = self.exp['groups'][m['group']]
            self.assertIn(self.exp['agents'][m['id']], text, m['id'])
            for bullet in pack['know'] + pack['method'] + pack['pitfalls'] + pack['done']: self.assertIn(bullet, text, m['id'])
            self.assertEqual(m['specialist_focus'], self.exp['agents'][m['id']]); self.assertEqual(m['field_rules'], pack['rules'])

    def test_prompts_have_no_template_debris_and_sensible_size(self):
        for f, m in manifests():
            text = (f.parent / 'system-prompt.md').read_text(encoding='utf-8')
            self.assertTrue(4500 < len(text) < 12000, (m['id'], len(text)))
            for debris in ('{', '}', 'TODO', 'TBD', 'lorem', 'None', 'undefined'):
                if debris in ('{', '}') and m['id'] == 'AGENT-000': continue  # the brain prompt shows a JSON shape
                self.assertNotIn(debris, text, (m['id'], debris))
            self.assertNotRegex(text, r'\S  +\S', m['id'])
            self.assertIn('You are %s (' % m['id'], text); self.assertTrue(text.startswith('# Operating standard'))

    def test_prompts_match_the_generator_exactly(self):
        out = subprocess.run([sys.executable, str(ROOT / 'scripts/build_prompts.py'), '--check'], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout)

    def test_focus_lines_are_specific_and_unique(self):
        focus = self.exp['agents']; self.assertEqual(len(focus), len(set(focus.values())))
        for aid, text in focus.items():
            self.assertTrue(60 <= len(text) <= 340 and text.endswith('.'), (aid, len(text)))

    def test_expertise_packs_are_complete_and_cover_every_group(self):
        groups = {json.loads(l)['group'] if False else None for l in []}
        agents = json.loads((ROOT / 'registry/agents.json').read_text(encoding='utf-8'))
        self.assertEqual({a['group'] for a in agents}, set(self.exp['groups']))
        for name, pack in self.exp['groups'].items():
            self.assertEqual([len(pack[k]) for k in ('know', 'method', 'pitfalls', 'rules')], [3, 3, 3, 3], name)
            self.assertGreaterEqual(len(pack['done']), 1, name); self.assertGreater(len(pack['keywords'].split()), 5, name)

class Skills(unittest.TestCase):
    def test_every_skill_is_well_formed(self):
        for f in sorted((ROOT / 'skills').glob('*/SKILL.md')):
            text = f.read_text(encoding='utf-8'); m = re.match(r'^---\nname: (.+)\ndescription: "(.+)"\n---\n', text)
            self.assertIsNotNone(m, f); self.assertEqual(m.group(1), f.parent.name); self.assertTrue(40 <= len(m.group(2)) <= 300, f)
            for h in ('## When to apply', '## How to apply', '## Output expectation'): self.assertIn(h, text, f)
            self.assertTrue(700 < len(text) < 6500, (f, len(text))); self.assertNotRegex(text, r'TODO|TBD|lorem')

    def test_no_skill_is_orphaned_and_every_reference_resolves(self):
        used = set()
        for f, m in manifests():
            mods = m['skill_modules']; self.assertEqual(len(mods), len(set(mods)), m['id'])
            for rel in mods: self.assertTrue((ROOT / rel).is_file(), (m['id'], rel)); used.add(rel)
        every = {str(p.relative_to(ROOT)) for p in (ROOT / 'skills').glob('*/SKILL.md')}
        self.assertEqual(every - used, set())

if __name__ == '__main__':
    unittest.main()

class SharedPrefix(unittest.TestCase):
    def test_every_prompt_starts_with_the_identical_shared_rules(self):
        shared = None
        for f, m in manifests():
            text = (f.parent / 'system-prompt.md').read_text(encoding='utf-8'); prefix = text[:text.index('\n# AGENT-')]
            shared = shared or prefix; self.assertEqual(prefix, shared, m['id'])
        self.assertGreater(len(shared), 2000)
