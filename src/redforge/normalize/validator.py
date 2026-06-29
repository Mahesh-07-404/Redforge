from typing import List
from .schema import NormalizedEntity
from .contracts import EntityRelation, NormalizationStatus

class NormalizationValidator:
    def validate(self, entities: List[NormalizedEntity], relationships: List[EntityRelation]) -> NormalizationStatus:
        errors = []
        warnings = []
        
        seen_ids = set()
        for e in entities:
            if not e.id:
                errors.append(f"Entity is missing an ID (Type: {e.entity_type}, Value: {e.value})")
            elif e.id in seen_ids:
                warnings.append(f"Duplicate entity ID found: {e.id}")
            seen_ids.add(e.id)
            
        for r in relationships:
            if r.source_id not in seen_ids:
                errors.append(f"Relationship source_id {r.source_id} not found in entities list.")
            if r.target_id not in seen_ids:
                errors.append(f"Relationship target_id {r.target_id} not found in entities list.")
                
        for e in entities:
            if not e.value or not e.value.strip():
                errors.append(f"Entity {e.id} has empty value.")
                
        status = "FAIL" if errors else "PASS"
        return NormalizationStatus(status=status, errors=errors, warnings=warnings)
