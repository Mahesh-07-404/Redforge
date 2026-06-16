# EXECUTION: Reporting Standards

All reports and findings must be supported by verified tool output logs.

## Finding Fields
Every finding recorded in the database and report must contain:
- **Title**: Descriptive name of the issue.
- **Severity**: Critical, High, Medium, Low, or Info (based on CVSS metrics).
- **Target**: The active session target `{target}`.
- **Evidence**: The exact snippet of tool command outputs or response headers verifying the issue.
- **Tool Source**: The identifier of the tool used (e.g. `nmap`, `ffuf`).
- **Remediation**: Actionable patching or mitigation instructions.

## Report Rules
- Never compile a final report unless the findings have verified evidence attached.
- If no vulnerabilities were verified during testing, report a clean assessment ("no vulnerabilities identified").
- PII and private keys must be redacted from all report sections.
