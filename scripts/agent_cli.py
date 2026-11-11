#!/usr/bin/env python3
"""Offline agent catalog/export utility. Does not call models or execute tools."""
import argparse
import ast
import hashlib
import json
import os
import re
import time
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'brain'), str(ROOT / 'scripts')]
CODE_SUFFIXES = {'.py', '.js', '.jsx', '.ts', '.tsx', '.go', '.java', '.rb', '.c', '.h', '.cpp', '.hpp'}
MARKER_RE = re.compile(r'\b(TODO|FIXME|HACK|XXX)\b')
LONG_FILE_LINES = 400
LONG_FUNCTION_LINES = 60
DUP_WINDOW = 6
DUP_MIN_LEN = 40  # skip near-empty windows (braces/blank-only)

def catalog():
    return json.loads((ROOT / 'registry/prompt-index.json').read_text(encoding='utf-8'))

def validate():
    rows = catalog()
    original = json.loads((ROOT / 'registry/agents.json').read_text(encoding='utf-8'))
    expected = {a['id']: a for a in original}
    assert len(rows) == len(expected)
    assert len({a['id'] for a in rows}) == len(expected)
    assert {a['id'] for a in rows} == set(expected)
    hashes = set()
    for row in rows:
        aid = row['id']
        assert row['name'] == expected[aid]['name']
        assert row['category'] == expected[aid]['category']
        manifest_path = ROOT / row['manifest_path']
        prompt_path = ROOT / row['system_prompt_path']
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        content = prompt_path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        assert manifest['id'] == aid
        assert (manifest_path.parent / manifest['system_prompt_path']).resolve() == prompt_path.resolve()
        assert digest == manifest['system_prompt_sha256'] == row['system_prompt_sha256']
        text = content.decode()
        for required in [manifest['mission'], manifest['specialist_method'], manifest['verification'][0], '30+ years', 'Response contract']:
            assert required in text, (aid, required)
        assert manifest['tools'] == [], 'Unbound definitions must not pretend to grant tools'
        for skill_path in manifest.get('skill_modules', []):
            assert (ROOT / skill_path).is_file(), (aid, 'missing skill_modules target', skill_path)
        hashes.add(digest)
    assert len(hashes) == len(expected)
    cases = json.loads((ROOT / 'evals/agent-cases.json').read_text(encoding='utf-8'))
    assert len(cases) == len(expected)
    assert {c['agent_id'] for c in cases} == set(expected)
    assert all(len(c['cases']) == 3 and c['execution_status'] == 'not_run' for c in cases)
    return {'status': 'passed', 'agent_count': len(rows), 'unique_prompts': len(hashes),
            'eval_case_specifications': sum(len(c['cases']) for c in cases),
            'behavioral_evaluations_run': 0, 'live_runtime_tests_run': 0}

def _iter_code_files(target):
    if target.is_file():
        yield target
        return
    for path in sorted(target.rglob('*')):
        if path.is_file() and path.suffix in CODE_SUFFIXES and '/.git/' not in str(path):
            yield path

def _todo_markers(path, lines):
    return [{'line': i + 1, 'marker': m.group(1), 'text': line.strip()[:120]}
            for i, line in enumerate(lines) for m in [MARKER_RE.search(line)] if m]

def _long_python_functions(path, source):
    findings = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return findings
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, 'end_lineno', node.lineno)
            length = end - node.lineno + 1
            if length > LONG_FUNCTION_LINES:
                findings.append({'name': node.name, 'start_line': node.lineno, 'lines': length,
                                  'decision': 'SIMPLIFY — split or shorten; review for a single responsibility'})
    return findings

