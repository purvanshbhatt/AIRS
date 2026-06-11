import urllib.request
import json

req = urllib.request.Request('https://api.github.com/repos/purvanshbhatt/AIRS/actions/runs?branch=main')
req.add_header('Accept', 'application/vnd.github.v3+json')
res = urllib.request.urlopen(req)
data = json.loads(res.read())
for r in data['workflow_runs'][:6]:
    print(f"Name: {r['name']}, Status: {r['conclusion']} (SHA: {r['head_sha']})")
