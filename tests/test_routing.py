import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'brain'))
import runtime  # noqa: E402

# Development set: written while building the router and used to tune aliases and thresholds. Every item must route correctly.
DEVELOPMENT = {
 "review my pull request for bugs": "AGENT-042",
 "write unit tests for the payment module": "AGENT-034",
 "scan our network for open ports": "AGENT-218",
 "summarize this research paper": "AGENT-063",
 "set up a CI pipeline": "AGENT-043",
 "fix the failing build": "AGENT-038",
 "design a database schema": "AGENT-074",
 "optimize slow SQL queries": "AGENT-073",
 "crawl a website and extract prices": "AGENT-426",
 "search the web for the latest python release": "AGENT-427",
 "fill in a web form automatically": "AGENT-428",
 "explain this error message": "AGENT-157",
 "deploy the app to kubernetes": "AGENT-044",
 "write documentation for the API": "AGENT-420",
 "threat model our login system": "AGENT-084",
 "analyze logs for an intrusion": "AGENT-263",
 "create a data visualization from a csv": "AGENT-078",
 "plan a multi-step project": "AGENT-007",
 "remember what we decided last week": "AGENT-017",
 "run my local llama model": "AGENT-433",
 "test accessibility of the page": "AGENT-409",
 "refactor this function to be simpler": "AGENT-032",
 "delete unused code": "AGENT-143",
 "check my code for security vulnerabilities": "AGENT-255",
 "migrate the database safely": "AGENT-327",
 "back up and restore the server": "AGENT-423",
 "monitor cpu and memory usage": "AGENT-190",
 "write a literature review": "AGENT-061",
 "design an experiment": "AGENT-066",
 "clean messy spreadsheet data": "AGENT-103",
 "translate the ui strings": "AGENT-421",
 "set up a docker container": "AGENT-195",
 "configure a firewall": "AGENT-191",
 "investigate a phishing email": "AGENT-276",
 "rotate leaked credentials": "AGENT-223",
 "review terraform changes": "AGENT-256",
 "profile and speed up the app": "AGENT-045",
 "install these agents in claude code": "AGENT-432",
 "create a REST api": "AGENT-027"
}
# Held-out set A (30 queries): used for diagnosis, then to tune the ranker and its thresholds.
HELD_OUT_A = {
 "break this big goal into smaller steps": [
  6
 ],
 "which agent should handle this request": [
  9
 ],
 "make the app load faster": [
  45,
  135
 ],
 "write a function that parses dates": [
  27,
  30
 ],
 "add a login feature to the website": [
  30,
  406,
  407
 ],
 "find out why the server keeps crashing": [
  31,
  122,
  198
 ],
 "compare two versions of a report": [
  119
 ],
 "check whether this claim is true": [
  112,
  118
 ],
 "turn this PDF into text": [
  101,
  102,
  105
 ],
 "generate an image of a mountain": [
  107
 ],
 "transcribe this audio recording": [
  108,
  109
 ],
 "how much are we spending on tokens": [
  23,
  134,
  396
 ],
 "reduce the context size of this conversation": [
  20,
  22,
  23
 ],
 "reproduce my environment on another machine": [
  316,
  331
 ],
 "upgrade our dependencies to the latest versions": [
  39,
  315,
  328
 ],
 "roll back the last deployment": [
  129,
  329,
  363
 ],
 "find hardcoded passwords in the repo": [
  90,
  223,
  254
 ],
 "test our website for cross site scripting": [
  231,
  238
 ],
 "handle a ransomware incident": [
  276,
  277,
  279
 ],
 "analyze this suspicious executable": [
  270
 ],
 "check that we comply with open source licenses": [
  422
 ],
 "set up monitoring dashboards and alerts": [
  131,
  139,
  361
 ],
 "estimate how risky deleting this database is": [
  367,
  368,
  369
 ],
 "train a classifier on our data": [
  411,
  412
 ],
 "serve a model behind an api": [
  414
 ],
 "write the postmortem for last night's outage": [
  280,
  364
 ],
 "explain what this function does line by line": [
  142,
  151,
  153
 ],
 "does this design have too many layers": [
  144,
  146,
  180
 ],
 "convert this csv to a clean database table": [
  75,
  76,
  77
 ],
 "audit who accessed the customer records": [
  374
 ]
}
# Held-out set B (30 queries): measured once, then used while fixing the router (an API-design request was being sent to the mobile-app agent).
HELD_OUT_B = {
 "figure out the root cause of intermittent test failures": [
  31,
  122
 ],
 "make sure our pdf invoices are parsed correctly": [
  101,
  102
 ],
 "what should we build first given limited time": [
  7,
  13
 ],
 "check if the website is vulnerable to sql injection": [
  231,
  236,
  237
 ],
 "set up a python environment with the right versions": [
  40,
  312,
  314
 ],
 "stop an agent from leaking api keys in its replies": [
  223,
  254,
  291,
  307
 ],
 "remember my preferences for next time": [
  17,
  18
 ],
 "chart monthly revenue by region": [
  72,
  78
 ],
 "write a script to rename many files": [
  27,
  50,
  193
 ],
 "explain how this regex works": [
  142,
  151,
  153
 ],
 "why did the last release go wrong": [
  122,
  280,
  364
 ],
 "test the app on a phone": [
  36,
  410
 ],
 "estimate how many tokens this will use": [
  14,
  23,
  396
 ],
 "scan the dependencies for known vulnerabilities": [
  89,
  225,
  252,
  253
 ],
 "build a simple dashboard for server health": [
  131,
  139,
  361
 ],
 "diagnose why the database is slow": [
  45,
  73,
  74,
  135
 ],
 "extract the tables from a scanned report": [
  102,
  105
 ],
 "can this agent be trusted with admin access": [
  96,
  301,
  370
 ],
 "compare two language models for our use case": [
  136,
  140,
  355
 ],
 "review the two factor authentication setup": [
  219,
  233
 ],
 "clean up old unused feature flags in the code": [
  143,
  145,
  150
 ],
 "design an api for our mobile app": [
  26,
  407
 ],
 "summarize last week's meeting notes": [
  20,
  101
 ],
 "find open source papers about transformers": [
  58,
  61,
  62
 ],
 "tune the kernel parameters on this linux box": [
  182,
  185,
  199
 ],
 "restore the database from yesterday's backup": [
  329,
  423,
  424
 ],
 "write end to end tests for checkout": [
  35,
  36
 ],
 "check the tls configuration of our server": [
  208,
  243
 ],
 "what do we know about this domain name": [
  203,
  204,
  205
 ],
 "turn these notes into a presentation": [
  104
 ]
}
# Held-out set C (30 queries): written before the final router work and never used to tune anything. Acceptable agent numbers per query.
HELD_OUT_C = {
 "write a python function that merges two sorted lists": [
  27,
  30
 ],
 "our ci keeps failing after the dependency bump": [
  31,
  38,
  39,
  43,
  122
 ],
 "find out who has access to the production database": [
  250,
  251,
  370,
  374
 ],
 "create a threat model for our payment service": [
  84,
  281,
  282
 ],
 "figure out why memory usage keeps growing": [
  31,
  122,
  190,
  199
 ],
 "turn the survey results into charts": [
  72,
  78
 ],
 "check this contract pdf for unusual clauses": [
  101,
  102
 ],
 "plan the migration from mysql to postgres": [
  6,
  7,
  327
 ],
 "what is the best way to cache api responses": [
  26,
  400,
  401,
  407
 ],
 "monitor for suspicious logins": [
  264,
  265,
  266,
  275
 ],
 "teach me how this codebase is organized": [
  28,
  29,
  158
 ],
 "build a retrieval system over our docs": [
  79,
  80,
  81
 ],
 "audit our container images for vulnerabilities": [
  247,
  252
 ],
 "check if the new release is actually live": [
  167,
  170,
  360
 ],
 "reduce the cost of our cloud bill": [
  134,
  397,
  405
 ],
 "make the login page accessible with a screen reader": [
  409
 ],
 "review our incident response plan": [
  276,
  277,
  280
 ],
 "write a postgres query to find duplicate customers": [
  73,
  77
 ],
 "automate filling out expense reports on a website": [
  46,
  56,
  428
 ],
 "decide whether we need another agent for this": [
  10,
  173,
  176,
  177
 ],
 "reproduce the bug on a clean machine": [
  31,
  122,
  316
 ],
 "scan our open ports from the outside": [
  217,
  218,
  229
 ],
 "write a clear changelog for users": [
  358,
  420
 ],
 "why does my docker build fail": [
  38,
  195,
  352
 ],
 "fine tune a small model on our support tickets": [
  411,
  412
 ],
 "summarize this long email thread": [
  20,
  22,
  101
 ],
 "estimate the blast radius of changing this config": [
  367,
  368,
  369
 ],
 "set up alerts when the error rate spikes": [
  131,
  139,
  361
 ],
 "is our s3 bucket public": [
  211,
  249
 ],
 "review this pull request for style and bugs": [
  33,
  42
 ]
}
NOT_ROUTED = ['tell me a joke', 'what is the weather today', 'qzxv wxyk', 'hello', 'write me a poem about the sea', 'please book me a flight to paris', "what's the capital of france", 'i feel tired today', 'sing a song', 'calculate 17 times 23']
# Measured results (correct, wrong, abstained, acceptable agent among top 3 candidates). Tests fail if quality drops below these.
BASELINE = {"A": [12, 1, 17, 25], "B": [13, 1, 16, 25], "C": [10, 5, 15, 24]}
SETS = {'A': HELD_OUT_A, 'B': HELD_OUT_B, 'C': HELD_OUT_C}

