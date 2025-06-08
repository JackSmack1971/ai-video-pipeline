# Performance Optimization Guide

Follow these tips to keep the AI Video Pipeline responsive and efficient.

1. **Resource Limits**: Configure CPU and memory limits in your Kubernetes manifests to prevent resource starvation.
2. **Parallelism**: Adjust the number of worker processes based on available hardware.
3. **Cache Results**: Reuse previously generated assets when possible to save time and costs.
4. **Monitoring**: Use Prometheus metrics to identify bottlenecks and adjust settings accordingly.
5. **Timeouts and Retries**: Implement sane defaults for API timeouts and retry intervals as defined in `AGENTS.md`.
