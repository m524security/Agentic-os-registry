#!/usr/bin/env python3
"""Protocol example, deliberately blocked until a real model/tool runtime is integrated."""
import json
import sys
request = json.load(sys.stdin)
# Replace this section with your trusted model/tool runtime.
# Pass system_prompt as system instructions and task/context as data.
# The adapter must enforce its own tool permissions and execution isolation.
# For mode=plan, return {goal, tasks}; for execute/verify return the contract below.
response = {
    'agent_id': request['agent_id'], 'status': 'blocked',
    'result': 'No model/tool runtime is connected to this example adapter.',
    'evidence': [], 'assumptions': [],
    'limitations': ['Protocol example only'], 'next_action': 'Integrate an actual runtime'
}
if request['mode'] == 'verify': response['verdict'] = 'fail'
json.dump(response, sys.stdout)
