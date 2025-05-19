from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from curl_cffi import requests
import random

app = Flask(__name__)

STARGATE_URL = "http://127.0.0.1:9999"
IMPERSONATE_LIST = [
    "chrome99", "chrome100", "chrome101", "chrome104", "chrome107", "chrome110", "chrome116",
    "chrome119", "chrome120", "chrome123", "chrome124", "chrome131", "chrome133a", "chrome136",
    "chrome99_android", "chrome131_android", "edge99", "edge101", "safari15_3", "safari15_5",
    "safari17_0", "safari17_2_ios", "safari18_0", "safari18_0_ios", "safari18_4", "safari18_4_ios",
    "firefox133", "tor145"
]

VOTE_URL = 'https://internet-roadtrip.neal.fun/vote'
HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://neal.fun/',
    'Content-Type': 'text/plain;charset=UTF-8',
    'Origin': 'https://neal.fun',
    'Sec-GPC': '1',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Priority': 'u=0',
}

@app.route('/vote', methods=['POST'])
def vote():
    data = request.get_json(force=True)
    option = data.get('option')
    stop = data.get('stop')
    votes = data.get('votes', 400)
    threads = data.get('threads', 200)

    successful_impersonates = []
    results = []

    def send_vote(_):
        use_success = successful_impersonates and random.random() < 0.75
        if use_success:
            impersonate = random.choice(successful_impersonates)
        else:
            impersonate = random.choice(IMPERSONATE_LIST)
        vote_data = f'{{"option":{option},"stop":{stop}}}'
        try:
            response = requests.post(
                VOTE_URL,
                timeout=2,
                headers=HEADERS,
                data=vote_data,
                impersonate=impersonate,
                proxy=STARGATE_URL,
                verify=False
            )
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
        if response.status_code == 200:
            if impersonate not in successful_impersonates:
                successful_impersonates.append(impersonate)
        return {'status': response.status_code}

    max_workers = min(threads, votes)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(send_vote, range(votes)))

    success_count = sum(1 for r in results if r.get('status') == 200)
    error_count = sum(1 for r in results if r.get('status') == 'error')
    return jsonify({
        'success': success_count,
        'errors': error_count,
        'total': votes,
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)