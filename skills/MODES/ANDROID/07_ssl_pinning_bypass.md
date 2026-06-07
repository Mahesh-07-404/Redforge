# ANDROID Skill: SSL Pinning Bypass

## Purpose
Bypass SSL certificate pinning in Android apps.

## What is SSL Pinning?

```
App stores expected certificate/public key
Rejects connections unless certificate matches
Prevents MITM attacks
```

## Detection Methods

### Static Analysis
```bash
# Search for pinning indicators
grep -r "X509TrustManager" output/smali/
grep -r "checkServerTrusted" output/smali/
grep -r "pin" output/ --include="*.java"
grep -r "CertificatePinner" output/
```

### Frida Detection
```javascript
Java.perform(function() {
    var TrustManagerImpl = Java.use('[Landroid.app.Application;');
    // Look for custom TrustManager implementations
});
```

## Frida Bypass Scripts

### Universal SSL Bypass
```javascript
// Bypass all SSL pinning
Java.perform(function() {
    var TrustManager = Java.use('javax.net.ssl.TrustManager');
    var TrustManagerFactory = Java.use('javax.net.ssl.TrustManagerFactory');
    
    // Initialize with empty keystore
    TrustManagerFactory.init.implementation = function(ks) {
        console.log('[*] TrustManagerFactory.init called');
    };
    
    TrustManagerFactory.getTrustManagers.implementation = function() {
        console.log('[*] Getting trust managers');
        var tm = this.getTrustManagers();
        // Replace with trusting trust manager
        return tm;
    };
});
```

### OkHttp Bypass
```javascript
Java.perform(function() {
    var OkHttpClient = Java.use('okhttp3.OkHttpClient$Builder');
    
    OkHttpClient.build.implementation = function() {
        console.log('[*] Building OkHttpClient');
        var client = this.build();
        return client;
    };
});
```

### WebView SSL Bypass
```javascript
Java.perform(function() {
    var WebViewClient = Java.use('android.webkit.WebViewClient');
    
    WebViewClient.onReceivedSslError.implementation = function(view, handler, error) {
        console.log('[*] Ignoring SSL error');
        handler.proceed();  // Bypass!
    };
});
```

## Network Security Config

### Create Bypass Config
```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="true">
        <trust-anchors>
            <certificates src="user"/>
            <certificates src="system"/>
        </trust-anchors>
    </base-config>
</network-security-config>
```

### Add to Manifest
```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    ...>
</application>
```

## Common Pinning Libraries

### Implementation Types

### 1. Android Network Security Config
```xml
<domain-config cleartextTrafficPermitted="false">
    <domain includeSubdomains="true">api.example.com</domain>
    <pin-set expiration="2025-01-01">
        <pin digest="SHA-256">base64encodedpin=</pin>
        <pin digest="SHA-256">backupbase64encodedpin=</pin>
    </pin-set>
</domain-config>
```

### 2. Custom TrustManager
```java
public class CustomTrustManager implements X509TrustManager {
    @Override
    public void checkServerTrusted(X509Certificate[] chain, String authType) 
            throws CertificateException {
        // Custom validation
        if (!isValidPin(chain[0])) {
            throw new CertificateException();
        }
    }
}
```

### 3. Apache Harmony (Old)
```java
// Uses internal TrustManagerImpl
```

## Frida Scripts Repository

### Universal Bypass Script
```javascript
// universal-ssl-bypass.js
setTimeout(function() {
    Java.perform(function() {
        try {
            // Disable all certificate validation
            var SSLContext = Java.use('javax.net.ssl.SSLContext');
            SSLContext.getInstance.overload('java.lang.String').implementation = function(protocol) {
                console.log('[*] Creating SSLContext for: ' + protocol);
                var ctx = this.getInstance(protocol);
                var defaultTrustManager = Java.use('javax.net.ssl.TrustManager')[0];
                ctx.init(null, [defaultTrustManager.$new()], null);
                return ctx;
            };
            
            // Hook certificate check
            var TrustManagerFactory = Java.use('javax.net.ssl.TrustManagerFactory');
            TrustManagerFactory.getInstance.implementation = function(algorithm) {
                console.log('[*] TrustManagerFactory.getInstance: ' + algorithm);
                return this.getInstance(algorithm);
            };
            
            console.log('[+] SSL bypass loaded');
        } catch(e) {
            console.log('[-] Error: ' + e);
        }
    });
}, 0);
```

## Objection Commands

### Quick Bypass
```bash
# Using objection
objection -g com.example.app explore
android sslpinning disable

# Or with Frida
android hooking set sslpinning disable
```

## Manual Patching

### Remove Pinning from APK
```bash
# 1. Decompile
apktool d app.apk -o output/

# 2. Modify code
# Find and remove checkServerTrusted calls
# Or make them always return true

# 3. Recompile
apktool b output/ -o patched.apk

# 4. Sign
apktool sign patched.apk
```

### Patch TrustManager
```smali
# In smali/classes
.method public checkServerTrusted([Ljava/security/cert/X509Certificate;Ljava/lang/String;)V
    .locals 1
    const/4 v0, 0x0
    return-void
.end method
```

## Testing Bypass

### Burp Suite Setup
```bash
# 1. Install Burp CA cert on device
# 2. Proxy configured
# 3. Run bypass script
# 4. Check traffic in Burp
```

### Verification
```javascript
// Check if traffic is flowing
// Verify certificate in Burp
// Check for plaintext in requests
```

## Common Issues

### Bypass Not Working
```
- App may use custom pinning library
- May need specific script
- Check for root detection
- App may bundle certificate
```

### App Crashing
```
- Script interfering with app logic
- Version mismatch
- Native library pinning
```

## Checklist
```
[ ] Identify pinning type
[ ] Choose bypass method
[ ] Load Frida script
[ ] Verify traffic capture
[ ] Document bypass
```
