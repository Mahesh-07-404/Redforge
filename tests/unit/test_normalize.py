import pytest
import json
from redforge.evidence.contracts import EvidenceBundle, Evidence, Artifact
from redforge.evidence.metadata import ArtifactMetadata
from redforge.evidence.timeline import ExecutionTimeline, TimelineEvent
from redforge.normalize.schema import EvidenceReference
from redforge.normalize.entities import (
    HostEntity, URLResource, TechnologyEntity, PortEntity, ServiceEntity,
    FindingEntity, CVEEntity, DirectoryEntity
)
from redforge.normalize.contracts import EntityRelation
from redforge.normalize.registry import MapperRegistry
from redforge.normalize.resolver import RelationshipResolver
from redforge.normalize.validator import NormalizationValidator
from redforge.normalize.normalizer import ResultNormalizer

def test_mapper_registry():
    registry = MapperRegistry()
    
    # Subfinder mapper
    sub_map = registry.get_mapper("subfinder")
    assert sub_map is not None
    assert sub_map.tool_name == "subfinder"
    
    # Httpx mapper
    httpx_map = registry.get_mapper("httpx")
    assert httpx_map is not None
    assert httpx_map.tool_name == "httpx"
    
    # Unknown tool
    assert registry.get_mapper("nonexistent") is None

def test_relationship_resolver():
    meta_args = {
        "session_id": "s1", "execution_id": "ex1", "target": "example.com",
        "timestamp": "2026-06-29T12:00:00"
    }
    
    entities = [
        HostEntity(id="host_example.com", value="example.com", source_tool="subfinder", **meta_args),
        PortEntity(id="port_80", value="80", source_tool="nmap", **meta_args),
        ServiceEntity(id="service_http", value="http", source_tool="nmap", **meta_args),
        TechnologyEntity(id="tech_nginx", value="nginx", source_tool="httpx", **meta_args),
        FindingEntity(id="finding_vuln", value="vuln", source_tool="nuclei", **meta_args),
        CVEEntity(id="cve_2026", value="CVE-2026-1234", source_tool="nuclei", **meta_args),
        URLResource(id="url_http://example.com/test", value="http://example.com/test", source_tool="httpx", **meta_args),
        DirectoryEntity(id="dir_/test", value="/test", source_tool="ffuf", **meta_args)
    ]
    
    relations = RelationshipResolver.resolve_relationships(entities)
    rel_types = [r.relation_type for r in relations]
    
    assert "Port_TO_Service" in rel_types
    assert "Host_TO_Port" in rel_types
    assert "Host_TO_Technology" in rel_types
    assert "Host_TO_Finding" in rel_types
    assert "Finding_TO_CVE" in rel_types
    assert "URL_TO_Directory" in rel_types

def test_normalization_validator():
    validator = NormalizationValidator()
    meta_args = {
        "session_id": "s1", "execution_id": "ex1", "target": "example.com",
        "timestamp": "2026-06-29T12:00:00", "source_tool": "subfinder"
    }
    
    # 1. Valid validation
    entities = [
        HostEntity(id="h1", value="example.com", **meta_args),
        PortEntity(id="p1", value="80", **meta_args)
    ]
    relations = [
        EntityRelation(source_id="h1", target_id="p1", relation_type="Host_TO_Port")
    ]
    status = validator.validate(entities, relations)
    assert status.status == "PASS"
    assert not status.errors
    
    # 2. Duplicate validation
    duplicate_entities = [
        HostEntity(id="h1", value="example.com", **meta_args),
        HostEntity(id="h1", value="another.com", **meta_args)
    ]
    status_dup = validator.validate(duplicate_entities, [])
    assert len(status_dup.warnings) == 1
    assert "Duplicate entity ID found" in status_dup.warnings[0]
    
    # 3. Missing references
    invalid_relations = [
        EntityRelation(source_id="h1", target_id="p999", relation_type="Host_TO_Port")
    ]
    status_invalid = validator.validate(entities, invalid_relations)
    assert status_invalid.status == "FAIL"
    assert any("not found" in err for err in status_invalid.errors)

def test_result_normalizer_pipeline():
    normalizer = ResultNormalizer()
    
    # Construct EvidenceBundle
    art_meta = ArtifactMetadata(
        session_id="s123", execution_id="ex456", task_id="subfinder",
        tool="subfinder", target="example.com", timestamp="2026-06-29T12:00:00",
        duration=1.2, exit_code=0, risk="LOW", status="COMPLETED", hash="abc",
        platform="Kali Linux"
    )
    
    timeline = ExecutionTimeline(
        session_id="s123", execution_id="ex456",
        events=[TimelineEvent(timestamp="2026-06-29T12:00:00", event="Started", description="desc")]
    )
    
    evidence_item = Evidence(
        id="ev_sub",
        task_id="subfinder",
        status="COMPLETED",
        duration=1.2,
        exit_code=0,
        artifacts=[
            Artifact(
                id="sub_parsed",
                name="subfinder parsed",
                content_type="parsed_output",
                content=json.dumps({"subdomains": ["one.example.com", "two.example.com"]}),
                metadata=art_meta
            )
        ]
    )
    
    bundle = EvidenceBundle(
        session_id="s123",
        execution_id="ex456",
        plan_goal="Passive recon",
        timeline=timeline,
        evidence_list=[evidence_item]
    )
    
    res = normalizer.normalize(bundle)
    assert res.status.status == "PASS"
    
    entities = res.bundle.entities
    assert len(entities) == 2
    assert all(e.entity_type == "Host" for e in entities)
    assert entities[0].value == "one.example.com"
    assert entities[1].value == "two.example.com"
    
    # Original evidence remains untouched
    assert bundle.evidence_list[0].artifacts[0].content_type == "parsed_output"
