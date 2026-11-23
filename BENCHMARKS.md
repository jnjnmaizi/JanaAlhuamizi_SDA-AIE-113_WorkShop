# Benchmarks

## Lab 2b: before warm-up

| Request | Time |
|---|---|
| First | 0.041225 s |
| Second | 0.004742 s |
| Third | 0.003689 s |

The first request is slower, possibly due to lazy initialization.

## Lab 2b: after warm-up

| Request | Time |
|---|---|
| First | 0.021798 s |
| Second | 0.003773 s |
| Third | 0.003318 s |

First-request latency improved by approximately 47.1%.

## Lab 2b: Load Testing

Test configuration: 2000 requests, 25 concurrent clients.

| Metric | 1 Worker | 4 Workers |
|---|---:|---:|
| p50 | 124.8 ms | 121.6 ms |
| p99 | 170.7 ms | 139.5 ms |
| Throughput | 194.6 req/s | 203.8 req/s |
| Non-2xx | 0 | 0 |

Four workers improved throughput by 4.7% and reduced
p99 latency by 18.3% in this test.
Results may vary across repeated runs and machines.
