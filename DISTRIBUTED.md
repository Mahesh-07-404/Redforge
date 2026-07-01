# RedForge Distributed Execution Platform

This document describes the design, configuration, and operation of the Distributed Execution Platform introduced in Phase 18.

---

## Architecture Overview

The distributed execution engine enables RedForge to orchestrate security workflows across a multi-node worker pool:

```
                  Planner
                     │
              Workflow Engine
                     │
        Distributed Manager / Coordinator
                     │
            Distributed Scheduler (Dependency-aware)
                     │
             Queue (InMemory, Redis, RabbitMQ)
                     │
            Task Dispatcher (Lease managed)
                     │
             Load Balancer
                     │
             Distributed Worker Pool
```

---

## Sub-Components

1. **DistributedManager** ([manager.py](file:///home/mahesh/RedForge/src/redforge/distributed/manager.py)):
   The main manager orchestrating the platform. Exposes task submission APIs, manages local worker worker pools, and handles coordinator hooks.
2. **DistributedScheduler** ([scheduler.py](file:///home/mahesh/RedForge/src/redforge/distributed/scheduler.py)):
   Tracks dependency graphs. Holds tasks with unresolved parent tasks in a `PENDING` list and pushes them to the queue only when all upstream dependencies complete successfully. Cascades cancellations down the graph on parent failures.
3. **Queue System** ([queue.py](file:///home/mahesh/RedForge/src/redforge/distributed/queue.py)):
   Provides unified queue wrappers. Supports:
   * `InMemoryQueue`: Thread-safe, priority-sorted priority queue.
   * `RedisQueue`: ZSet-based priority queue with automated in-memory fallbacks if the connection fails.
   * `RabbitMQQueue`: AMQP-based client wrapper.
4. **TaskDispatcher** ([dispatcher.py](file:///home/mahesh/RedForge/src/redforge/distributed/dispatcher.py)):
   Pops tasks from the active queue, queries online nodes, selects routes using the Load Balancer, and assigns execution leases.
5. **LoadBalancer** ([load_balancer.py](file:///home/mahesh/RedForge/src/redforge/distributed/load_balancer.py)):
   Supports multiple routing algorithms:
   * **Round Robin**: Cycle through nodes.
   * **Least Loaded**: Assign to the node running the fewest concurrent tasks.
   * **Capability-Based Routing**: Restricts task dispatching to workers reporting support for the required tool.
   * **Weighted**: Select minimum `load / weight` ratio.
6. **LeaseManager** ([lease.py](file:///home/mahesh/RedForge/src/redforge/distributed/lease.py)):
   Controls worker leases. Prevents task starvation and locks. Detects expired leases to trigger rescheduling.
7. **HeartbeatMonitor** ([heartbeat.py](file:///home/mahesh/RedForge/src/redforge/distributed/heartbeat.py)):
   Runs health checks and automatically cleans up stale offline workers.
8. **DistributedWorker** ([worker.py](file:///home/mahesh/RedForge/src/redforge/distributed/worker.py)):
   Autonomous execution worker. Auto-registers, sends heartbeats, consumes task payloads, checks timeouts, and returns structured result objects.
9. **DistributedAutoscaler** ([autoscaler.py](file:///home/mahesh/RedForge/src/redforge/distributed/autoscaler.py)):
   Dynamically scales local worker pools up or down based on queue sizes and active worker loads.

---

## Fault Tolerance & Resilience

* **Stale Worker Removal**: Stale workers that miss heartbeats for more than `heartbeat_timeout` seconds are automatically marked offline.
* **Lease Rescheduling**: If a worker fails, its active tasks are recovered, lease records are cleared, and tasks are rescheduled.
* **Retry Policies**: Tasks are retried with exponential backoff. Failed tasks exceeding the maximum retry limit are sent to a Dead-Letter Queue (DLQ).
* **Cascading Failures**: If a parent task fails and exhausts its retries, all downstream dependent tasks are recursively cancelled.

---

## Developer Guide & Testing

Run the distributed test suite with the following command:

```bash
pytest tests/unit/test_distributed.py
```
