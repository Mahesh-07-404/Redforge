import pytest
import os
import shutil
from redforge.executor.contracts import ExecutionResult, TaskResult
from redforge.executor.state import ExecutionStatus
from redforge.evidence.hashing import calculate_sha256
from redforge.evidence.artifacts import ArtifactManager
from redforge.evidence.timeline import TimelineGenerator
from redforge.evidence.collector import EvidenceCollector
from redforge.evidence.store import EvidenceStore
from redforge.evidence.serializer import EvidenceSerializer

def test_hash_generation():
    content = "test content"
    expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
    assert calculate_sha256(content) == expected

def test_artifact_manager():
    task_res = TaskResult(
        task_id="nmap",
        status=ExecutionStatus.COMPLETED,
        raw_output="raw nmap scan",
        structured_output={"ports": [{"port": 80}]},
        exit_code=0,
        duration=1.5
    )
    
    art = ArtifactManager.create_artifact(
        task_result=task_res,
        content_type="raw_output",
        content=task_res.raw_output,
        session_id="session123",
        execution_id="exec456",
        tool="nmap",
        target="example.com",
        risk="MEDIUM",
        platform="Kali Linux"
    )
    
    assert art.content == "raw nmap scan"
    assert art.content_type == "raw_output"
    assert art.metadata.session_id == "session123"
    assert art.metadata.tool == "nmap"
    assert art.metadata.risk == "MEDIUM"
    assert art.metadata.platform == "Kali Linux"

def test_timeline_generation():
    exec_result = ExecutionResult(
        plan_goal="Scan ports",
        status=ExecutionStatus.COMPLETED,
        task_results=[
            TaskResult(task_id="nmap", status=ExecutionStatus.COMPLETED, duration=2.0)
        ]
    )
    
    timeline = TimelineGenerator.generate_timeline("sess1", "ex1", exec_result)
    assert timeline.session_id == "sess1"
    assert timeline.execution_id == "ex1"
    assert len(timeline.events) == 4 # ExecutionStarted, TaskStarted, TaskFinished, ExecutionFinished
    assert timeline.events[0].event == "ExecutionStarted"

def test_evidence_collector():
    collector = EvidenceCollector()
    exec_result = ExecutionResult(
        plan_goal="Passive recon",
        status=ExecutionStatus.COMPLETED,
        task_results=[
            TaskResult(
                task_id="subfinder",
                status=ExecutionStatus.COMPLETED,
                raw_output="sub1\nsub2",
                structured_output={"subdomains": ["sub1", "sub2"]},
                duration=3.0
            )
        ]
    )
    
    bundle = collector.collect("sess1", exec_result, "example.com", "Kali Linux")
    assert bundle.session_id == "sess1"
    assert bundle.plan_goal == "Passive recon"
    assert len(bundle.evidence_list) == 1
    
    evidence = bundle.evidence_list[0]
    assert evidence.task_id == "subfinder"
    assert len(evidence.artifacts) == 2 # raw_output and parsed_output

def test_evidence_store(tmp_path):
    store_dir = str(tmp_path / "test_data")
    store = EvidenceStore(base_dir=store_dir)
    
    exec_result = ExecutionResult(
        plan_goal="Check ports",
        status=ExecutionStatus.COMPLETED,
        task_results=[
            TaskResult(task_id="nmap", status=ExecutionStatus.COMPLETED, raw_output="ports data")
        ]
    )
    collector = EvidenceCollector()
    bundle = collector.collect("sess99", exec_result, "example.com", "Ubuntu")
    
    # Store bundle
    store.store_bundle(bundle)
    
    # Verify file structures
    sess_dir = os.path.join(store_dir, "evidence", "sess99")
    assert os.path.exists(os.path.join(sess_dir, "evidence.json"))
    assert os.path.exists(os.path.join(sess_dir, "timeline.json"))
    assert os.path.exists(os.path.join(sess_dir, "artifacts", "nmap_raw_output.json"))
    
    # Load bundle back
    loaded = store.load_bundle("sess99")
    assert loaded.session_id == "sess99"
    assert loaded.plan_goal == "Check ports"

def test_evidence_serializer():
    exec_result = ExecutionResult(
        plan_goal="Scan target",
        status=ExecutionStatus.COMPLETED,
        task_results=[
            TaskResult(task_id="subfinder", status=ExecutionStatus.COMPLETED, raw_output="subdomain.com")
        ]
    )
    collector = EvidenceCollector()
    bundle = collector.collect("sess1", exec_result, "example.com", "Ubuntu")
    
    # JSON serialization
    js = EvidenceSerializer.serialize_to_json(bundle)
    assert "sess1" in js
    
    # Markdown serialization
    md = EvidenceSerializer.serialize_to_markdown(bundle)
    assert "# Evidence Bundle:" in md
    assert "subdomain.com" in md
    
    # Plain Text serialization
    txt = EvidenceSerializer.serialize_to_text(bundle)
    assert "Evidence Bundle:" in txt
    assert "subdomain.com" in txt
