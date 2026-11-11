"""Build, check and install the Claude Code pack (.claude/agents and .claude/skills) from the registry.
The registry (agents/, skills/) is the single source; .claude/ is generated and verified for drift."""
import filecmp, json, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWN_TOOLS = {'Read', 'Grep', 'Glob', 'Edit', 'Write', 'Bash', 'WebFetch', 'WebSearch', 'NotebookEdit', 'TodoWrite'}
CAP_TOOLS = {
    'Read': ['repository_read', 'document_read', 'evidence_read', 'registry_read', 'task_state_read', 'memory_read', 'source_read',
             'artifact_inspection', 'metrics_read', 'environment_inspect', 'host_inspect', 'system_metrics', 'authorized_data_read',
             'authorized_security_data_read'],
    'Edit': ['scoped_file_edit', 'task_state_write', 'authorized_memory_write'],
    'Write': ['scoped_file_edit', 'task_state_write', 'authorized_memory_write'],
    'Bash': ['test_runner', 'verification_runner', 'evaluation_runner', 'analysis_runtime', 'query_runtime', 'isolated_analysis',
             'scoped_assessment_tools', 'scoped_operations', 'authorized_shell', 'authorized_restore', 'crawl_runtime',
             'model_api_access', 'tool_call_audit'],
    'WebSearch': ['source_search', 'web_search'],
    'WebFetch': ['source_search', 'web_fetch'],
}
MCP = {'playwright': {'type': 'stdio', 'command': 'npx', 'args': ['-y', '@playwright/mcp@0.0.83', '--browser=chrome']}}

def slug(text, limit):
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', text.lower())).strip('-')[:limit].strip('-')

def agent_slug(m):
    return m['id'].lower() + '-' + slug(m['name'], 50)

def tools_for(m):
    if m.get('claude_code_tools'):
        return list(m['claude_code_tools'])
    caps = set(m.get('suggested_capabilities', []))
    out = [t for t, wanted in CAP_TOOLS.items() if caps & set(wanted)]
    if 'Read' in out: out += ['Grep', 'Glob']
    return sorted(set(out), key=['Read', 'Grep', 'Glob', 'Edit', 'Write', 'Bash', 'WebFetch', 'WebSearch'].index)

def render_agent(m, prompt):
    every = [Path(p).parent.name for p in m.get('skill_modules', [])]
    # Preloading costs tokens on every start: load the baseline plus the two most specific skills; the rest stay one command away.
    skills, spare = (every, []) if len(every) <= 3 else ([every[0]] + every[-2:], every[1:-2])
    desc = '%s %s: %s' % (m['id'], m['name'], m['mission'])
    desc = desc.replace('"', "'")
    fm = ['---', 'name: ' + agent_slug(m), 'description: "%s"' % desc]
    mcp = m.get('claude_code_mcp')
    if mcp:  # MCP tools must stay available, so inherit tools and deny file writes instead of listing.
        fm += ['disallowedTools: Edit, Write', 'mcpServers:', '  - %s:' % mcp]
        for k, v in MCP[mcp].items():
            fm.append('      %s: %s' % (k, json.dumps(v)))
    else:
        fm.append('tools: ' + ', '.join(tools_for(m)))
    if skills: fm.append('skills:\n' + '\n'.join('  - ' + s for s in skills))
    fm.append('---')
    verification = '\n'.join('- ' + v for v in m['verification'])
    bind = ('\n\n## Registry binding\nAgent ID: %s. Category: %s. Granted tools are limited to the allowlist above; anything else is unavailable, '
            'so report a blocker instead of improvising.\nCompletion gates:\n%s\n' % (m['id'], m['category'], verification))
    if spare: bind += 'Other skills you may ask the main session to load: %s.\n' % ', '.join(spare)
    bind += 'If another specialist should continue, end with "Handoff: <agent slug> - <objective>"; the main session will delegate.\n'
    return '\n'.join(fm) + '\n\n' + prompt.rstrip() + bind

