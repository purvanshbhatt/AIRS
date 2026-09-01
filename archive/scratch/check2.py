import urllib.request, re
html = urllib.request.urlopen('https://resilai-sentinel.web.app/').read().decode('utf-8')
m = re.search(r'src="(/assets/index-.*?\.js)"', html)
if m:
    js_url = 'https://resilai-sentinel.web.app' + m.group(1)
    js = urllib.request.urlopen(js_url).read().decode('utf-8')
    matches = [m.start() for m in re.finditer('resilai.org', js)]
    for idx in matches:
        print('MATCH:', js[max(0, idx-50):min(len(js), idx+50)])
