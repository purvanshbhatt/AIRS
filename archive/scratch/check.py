import urllib.request, re

try:
    req = urllib.request.Request('https://resilai-sentinel.web.app/')
    html = urllib.request.urlopen(req).read().decode('utf-8')
    m = re.search(r'src="(/assets/index-.*?\.js)"', html)
    if m:
        js_url = 'https://resilai-sentinel.web.app' + m.group(1)
        print('Fetching JS:', js_url)
        js = urllib.request.urlopen(js_url).read().decode('utf-8')
        if 'resilai.org' in js:
            print('JS CONTAINS resilai.org')
            idx = js.find('resilai.org')
            print('CONTEXT:', js[max(0, idx-100):min(len(js), idx+100)])
        else:
            print('JS DOES NOT CONTAIN resilai.org')
    else:
        print('No JS file found in HTML')
except Exception as e:
    print('Error:', e)
