---
name: gpu-compute-specialist
description: "Tune GPU and accelerator workloads from evidence: confirm the bottleneck on the device, fix memory and transfer behavior first, and verify numerical correctness after every change."
---

# GPU Compute Specialist

## When to apply
A task names a GPU, CUDA or another accelerator, or a workload whose profile shows time spent on the device or moving data to it.

## How to apply
1. Profile before touching code. Establish whether the time is in kernels, host-device transfers, synchronization, data loading or the host. Optimizing the wrong stage changes nothing.
2. Fix the largest cost first. Usual order: avoid unnecessary transfers and syncs, batch small launches, fix memory access patterns (coalescing, layout, alignment), then raise occupancy and use shared memory or fused kernels.
3. Use the platform's tuned libraries and compiler flags before hand-written kernels; write a kernel only when the profile shows no library covers the operation.
4. Change one thing at a time and re-profile on realistic sizes, not toy inputs. Report throughput, memory bandwidth and utilization together; one metric hides regressions in the others.
5. Check correctness after every change: compare against a trusted reference with an explicit tolerance, and watch for precision changes (mixed precision, fused operations, reduction order) and race conditions.
6. Note the hardware, driver and library versions; results do not transfer across architectures without a check.

## Anti-patterns
- Tuning kernels when the pipeline is input-bound.
- Reporting a speedup measured on an unrepresentative size or without checking results.
- Premature fusion or custom kernels that make the code unmaintainable for a small gain.

## Output expectation
Before-and-after profiles for the same workload, the change made and why, the correctness comparison with its tolerance, and the environment it was measured on.
