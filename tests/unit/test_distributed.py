from __future__ import annotations

import asyncio
import time
import pytest
from redforge.distributed import (
    DistributedManager,
    InMemoryQueue,
    RedisQueue,
    WorkerRegistry,
    DistributedScheduler,
    TaskDispatcher,
    LoadBalancer,
    LeaseManager,
    RetryPolicy,
    DistributedWorker,
    TaskMessage,
    TaskStatus,
    WorkerStatus,
    TaskResult,
    WorkerMetadata,
    DistributedAutoscaler,
)


@pytest.mark.asyncio
async def test_queue_priority_and_operations() -> None:
    queue = InMemoryQueue()
    assert await queue.size() == 0

    task1 = TaskMessage(
        task_id="t1", session_id="s1", tool="nmap", command=["nmap", "127.0.0.1"], priority=1
    )
    task2 = TaskMessage(
        task_id="t2", session_id="s1", tool="nmap", command=["nmap", "127.0.0.1"], priority=10
    )
    task3 = TaskMessage(
        task_id="t3", session_id="s1", tool="nmap", command=["nmap", "127.0.0.1"], priority=5
    )

    await queue.push(task1)
    await queue.push(task2)
    await queue.push(task3)

    assert await queue.size() == 3

    # Priority POP should return highest priority first (t2 -> t3 -> t1)
    popped = await queue.pop()
    assert popped.task_id == "t2"
    assert popped.status == TaskStatus.ASSIGNED

    popped = await queue.pop()
    assert popped.task_id == "t3"

    # Remove t1
    await queue.remove("t1")
    assert await queue.size() == 0

    # Redis queue fallback test
    redis_q = RedisQueue(host="invalid_host", port=9999)
    await redis_q.connect()
    # Should fall back to in-memory silently
    await redis_q.push(task1)
    assert await redis_q.size() == 1
    popped = await redis_q.pop()
    assert popped.task_id == "t1"


@pytest.mark.asyncio
async def test_worker_registration_and_heartbeats() -> None:
    registry = WorkerRegistry(heartbeat_timeout=1.0)
    
    # Register worker
    worker = registry.register("w1", "127.0.0.1", ["nmap", "nuclei"], weight=2.0)
    assert worker.worker_id == "w1"
    assert worker.weight == 2.0
    assert worker.status == WorkerStatus.ONLINE

    assert len(registry.list_online_workers()) == 1

    # Heartbeat update
    registry.heartbeat("w1", load=2)
    meta = registry.get("w1")
    assert meta.load == 2

    # Simulate heartbeat timeout
    time.sleep(1.2)
    marked = registry.cleanup_offline_workers()
    assert "w1" in marked
    assert registry.get("w1").status == WorkerStatus.OFFLINE
    assert len(registry.list_online_workers()) == 0

    # Unregister
    registry.unregister("w1")
    assert registry.get("w1") is None


@pytest.mark.asyncio
async def test_load_balancer_algorithms() -> None:
    lb = LoadBalancer()
    
    workers = [
        WorkerMetadata(worker_id="w1", host="h1", capabilities=["nmap"], load=1, weight=1.0),
        WorkerMetadata(worker_id="w2", host="h2", capabilities=["nmap"], load=0, weight=2.0),
        WorkerMetadata(worker_id="w3", host="h3", capabilities=["ffuf"], load=0, weight=1.0),
    ]

    task_nmap = TaskMessage(
        task_id="t1", session_id="s1", tool="nmap", command=["nmap"], priority=1
    )
    task_ffuf = TaskMessage(
        task_id="t2", session_id="s1", tool="ffuf", command=["ffuf"], priority=1
    )

    # Capability routing
    selected = lb.select(task_ffuf, workers, "least_loaded")
    assert selected.worker_id == "w3"

    # Least Loaded algorithm for nmap (w2 is load=0, w1 is load=1)
    selected = lb.select(task_nmap, workers, "least_loaded")
    assert selected.worker_id == "w2"

    # Weighted load balance
    workers[0].load = 2  # w1 load/weight = 2/1 = 2.0
    workers[1].load = 3  # w2 load/weight = 3/2 = 1.5
    selected = lb.select(task_nmap, workers, "weighted")
    assert selected.worker_id == "w2"

    # Round Robin
    workers[0].load = 0
    workers[1].load = 0
    selected_rr1 = lb.select(task_nmap, workers, "round_robin")
    selected_rr2 = lb.select(task_nmap, workers, "round_robin")
    assert selected_rr1.worker_id != selected_rr2.worker_id


