---
name: physical-ai-specialist
description: "Design and evaluate robotics and embodied-AI work safely: define the safety envelope first, validate in simulation, measure the sim-to-real gap and keep hardware changes reviewable."
---

# Physical AI Specialist

## When to apply
A task involves a robot, actuator, sensor stack, control loop or a simulation intended to transfer to hardware.

## How to apply
1. Define the safety envelope before any control change: speed, force and workspace limits, emergency-stop behavior, and the conditions under which the system must refuse to act. Enforce it below the learned or planned layer, not inside it.
2. Model the loop: sensing latency and noise, state estimation, the controller and the actuator limits. Most failures come from timing, saturation and bad estimates rather than from the plan.
3. Validate in simulation first, with randomized physics, sensor noise and delays. Treat a policy that works only in the nominal case as untested.
4. Quantify the sim-to-real gap with a small set of hardware trials under supervision and a hard abort, and record what differed.
5. Keep calibration, controller parameters and hardware configuration under version control with the date and the unit they apply to.
6. Roll out in stages (restrained, supervised, then autonomous), with logged data that lets you replay a failure.

## Anti-patterns
- Shipping a control change straight to hardware.
- Treating simulation success as proof of real-world safety.
- Safety logic that depends on the model behaving.

## Output expectation
The safety envelope, simulation evidence with the conditions varied, the measured sim-to-real differences, the staged rollout plan with abort criteria, and what remains unverified.
