import argparse
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:8000/v1/predict")
parser.add_argument("-n", type=int, default=2000)
parser.add_argument("-c", type=int, default=25)
parser.add_argument("--body", type=Path, default=Path("payloads/sample.json"))
args = parser.parse_args()

body = args.body.read_bytes()

def send_request(client):
    start = time.perf_counter()
    response = client.post(
        args.url,
        content=body,
        headers={"Content-Type": "application/json"},
    )
    elapsed = (time.perf_counter() - start) * 1000
    return elapsed, response.status_code

start = time.perf_counter()

with httpx.Client(
    limits=httpx.Limits(max_connections=args.c),
    timeout=30,
) as client:
    with ThreadPoolExecutor(max_workers=args.c) as pool:
        results = list(pool.map(send_request, [client] * args.n))

duration = time.perf_counter() - start
times = sorted(result[0] for result in results)
errors = sum(status >= 400 for _, status in results)

print(f"Requests: {args.n}")
print(f"Concurrency: {args.c}")
print(f"p50: {statistics.median(times):.1f} ms")
print(f"p99: {times[int(len(times) * 0.99) - 1]:.1f} ms")
print(f"Throughput: {args.n / duration:.1f} req/s")
print(f"Non-2xx: {errors}")
