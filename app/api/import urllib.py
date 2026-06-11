import urllib.request
import urllib.error

urls = [
    "https://resilai.org",
    "https://staging.resilai.org",
    "https://demo.resilai.org",
    "https://api.resilai.org/health",
    "https://api-staging.resilai.org/health"
]

print("Starting diagnostics...")
for url in urls:
    try:
        response = urllib.request.urlopen(url, timeout=10)
        print(f"SUCCESS: {url} -> {response.getcode()}")
    except urllib.error.HTTPError as e:
        print(f"HTTP ERROR: {url} -> {e.code} ({e.reason})")
    except urllib.error.URLError as e:
        print(f"URL ERROR (Connection/DNS): {url} -> {e.reason}")
    except Exception as e:
        print(f"OTHER ERROR: {url} -> {e}")