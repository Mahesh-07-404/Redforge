#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import time
import os
import sys
import json
from typing import Dict, Any

# Ensure redforge is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from redforge.observability import ObservabilityManager
from redforge.distributed import DistributedManager
from redforge.reporting import ReportingEngine
from redforge.rag.engine import RAGEngine
from redforge.rag.contracts import RAGQuery


async def benchmark_suite() -> Dict[str, Any]:
    print("=========================================")
    print("Running RedForge Performance Benchmark...")
    print("=========================================")

    results: Dict[str, Any] = {}

    # 1. Startup / Sizing Imports time
    start = time.time()
    import redforge.core
    import redforge.orchestrator
    import redforge.planner
    import redforge.executor
    import redforge.api
    import redforge.distributed
    import redforge.observability
    results["import_startup_ms"] = (time.time() - start) * 1000.0
    print(f"[*] Import Startup latency: {results['import_startup_ms']:.2f} ms")

    # 2. Memory Usage RSS sizing
    try:
        import psutil
        process = psutil.Process(os.getpid())
        results["memory_rss_mb"] = process.memory_info().rss / (1024 * 1024)
    except ImportError:
        results["memory_rss_mb"] = 0.0
    print(f"[*] Memory Usage RSS: {results['memory_rss_mb']:.2f} MB")

    # 3. Observability & Tracing Latency
    obs_mgr = ObservabilityManager(service_name="benchmark")
    start = time.time()
    for i in range(1000):
        with obs_mgr.tracer.span("BenchmarkSpan", attributes={"index": i}):
            obs_mgr.metrics.increment("benchmark_counter")
    results["obs_trace_increment_1k_ms"] = (time.time() - start) * 1000.0
    print(f"[*] Tracing/Metrics loop (1k iterations): {results['obs_trace_increment_1k_ms']:.2f} ms")

    # 4. Distributed Scheduler Latency
    dist_mgr = DistributedManager()
    start = time.time()
    # Schedule a dummy task
    await dist_mgr.submit(
        task_id="t-bench-1",
        session_id="s-bench",
        tool="nmap",
        command=[],
    )
    results["distributed_submit_latency_ms"] = (time.time() - start) * 1000.0
    print(f"[*] Distributed task scheduling submission latency: {results['distributed_submit_latency_ms']:.2f} ms")

    # 5. Report compile time
    start = time.time()
    # Mock compile report
    ReportingEngine.generate_report(
        session_id="s-demo",
        execution_id="e-demo",
        target="127.0.0.1",
        raw_evidence=[],
        entities=[],
        world_state_findings=[],
    )
    results["report_compile_markdown_ms"] = (time.time() - start) * 1000.0
    print(f"[*] Report compile latency: {results['report_compile_markdown_ms']:.2f} ms")

    # 6. RAG Retrieval time
    rag = RAGEngine()
    start = time.time()
    await rag.query(
        rag_query=RAGQuery(session_id="s-bench", query_text="SQL Injection vulnerabilities remediation"),
        all_chunks=[],
    )
    results["rag_retrieval_ms"] = (time.time() - start) * 1000.0
    print(f"[*] RAGEngine query latency: {results['rag_retrieval_ms']:.2f} ms")

    print("=========================================")
    print("Benchmark complete!")
    print("=========================================")
    return results


async def main():
    metrics = await benchmark_suite()
    # Save output to a report file
    with open("benchmark_report.json", "w") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
