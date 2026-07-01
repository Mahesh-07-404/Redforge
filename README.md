# RedForge Enterprise Platform (v3.0.0)

**Autonomous Distributed Penetration Testing AI Orchestration System**

RedForge is a production-grade autonomous security testing platform. It integrates reasoning LLMs, a distributed task queue, unified API Gateway, a React operations dashboard, and complete observability tracing.

---

## Technical Architecture Overview

* **React Operator Dashboard** (`dashboard/`): React + Vite + Tailwind dashboard.
* **Unified API Gateway** (`src/redforge/api/`): FastAPI REST & WebSocket entry point.
* **Distributed Engine** (`src/redforge/distributed/`): Priority queues (Redis, RabbitMQ) and automated worker pools.
* **Observability Subsystem** (`src/redforge/observability/`): Prometheus scrape outputs, context logs, Tracer spans, and immutable cryptographic audit trails.
* **Kernel & Core Execution**: Agent reasoning loop, planning engine, and tool executors.

---

## Features & Supported Tools

* **Modes**: Bug Bounty, CTF Solver, Pentesting, Secure Coding, Mobile Android testing.
* **Integrations**: Nmap, Subfinder, Nuclei, Ffuf, Nikto, Gobuster, and John the Ripper.
* **Distributed Scheduling**: Dependency graphs with recursive cancellations.
* **Autoscaling**: Automatic worker registry and heartbeat-based failure recovery.
* **Cryptographic Trail**: Sequential SHA-256 hash chains verifying audit integrity.

---

## Installation & Deployment

Refer to the operational guides for details:

* **Basic installation**: Read [INSTALL.md](file:///home/mahesh/RedForge/INSTALL.md)
* **Production deployment**: Read [DEPLOYMENT.md](file:///home/mahesh/RedForge/DEPLOYMENT.md)
* **API Documentation**: Read [API_REFERENCE.md](file:///home/mahesh/RedForge/API_REFERENCE.md)
* **Security & Audits**: Read [SECURITY.md](file:///home/mahesh/RedForge/SECURITY.md)
* **Developer Guidelines**: Read [CONTRIBUTING.md](file:///home/mahesh/RedForge/CONTRIBUTING.md)
* **Plugin System**: Read [PLUGIN_GUIDE.md](file:///home/mahesh/RedForge/PLUGIN_GUIDE.md)

---

## Quick Start

### 1. Launch with Docker Compose
To run RedForge instantly with Redis, RabbitMQ, and the worker pool:
```bash
docker compose -f docker/docker-compose.yml up --build -d
```

### 2. Verify Health
Verify the gateway service is live:
```bash
curl http://localhost:8000/api/v1/health
```

### 3. Launch React Dashboard
Start the local dashboard developer server:
```bash
cd dashboard
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.
