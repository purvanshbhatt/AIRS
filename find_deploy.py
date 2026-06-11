import urllib.request
import json
import datetime

req = urllib.request.Request('https://api.github.com/repos/purvanshbhatt/AIRS/actions/runs?branch=main&status=success')
req.add_header('Accept', 'application/vnd.github.v3+json')
res = urllib.request.urlopen(req)
data = json.loads(res.read())
for r in data['workflow_runs']:
    if r['name'] == 'ci-deploy':
        print(f"Deploy Success - Commit: {r['head_sha']} at {r['created_at']}")
