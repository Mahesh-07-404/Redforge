class EvidenceError(Exception):
    """Base exception for evidence management errors"""

    pass


class StoreError(EvidenceError):
    """Raised when storing evidence fails"""

    pass