def lean_audit(target_path):
    """Deterministic pre-scan: the mechanical pass a lean-change-discipline review starts from.
    Flags candidates for a human or agent WHAT/WHY/REQUIRED judgment call; it does not itself
    decide KEEP vs DELETE. See skills/lean-change-discipline/SKILL.md and
    brain/LINE-CODE-AUDITOR.md."""
    target = (ROOT / target_path) if not Path(target_path).is_absolute() else Path(target_path)
    if not target.exists():
        raise FileNotFoundError(target_path)
    files_report = []
    window_locations = {}
    for path in _iter_code_files(target):
        try:
            text = path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        lines = text.splitlines()
        rel = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
        markers = _todo_markers(path, lines)
        long_funcs = _long_python_functions(path, text) if path.suffix == '.py' else []
        entry = {'file': rel, 'total_lines': len(lines), 'todo_fixme_markers': markers,
                  'long_functions': long_funcs}
        if len(lines) > LONG_FILE_LINES:
            entry['decision'] = 'SIMPLIFY — file exceeds %d lines; consider splitting by responsibility' % LONG_FILE_LINES
        if markers or long_funcs or len(lines) > LONG_FILE_LINES:
            files_report.append(entry)
        for i in range(0, max(0, len(lines) - DUP_WINDOW + 1)):
            chunk = [l.strip() for l in lines[i:i + DUP_WINDOW]]
            norm = '\n'.join(chunk)
            if len(norm) < DUP_MIN_LEN:
                continue
            key = hashlib.sha256(norm.encode()).hexdigest()
            window_locations.setdefault(key, []).append({'file': rel, 'start_line': i + 1})
    duplicates = [{'locations': locs, 'decision': 'MERGE — identical %d-line block repeated; extract a shared helper' % DUP_WINDOW}
                  for locs in window_locations.values() if len(locs) > 1]
    return {
        'scanned_path': str(target_path),
        'files_flagged': files_report,
        'duplicate_blocks': duplicates,
        'note': 'Mechanical pre-scan only. Apply the WHAT/WHY/REQUIRED judgment pass '
                '(skills/what-why-required/SKILL.md) before acting on any finding.',
    }

def _skills():
    out = {}
    for path in sorted((ROOT / 'skills').glob('*/SKILL.md')):
        text = path.read_text(encoding='utf-8')
        desc = re.search(r'^description: "(.*)"$', text, re.M)
        out[path.parent.name] = {'path': path.relative_to(ROOT).as_posix(), 'description': desc.group(1) if desc else ''}
    return out

def resolve_target(query):
    """Exact agent ID, agent slug, or skill name wins; then name/alias ranking; ambiguity is returned, never guessed."""
    import runtime, claude_code_pack as pack
    cat = runtime.Catalog()
    q = query.strip()
    if q.upper() in cat.rows: return {'kind': 'agent', 'id': q.upper(), 'method': 'exact-id'}
    skills = _skills()
    if q.lower().lstrip('/') in skills: return {'kind': 'skill', 'id': q.lower().lstrip('/'), 'method': 'exact-skill'}
    for aid, row in cat.rows.items():
        if pack.agent_slug({'id': aid, 'name': row['name']}) == q.lower(): return {'kind': 'agent', 'id': aid, 'method': 'exact-slug'}
    try:
        aid, why = cat.resolve({'objective': q})
        return {'kind': 'agent', 'id': aid, 'method': 'ranked-match'}
    except runtime.BrainError as exc:
        return {'kind': 'ambiguous', 'reason': str(exc), 'candidates': cat.rank(q)[:5]}

SESSIONS = ROOT / '.agentic' / 'sessions'
RUNS = ROOT / '.agentic' / 'runs'
PASS_ENV = ['ANTHROPIC_API_KEY', 'ANTHROPIC_MODEL', 'ANTHROPIC_BASE_URL', 'OPENAI_API_KEY', 'LLM_PROVIDER', 'LLM_BASE_URL', 'LLM_MODEL', 'LLM_API_KEY',
            'LLM_PROFILE', 'LLM_CONTEXT', 'LLM_TIMEOUT', 'LLM_COMMAND', 'LLM_SKILL_CHARS', 'SEARCH_URL', 'WEB_ALLOW_PRIVATE', 'HOME']

def _clip(text, n): return text if len(text) <= n else text[:n - 1] + '…'

def _session_brief(turns, limit=1500):
    """The last few exchanges in a few hundred tokens, so a long conversation costs the same each turn and survives a lost context."""
    turns = list(turns)
    while True:
        text = 'Earlier in this session (compact):\n' + '\n'.join('Q%d: %s\nA%d: %s' % (i, t['q'], i, t['a']) for i, t in enumerate(turns, 1))
        if len(text) <= limit or len(turns) <= 1: return _clip(text, limit)
        turns = turns[1:]