def build(dest=None):
    dest = Path(dest or ROOT / '.claude')
    for part in ('agents', 'skills'):  # leave other files in .claude (settings, commands) untouched
        if (dest / part).exists(): shutil.rmtree(dest / part)
    count = 0
    for mf in sorted((ROOT / 'agents').glob('*/AGENT-*/manifest.json')):
        m = json.loads(mf.read_text(encoding='utf-8'))
        out = dest / 'agents' / m['category'] / (agent_slug(m) + '.md')
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_agent(m, (mf.parent / m['system_prompt_path']).read_text(encoding='utf-8')), encoding='utf-8')
        count += 1
    skills = 0
    for sk in sorted((ROOT / 'skills').glob('*/SKILL.md')):
        (dest / 'skills' / sk.parent.name).mkdir(parents=True, exist_ok=True)
        shutil.copy(sk, dest / 'skills' / sk.parent.name / 'SKILL.md'); skills += 1
    return {'agents': count, 'skills': skills, 'path': str(dest)}

def parse_front(text):
    assert text.startswith('---\n'), 'no front matter'
    head = text.split('\n---\n', 1)[0].splitlines()[1:]
    return head

def check():
    """Verify .claude/ exists, is in sync with a fresh build, and every file is well formed."""
    import tempfile
    pack = ROOT / '.claude'
    problems = []
    with tempfile.TemporaryDirectory() as t:
        build(t)
        cmp = filecmp.dircmp(t, pack)
        def walk(c, rel=''):
            for n in c.left_only: problems.append('missing in .claude: ' + rel + n)
            for n in c.right_only: problems.append('stale in .claude: ' + rel + n)
            for n in c.diff_files: problems.append('out of date: ' + rel + n)
            for n, sub in c.subdirs.items(): walk(sub, rel + n + '/')
        walk(cmp)
    names = set()
    skills = {p.parent.name for p in (pack / 'skills').glob('*/SKILL.md')}
    agents = list((pack / 'agents').rglob('*.md'))
    for f in agents:
        head = parse_front(f.read_text(encoding='utf-8'))
        kv = {l.split(':', 1)[0]: l.split(':', 1)[1].strip() for l in head if re.match(r'^[A-Za-z]+:', l)}
        name = kv.get('name', '')
        if not re.fullmatch(r'[a-z0-9-]{1,64}', name) or name in names: problems.append('bad or duplicate name: ' + f.name)
        names.add(name)
        if not kv.get('description'): problems.append('no description: ' + f.name)
        if 'tools' in kv:
            bad = [x.strip() for x in kv['tools'].split(',') if x.strip() not in KNOWN_TOOLS]
            if bad: problems.append('unknown tools %s in %s' % (bad, f.name))
        for l in head:
            if l.startswith('  - ') and l[4:].strip() not in skills and not l.strip().startswith('- playwright'):
                if l[4:].strip() != 'playwright:': problems.append('unknown skill %s in %s' % (l[4:].strip(), f.name))
    for f in agents:
        text = f.read_text(encoding='utf-8')
        if 'mcpServers:' in text and '  - browser-automation' not in text: problems.append('MCP server on a non-browser agent: ' + f.name)
    desc_tokens = sum(len(f.read_text(encoding='utf-8').split('\ndescription: ', 1)[1].split('\n', 1)[0]) for f in agents) // 4
    return {'status': 'passed' if not problems else 'failed', 'agents': len(agents), 'skills': len(skills),
            'approx_description_tokens': desc_tokens, 'problems': problems[:20]}

def install(scope='project', dest=None, force=False):
    base = Path(dest).expanduser() / '.claude' if dest else (Path.home() / '.claude' if scope == 'user' else Path.cwd() / '.claude')
    src = ROOT / '.claude'
    if base.resolve() == src.resolve():
        return {'installed_to': str(base), 'files_copied': 0, 'skipped_count': 0, 'note': 'Destination is the registry itself; the pack is already in place.'}
    copied, skipped = 0, []
    for f in sorted(src.rglob('*')):
        if not f.is_file(): continue
        target = base / f.relative_to(src)
        if target.exists() and not filecmp.cmp(f, target, shallow=False) and not force:
            skipped.append(str(target)); continue
        try:
            target.parent.mkdir(parents=True, exist_ok=True); shutil.copy(f, target); copied += 1
        except OSError as exc:
            return {'status': 'failed', 'reason': 'Cannot write to %s: %s' % (base, exc.strerror or exc), 'files_copied': copied}
    return {'installed_to': str(base), 'files_copied': copied, 'skipped_existing_different': skipped[:10], 'skipped_count': len(skipped)}
