# ANDROID Skill: CTF Mobile Walkthrough

## Purpose
Step-by-step guide for solving mobile CTF challenges.

## Challenge Types

### 1. Hardcoded Secrets
```
Steps:
1. Decompile APK
2. Search for flag pattern
3. Extract the flag
```

### 2. Flawed Crypto
```
Steps:
1. Find encryption/decryption function
2. Analyze algorithm
3. Implement decryption
```

### 3. APK Modification
```
Steps:
1. Decompile APK
2. Modify behavior
3. Recompile and sign
```

### 4. Runtime Bypass
```
Steps:
1. Find check function
2. Write Frida script
3. Bypass the check
```

## Walkthrough 1: Hardcoded Flag

### Setup
```bash
# Decompile
apktool d challenge.apk -o output
jadx -d jadx_output/ challenge.apk
```

### Analysis
```bash
# Search for flag
grep -r "flag{" output/
grep -r "FLAG{" output/

# Or use jadx-gui and search
```

### Solution
```java
// Found in MainActivity.java:
public String getFlag() {
    return "flag{w0w_such_insecure}";
}
```

## Walkthrough 2: Flawed Crypto

### Setup
```bash
jadx -d output/ challenge.apk
```

### Analysis
```java
// In CryptoUtil.java:
public static String encrypt(String input) {
    byte[] bytes = input.getBytes();
    for (int i = 0; i < bytes.length; i++) {
        bytes[i] = (byte)(bytes[i] ^ 0x42);
    }
    return Base64.encodeToString(bytes, 0);
}
```

### Solution
```python
import base64

encrypted = "SGVsbG8gV29ybGQ="  # Given in challenge
decrypted = base64.b64decode(encrypted)
flag = ''.join(chr(b ^ 0x42) for b in decrypted)
print(flag)  # flag{xor_is_fun}
```

## Walkthrough 3: SSL Pinning Bypass

### Setup
```bash
frida-server running
frida -U -f com.example.app
```

### Analysis
```javascript
// SSL Pinning code found in NetworkManager.java
// Uses custom TrustManager
```

### Solution
```javascript
// Bypass script
Java.perform(function() {
    var TrustManagerImpl = Java.use('com.example.utils.TrustManagerImpl');
    TrustManagerImpl.checkServerTrusted.implementation = function(chain, authType) {
        return;  // Accept all
    };
});

setTimeout(function() {
    Java.perform(function() {
        // Additional bypasses
    });
}, 0);
```

## Walkthrough 4: Native Library Analysis

### Setup
```bash
unzip app.apk lib/arm64-v8a/libnative.so
```

### Analysis
```bash
strings libnative.so | grep flag
# Output: Enter password: %s
#        Correct! flag is: %s
```

### Solution
```javascript
// Frida hook
var func = Module.findExportByName('libnative.so', 'Java_com_example_NativeLib_check');

Interceptor.attach(func, {
    onLeave: function(retval) {
        console.log('[*] Return value address:', retval);
        // Read flag from return
        console.log('[*] Checking memory at:', retval);
    }
});
```

## Walkthrough 5: Insecure Storage

### Setup
```bash
adb shell run-as com.example.app ls files/
adb shell run-as com.example.app cat files/secrets.txt
```

### Analysis
```java
// Found in SharedPrefsManager.java:
prefs.edit().putString("flag", "flag{st0r4g3_n0t_s3cur3").apply();
```

### Solution
```bash
adb shell run-as com.example.app cat shared_prefs/prefs.xml
# Output: <flag>flag{st0r4g3_n0t_s3cur3}</flag>
```

## Walkthrough 6: Code Modification

### Setup
```bash
apktool d challenge.apk -o output
```

### Analysis
```java
// In CheckActivity.java:
public boolean checkLicense(String input) {
    return input.equals("wrong_license");
}
```

### Solution
```bash
# Modify to always return true
sed -i 's/input.equals("wrong_license")/true/' output/smali/com/example/CheckActivity.smali

# Recompile
apktool b output -o modified.apk

# Sign
# (use apksigner or zipalign + signapk)
```

## Walkthrough 7: Runtime Hooking

### Setup
```bash
objection -g com.example.app explore
```

### Analysis
```bash
android hooking search classes password
```

### Solution
```bash
# Hook the password check
android hooking watch class_method com.example.utils.AuthUtil.verifyPassword --dump-args --dump-return
```

## Common Patterns

### Pattern 1: Boolean Bypass
```javascript
Java.perform(function() {
    var Check = Java.use('com.example.Check');
    Check.isValid.implementation = function() {
        return true;
    };
});
```

### Pattern 2: Return String
```javascript
Java.perform(function() {
    var Flag = Java.use('com.example.Flag');
    Flag.getFlag.implementation = function() {
        return "flag{bypassed}";
    };
});
```

### Pattern 3: Argument Capture
```javascript
Java.perform(function() {
    var Check = Java.use('com.example.Check');
    Check.verify.implementation = function(arg) {
        console.log('[*] Trying:', arg);
        return this.verify(arg);
    };
});
```

## Tools Summary

### For Each Challenge Type
```
Hardcoded     → jadx, grep
Crypto        → jadx, python
SSL Pinning   → Frida, objection
Native        → strings, IDA, Frida
Storage       → adb, objection
Modification  → apktool, smali
Runtime       → Frida, objection
```

## Checklist
```
[ ] Decompile APK
[ ] Analyze code
[ ] Identify vulnerability
[ ] Choose approach
[ ] Execute solution
[ ] Get flag
```
