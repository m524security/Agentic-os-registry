# Coverage

435 definitions in 30 groups across 10 categories. Every group has a field-expertise pack and every agent has its own specialization focus, both compiled into its prompt from `registry/expertise.json` by `scripts/build_prompts.py`.

| Category | Group | Agents | IDs |
| --- | --- | ---: | --- |
| meta | Brain / Meta Agents | 18 | 000–429 |
| meta | Agent-System Optimization | 8 | 173–180 |
| meta | Governance | 10 | 366–375 |
| meta | Communication / Coordination | 10 | 376–385 |
| memory-learning | Memory / Context / Learning | 11 | 016–434 |
| memory-learning | Skill Management | 18 | 333–350 |
| software-engineering | Software Engineering / Dev | 28 | 026–421 |
| software-engineering | Code Necessity / Anti-Overengineering | 10 | 141–150 |
| software-engineering | Code Understanding | 8 | 151–158 |
| computer-tools | Computer / Web / Tool | 17 | 046–433 |
| computer-tools | Document / Multimodal | 10 | 101–110 |
| research-science | Research / Scientific | 17 | 058–427 |
| data-knowledge | Data / Knowledge | 12 | 072–419 |
| cybersecurity | Cybersecurity / Safety | 18 | 083–100 |
| cybersecurity | Reconnaissance / Attack Surface | 30 | 201–230 |
| cybersecurity | Vulnerability Assessment | 30 | 231–260 |
| cybersecurity | Defensive Security Operations | 20 | 261–280 |
| cybersecurity | Security Engineering | 15 | 281–295 |
| cybersecurity | Agent / LLM Security | 15 | 296–310 |
| cybersecurity | Cyber Governance | 1 | 311–311 |
| verification-recovery | Verification / Quality | 12 | 111–431 |
| verification-recovery | Recovery / Self-Correction | 10 | 121–130 |
| verification-recovery | Assumption / Gap Hunters | 8 | 159–166 |
| verification-recovery | Reality / Evidence | 6 | 167–172 |
| verification-recovery | Failure Intelligence | 10 | 386–395 |
| infrastructure | Infrastructure / Operations | 15 | 131–424 |
| infrastructure | Environment / Setup | 21 | 312–332 |
| infrastructure | Workflow / Lifecycle | 15 | 351–365 |
| infrastructure | Economy / Efficiency | 10 | 396–405 |
| os-systems | OS / Systems Engineering | 22 | 181–417 |

IDs within a group are not always contiguous. There is no objective universal count of necessary agents: roles are added when a task needs distinct expertise, a distinct authorization boundary or a distinct verification method, and merged or retired when they overlap. The executive brain (AGENT-000) schedules; AGENT-001 advises on strategy.
