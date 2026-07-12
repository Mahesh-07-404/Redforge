# MODE: Android Security

Perform mobile application security testing, dynamic instrumentation, and static reverse engineering.

## Methodology
- **APK Inspection**: Unpack packages, inspect `AndroidManifest.xml` for exported components, backups, and custom permissions.
- **Static Analysis**: Audit decompiled Java/Kotlin classes (via JADX/bytecode) for hardcoded secrets, insecure storage (shared preferences), and native calls.
- **Dynamic Instrumentation**: Use Frida scripts to bypass SSL pinning, hook target routines, and monitor class loading.
- **Native Code Reversing**: Reverse native `.so` files using standard disassemblers, look for buffer overflows or logic flaws.
- **Local Storage Audit**: Inspect mobile app sandboxes for unencrypted SQL databases or cache leakage.
- **Bypasses**: Implement root detection and integrity check bypass hooks.