def _session_path(name):
    safe = re.sub(r'[^A-Za-z0-9_-]', '_', name)[:60]
    return SESSIONS / (safe + '.json')

def ask(target, message, extra_skills=(), web=False, command=None, env=None, session=None):
    """Call one agent or skill directly through the live adapter and return its answer."""
    import runtime
    hit = resolve_target(target)
    if hit['kind'] == 'ambiguous': return {'status': 'needs_selection', **hit}
    cat = runtime.Catalog()
    skills = {}
    if hit['kind'] == 'agent':
        try:
            aid, system, skills = hit['id'], cat.prompt(hit['id']), cat.skills(hit['id'])
        except runtime.BrainError as exc:
            return {'status': 'blocked', 'reason': str(exc), 'resolved': hit}
        agent = cat.agent_info(hit['id'])
    else:
        agent = None
        aid = 'SKILL:' + hit['id']
        system = 'You are a careful assistant. Apply the skill module below to the request.'
        skills = {_skills()[hit['id']]['path']: (ROOT / _skills()[hit['id']]['path']).read_text(encoding='utf-8')}
    for name in extra_skills:
        if name not in _skills(): return {'status': 'blocked', 'reason': 'Unknown skill: ' + name}
        skills[_skills()[name]['path']] = (ROOT / _skills()[name]['path']).read_text(encoding='utf-8')
    turns = []
    if session:
        path = _session_path(session)
        turns = json.loads(path.read_text(encoding='utf-8')).get('turns', []) if path.exists() else []
    sent = (_session_brief(turns) + '\n\nNow: ' + message) if turns else message
    envelope = {'protocol_version': '1', 'mode': 'ask', 'agent_id': aid, 'system_prompt': system, 'skills': skills,
                'agent': agent, 'message': sent, 'granted_capabilities': ['web_search'] if web else []}
    cmd = command or [sys.executable, str(ROOT / 'examples/llm_adapter.py')]
    proc = subprocess.run(cmd, input=json.dumps(envelope), capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=3600, env={**os.environ, **(env or {})})
    if proc.returncode:
        return {'status': 'blocked', 'reason': (proc.stderr.strip() or 'adapter failed')[:300], 'resolved': hit}
    reply = json.loads(proc.stdout)
    if session:
        turns.append({'q': _clip(message, 300), 'a': _clip(reply.get('text', ''), 500)})
        path = _session_path(session); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'turns': turns[-8:]}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return {'status': 'ok', 'resolved': hit, **reply}

