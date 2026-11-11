# Routing quality

`python scripts/agent_cli.py find "<request>"` ranks agents; `ask`, `work` and the controller auto-route only when the best match is strong and
clearly ahead, and otherwise stop and list candidates. Calling an agent by ID, slug or skill name never involves ranking.

| Request set | Size | correct / wrong / abstained | acceptable agent in top 3 |
| --- | ---: | --- | --- |
| Development (tuned on; aliases written for these) | 39 | 39 / 0 / 0 | 39 of 39 |
| Set A (diagnosis, then tuned on) | 30 | 12 / 1 / 17 | 25 of 30 |
| Set B (found a misroute; fixed while tuning) | 30 | 13 / 1 / 16 | 25 of 30 |
| Set C (never used to tune anything) | 30 | 10 / 5 / 15 | 24 of 30 |

Other checks: every agent resolves from its own name and mission (434 of 434 non-brain agents); 10 of 10 unrelated requests stay unrouted;
"design an API for our mobile app" no longer goes to the mobile-app agent (a phrase that describes only the setting of a request, after
"for" or "on", counts for far less than one that names the thing wanted).

How to read this: only set C is evidence of accuracy on requests the router has not seen, and it is small. On it, a third of requests go to
a suitable agent automatically, about one in six to a different agent, and half stop and show candidates, with a suitable agent among the top
three 24 times in 30. "Suitable" means one of the agents the author judged acceptable. Misroutes in set C: "what is the best way to cache api responses" went to AGENT-054 (API Discovery Agent); "monitor for suspicious logins" went to AGENT-139 (Health Monitor); "audit our container images for vulnerabilities" went to AGENT-195 (Container Agent); "check if the new release is actually live" went to AGENT-358 (Release Agent); "fine tune a small model on our support tickets" went to AGENT-433 (Local Model Operations Agent).

The acceptance rule (a clear gap or ratio over the runner-up) was chosen on the development sets and A and B, then set C was measured again;
a stricter rule trades fewer misroutes for more candidate lists. For important work name the agent (`AGENT-NNN` or its slug). To improve
auto-routing for your own phrasing, add phrases to `registry/routing-aliases.json` (a leading `=` means exact phrase only) or words to
`registry/synonyms.json`; `tests/test_routing.py` records the measured baselines and fails if quality drops. Matching is lexical, with
stemming and a small synonym list, not semantic.
