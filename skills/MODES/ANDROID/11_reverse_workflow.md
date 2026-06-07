# ANDROID Skill: Reverse Engineering Workflow

## Purpose
Complete workflow for reversing Android applications.

## Overview

```
┌─────────────┐
│   APK File  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Static     │──► Manifest, Resources, Strings
│  Analysis   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Decompile   │──► Java/Smali code
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Dynamic    │──► Runtime behavior
│  Analysis   │    Frida hooks
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Identify   │──► Vulnerabilities
│  Findings   │    Secrets, Weaknesses
└─────────────┘
```

## Step 1: Initial Recon

### Get APK Info
```bash
# Basic info
aapt dump badging app.apk | grep -E "package:|application-label:|sdkVersion|targetSdkVersion"

# APK metadata
apktool d app.apk -o output/
cat output/AndroidManifest.xml

# Check signing
apksigner verify --print-certs app.apk
jarsigner -verify -verbose app.apk
```

### Quick String Search
```bash
# Extract strings
strings app.apk | grep -i "password\|api_key\|secret\|token" | head -20

# With apkx
apkx extract app.apk
```

## Step 2: Automated Analysis

### MobSF
```bash
docker run -it -p 8000:8000 opensecurity/mobsf:latest

# Open browser
# Upload APK
# Get full report
```

### Quark Analysis
```bash
# Quick malware analysis
python -m quark -i app.apk --api api.json

# Check for behaviors
python -m quark -i app.apk --rule rules/
```

### ViralTotal
```bash
# Upload and scan
curl -X POST \
    -F "file=@app.apk" \
    -F "apikey=YOUR_API_KEY" \
    https://www.virustotal.com/api/v3/files
```

## Step 3: Manual Decompilation

### Decompile to Java
```bash
# jadx (recommended)
jadx -d output/ app.apk
jadx-gui app.apk

# Or d2j-dex2jar + JD-GUI
d2j-dex2jar app.apk -o output.jar
jd-gui output.jar
```

### Decompile to Smali
```bash
# For modification
apktool d app.apk -o smali_output/

# Recompile after changes
apktool b smali_output/ -o modified.apk
```

## Step 4: Code Analysis

### Find Entry Points
```java
// Look in AndroidManifest.xml
<activity android:name=".MainActivity">
    <intent-filter>
        <action android:name="android.intent.action.MAIN"/>
        <category android:name="android.intent.category.LAUNCHER"/>
    </intent-filter>
</activity>
```

### Search for Vulnerabilities
```bash
# Search for common patterns
grep -r "Runtime.getRuntime().exec" output/
grep -r "HttpURLConnection" output/
grep -r "HTTPS" output/
grep -r "SharedPreferences" output/

# Look for hardcoded secrets
grep -rE "api[_-]?key|secret|token|password" --include="*.java"
```

### Analyze Crypto
```bash
# Find crypto usage
grep -r "Cipher" --include="*.java" output/
grep -r "SecretKey" --include="*.java" output/
grep -r "MessageDigest" --include="*.java" output/
grep -r "Base64" --include="*.java" output/
```

## Step 5: Dynamic Analysis

### Setup Frida
```bash
# Start Frida server
adb push frida-server /data/local/tmp/
adb shell "/data/local/tmp/frida-server &"

# List apps
frida-ps -U

# Attach to app
frida -U -f com.example.app
```

### Common Frida Hooks
```javascript
// Hook all classes in package
Java.perform(function() {
    Java.enumerateLoadedClasses({
        onMatch: function(className) {
            if (className.startsWith('com.target.')) {
                console.log('[*] Found: ' + className);
            }
        },
        onComplete: function() {}
    });
});

// Hook specific method
Java.perform(function() {
    var Target = Java.use('com.target.TargetClass');
    Target.method.implementation = function(arg) {
        console.log('[*] Called with: ' + arg);
        return this.method(arg);
    };
});
```

### Network Analysis
```javascript
// Hook HTTP
Java.perform(function() {
    var HttpURLConnection = Java.use('java.net.HttpURLConnection');
    HttpURLConnection.getInputStream.implementation = function() {
        console.log('[*] URL: ' + this.getURL());
        return this.getInputStream();
    };
});
```

## Step 6: Exploitation

### SSL Pinning Bypass
```javascript
// Universal bypass
Java.perform(function() {
    var TrustManager = Java.use('javax.net.ssl.X509TrustManager');
    TrustManager.checkServerTrusted.implementation = function() {
        return;
    };
});
```

### Root Detection Bypass
```javascript
Java.perform(function() {
    var File = Java.use('java.io.File');
    File.exists.implementation = function() {
        if (this.getAbsolutePath().contains('su')) {
            return false;
        }
        return this.exists();
    };
});
```

### Extract Secrets
```javascript
Java.perform(function() {
    var Utils = Java.use('com.target.Utils');
    Utils.getApiKey.implementation = function() {
        var key = this.getApiKey();
        console.log('[*] API Key: ' + key);
        return key;
    };
});
```

## Step 7: Documentation

### Report Template
```markdown
## Android Application Security Assessment

### Application Information
- Name: [App Name]
- Package: com.example.app
- Version: [X.Y.Z]
- Architecture: [ARM/x86]

### Static Analysis Findings
| Finding | Location | Risk |
|---------|----------|------|
| Hardcoded API Key | Utils.java:42 | High |

### Dynamic Analysis Findings
| Finding | Trigger | Risk |
|---------|---------|------|
| SSL Pinning Bypass | Frida Script | Medium |

### Recommendations
1. Remove hardcoded secrets
2. Implement SSL Pinning properly
```

## Common Tools

### Static Analysis
```
jadx - Java decompiler
apktool - APK tool
 MobSF - Automated analysis
Quark - Malware analysis
VT - VirusTotal
```

### Dynamic Analysis
```
Frida - Instrumentation
Objection - Runtime exploration
Burp Suite - Proxy
Wireshark - Network capture
```

### Automation
```
Objection - Quick commands
Fridax - Function extraction
frida-dexlib - DEX manipulation
```

## Checklist
```
[ ] Initial APK info gathering
[ ] Automated scan (MobSF)
[ ] Manual decompilation
[ ] Code analysis
[ ] Dynamic analysis with Frida
[ ] Vulnerability exploitation
[ ] Documentation
```
