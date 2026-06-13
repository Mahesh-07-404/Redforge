# CORE SYSTEM: Intent Detection

Every query must be classified into one of the following intents before operational execution:

## Intents
- **CHAT**: Greetings, small talk, thanks, and simple dialog. Bypasses target requirements.
- **LEARNING**: Explanations of concepts, training requests. Bypasses target requirements.
- **CODING**: Secure development support, code reviews. Bypasses target requirements.
- **PLANNING**: Formulating high-level attack strategies or plans.
- **RESEARCH**: Analyzing CVEs, technologies, or architectures.
- **RECON**: Passive DNS/WHOIS queries, asset discovery (requires target verification).
- **SCANNING**: Active port scanning and vulnerability scanning (requires target verification).
- **REPORTING**: Finalizing and generating vulnerability reports (requires target verification).
