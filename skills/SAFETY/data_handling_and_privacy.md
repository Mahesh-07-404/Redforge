# SAFETY: Data Handling & Privacy

Strictly protect target data, credentials, and personally identifiable information (PII).

## Data Retention & Privacy
- **Redaction**: All PII, customer records, API keys, and credentials must be redacted from reports, output logs, and screenshots.
- **Secure Storage**: Save target configuration files and evidence logs strictly in the dedicated workspace directory.
- **De-escalation**: Do not download large datasets or database dumps. Verify access with minimal database queries (e.g. `SELECT version()`).
- **Cleanup**: Delete all collected local assessment logs and temporary credentials once the final report is compiled and delivered.
