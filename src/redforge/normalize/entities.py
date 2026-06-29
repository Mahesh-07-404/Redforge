from .schema import NormalizedEntity

class HostEntity(NormalizedEntity):
    entity_type: str = "Host"

class IPAddressEntity(NormalizedEntity):
    entity_type: str = "IPAddress"

class PortEntity(NormalizedEntity):
    entity_type: str = "Port"

class ServiceEntity(NormalizedEntity):
    entity_type: str = "Service"

class URLResource(NormalizedEntity):
    entity_type: str = "URLResource"

class TechnologyEntity(NormalizedEntity):
    entity_type: str = "Technology"

class DirectoryEntity(NormalizedEntity):
    entity_type: str = "Directory"

class EndpointEntity(NormalizedEntity):
    entity_type: str = "Endpoint"

class ParameterEntity(NormalizedEntity):
    entity_type: str = "Parameter"

class DNSRecordEntity(NormalizedEntity):
    entity_type: str = "DNSRecord"

class EmailEntity(NormalizedEntity):
    entity_type: str = "Email"

class IdentityEntity(NormalizedEntity):
    entity_type: str = "Identity"

class CertificateEntity(NormalizedEntity):
    entity_type: str = "Certificate"

class HeaderEntity(NormalizedEntity):
    entity_type: str = "Header"

class CookieEntity(NormalizedEntity):
    entity_type: str = "Cookie"

class JavaScriptFile(NormalizedEntity):
    entity_type: str = "JavaScriptFile"

class FindingEntity(NormalizedEntity):
    entity_type: str = "Finding"

class VulnerabilityEntity(NormalizedEntity):
    entity_type: str = "Vulnerability"

class CVEEntity(NormalizedEntity):
    entity_type: str = "CVE"

class ReferenceEntity(NormalizedEntity):
    entity_type: str = "Reference"

class ScreenshotEntity(NormalizedEntity):
    entity_type: str = "Screenshot"
