# CTF Skill: Mobile CTF Challenges

## Purpose
Solve mobile application (Android/iOS) CTF challenges.

## Android Setup

### Tools
```bash
# APK Tools
apktool d target.apk -o output/
apktool b output/ -o rebuilt.apk

# Jadx (Java decompiler)
jadx -d output/ target.apk

# MobSF (Automated analysis)
docker pull opensecurity/mobile-security-framework-mobsf:latest
docker run -it -p 8000:8000 opensecurity/mobile-security-framework-mobsf

# Frida
pip install frida-tools
frida --version
```

### ADB Commands
```bash
# Connect to device/emulator
adb connect localhost:5555
adb devices
adb shell

# Install/uninstall
adb install target.apk
adb uninstall com.package.name

# Pull files
adb pull /data/app/com.target.apk

# Logcat
adb logcat | grep -i "flag\|password\|secret"
```

## Static Analysis

### APK Structure
```
target.apk/
├── AndroidManifest.xml
├── classes.dex
├── lib/
├── META-INF/
├── res/
└── assets/
```

### Decompile APK
```bash
# Extract resources
apktool d target.apk -o output/

# Decompile DEX
jadx -d jadx_output/ target.apk

# Or use d2j
d2j-dex2jar target.apk -o output.jar
```

### Manifest Analysis
```xml
<!-- Check permissions -->
<uses-permission android:name="android.permission.INTERNET"/>
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>

<!-- Check exported components -->
<activity android:name=".MainActivity" android:exported="true"/>
<service android:name=".MyService" android:exported="true"/>
<receiver android:name=".MyReceiver" android:exported="true"/>
```

### DEX Analysis
```bash
# List DEX contents
d2j-dex2jar target.apk
unzip target.apk classes.dex
javap -c classes.dex

# Use jadx for readable code
jadx target.apk
```

### Code Analysis
```java
// Find hardcoded secrets
grep -r "password" --include="*.java"
grep -r "api.key" --include="*.java"
grep -r "BASE64" --include="*.java"

// Find crypto usage
grep -r "Cipher" --include="*.java"
grep -r "SecretKey" --include="*.java"
grep -r "MessageDigest" --include="*.java"
```

## Dynamic Analysis

### Frida Hooking
```javascript
// Basic function hook
Java.perform(function() {
    var MainActivity = Java.use("com.target.MainActivity");
    MainActivity.checkPassword.implementation = function(arg) {
        console.log("Password check:", arg);
        return true;  // Bypass
    };
});
```

### Frida Scripts
```javascript
// Hook native functions
Interceptor.attach(Module.findBaseAddress("libnative.so"), {
    onEnter: function(args) {
        console.log("Called function with:", args);
    },
    onLeave: function(retval) {
        console.log("Returned:", retval);
    }
});

// SSL Unpinning
Java.perform(function() {
    var TrustManager = Java.use('javax.net.ssl.X509TrustManager');
    TrustManager.checkServerTrusted.implementation = function() {
        return true;
    };
});
```

### Run Frida
```bash
# Frida server on device
adb push frida-server /data/local/tmp/
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "/data/local/tmp/frida-server &"

# Hook app
frida -U -f com.target.app -l script.js

# List processes
frida-ps -U
```

## Common Vulnerabilities

### Insecure Storage
```java
// Bad - SharedPreferences in cleartext
SharedPreferences prefs = getSharedPreferences("data", MODE_PRIVATE);
prefs.edit().putString("token", token).apply();

// Check for files
adb shell "run-as com.target ls files/"
adb shell "run-as com.target cat files/shared_prefs/*.xml"
```

### Hardcoded Secrets
```java
// Bad - hardcoded API key
String apiKey = "sk_live_1234567890";

// Bad - hardcoded password
private static final String PASSWORD = "secret123";

// Bad - hardcoded flag
String flag = "flag{th1s_1s_b4d}";
```

### SQL Injection
```java
// Vulnerable query
String query = "SELECT * FROM users WHERE name='" + name + "'";
Cursor cursor = db.rawQuery(query, null);

// Safe - parameterized
Cursor cursor = db.rawQuery("SELECT * FROM users WHERE name=?", new String[]{name});
```

### Intent-based Attacks
```java
// Check for exported activities
// Send malicious intent
adb shell am start -n com.target/.ExportedActivity -e flag "$(cat /data/local/tmp/flag.txt)"

// Broadcast receivers
adb shell am broadcast -a com.target.ACTION -e data "exploit"
```

## iOS Analysis

### Tools
```bash
# Class-dump
class-dump TargetApp

# Hopper
hopper target.ipa

# MobSF
docker run -it -p 8000:8000 opensecurity/mobsf:latest

# Frida
frida-ios-dump TargetApp.ipa
```

### iOS Setup
```bash
# Jailbreak required for most analysis
# Cydia packages:
# - OpenSSH
# - Frida
# - Cycript
# - AppSync Unified

# SSH into device
ssh root@ip

# Install IPA
ipainstaller TargetApp.ipa
```

### iOS Analysis
```bash
# Dump app data
frida-ios-dump -H ip:port TargetApp

# Decrypt binary
class-dump-z TargetApp > dump.txt

# Analyze binary
otool -L TargetApp
otool -hv TargetApp

# Find strings
strings TargetApp | grep -i flag
```

## Reverse Engineering

### Native Library Analysis
```bash
# Find native libraries
find . -name "*.so"

# Analyze ARM
arm-linux-gnueabi-readelf -h libnative.so
arm-linux-gnueabi-objdump -d libnative.so

# Cross-compile tools
apt install arm-linux-gnueabi-binutils
```

### Common Flags
```
Java/Kotlin: String flag = "flag{...}"
Native: look in .so strings
Resources: strings.xml, raw/, assets/
Build: BuildConfig.java
```

## CTF Walkthrough Example

```bash
# 1. Extract APK
apktool d challenge.apk -o extracted/

# 2. Find interesting files
grep -r "flag{" extracted/

# 3. Analyze native library
find extracted/ -name "*.so" -exec strings {} \; | grep flag

# 4. Hook the check
frida -U -f com.target.challenge -l hook.js

# hook.js content:
Java.perform(function() {
    var Native = Module.findExportByName("libnative.so", "check_flag");
    Interceptor.attach(Native, {
        onEnter: function(args) {
            console.log("Checking:", Memory.readCString(args[1]));
        },
        onLeave: function(retval) {
            console.log("Result:", retval);
        }
    });
});
```

## Checklist
```
[ ] Extract APK
[ ] Analyze manifest
[ ] Decompile Java code
[ ] Find hardcoded secrets
[ ] Analyze native libraries
[ ] Check for SSL pinning
[ ] Hook crypto functions
[ ] Analyze storage
[ ] Test exported components
[ ] Dynamic analysis
```
