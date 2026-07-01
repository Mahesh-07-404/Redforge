from .contracts import Finding


class CorrelationEngine:
    @staticmethod
    def correlate_findings(findings: list[Finding]) -> list[Finding]:
        correlated = []
        for f in findings:
            existing = next((c for c in correlated if c.cve == f.cve and f.cve is not None), None)
            if existing:
                for asset in f.affected_assets:
                    if asset not in existing.affected_assets:
                        existing.affected_assets.append(asset)
            else:
                correlated.append(f)
        return correlated