def outcome(cat, query, acceptable):
    top = {int(x['agent_id'][6:]) for x in cat.rank(query)[:3]}
    try:
        got = int(cat.resolve({'objective': query})[0][6:])
        return ('correct' if got in acceptable else 'wrong'), bool(top & acceptable)
    except runtime.BrainError:
        return 'abstained', bool(top & acceptable)

def measure(cat, queries):
    counts = {'correct': 0, 'wrong': 0, 'abstained': 0}; top3 = 0
    for query, acceptable in queries.items():
        kind, hit = outcome(cat, query, set(acceptable)); counts[kind] += 1; top3 += hit
    return counts['correct'], counts['wrong'], counts['abstained'], top3

class Routing(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.cat = runtime.Catalog()
    def test_development_requests_route_to_the_expected_agent(self):
        wrong = {q: self.cat.resolve({'objective': q})[0] for q, want in DEVELOPMENT.items() if self.cat.resolve({'objective': q})[0] != want}
        self.assertEqual(wrong, {}); self.assertEqual(len(DEVELOPMENT), 39)
    def test_unrelated_requests_are_not_forced(self):
        for q in NOT_ROUTED:
            with self.assertRaises(runtime.BrainError, msg=q): self.cat.resolve({'objective': q})
    def test_held_out_quality_does_not_regress(self):
        for name, queries in SETS.items():
            correct, wrong, abstained, top3 = measure(self.cat, {q: set(v) for q, v in queries.items()})
            base = BASELINE[name]
            self.assertEqual(len(queries), 30)
            self.assertGreaterEqual(correct, base[0], name); self.assertLessEqual(wrong, base[1], name); self.assertGreaterEqual(top3, base[3], name)
    def test_every_agent_resolves_from_its_own_name_and_mission(self):
        miss = []
        for aid, row in self.cat.rows.items():
            if aid == 'AGENT-000': continue
            try:
                if self.cat.resolve({'objective': row['name'] + ' ' + row['mission']})[0] != aid: miss.append(aid)
            except runtime.BrainError: miss.append(aid)
        self.assertEqual(miss, [])
    def test_api_design_for_a_mobile_app_is_not_sent_to_the_mobile_app_agent(self):
        query = 'design an API for our mobile app'
        top = [x['agent_id'] for x in self.cat.rank(query)[:3]]
        self.assertIn('AGENT-407', top[:2])
        try: self.assertNotEqual(self.cat.resolve({'objective': query})[0], 'AGENT-410')
        except runtime.BrainError: pass
    def test_stemming_joins_word_forms(self):
        self.assertEqual(runtime.tokens('optimizing queries'), runtime.tokens('optimization query'))
    def test_aliases_and_synonyms_are_well_formed(self):
        self.assertTrue(set(self.cat.aliases) <= set(self.cat.rows))
        self.assertTrue(all(isinstance(v, list) and v for v in self.cat.aliases.values()))

if __name__ == '__main__':
    unittest.main()
