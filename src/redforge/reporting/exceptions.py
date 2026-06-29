class ReportingError(Exception):
    """Base exception for reporting engine"""
    pass

class SynthesisError(ReportingError):
    """Synthesis stage errors"""
    pass

class ExportError(ReportingError):
    """Report export errors"""
    pass
