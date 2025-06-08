# Production Deployment Guide

This guide describes how to deploy the AI Video Pipeline in a production environment.

## Docker Image

- Use a multi-stage Docker build to keep the runtime image lightweight.
- Build the image with `docker build -t ai-video-pipeline:latest .`.
- Store configuration values such as API keys in environment variables.

## Kubernetes Deployment

1. Create a Kubernetes cluster and install Helm.
2. Use the provided Helm chart in `deploy/helm/` to deploy the service.
3. Apply environment-specific values using `helm install ai-video-pipeline ./deploy/helm -f values-production.yaml`.

## Configuration Management

Environment variables are loaded from Kubernetes Secrets and ConfigMaps. Do not commit secrets to source control.

## Monitoring and Alerting

- Deploy Prometheus and Grafana for metrics collection and dashboards.
- Configure alert rules for CPU usage, memory, and request latency.

## Backup and Disaster Recovery

- Persist generated videos to an external volume or cloud storage.
- Regularly back up the database and user uploads.
- Maintain an automated recovery plan that restores from backups.

