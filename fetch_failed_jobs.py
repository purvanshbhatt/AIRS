import urllib.request
import json
import sys

req = urllib.request.Request('https://api.github.com/repos/purvanshbhatt/AIRS/actions/runs?branch=main')
req.add_header('Accept', 'application/vnd.github.v3+json')
res = urllib.request.urlopen(req)
data = json.loads(res.read())
for r in data['workflow_runs'][:5]:
    if r['name'] == 'ci-deploy':
        run_id = r['id']
        jobs_req = urllib.request.Request(f'https://api.github.com/repos/purvanshbhatt/AIRS/actions/runs/{run_id}/jobs')
        jobs_req.add_header('Accept', 'application/vnd.github.v3+json')
        jobs_res = urllib.request.urlopen(jobs_req)
        jobs_data = json.loads(jobs_res.read())
        for j in jobs_data['jobs']:
            if j['conclusion'] == 'failure':
                print(f"Failed job in run {run_id}: {j['name']}")
                # We can't fetch logs directly without redirect, but we can print the steps
                for step in j['steps']:
                    if step['conclusion'] == 'failure':
                        print(f"  Failed step: {step['name']}")
