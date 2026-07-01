# RedForge Production Deployment Guide

This guide provides configuration instructions to deploy RedForge in containerized environments.

---

## 1. Docker Compose (Single-Server Deployment)

For standalone servers, run all services using Docker Compose:

```bash
docker compose -f docker/docker-compose.yml up -d
```

This starts:
1. `api` (FastAPI Gateway) on port `8000`
2. `worker` (Distributed task runner)
3. `redis` (Queue/Cache registry) on port `6379`
4. `rabbitmq` (AMQP queue broker) on port `5672`

---

## 2. Kubernetes Deployment

To deploy RedForge on an active Kubernetes cluster:

### Manifest Files
Deploy the manifest files located under `k8s/`:
```bash
kubectl apply -f k8s/deployment.yaml
```

### Helm Installation
To install the Helm chart:
```bash
helm install redforge ./helm
```

---

## 3. Environment Profiles

RedForge supports profiles to load distinct configurations:
* **Development** (`.env.development`): Verbose debug logging, relaxed rate-limiting, and test secret parameters.
* **Testing** (`.env.testing`): Local isolated parameters suitable for unit and integration pipelines.
* **Staging** (`.env.staging`): Links to staging databases and API setups.
* **Production** (`.env.production`): High security configuration, warnings-only logging, strict rate-limiting, and secure secrets.

Set the profile by specifying the environment variable:
```bash
export REDFORGE_ENV=production
```