def work(target, message, max_turns=3, verify=False, web=False, env=None, resume=None):
    """Understand, execute and loop on one agent until its result is complete (or turns run out), journaling every step so the work can be
    resumed from what is left. Returns the final text plus where the state, journal and brief are saved."""
    import runtime
    if resume:
        state_path = Path(resume)
        try: side = json.loads(state_path.with_name(state_path.stem + '.plan.json').read_text(encoding='utf-8'))
        except OSError: return {'status': 'blocked', 'reason': 'No saved plan next to ' + str(resume)}
        plan, cfg = side['plan'], side['config']
    else:
        hit = resolve_target(target)
        if hit['kind'] == 'ambiguous': return {'status': 'needs_selection', **hit}
        if hit['kind'] != 'agent': return {'status': 'blocked', 'reason': 'work needs an agent; use ask for a skill'}
        caps = ['web_search'] if web else []
        plan = {'goal': message, 'tasks': [{'id': 't1', 'objective': message, 'agent_id': hit['id'], 'depends_on': [], 'required_capabilities': caps,
                'acceptance_criteria': ['The request is fully answered and checked'], 'verify': verify}]}
        cfg = {'allowed_agents': ['*'], 'granted_capabilities': caps + ['web_fetch', 'crawl_runtime'], 'timeout_seconds': 900, 'verifier_agent_id': 'AGENT-111',
               'allow_unverified': not verify, 'max_iterations': max_turns, 'pass_env': PASS_ENV, 'default_command': ['python3', 'examples/llm_adapter.py']}
        state_path = RUNS / (time.strftime('%Y%m%d-%H%M%S') + '.json'); state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.with_name(state_path.stem + '.plan.json').write_text(json.dumps({'plan': plan, 'config': cfg}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    saved = {k: os.environ.get(k) for k in (env or {})}; os.environ.update(env or {})
    try:
        state = runtime.Brain(runtime.Catalog(), runtime.SubprocessAdapter(cfg), cfg).run(plan, str(state_path), resume=bool(resume))
    except runtime.BrainError as exc:
        return {'status': 'blocked', 'reason': str(exc), 'state': str(state_path)}
    finally:
        for k, v in saved.items(): os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
    entry = state['tasks']['t1']; out = entry.get('output') or {}; usage = state.get('usage') or {}
    return {'status': entry['status'], 'text': out.get('result', ''), 'understood': out.get('understood'), 'left': out.get('next_action'), 'reason': entry.get('reason'),
            'turns': entry.get('attempts', 1), 'tokens': usage.get('in', 0) + usage.get('out', 0), 'state': str(state_path),
            'brief': str(state_path.with_name(state_path.stem + '.brief.md'))}

def check_live(env=None):
    proc = subprocess.run([sys.executable, str(ROOT / 'examples/llm_adapter.py'), '--check'], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=3600, env={**os.environ, **(env or {})})
    return json.loads(proc.stdout)

def _model_env(args):
    pairs = {'LLM_PROVIDER': args.provider, 'LLM_MODEL': args.model, 'LLM_BASE_URL': args.base_url, 'LLM_PROFILE': args.profile}
    return {k: v for k, v in pairs.items() if v}

def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'): stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    ls = subs.add_parser('list')
    ls.add_argument('--category')
    ls.add_argument('--search', default='')
    for name in ('prompt', 'manifest', 'export'):
        p = subs.add_parser(name)
        p.add_argument('agent_id', help='Exact ID, for example AGENT-031')
    subs.add_parser('validate')
    la = subs.add_parser('lean-audit', help='Deterministic lean-change-discipline pre-scan of a file or directory')
    la.add_argument('path', help='File or directory, relative to the repository root or absolute')
    subs.add_parser('skills', help='List skills')
    sh = subs.add_parser('show', help='Show an agent prompt or skill by ID, slug or skill name'); sh.add_argument('target')
    fd = subs.add_parser('find', help='Rank agents for an objective'); fd.add_argument('objective')
    ak = subs.add_parser('ask', help='Call one agent or skill directly through the live model adapter')
    ak.add_argument('target'); ak.add_argument('message')
    ak.add_argument('--skill', action='append', default=[], help='Extra skill to load (repeatable)')
    ak.add_argument('--web', action='store_true', help='Allow live web search')
    ak.add_argument('--session', help='Keep a compact record of this conversation under .agentic/sessions and use it next time')
    wk = subs.add_parser('work', help='Understand, execute and loop on one agent until done; journals every step and can resume')
    wk.add_argument('target', nargs='?'); wk.add_argument('message', nargs='?'); wk.add_argument('--turns', type=int, default=3); wk.add_argument('--verify', action='store_true', help='Add an independent verification pass')
    wk.add_argument('--web', action='store_true'); wk.add_argument('--resume', help='Continue a saved run from its state file')
    jn = subs.add_parser('journal', help='Print the resume brief saved next to a run state file'); jn.add_argument('state')
    cl = subs.add_parser('check-live', help='Smoke-test the model connection (any provider)')
    for sp in (ak, cl, wk):
        sp.add_argument('--provider', help='anthropic|openai|ollama|lmstudio|llamacpp|vllm|command')
        sp.add_argument('--model'); sp.add_argument('--base-url'); sp.add_argument('--profile', choices=['auto', 'full', 'compact', 'tiny'])
    subs.add_parser('build-claude-code', help='Regenerate .claude/agents and .claude/skills')
    subs.add_parser('check-claude-code', help='Verify the .claude pack is complete and in sync')
    ic = subs.add_parser('install-claude-code', help='Copy the pack into a project or user .claude folder')
    ic.add_argument('--scope', choices=['project', 'user'], default='project'); ic.add_argument('--dest'); ic.add_argument('--force', action='store_true')
    args = parser.parse_args()
    if args.command == 'skills':
        print(json.dumps(_skills(), indent=2)); return
    if args.command == 'show':
        hit = resolve_target(args.target)
        if hit['kind'] == 'agent': print((ROOT / [r for r in catalog() if r['id'] == hit['id']][0]['system_prompt_path']).read_text(encoding='utf-8'))
        elif hit['kind'] == 'skill': print((ROOT / _skills()[hit['id']]['path']).read_text(encoding='utf-8'))
        else: print(json.dumps(hit, indent=2))
        return
    if args.command == 'find':
        import runtime
        print(json.dumps(runtime.Catalog().rank(args.objective)[:8], indent=2)); return
    if args.command == 'ask':
        out = ask(args.target, args.message, args.skill, args.web, env=_model_env(args), session=args.session)
        print(out.get('text') if out.get('status') == 'ok' else json.dumps(out, indent=2))
        if out.get('status') == 'ok' and out.get('sources'): print('\nSources:\n' + '\n'.join(out['sources']))
        for note in out.get('notes', []) if out.get('status') == 'ok' else []: print('note: ' + note, file=sys.stderr)
        sys.exit(0 if out.get('status') == 'ok' else 2)
    if args.command == 'journal':
        brief = Path(args.state).with_name(Path(args.state).stem + '.brief.md')
        print(brief.read_text(encoding='utf-8') if brief.exists() else json.dumps({'status': 'blocked', 'reason': 'No brief found next to ' + args.state})); sys.exit(0 if brief.exists() else 2)
    if args.command == 'work':
        if not args.resume and not (args.target and args.message): parser.error('work needs a target and a message, or --resume STATE')
        out = work(args.target, args.message, args.turns, args.verify, args.web, env=_model_env(args), resume=args.resume)
        if out.get('status') == 'completed':
            print(out['text'])
            print('[completed · %d turn(s) · ~%d tokens · saved: %s]' % (out['turns'], out['tokens'], out['brief']), file=sys.stderr); sys.exit(0)
        print(json.dumps(out, indent=2, ensure_ascii=False)); sys.exit(2)
    if args.command == 'check-live':
        out = check_live(_model_env(args)); print(json.dumps(out)); sys.exit(0 if out['status'] == 'connected' else 2)
    if args.command in ('build-claude-code', 'check-claude-code', 'install-claude-code'):
        import claude_code_pack as pack
        out = {'build-claude-code': pack.build, 'check-claude-code': pack.check}.get(args.command, lambda: pack.install(args.scope, args.dest, args.force))()
        print(json.dumps(out, indent=2)); sys.exit(0 if out.get('status') != 'failed' else 2)
    if args.command == 'validate':
        print(json.dumps(validate(), indent=2))
        return
    if args.command == 'lean-audit':
        try:
            print(json.dumps(lean_audit(args.path), indent=2))
        except FileNotFoundError:
            print(json.dumps({'status': 'blocked', 'reason': 'Path not found: ' + args.path})); sys.exit(2)
        return
    rows = catalog()
    if args.command == 'list':
        for row in rows:
            if args.category and args.category != row['category']:
                continue
            if args.search.lower() not in (row['name'] + ' ' + row['mission']).lower():
                continue
            print(f"{row['id']}\t{row['category']}\t{row['name']}")
        return
    row = next((a for a in rows if a['id'] == args.agent_id), None)
    if row is None:
        parser.error('Unknown agent ID; use list to find an exact ID.')
    if args.command == 'manifest':
        print((ROOT / row['manifest_path']).read_text(encoding='utf-8'), end='')
    else:
        prompt = (ROOT / row['system_prompt_path']).read_text(encoding='utf-8')
        if args.command == 'prompt':
            print(prompt, end='')
        else:
            print(json.dumps({'agent_id': row['id'], 'system_prompt': prompt,
                              'tools': [], 'runtime_binding': 'required'}, indent=2))

if __name__ == '__main__':
    try:
        main()
    except BrokenPipeError:  # output piped to a program that closed early, such as head
        sys.stderr.close(); sys.exit(0)
