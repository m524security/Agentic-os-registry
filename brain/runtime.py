#!/usr/bin/env python3
"""Provider-neutral, on-demand agent controller. Python standard library only."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
TERMINAL = {'completed', 'failed', 'blocked'}
STOP = set(('a an the to of and or for in on with this that is are be as by from my our please agent task create make build help '
            'me we us you your it its i he she they them what which who whom how why when where there here do does did can could will would should shall may might must '
            'have has had been being was were am about above after again all also any at before between both but down during each few into just more most no nor not now '
            'off once only other out over own same so some such than then these those through too under until up very while today tell want need like get got use using').split())

def stem(word):
    """Light suffix stripping so 'queries', 'optimizing' and 'optimization' meet their root; applied to queries and catalog alike."""
    for suffix, replacement in (('ization', 'ize'), ('isation', 'ise'), ('ies', 'y'), ('ing', ''), ('ed', ''), ('es', ''), ('s', '')):
        if len(word) > len(suffix) + 2 and word.endswith(suffix) and not (suffix == 's' and word.endswith('ss')):
            word = word[:-len(suffix)] + replacement
            break
    return word[:-1] if len(word) > 4 and word.endswith('e') else word

def tokens(text):
    return {stem(w) for w in re.findall(r'[a-z0-9]+', text.lower()) if w not in STOP}

def alias_hit(phrase, query, flat_stems):
    """An alias fires on the contiguous phrase, or on all its words when it has at least two meaningful words.
    One-word aliases must be the word itself, so generic verbs never pull a query toward the wrong agent."""
    words = re.findall(r'[a-z0-9]+', phrase.lower())
    if ' %s ' % ' '.join(stem(w) for w in words) in flat_stems: return True
    if phrase.startswith('='): return False  # '=' marks an exact-phrase alias
    meaningful = tokens(phrase)
    return len(meaningful) >= 2 and meaningful <= query

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def atomic_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)

TUNABLE = {'timeout_seconds', 'max_iterations', 'context_chars', 'context_total_chars'}  # may change between a stop and a resume

def atomic_text(path, text):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp'); tmp.write_text(text, encoding='utf-8'); tmp.replace(path)

def build_journal(state, goal, tasks):
    """A compact, deterministic record of a run: what was asked, what each agent answered, what is required, what is left and where it
    got stuck. Built from the run state at no model cost, so a stopped run can be continued from this alone."""
    done, left, stuck, required = [], [], [], []
    for t in tasks:
        e = state['tasks'][t['id']]; out = e.get('output') or {}
        base = {'task': t['id'], 'agent': e.get('agent_id') or t.get('agent_id'), 'objective': clip(t['objective'], 160)}
        if e['status'] == 'completed':
            done.append(dict(base, result=clip(out.get('result', ''), 160), understood=clip(out.get('understood', ''), 120) or None))
            continue
        left.append(dict(base, status=e['status'], next=clip(out.get('next_action') or '', 160) or None))
        required += ['%s: %s' % (t['id'], clip(c, 120)) for c in t['acceptance_criteria'][:3]]
        if e['status'] in ('blocked', 'failed'):
            stuck.append(dict(base, status=e['status'], why=clip(e.get('reason', ''), 200), attempts=e.get('attempts')))
    return {'version': 1, 'asked': clip(goal, 400), 'done': done, 'left': left, 'stuck': stuck, 'required': required[:12],
            'facts': {k: v['value'] for k, v in list(state.get('blackboard', {}).items())[-12:]}, 'usage': state.get('usage'), 'status': state.get('status')}

def render_brief(journal, limit=1800):
    """Plain text another model can read to continue the work. Older finished items are dropped first when space is short."""
    def build(done):
        lines = ['ASKED: ' + journal['asked']]
        if done: lines.append('DONE: ' + '; '.join('%s (%s): %s' % (d['task'], d['agent'], d['result']) for d in done))
        if journal['left']: lines.append('LEFT: ' + '; '.join('%s [%s]: %s%s' % (l['task'], l['status'], l['objective'], ' -> ' + l['next'] if l['next'] else '') for l in journal['left']))
        if journal['stuck']: lines.append('STUCK: ' + '; '.join('%s: %s' % (x['task'], x['why']) for x in journal['stuck']))
        if journal['required']: lines.append('REQUIRED: ' + '; '.join(journal['required']))
        if journal['facts']: lines.append('FACTS: ' + '; '.join('%s=%s' % kv for kv in journal['facts'].items()))
        if journal['left']: lines.append('NEXT: continue with %s; do not redo DONE items.' % journal['left'][0]['task'])
        return '\n'.join(lines)
    done = list(journal['done']); text = build(done)
    while len(text) > limit and done:
        done = done[1:]; text = build(done)
    return text if len(text) <= limit else text[:limit - 1] + '…'

def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

class BrainError(Exception):
    pass

FIELD_WEIGHTS = (('name', 3.0), ('mission', 2.0), ('specialist_focus', 1.5), ('specialist_method', 1.0), ('group', 0.7))
MAX_TERM_WEIGHT = 5.0      # a term counts at most this much per agent, however many fields repeat it
SYNONYM_FACTOR = 0.6       # an expanded term counts for less than a word the user wrote
MIN_SCORE, MIN_RATIO, MIN_GAP = 10.0, 1.5, 6.0   # accept only a strong match that leads the runner-up by a ratio or by a clear gap

CONTEXT_WORDS = {'for', 'on'}   # words after these often name the setting ("an API for our mobile app"), not the thing wanted
CONTEXT_ALIAS_FACTOR = 0.3   # an alias whose words all sit in that setting part counts for less

def route_weights(rows, root):
    """Per-agent term weights built from name, mission, focus, method and group; also used to precompute registry/route-index.json."""
    weights = {}
    for aid, row in rows.items():
        if aid == 'AGENT-000': continue
        manifest = load(root / row['manifest_path'])
        terms = {}
        for field, weight in FIELD_WEIGHTS:
            text = row['name'] if field == 'name' else row['mission'] if field == 'mission' else manifest.get(field, '')
            for term in tokens(text): terms[term] = min(MAX_TERM_WEIGHT, terms.get(term, 0.0) + weight)
        weights[aid] = terms
    return weights

def split_query(objective):
    """Return (head terms, context terms). Words after the first for/in/on describe the setting and count for less."""
    words = re.findall(r'[a-z0-9]+', objective.lower())
    cut = next((i for i, w in enumerate(words) if w in CONTEXT_WORDS and i > 0), len(words))
    head, context = tokens(' '.join(words[:cut])), tokens(' '.join(words[cut:]))
    return head, context - head

class Catalog:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        index_bytes = (self.root / 'registry/prompt-index.json').read_bytes()
        self.rows = {r['id']: r for r in json.loads(index_bytes)}
        self.aliases = load(self.root / 'registry/routing-aliases.json')
        syn_path = self.root / 'registry/synonyms.json'
        raw = load(syn_path).get('synonyms', {}) if syn_path.exists() else {}
        self.synonyms = {}
        for word, extra in raw.items():
            self.synonyms.setdefault(stem(word), set()).update(t for e in extra for t in tokens(e))
        cached = None
        cache_path = self.root / 'registry/route-index.json'
        if cache_path.exists():
            try:
                cached = json.loads(cache_path.read_text(encoding='utf-8'))
                if cached.get('source_sha256') != hashlib.sha256(index_bytes).hexdigest(): cached = None
            except (OSError, ValueError):
                cached = None
        self.weights = cached['weights'] if cached else route_weights(self.rows, self.root)
        self.df = {}
        for weights in self.weights.values():
            for term in weights: self.df[term] = self.df.get(term, 0) + 1

    def idf(self, term):
        return math.log(1 + len(self.weights) / self.df[term])

    def rank(self, objective):
        head, context = split_query(objective)
        query = head | context
        expanded = set()
        for term in query: expanded |= self.synonyms.get(term, set())
        expanded -= query
        words = re.findall(r'[a-z0-9]+', objective.lower())
        cut = next((i for i, w in enumerate(words) if w in CONTEXT_WORDS and i > 0), len(words))
        head_stems = ' %s ' % ' '.join(stem(w) for w in words[:cut]); all_stems = ' %s ' % ' '.join(stem(w) for w in words)
        candidates = []
        for aid, weights in self.weights.items():
            direct = query & set(weights); extra = expanded & set(weights)
            score = sum(self.idf(t) * weights[t] for t in direct) + SYNONYM_FACTOR * sum(self.idf(t) * weights[t] for t in extra)
            alias_matches, bonus = [], 0.0
            for phrase in self.aliases.get(aid, []):
                size = len(re.findall(r'[a-z0-9]+', phrase.lower()))
                if not alias_hit(phrase, query, all_stems): continue
                alias_matches.append(phrase)
                setting_only = bool(context) and not (tokens(phrase) & head) and not alias_hit(phrase, head, head_stems)
                bonus = max(bonus, (20 + size * 4) * (CONTEXT_ALIAS_FACTOR if setting_only else 1.0))
            score += bonus
            if score:
                candidates.append({'agent_id': aid, 'name': self.rows[aid]['name'], 'score': round(score, 3), 'matched_terms': sorted(direct | extra), 'matched_aliases': alias_matches})
        return sorted(candidates, key=lambda x: (-x['score'], x['agent_id']))[:5]

    def resolve(self, task):
        aid = task.get('agent_id')
        if aid:
            if aid not in self.rows or aid == 'AGENT-000':
                raise BrainError('Unknown or recursive executive assignment: ' + str(aid))
            return aid, {'method': 'explicit', 'agent_id': aid}
        candidates = self.rank(task['objective'])
        if not candidates or candidates[0]['score'] < MIN_SCORE:
            raise BrainError('No sufficiently supported capability match; supply an exact agent_id or refine the task.')
        if len(candidates) > 1 and candidates[0]['score'] - candidates[1]['score'] < MIN_GAP and candidates[0]['score'] < MIN_RATIO * candidates[1]['score']:
            raise BrainError('Ambiguous capability match; choose an exact agent_id from route candidates.')
        return candidates[0]['agent_id'], {'method': 'weighted-lexical-plus-aliases', 'candidates': candidates}

    def prompt(self, aid):
        row = self.rows[aid]
        path = (self.root / row['system_prompt_path']).resolve()
        if not path.is_relative_to(self.root.resolve()):
            raise BrainError('Prompt path escaped package')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != row['system_prompt_sha256']:
            raise BrainError('Prompt integrity mismatch: ' + aid)
        return data.decode()

    def agent_info(self, aid):
        """Compact role facts for adapters that must work with small context windows."""
        m = json.loads((self.root / self.rows[aid]['manifest_path']).read_text(encoding='utf-8'))
        return {'name': m['name'], 'group': m.get('group', ''), 'mission': m['mission'], 'method': m['specialist_method'], 'verification': m['verification'],
                'focus': m.get('specialist_focus', ''), 'rules': m.get('field_rules', [])}

    def skills(self, aid):
        """Skill documents named by the agent's manifest. A declared skill that is missing, unreadable, empty or outside the
        package is an error: the agent must not run without guidance its manifest says it needs."""
        manifest = json.loads((self.root / self.rows[aid]['manifest_path']).read_text(encoding='utf-8'))
        out = {}
        for rel in manifest.get('skill_modules', []):
            path = (self.root / rel).resolve()
            if not path.is_relative_to(self.root.resolve()):
                raise BrainError('Skill path escaped package: %s (agent %s)' % (rel, aid))
            if not path.is_file():
                raise BrainError('Declared skill module is missing: %s (agent %s)' % (rel, aid))
            try:
                text = path.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError) as exc:
                raise BrainError('Declared skill module is unreadable: %s (%s)' % (rel, exc.__class__.__name__))
            if not text.strip():
                raise BrainError('Declared skill module is empty: %s (agent %s)' % (rel, aid))
            out[rel] = text
        return out

    def compact(self):
        return [{'id': r['id'], 'name': r['name'], 'category': r['category']} for r in self.rows.values() if r['id'] != 'AGENT-000']

def validate_plan(plan, catalog):
    if not isinstance(plan, dict) or not isinstance(plan.get('goal'), str) or not plan['goal'].strip():
        raise BrainError('Plan needs a nonempty goal')
    tasks = plan.get('tasks')
    if not isinstance(tasks, list) or not tasks or len(tasks) > 100:
        raise BrainError('Plan requires 1..100 tasks')
    ids = set()
    for task in tasks:
        if not isinstance(task, dict):
            raise BrainError('Each task must be an object')
        tid = task.get('id')
        if not isinstance(tid, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', tid) or tid in ids:
            raise BrainError('Invalid or duplicate task ID')
        ids.add(tid)
        if not isinstance(task.get('objective'), str) or not task['objective'].strip():
            raise BrainError('Task needs an objective')
        for field in ['depends_on', 'acceptance_criteria', 'required_capabilities']:
            value = task.get(field)
            if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
                raise BrainError('Task needs a string list: ' + field)
        if not task['acceptance_criteria']:
            raise BrainError('Each task needs acceptance criteria')
        if task.get('agent_id') is not None and (task['agent_id'] not in catalog.rows or task['agent_id'] == 'AGENT-000'):
            raise BrainError('Invalid specialist ID for task %s: %s' % (tid, task['agent_id']))
        if type(task.get('verify')) is not bool:
            raise BrainError('verify must be boolean')
    remaining = {t['id']: set(t['depends_on']) for t in tasks}
    for tid, deps in remaining.items():
        if not deps <= ids:
            raise BrainError('Unknown dependency: task %s depends on %s, which is not in the plan' % (tid, ', '.join(sorted(deps - ids))))
    while remaining:
        ready = {tid for tid, deps in remaining.items() if not deps}
        if not ready:
            raise BrainError('Dependency cycle')
        remaining = {tid: deps - ready for tid, deps in remaining.items() if tid not in ready}
    return plan

def resolve_command(command):
    """Make host commands work from any directory and on systems without a `python3` name."""
    out = list(command)
    if out[0] in ('python', 'python3'): out[0] = sys.executable
    for i, arg in enumerate(out[1:], 1):
        if not os.path.isabs(arg) and not arg.startswith('-') and not os.path.exists(arg) and (ROOT / arg).is_file():
            out[i] = str(ROOT / arg)
    return out

class SubprocessAdapter:
    """Runs trusted host-configured commands; task text is sent only over stdin."""
    def __init__(self, config):
        self.config = config
        self.commands = config.get('agent_commands', {})
        self.default = config.get('default_command')
        self.planner = config.get('planner_command')
        for command in list(self.commands.values()) + [self.default, self.planner]:
            if command is not None and (not isinstance(command, list) or not command or not all(isinstance(s, str) for s in command)):
                raise BrainError('Commands must be nonempty argument arrays, never shell strings')

    def supports(self, aid, mode='execute'):
        return bool(self.planner if mode == 'plan' else self.commands.get(aid, self.default))

    def invoke(self, envelope, timeout):
        aid = envelope['agent_id']
        command = self.planner if envelope['mode'] == 'plan' else self.commands.get(aid, self.default)
        if not command:
            raise BrainError('No runtime adapter bound for ' + aid)
        command = resolve_command(command)
        env = {k: os.environ[k] for k in ['PATH', 'SYSTEMROOT', 'WINDIR', 'LANG', 'LC_ALL'] + self.config.get('pass_env', []) if k in os.environ}
        env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
        # The host owns the executable and its sandbox. No credentials are read from task data.
        with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', env=env, shell=False, start_new_session=(os.name != 'nt')) as proc:
            try:
                stdout, stderr = proc.communicate(json.dumps(envelope), timeout=timeout)
            except subprocess.TimeoutExpired:
                if os.name != 'nt':
                    import signal
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
                proc.communicate()
                raise BrainError('Adapter timeout; side effects may have occurred; no automatic retry')
            if proc.returncode:
                # Avoid exposing arbitrary stderr, which may contain secrets.
                detail = ''
                try:
                    err = json.loads(stdout).get('adapter_error')
                    if isinstance(err, dict): detail = ': %s: %s' % (str(err.get('kind'))[:40], str(err.get('message'))[:300])
                except (ValueError, AttributeError):
                    pass
                raise BrainError('Adapter exited with code ' + str(proc.returncode) + detail)
        if len(stdout.encode()) > 2_000_000:
            raise BrainError('Adapter response too large')
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise BrainError('Adapter must return one JSON object on stdout') from exc

class DemoAdapter:
    """Deterministic fixture only: no model, tools, or real task execution."""
    def invoke(self, envelope, timeout):
        if envelope['mode'] == 'plan':
            raise BrainError('Demo adapter cannot plan real work')
        result = {'agent_id': envelope['agent_id'], 'status': 'completed',
                  'result': 'SIMULATION ONLY: fixture response for ' + envelope['task']['id'],
                  'evidence': [{'kind': 'simulation', 'reference': envelope['invocation_id']}],
                  'assumptions': [], 'limitations': ['No real user task was executed'], 'next_action': None}
        if envelope['mode'] == 'verify':
            result['verdict'] = 'pass'
        return result

def clip(value, limit):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= limit else text[:max(0, limit - 1)] + '…'

def packet(entry, limit):
    """Compact view of a finished task for the agents that depend on it. The full output stays in the run state."""
    out = entry.get('output') or {}
    return {'agent_id': entry.get('agent_id'), 'status': entry.get('status'), 'summary': clip(out.get('result', ''), limit),
            'evidence': [clip(e, 200) for e in (out.get('evidence') or [])[:3]], 'limitations': [clip(x, 160) for x in (out.get('limitations') or [])[:2]]}

class Brain:
    def __init__(self, catalog, adapter, config, simulation=False):
        self.catalog, self.adapter, self.config = catalog, adapter, config
        self.simulation = simulation
        self.timeout = config.get('timeout_seconds', 120)
        if type(self.timeout) not in (int, float) or not 0 < self.timeout <= 3600:
            raise BrainError('timeout_seconds must be 0..3600')
        for key, low, high in (('max_handoffs_per_task', 0, 10), ('max_handoff_depth', 0, 5), ('context_chars', 200, 20000), ('context_total_chars', 500, 60000), ('max_iterations', 1, 10)):
            if key in config and (type(config[key]) is not int or not low <= config[key] <= high):
                raise BrainError('%s must be an integer %d..%d' % (key, low, high))
        self.verifier = config.get('verifier_agent_id', 'AGENT-111')
        if self.verifier not in catalog.rows or self.verifier == 'AGENT-000':
            raise BrainError('Invalid verifier')
        if not isinstance(config.get('allowed_agents', []), list) or not isinstance(config.get('granted_capabilities', []), list):
            raise BrainError('Host allowlists must be arrays')

    def permit(self, aid, task):
        allowed = self.config.get('allowed_agents', [])
        if '*' not in allowed and aid not in allowed:
            raise BrainError('Agent not enabled by host: ' + aid)
        missing = set(task['required_capabilities']) - set(self.config.get('granted_capabilities', []))
        if missing:
            raise BrainError('Missing host capabilities: ' + ', '.join(sorted(missing)))

    def invoke(self, aid, task, state, path, mode, context):
        self.permit(aid, task)
        if hasattr(self.adapter, 'supports') and not self.adapter.supports(aid, mode):
            raise BrainError('No runtime adapter bound for ' + aid)
        # Read the full prompt only at the moment this role is activated.
        prompt = self.catalog.prompt(aid)
        skills, info = self.catalog.skills(aid), self.catalog.agent_info(aid)  # fail before the run state records an activation
        state['activation_count'] += 1
        invocation_id = state['run_id'] + ':' + str(state['activation_count'])
        state['inflight'] = {'task_id': task['id'], 'agent_id': aid, 'invocation_id': invocation_id, 'mode': mode}
        state['events'].append({'event': 'activated', **state['inflight']})
        atomic_write(path, state)
        envelope = {'protocol_version': '1', 'mode': mode, 'agent_id': aid,
                    'invocation_id': invocation_id, 'system_prompt': prompt, 'skills': skills, 'agent': info, 'task': task,
                    'context': context, 'granted_capabilities': task['required_capabilities'],
                    'verification_instruction': 'Inspect evidence independently against each acceptance criterion. Return verdict pass or fail; do not repeat the implementation action.' if mode == 'verify' else None}
        response = self.adapter.invoke(envelope, self.timeout)
        self.check_response(response, aid, mode)
        self.account(state, envelope, response)
        state['events'].append({'event': 'released', 'agent_id': aid, 'task_id': task['id'], 'status': response['status']})
        state['inflight'] = None
        atomic_write(path, state)
        return response

    # ---- token use is recorded per run (adapters report it; otherwise it is estimated from text length) so waste is visible ----
    @staticmethod
    def account(state, envelope, response):
        u = state.setdefault('usage', {'in': 0, 'out': 0, 'calls': 0, 'estimated_calls': 0})
        reported = response.get('usage')
        if isinstance(reported, dict) and all(type(reported.get(k)) is int and reported[k] >= 0 for k in ('in', 'out')):
            u['in'] += reported['in']; u['out'] += reported['out']
        else:
            u['in'] += len(json.dumps(envelope)) // 4; u['out'] += len(json.dumps(response)) // 4; u['estimated_calls'] += 1
        u['calls'] += 1

    # ---- agent-to-agent communication, always mediated by the brain ----
    def work_task(self, task, aid, entry, state, path):
        """Understand, execute, check, and loop: when a result is partial, failed or rejected by verification, the same agent is called again with
        what was done and what is left (not the whole history), up to max_iterations and within the activation and token limits."""
        limit = task.get('max_iterations', self.config.get('max_iterations', 1))
        feedback, history, result = None, [], None
        skip_execute = bool(entry.pop('awaiting_verification', False) and entry.get('output'))  # resumed after an interruption between execute and verify
        for attempt in range(1, limit + 1):
            context = self.context_for(task, state)
            if feedback: context['previous'] = feedback
            entry['status'] = 'running'
            if skip_execute:
                result, skip_execute = entry['output'], False
            else:
                result = self.invoke(aid, task, state, path, 'execute', context)
            entry['output'], entry['attempts'] = result, attempt
            note = None
            if result['status'] == 'completed' and not task['verify']:
                entry.update(status='completed', verification={'status': 'unverified-host-opt-in'}); entry.pop('reason', None)
            elif result['status'] == 'completed':
                entry['status'] = 'verifying'
                check = self.invoke(self.verifier, dict(task, required_capabilities=self.config.get('verification_capabilities', [])), state, path, 'verify',
                                    {'candidate': result, 'specialist_agent_id': aid})
                entry['verification'] = check
                if check.get('retryable'):  # the model was unavailable: keep the finished work, only verification is left
                    entry.update(status='blocked', reason='Verification interrupted: model temporarily unavailable', resumable=True, awaiting_verification=True); break
                if check['status'] == 'completed' and check['verdict'] == 'pass':
                    entry['status'] = 'completed'; entry.pop('reason', None)
                else:
                    entry.update(status='failed', reason='Independent verification did not pass'); note = {'verification': 'failed', 'why': clip(check.get('result', ''), 400)}
            elif result['status'] == 'blocked' and result.get('retryable'):
                entry.update(status='blocked', reason='Model temporarily unavailable', resumable=True); note = {'status': 'blocked', 'why': 'the model was temporarily unavailable'}
            elif result['status'] == 'blocked':
                entry.update(status='blocked', reason='Specialist returned blocked')  # needs something a repeat cannot supply
            else:
                entry.update(status='failed' if result['status'] == 'failed' else 'blocked', reason='Specialist returned ' + result['status']); note = {'status': result['status']}
            history.append({'attempt': attempt, 'status': result['status'], 'task_status': entry['status']})
            if entry['status'] == 'completed' or note is None or attempt >= limit: break
            feedback = dict(note, attempt=attempt + 1, done=clip(result.get('result', ''), 400), left=clip(result.get('next_action') or '', 200))
            state['events'].append({'event': 'retry', 'task_id': task['id'], 'attempt': attempt + 1})
        entry['history'] = history
        return result

    def save_journal(self, path, state, plan):
        base = Path(path); journal = build_journal(state, plan['goal'], list(plan['tasks']) + state['dynamic'])
        atomic_write(base.with_name(base.stem + '.journal.json'), journal)
        atomic_text(base.with_name(base.stem + '.brief.md'), render_brief(journal) + '\n')

    def reopen(self, state, tasks):
        """On resume, tasks that stopped only because the model was temporarily unavailable (and the tasks waiting on them) become pending again."""
        for tid, entry in state['tasks'].items():
            if entry['status'] == 'blocked' and entry.get('resumable'):
                keep = {k: entry[k] for k in ('output', 'awaiting_verification', 'agent_id', 'attempts') if k in entry} if entry.get('awaiting_verification') else {}
                state['tasks'][tid] = dict(keep, status='pending')
        changed = True
        while changed:
            changed = False
            for t in tasks:
                entry = state['tasks'][t['id']]
                if entry['status'] == 'blocked' and entry.get('reason') == 'A prerequisite did not complete' and any(state['tasks'][d]['status'] == 'pending' for d in self.deps(t, state)):
                    state['tasks'][t['id']] = {'status': 'pending'}; changed = True

    @staticmethod
    def deps(task, state):
        return list(task['depends_on']) + state['extra_deps'].get(task['id'], [])

    def context_for(self, task, state):
        """What an agent is told about earlier work: compact packets of the tasks it depends on, facts other agents published, and
        any inputs or requester attached to a handoff. Sizes are capped so context does not grow with the length of a run."""
        total = self.config.get('context_total_chars', 6000)
        deps = self.deps(task, state)
        limit = min(self.config.get('context_chars', 1500), max(200, total // max(1, len(deps))))
        ctx = {'dependencies': {d: packet(state['tasks'][d], limit) for d in deps}}
        used = sum(len(json.dumps(v, ensure_ascii=False)) for v in ctx['dependencies'].values())
        board = {}
        for key, item in reversed(list(state['blackboard'].items())):  # newest first
            cost = len(key) + len(item['value']) + 40
            if used + cost > total: break
            board[key] = {'value': item['value'], 'from': item['agent_id']}; used += cost
        if board: ctx['blackboard'] = board
        if task.get('inputs'): ctx['inputs'] = task['inputs']
        if task.get('spawned_by'): ctx['requested_by'] = task['spawned_by']
        return ctx

    @staticmethod
    def note(state, task, aid, target, new_id, objective, status, reason=''):
        state['messages'].append({'n': len(state['messages']) + 1, 'from_task': task['id'], 'from_agent': aid, 'to': target or 'route', 'task_id': new_id,
                                  'objective': clip(objective or '', 120), 'status': status, 'reason': reason})
        del state['messages'][:-500]

    def check_handoff(self, item, task, aid, accepted, all_tasks):
        limit, max_depth = self.config.get('max_handoffs_per_task', 3), self.config.get('max_handoff_depth', 2)
        if not isinstance(item, dict): return 'a handoff must be an object', None
        if accepted >= limit: return 'too many handoffs from one task (limit %d)' % limit, None
        if task.get('depth', 0) + 1 > max_depth: return 'handoff depth limit (%d) reached' % max_depth, None
        objective = item.get('objective')
        if not isinstance(objective, str) or not objective.strip() or len(objective) > 1000: return 'objective must be a non-empty string under 1000 characters', None
        target = item.get('to')
        target = None if target in (None, '', 'null', 'none', 'None') else target
        if target is not None:
            if target not in self.catalog.rows or target == 'AGENT-000': return 'unknown or executive agent: %s' % target, None
            if target == aid: return 'an agent cannot hand work to itself', None
            allowed = self.config.get('allowed_agents', [])
            if '*' not in allowed and target not in allowed: return 'agent not enabled by host: %s' % target, None
        criteria = item.get('acceptance_criteria')
        if not isinstance(criteria, list) or not criteria or not all(isinstance(c, str) and c.strip() for c in criteria): return 'acceptance_criteria must be a non-empty list of strings', None
        caps = item.get('required_capabilities', [])
        if not isinstance(caps, list) or not all(isinstance(c, str) for c in caps): return 'required_capabilities must be a list of strings', None
        if not set(caps) <= set(task['required_capabilities']): return 'a handoff cannot widen capabilities: %s' % ', '.join(sorted(set(caps) - set(task['required_capabilities']))), None
        key = (target or '', ' '.join(objective.lower().split()))
        if any(((t.get('agent_id') or ''), ' '.join(t['objective'].lower().split())) == key for t in all_tasks): return 'duplicate of an existing task', None
        if len(all_tasks) + accepted >= 100: return 'plan size limit reached', None
        inputs = item.get('inputs')
        return '', {'objective': objective.strip(), 'agent_id': target, 'acceptance_criteria': [c.strip() for c in criteria], 'required_capabilities': caps,
                    'inputs': clip(inputs, 2000) if inputs not in (None, '', [], {}) else None}

    def after_completion(self, task, aid, result, state, all_tasks):
        """Runs only after a task completed and passed verification: publishes facts to the shared board and queues handoffs."""
        for entry in result.get('publish') or []:
            if (isinstance(entry, dict) and isinstance(entry.get('key'), str) and re.fullmatch(r'[A-Za-z0-9_.-]{1,60}', entry['key'])
                    and isinstance(entry.get('value'), (str, int, float, bool)) and len(state['blackboard']) < 200):
                state['blackboard'][entry['key']] = {'value': clip(str(entry['value']), 500), 'task': task['id'], 'agent_id': aid}
        handoffs = result.get('handoffs')
        if not handoffs: return
        if not isinstance(handoffs, list):
            self.note(state, task, aid, None, None, '', 'rejected', 'handoffs must be a list'); return
        accepted = 0
        for item in handoffs:
            reason, new = self.check_handoff(item, task, aid, accepted, all_tasks)
            if reason:
                self.note(state, task, aid, item.get('to') if isinstance(item, dict) else None, None, item.get('objective') if isinstance(item, dict) else '', 'rejected', reason); continue
            n = sum(1 for t in state['dynamic'] if t.get('spawned_by') == task['id']) + 1
            new.update(id='%s-h%d' % (task['id'], n), depends_on=[task['id']], verify=True, spawned_by=task['id'], depth=task.get('depth', 0) + 1)
            state['tasks'][new['id']] = {'status': 'pending'}; state['dynamic'].append(new); all_tasks = all_tasks + [new]; accepted += 1
            for other in all_tasks:  # whatever was waiting on the requester now also waits for the requested work
                if other['id'] != new['id'] and state['tasks'][other['id']]['status'] == 'pending' and task['id'] in self.deps(other, state):
                    state['extra_deps'].setdefault(other['id'], []).append(new['id'])
            self.note(state, task, aid, new['agent_id'], new['id'], new['objective'], 'queued')

    @staticmethod
    def check_response(response, aid, mode):
        keys = {'agent_id', 'status', 'result', 'evidence', 'assumptions', 'limitations', 'next_action'}
        if not isinstance(response, dict) or not keys <= response.keys():
            raise BrainError('Malformed agent response')
        if response['agent_id'] != aid or response['status'] not in {'completed', 'partial', 'blocked', 'failed'}:
            raise BrainError('Invalid response identity or status')
        if not all(isinstance(response[k], list) for k in ['evidence', 'assumptions', 'limitations']):
            raise BrainError('Evidence, assumptions and limitations must be arrays')
        if response['status'] == 'completed' and (not response['evidence'] or not response['result']):
            raise BrainError('False success: completed response lacks result or evidence')
        if mode == 'verify' and response.get('verdict') not in {'pass', 'fail'}:
            raise BrainError('Verifier must return verdict pass or fail')

    def run(self, plan, state_path, resume=False):
        validate_plan(plan, self.catalog)
        path = Path(state_path)
        signature = fingerprint({'plan': plan, 'config': {k: v for k, v in self.config.items() if k not in TUNABLE}, 'simulation': self.simulation,
                                 'prompts': {k:v['system_prompt_sha256'] for k,v in self.catalog.rows.items()}})
        if path.exists() and not resume:
            raise BrainError('State file exists; use --resume or a new state path')
        if resume:
            if not path.exists():
                raise BrainError('No checkpoint to resume')
            state = load(path)
            if state.get('signature') != signature:
                raise BrainError('Plan, configuration, mode or prompt catalog changed; cannot resume this checkpoint')
            if state.get('inflight') or any(t.get('status') in {'running', 'verifying'} for t in state.get('tasks', {}).values()):
                raise BrainError('Interrupted invocation requires manual reconciliation; it will not be replayed automatically')
            for key, empty in (('dynamic', []), ('extra_deps', {}), ('blackboard', {}), ('messages', [])): state.setdefault(key, empty)
            self.reopen(state, list(plan['tasks']) + state['dynamic'])
        else:
            state = {'run_id': 'run-' + str(time.time_ns()), 'signature': signature, 'simulation': self.simulation,
                     'status': 'running', 'activation_count': 0, 'inflight': None, 'events': [],
                     'dynamic': [], 'extra_deps': {}, 'blackboard': {}, 'messages': [],
                     'tasks': {t['id']: {'status': 'pending'} for t in plan['tasks']}}
        for key, empty in (('dynamic', []), ('extra_deps', {}), ('blackboard', {}), ('messages', [])): state.setdefault(key, empty)
        atomic_write(path, state)
        while any(v['status'] == 'pending' for v in state['tasks'].values()):
            advanced = False
            for task in list(plan['tasks']) + state['dynamic']:
                tid = task['id']; entry = state['tasks'][tid]
                if entry['status'] != 'pending':
                    continue
                dependencies = [state['tasks'][d] for d in self.deps(task, state)]
                if any(d['status'] in {'failed', 'blocked'} for d in dependencies):
                    entry.update(status='blocked', reason='A prerequisite did not complete')
                    advanced = True
                    continue
                if not all(d['status'] == 'completed' for d in dependencies):
                    continue
                advanced = True
                try:
                    aid, routing = self.catalog.resolve(task)
                    entry.update(agent_id=aid, routing=routing)
                    if not task['verify'] and not self.config.get('allow_unverified', False):
                        raise BrainError('Host requires verification for this task')
                    if task['verify'] and aid == self.verifier:
                        raise BrainError('Specialist and verifier must be different roles')
                    # Check both roles before starting a potentially mutating specialist.
                    self.permit(aid, task)
                    needed_roles = [aid, self.verifier] if task['verify'] else [aid]
                    if hasattr(self.adapter, 'supports') and any(not self.adapter.supports(role) for role in needed_roles):
                        raise BrainError('Missing specialist or verifier runtime binding')
                    if task['verify']:
                        self.permit(self.verifier, {'required_capabilities': self.config.get('verification_capabilities', [])})
                    result = self.work_task(task, aid, entry, state, path)
                    if entry['status'] == 'completed':
                        self.after_completion(task, aid, result, state, list(plan['tasks']) + state['dynamic'])
                except (BrainError, OSError) as exc:
                    entry.update(status='blocked', reason=str(exc))
                    if state['inflight']:
                        state['events'].append({'event': 'invocation_interrupted', **state['inflight']})
                        state['status'] = 'blocked'
                        atomic_write(path, state)
                        return state  # Never replay or conceal uncertain execution effects.
                atomic_write(path, state); self.save_journal(path, state, plan)
            if not advanced:
                raise BrainError('Scheduler made no progress')
        statuses = {t['status'] for t in state['tasks'].values()}
        state['status'] = 'completed' if statuses == {'completed'} else 'failed' if 'failed' in statuses else 'blocked'
        unverified = any(t.get('verification', {}).get('status') == 'unverified-host-opt-in' for t in state['tasks'].values())
        state['outcome'] = ('simulation_only' if self.simulation else 'incomplete' if state['status'] != 'completed'
                            else 'completed_unverified' if unverified else 'adapter_reported_and_verified')
        atomic_write(path, state); self.save_journal(path, state, plan)
        return state

def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'): stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    route = subs.add_parser('route'); route.add_argument('objective')
    plan = subs.add_parser('plan'); plan.add_argument('objective'); plan.add_argument('--config', required=True); plan.add_argument('--out', required=True)
    for name in ['run', 'demo']:
        sub = subs.add_parser(name); sub.add_argument('--plan', required=True); sub.add_argument('--state', required=True); sub.add_argument('--resume', action='store_true')
        if name == 'run': sub.add_argument('--config', required=True)
    args = parser.parse_args(); catalog = Catalog()
    try:
        if args.command == 'route':
            candidates = catalog.rank(args.objective)
            try:
                selected, rationale = catalog.resolve({'objective': args.objective})
                output = {'status': 'selected', 'agent_id': selected, 'candidates': candidates}
            except BrainError as exc:
                output = {'status': 'needs_selection', 'reason': str(exc), 'candidates': candidates}
        elif args.command == 'plan':
            config = load(args.config); adapter = SubprocessAdapter(config)
            brain = Brain(catalog, adapter, config)
            brain.permit('AGENT-000', {'required_capabilities': []})
            output = adapter.invoke({'mode': 'plan', 'agent_id': 'AGENT-000', 'system_prompt': catalog.prompt('AGENT-000'), 'goal': args.objective, 'catalog': catalog.compact()}, brain.timeout)
            validate_plan(output, catalog)
            if Path(args.out).exists(): raise BrainError('Plan output already exists')
            atomic_write(args.out, output)
        else:
            simulation = args.command == 'demo'
            config = {'allowed_agents': ['*'], 'granted_capabilities': []} if simulation else load(args.config)
            adapter = DemoAdapter() if simulation else SubprocessAdapter(config)
            output = Brain(catalog, adapter, config, simulation).run(load(args.plan), args.state, args.resume)
        print(json.dumps(output, indent=2))
        if output.get('status') in {'failed', 'blocked', 'needs_selection'}: return 2
        return 0
    except (BrainError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({'status': 'blocked', 'reason': str(exc)}))
        return 2

if __name__ == '__main__':
    try:
        sys.exit(main())
    except BrokenPipeError:  # output piped to a program that closed early, such as head
        sys.stderr.close(); sys.exit(0)
