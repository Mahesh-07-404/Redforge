class NormalizationError(Exception):
    """Base exception class for result normalization layer"""

    pass


class ValidationError(NormalizationError):
    """Raised when validation of entities fails"""

    pass
