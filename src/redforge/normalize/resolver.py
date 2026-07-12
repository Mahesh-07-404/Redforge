from .contracts import EntityRelation
from .schema import NormalizedEntity


class RelationshipResolver:
    @staticmethod
    def resolve_relationships(entities: list[NormalizedEntity]) -> list[EntityRelation]:
        relationships = []
        hosts = [e for e in entities if e.entity_type == "Host"]
        ports = [e for e in entities if e.entity_type == "Port"]
        services = [e for e in entities if e.entity_type == "Service"]
        techs = [e for e in entities if e.entity_type == "Technology"]
        findings = [e for e in entities if e.entity_type == "Finding"]
        cves = [e for e in entities if e.entity_type == "CVE"]
        urls = [e for e in entities if e.entity_type == "URLResource"]
        dirs = [e for e in entities if e.entity_type == "Directory"]

        for p in ports:
            for s in services:
                relationships.append(
                    EntityRelation(source_id=p.id, target_id=s.id, relation_type="Port_TO_Service")
                )

        for h in hosts:
            for p in ports:
                relationships.append(
                    EntityRelation(source_id=h.id, target_id=p.id, relation_type="Host_TO_Port")
                )

        for h in hosts:
            for t in techs:
                relationships.append(
                    EntityRelation(
                        source_id=h.id, target_id=t.id, relation_type="Host_TO_Technology"
                    )
                )

        for h in hosts:
            for f in findings:
                relationships.append(
                    EntityRelation(source_id=h.id, target_id=f.id, relation_type="Host_TO_Finding")
                )

        for f in findings:
            for c in cves:
                relationships.append(
                    EntityRelation(source_id=f.id, target_id=c.id, relation_type="Finding_TO_CVE")
                )

        for u in urls:
            for d in dirs:
                relationships.append(
                    EntityRelation(source_id=u.id, target_id=d.id, relation_type="URL_TO_Directory")
                )

        return relationships
