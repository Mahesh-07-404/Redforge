# ANDROID Skill: CTF Android Challenges

## Purpose
Strategies for solving CTF Android challenges.

## Challenge Types

### 1. Hardcoded Flags
```
Easiest type - flag in code
grep for "flag{" or similar
```

### 2. Flawed Crypto
```
Custom encryption/encoding
Find algorithm, reverse it
```

### 3. APK Modification
```
Modify behavior, rebuild
Patch checks
```

### 4. Runtime Bypass
```
Use Frida to bypass checks
Hook verification functions
```

### 5. Native Library
```
Hidden logic in .so files
ARM assembly analysis
```

## Walkthrough: Hardcoded Flag

### Setup
```bash
jadx -d output/ challenge.apk
```

### Find Flag
```bash
# Method 1: grep
grep -r "flag{" output/

# Method 2: jadx-gui
# Search for "flag"

# Method 3: strings
strings challenge.apk | grep -i "flag"
```

### Solution
```java
// Found in MainActivity:
String getFlag() {
    return "flag{th15_1s_345y}";
}
```

## Walkthrough: Flawed Crypto

### Setup
```bash
jadx -d output/ challenge.apk
```

### Analyze Crypto
```java
// Found in CryptoUtil.java:
public static String decrypt(String input) {
    byte[] data = Base64.decode(input);
    for (int i = 0; i < data.length; i++) {
        data[i] = (byte) (data[i] ^ 0x55);
    }
    return new String(data);
}
```

### Write Decryptor
```python
import base64

encrypted = "RXhlY3V0ZVswezEzfQ=="  # Given in challenge
data = base64.b64decode(encrypted)
decrypted = ''.join(chr(b ^ 0x55) for b in data)
print(decrypted)  # flag{...}
```

## Walkthrough: APK Modification

### Setup
```bash
apktool d challenge.apk -o output/
```

### Find Check
```java
// In CheckActivity.java:
public boolean checkLicense(String input) {
    return input.equals("wrong_license");
}
```

### Patch
```bash
# Method 1: Change return value
# Find the method in smali
# Change const/4 v0, 0x0 to const/4 v0, 0x1

# Method 2: NOP out the check
# Replace if-eqz with nop

# Method 3: Use Frida
Java.perform(function() {
    var Check = Java.use('com.example.CheckActivity');
    Check.checkLicense.implementation = function(input) {
        return true;
    };
});
```

### Rebuild
```bash
apktool b output/ -o modified.apk

# Sign (create test keys if needed)
keytool -genkey -v -keystore test.keystore -alias test -keyalg RSA -keysize 2048
apksigner sign --ks test.keystore modified.apk
```

## Walkthrough: Runtime Bypass

### Setup
```bash
frida-server running
frida -U -f com.example.app
```

### Find Check Function
```bash
objection -g com.example.app explore
android hooking search classes check
```

### Bypass
```javascript
Java.perform(function() {
    var LicenseCheck = Java.use('com.example.utils.LicenseCheck');
    
    LicenseCheck.isValid.implementation = function() {
        console.log('[*] Bypassing license check');
        return true;
    };
    
    // Or with specific logic
    LicenseCheck.verify.implementation = function(license) {
        if (license === '') {
            return true;
        }
        return this.verify(license);
    };
});
```

## Walkthrough: Native Library

### Setup
```bash
unzip challenge.apk lib/arm64-v8a/libnative.so
strings libnative.so | grep flag
```

### Analyze with IDA/Ghidra
```bash
ghidraRun
# Import libnative.so
# Analyze function Java_com_example_NativeLib_checkFlag
```

### Frida Hook
```javascript
var func = Module.findExportByName('libnative.so', 
    'Java_com_example_NativeLib_checkFlag');

Interceptor.attach(func, {
    onLeave: function(retval) {
        console.log('[*] Return value: ' + retval);
        // If flag is in memory, read it
    }
});
```

## Common CTF Patterns

### Pattern 1: XOR Encryption
```java
// Very common in CTFs
for (int i = 0; i < data.length; i++) {
    data[i] = (byte) (data[i] ^ key[i % key.length]);
}
```

### Pattern 2: Base64 + Custom
```java
// Multiple encodings
String encoded = Base64.encodeToString(input, Base64.DEFAULT);
encoded = customShuffle(encoded);
```

### Pattern 3: String Manipulation
```java
// Split strings
String s1 = "flag{";
String s2 = "hello";
String s3 = "_world}";
String flag = s1 + s2 + s3;
```

## Frida Templates

### Universal Bypass
```javascript
// Save as bypass.js
Java.perform(function() {
    // Hook all boolean returns
    Java.enumerateLoadedClasses({
        onMatch: function(className) {
            if (className.includes('com.ctf.')) {
                var clazz = Java.use(className);
                var methods = Object.keys(clazz);
                methods.forEach(function(method) {
                    try {
                        var overloads = clazz[method].overloads;
                        overloads.forEach(function(overload) {
                            overload.implementation = function() {
                                console.log('[*] Called: ' + className + '.' + method);
                                // Try returning true
                                if (method.toLowerCase().includes('check') ||
                                    method.toLowerCase().includes('valid')) {
                                    return true;
                                }
                                return this[method].apply(this, arguments);
                            };
                        });
                    } catch(e) {}
                });
            }
        },
        onComplete: function() {}
    });
});
```

### Flag Extractor
```javascript
Java.perform(function() {
    var FlagUtil = Java.use('com.ctf.utils.FlagUtil');
    FlagUtil.getFlag.implementation = function() {
        var flag = this.getFlag();
        console.log('[*] FLAG: ' + flag);
        return flag;
    };
});
```

## Solving Checklist

```
[ ] Decompile APK
[ ] Search for flag pattern
[ ] Analyze crypto functions
[ ] Look for native libraries
[ ] Check for Frida detection
[ ] Write decryption script
[ ] Use Frida to extract
[ ] Modify and rebuild if needed
```

## Useful Commands

```bash
# Decompile
jadx -d output/ app.apk

# Find strings
strings app.apk | grep -i flag
grep -r "flag" output/ --include="*.java"

# Dynamic analysis
frida -U -f com.example.app -l script.js

# Modify
apktool d app.apk -o output/
apktool b output/ -o modified.apk

# Sign
apksigner sign --ks test.keystore modified.apk
```
