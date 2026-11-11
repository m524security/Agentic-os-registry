# Agent activation factory

`runtime.py` loads a selected prompt only when its task is ready, verifies its hash, and sends the prompt plus scoped task data to a host-bound adapter. The adapter supplies the real model and tools. No executable command is taken from a task plan. A separate invocation verifies the candidate result before prerequisites are considered satisfied.

Agents are logical role invocations; the controller does not keep hundreds of background processes or independently trained models alive. A role is released when its adapter call returns. The runtime guide documents interruption and isolation limits.
