#!/usr/bin/env python3
"""Rebuild everything derived from the manifests and expertise file, in order: prompts, registry and docs, Claude Code pack.
`--check` verifies that nothing is out of date and writes nothing."""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [('prompts', 'build_prompts.py'), ('catalog', 'build_catalog.py'), ('claude-code pack', None)]

def main():
    check = '--check' in sys.argv; failed = []
    for name, script in STEPS:
        if script:
            cmd = [sys.executable, str(ROOT / 'scripts' / script)] + (['--check'] if check else [])
        else:
            cmd = [sys.executable, str(ROOT / 'scripts/agent_cli.py'), 'check-claude-code' if check else 'build-claude-code']
        p = subprocess.run(cmd, capture_output=True, text=True)
        print('%-17s %s' % (name, 'ok' if p.returncode == 0 else 'FAILED: ' + (p.stdout + p.stderr).strip()[:300]))
        if p.returncode: failed.append(name)
    sys.exit(1 if failed else 0)

if __name__ == '__main__':
    main()