@pytest.mark.asyncio
async def test_scheduler_dependencies_and_cancellation() -> None:
    queue = InMemoryQueue()
    sched = DistributedScheduler(queue=queue)

    # t2 depends on t1
    task1 = TaskMessage(task_id="t1", session_id="s1", tool="nmap", command=["nmap"])
    task2 = TaskMessage(
        task_id="t2", session_id="s1", tool="nuclei", command=["nuclei"], dependencies=["t1"]
    )

    await sched.schedule(task1)
    await sched.schedule(task2)

    # t1 should be queued (no dependencies), t2 is pending dependency
    assert await queue.size() == 1
    state = await sched.get_state()
    assert state["pending_count"] == 1

    # Pop and complete t1
    popped = await queue.pop()
    assert popped.task_id == "t1"
    
    unblocked = await sched.complete_task("t1")
    assert len(unblocked) == 1
    assert unblocked[0].task_id == "t2"
    assert await queue.size() == 1

    state = await sched.get_state()
    assert state["pending_count"] == 0
    assert state["completed_count"] == 1

    # Test recursive cancellation on failure
    await queue.clear()
    task_a = TaskMessage(task_id="ta", session_id="s1", tool="nmap", command=["nmap"])
    task_b = TaskMessage(
        task_id="tb", session_id="s1", tool="nuclei", command=["nuclei"], dependencies=["ta"]
    )
    task_c = TaskMessage(
        task_id="tc", session_id="s1", tool="ffuf", command=["ffuf"], dependencies=["tb"]
    )

    await sched.schedule(task_a)
    await sched.schedule(task_b)
    await sched.schedule(task_c)

    # ta is in queue, tb & tc are pending ta
    cancelled_ids = await sched.fail_task("ta")
    assert "tb" in cancelled_ids
    assert "tc" in cancelled_ids


@pytest.mark.asyncio
async def test_task_leases_and_timeouts() -> None:
    lm = LeaseManager()
    
    # Acquire lease
    lm.acquire("task-1", "worker-1", duration=0.5)
    assert lm.get_owner("task-1") == "worker-1"

    # Renew lease
    lm.renew("task-1", "worker-1", duration=10.0)
    assert lm.get_owner("task-1") == "worker-1"

    # Expire check
    lm.acquire("task-2", "worker-1", duration=-1.0)  # Expired instantly
    expired = lm.check_expired()
    assert "task-2" in expired
    assert lm.get_owner("task-2") is None


@pytest.mark.asyncio
async def test_autoscaler_dynamics() -> None:
    registry = WorkerRegistry()
    queue = InMemoryQueue()

    def worker_factory(wid: str) -> DistributedWorker:
        return DistributedWorker(worker_id=wid, registry=registry)

    # Min workers = 1, Max = 3
    autoscaler = DistributedAutoscaler(
        registry=registry,
        queue=queue,
        worker_factory=worker_factory,
        min_workers=1,
        max_workers=3,
        scale_up_threshold=2,
        check_interval=0.1,
    )

    await autoscaler.start()
    await asyncio.sleep(0.2)
    # Check that it scale up to min size
    assert len(autoscaler.active_autoscaled_workers) == 1

    # Load up the queue
    for i in range(5):
        await queue.push(
            TaskMessage(task_id=f"t-{i}", session_id="s1", tool="nmap", command=["nmap"])
        )

    # Let monitor check size and scale up
    await asyncio.sleep(0.3)
    # Should scale up to max_workers limit (3)
    assert len(autoscaler.active_autoscaled_workers) == 3

    # Empty queue and monitor scale down
    await queue.clear()
    await asyncio.sleep(0.3)
    assert len(autoscaler.active_autoscaled_workers) == 1

    await autoscaler.stop()


@pytest.mark.asyncio
async def test_retry_policies() -> None:
    policy = RetryPolicy(max_retries=2, base_delay=0.1, exponential=True)
    task = TaskMessage(task_id="t1", session_id="s1", tool="nmap", command=[], max_retries=2)

    assert policy.should_retry(task) is True
    assert policy.get_delay(task) == 0.1

    task.retries = 1
    assert policy.should_retry(task) is True
    assert policy.get_delay(task) == 0.2

    task.retries = 2
    assert policy.should_retry(task) is False


@pytest.mark.asyncio
async def test_full_distributed_execution_manager() -> None:
    manager = DistributedManager(heartbeat_timeout=1.0)
    await manager.start()

    # Create worker
    await manager.create_local_worker("worker-core", capabilities=["nmap"])

    # Submit task
    task = await manager.submit(
        task_id="t-nmap-1",
        session_id="s-demo",
        tool="nmap",
        command=["nmap", "127.0.0.1"],
        timeout=10.0,
    )

    # Wait for completion loop
    for _ in range(20):
        await asyncio.sleep(0.2)
        status = manager.get_status("t-nmap-1")
        if status == TaskStatus.COMPLETED:
            break

    assert manager.get_status("t-nmap-1") == TaskStatus.COMPLETED
    result = manager.get_result("t-nmap-1")
    assert result is not None
    assert "Host 127.0.0.1 up" in result.stdout
    assert result.exit_code == 0

    # Test stats
    stats = await manager.get_monitoring_stats()
    assert stats["total_tasks"] == 1
    assert stats["task_statuses"]["completed"] == 1

    await manager.stop()
