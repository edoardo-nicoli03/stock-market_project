import requests

# Configuration
BASE_URL = 'http://localhost:5500'
LOGIN_URL = f'{BASE_URL}/api/auth/login'
QUOTE_URL = f'{BASE_URL}/api/stocks/AAPL/quote'

def get_access_token(email, password):
    """Log in and return the access token."""
    resp = requests.post(LOGIN_URL, json={'email': email, 'password': password})
    resp.raise_for_status()
    tokens = resp.json()['data']['tokens']
    return tokens['access_token']

def test_rate_limit(token, max_requests=110):
    """Send repeated quote requests until rate limit (429) is hit."""
    headers = {'Authorization': f'Bearer {token}'}
    for i in range(1, max_requests + 1):
        resp = requests.get(QUOTE_URL, headers=headers)
        print(f"Request {i}: {resp.status_code}")
        if resp.status_code == 429:
            print(f"💡 Rate limit reached at request {i}")
            break
    else:
        print("💡 Did not hit rate limit within the given requests")

if __name__ == '__main__':
    # Basic user credentials
    email = 'user@example.com'
    password = 'user'

    print("🔐 Logging in as basic user...")
    token = get_access_token(email, password)
    print("✅ Access token obtained. Testing rate limit...\n")
    test_rate_limit(token)
