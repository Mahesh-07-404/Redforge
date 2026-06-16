# SAFETY: Scope & Authorization

Always verify targets are explicitly in scope before conducting any operational activities.

## Scope Definitions
- **In-Scope**: Explicitly authorized domain names, IP addresses, subdomains, and API endpoints.
- **Out-of-Scope**: Staging, dev, or third-party targets not specified in authorization agreements.
- **Strict Compliance**: Never scan, recon, or test targets outside of the authorized `{target}` context. If a target is mismatching, stop testing immediately.

## Verification Checklist
- [ ] Confirm active session target is set and correct.
- [ ] Verify program or organization boundaries match `{target}`.
- [ ] Note specific rate limits and scanning restrictions.
- [ ] Save scope definition files locally for documentation.
- [ ] Stop testing if redirection to third-party domains occurs.
