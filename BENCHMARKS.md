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

## Lab 3: Docker Containerization

### Image Comparison

| Metric | Naive | Optimized |
|---|---|---|
| Build time | 119.85 s | 67.36 s |
| Rebuild time | Not measured | 0.602 s |
| Disk usage | 3.33 GB | 846 MB |
| Content size | 845 MB | 180 MB |
| User | root | appuser |
| Fake secret excluded | No | Yes |

### Load Testing

2000 requests, 25 concurrent clients.

| Metric | 4 Workers | Docker |
|---|---|---|
| p50 | 121.6 ms | 55.3 ms |
| p99 | 139.5 ms | 85.0 ms |
| Throughput | 203.8 req/s | 441.7 req/s |
| Non-2xx | 0 | 0 |

### Container Resources

- Fraud API memory: 320.9 MiB / 512 MiB
- Redis memory: 10.3 MiB
- Graceful shutdown: 0.851 seconds
- Both containers passed health checks.

### Notes

Docker dependency layers were reused after a source-only change.
The observed performance improvement requires repeated testing
before attributing it to containerization.

---

## Lab 5: CI/CD Benchmarks

## GitHub Actions Performance

| Job | First Run (#1) | Latest Run (#6) |
|---|---|---|
| lint | 44s | 30s |
| test | 47s | 38s |
| image-smoke | 2m 24s | 37s |
| publish | 31s | Skipped |
| Total | 3m 50s | 1m 37s |

## Analysis

All required checks passed in both runs.

The image-smoke job improved from 144 seconds to
37 seconds, a reduction of approximately 74%.

Docker BuildKit caching likely contributed to this
improvement by reusing previously built image layers.

Run #6 was manually triggered, so the publish job
was skipped. Therefore, the total pipeline durations
are not directly comparable.

## Conclusion

Automated CI/CD validates code quality, tests,
architecture constraints, and Docker functionality.

Caching can reduce build time while preserving
the same quality checks.
