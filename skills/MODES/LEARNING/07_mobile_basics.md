# LEARNING Skill: Mobile Security Basics

## Purpose
Learn Android security fundamentals.

## Android Architecture
```
┌─────────────────────┐
│      Apps          │
├─────────────────────┤
│   Framework         │
│   (Java/Kotlin)    │
├─────────────────────┤
│   Native Libraries │
│   (C/C++)          │
├─────────────────────┤
│   Android Runtime  │
│   (ART, Dalvik)    │
├─────────────────────┤
│   HAL              │
├─────────────────────┤
│   Linux Kernel     │
└─────────────────────┘
```

## App Components

### Activities
```
- Single screen UI
- Main entry point
- AndroidManifest.xml
```

### Services
```
- Background operations
- No UI
- Long-running tasks
```

### Broadcast Receivers
```
- Listen for system events
- Can receive from other apps
```

### Content Providers
```
- Share data between apps
- SQLite backend
```

## Permissions

### Protection Levels
```
Normal    - Auto-granted (INTERNET)
Dangerous - User must approve (CAMERA, LOCATION)
Signature - Same cert required
```

### Dangerous Permissions
```
CAMERA, READ_CONTACTS, ACCESS_FINE_LOCATION
RECORD_AUDIO, READ_SMS, SEND_SMS
READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
```

## APK Structure
```
app.apk/
├── AndroidManifest.xml
├── classes.dex
├── lib/           # Native libraries
├── META-INF/      # Signatures
├── res/           # Resources
└── assets/        # Raw assets
```

## Reversing APKs

### Decompile
```bash
apktool d app.apk -o output/
jadx -d output/ app.apk
```

### Analyze
```bash
# View manifest
cat output/AndroidManifest.xml

# Find strings
grep -r "password" output/
grep -r "api.key" output/
```

## Common Vulnerabilities

### Hardcoded Secrets
```java
// Bad practice
String apiKey = "sk_live_1234567890";
```

### Insecure Storage
```java
// Bad - SharedPreferences in cleartext
prefs.getString("token", "");

// Good - EncryptedSharedPreferences
```

### SQL Injection
```java
// Vulnerable
db.rawQuery("SELECT * FROM users WHERE name='" + name + "'", null);

// Safe - Parameterized
db.rawQuery("SELECT * FROM users WHERE name=?", new String[]{name});
```

### Weak Crypto
```java
// Bad - MD5 for passwords
MessageDigest md = MessageDigest.getInstance("MD5");

// Good - PBKDF2 or Argon2
```

## SSL Pinning

### Purpose
```
Prevent MITM by pinning certificates
Validates server cert against known good
```

### Implementation
```java
// OkHttp with pinning
CertificatePinner.Builder builder = new CertificatePinner.Builder();
builder.add("domain.com", "sha256/...");
OkHttpClient client = new OkHttpClient.Builder()
    .certificatePinner(builder.build())
    .build();
```

## Frida Basics

### Hooking
```javascript
Java.perform(function() {
    var MyClass = Java.use("com.example.MyClass");
    MyClass.method.implementation = function(arg) {
        console.log("Called with:", arg);
        return this.method(arg);
    };
});
```

### Frida Server
```bash
# On device
adb push frida-server /data/local/tmp/
adb shell "/data/local/tmp/frida-server &"

# Connect
frida -U -f com.example.app
```

## Tools

### Static Analysis
```
Jadx - Java decompiler
Apktool - Resource extractor
AndroidStudio - IDE
```

### Dynamic Analysis
```
Frida - Hooking framework
Burp Suite - Proxy
Objection - Runtime exploration
```

## CTF Mobile
```
Common techniques:
- Hardcoded flags
- Weak crypto
- Insecure storage
- Native library analysis
- SSL pinning bypass
```
