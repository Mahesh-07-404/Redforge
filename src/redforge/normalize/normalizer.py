import logging

from ..evidence.contracts import EvidenceBundle
from .contracts import NormalizationResult, NormalizedBundle
from .registry import MapperRegistry
from .resolver import RelationshipResolver
from .schema import EvidenceReference
from .validator import NormalizationValidator

logger = logging.getLogger(__name__)


class ResultNormalizer:
    def __init__(self):
        self.registry = MapperRegistry()
        self.validator = NormalizationValidator()

    def normalize(self, bundle: EvidenceBundle) -> NormalizationResult:
        entities = []
        meta = {
            "session_id": bundle.session_id,
            "execution_id": bundle.execution_id,
            "target": bundle.plan_goal,
            "timestamp": bundle.timeline.events[0].timestamp if bundle.timeline.events else "",
        }

        for ev in bundle.evidence_list:
            tool_name = ev.task_id.lower()
            mapper = self.registry.get_mapper(tool_name)
            if not mapper:
                continue

            for art in ev.artifacts:
                ref = EvidenceReference(
                    task_id=ev.task_id, artifact_id=art.id, hash=art.metadata.hash
                )

                import json

                parsed_content = {}
                if art.content_type == "parsed_output":
                    try:
                        parsed_content = json.loads(art.content)
                    except (
                        ValueError,
                        TypeError,
                    ) as exc:  # nosec B110 - best-effort artifact JSON decode
                        logger.debug(
                            "Failed to decode artifact JSON (task=%s, artifact=%s): %s",
                            ev.task_id,
                            art.id,
                            exc,
                        )

                try:
                    tool_entities = mapper.map_output(
                        raw_content=art.content, parsed_content=parsed_content, ref=ref, meta=meta
                    )
                    entities.extend(tool_entities)
                except (
                    Exception
                ) as exc:  # nosec B110 - best-effort mapper execution; skip failing artifact
                    logger.warning(
                        "Mapper '%s' failed for artifact '%s': %s",
                        mapper.__class__.__name__,
                        art.id,
                        exc,
                    )

        unique_entities = []
        seen_ids = set()
        for e in entities:
            if e.id not in seen_ids:
                seen_ids.add(e.id)
                unique_entities.append(e)

        relationships = RelationshipResolver.resolve_relationships(unique_entities)
        val_status = self.validator.validate(unique_entities, relationships)

        normalized_bundle = NormalizedBundle(
            session_id=bundle.session_id,
            execution_id=bundle.execution_id,
            entities=unique_entities,
            relationships=relationships,
        )

        return NormalizationResult(bundle=normalized_bundle, status=val_status)
