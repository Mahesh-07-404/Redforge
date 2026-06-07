# ANDROID Skill: APK Analysis Fundamentals

## Purpose
Learn APK analysis techniques for Android pentesting.

## APK Structure
```
app.apk
├── AndroidManifest.xml    # App configuration
├── classes.dex            # Dalvik bytecode
├── lib/                    # Native libraries
│   ├── arm64-v8a/
│   ├── armeabi-v7a/
│   └── x86/
├── META-INF/               # Signatures
│   └── CERT.RSA/DSA
├── res/                    # Resources
│   ├── drawable/
│   ├── layout/
│   └── values/
└── assets/                # Raw assets
```

## Decompilation

### apktool
```bash
# Decompile
apktool d app.apk -o output/

# Recompile
apktool b output/ -o rebuilt.apk

# With debug flag
apktool d -d app.apk -o output/
```

### jadx
```bash
# Decompile to Java
jadx -d output/ app.apk

# GUI mode
jadx-gui app.apk

# Single class
jadx --select-class com.example.Class app.apk
```

### dex2jar
```bash
# DEX to JAR
d2j-dex2jar app.apk -o output.jar

# Then use JD-GUI
jd-gui output.jar
```

## Manifest Analysis

### Key Elements
```xml
<!-- Permissions -->
<uses-permission android:name="android.permission.INTERNET"/>
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>

<!-- Exported Components -->
<activity android:name=".MainActivity" android:exported="true"/>
<service android:name=".BackgroundService" android:exported="true"/>
<receiver android:name=".BootReceiver" android:exported="true"/>

<!-- Intent Filters -->
<intent-filter>
    <action android:name="android.intent.action.VIEW"/>
    <category android:name="android.intent.category.BROWSABLE"/>
</intent-filter>
```

### Common Vulnerabilities
```
- Exported activities without auth
- Exported services
- Exported broadcast receivers
- Dangerous permissions
- Debug enabled
- Backup enabled
```

## Smali Basics

### Basics
```smali
# Method declaration
.method public getPassword()Ljava/lang/String;
    .locals 1
    const-string v0, "hardcoded_password"
    return-object v0
.end method

# Field
.field private token:Ljava/lang/String;

# Conditional
if-nez v0, :cond_0
# if not equal zero, jump
```

### Tools
```bash
# jadx for readability
# apktool for smali
# smali.jar for assembly
```

## Hardcoded Secrets

### Common Locations
```java
// BuildConfig
BuildConfig.API_KEY
BuildConfig.DEBUG_URL

// Hardcoded strings
String apiKey = "sk_live_...";
String jwtSecret = "secret";

// Resources
strings.xml
assets/config.json
```

### Search Patterns
```bash
grep -r "api_key\|API_KEY" output/
grep -r "password\|PASSWORD" output/
grep -r "secret\|SECRET" output/
grep -r "token\|TOKEN" output/
grep -r "sk_\|pk_" output/
```

## Network Traffic Analysis

### HTTP Traffic
```bash
# Use Burp Suite proxy
# Configure proxy in app or system
# Or use Frida to bypass SSL
```

### Frida SSL Bypass
```javascript
// Disable SSL verification
Java.perform(function() {
    var SSLContext = Java.use('javax.net.ssl.SSLContext');
    SSLContext.init.implementation = function(a, b, c) {
        this.init(null, null, null);
    };
});
```

### Certificate Pinning Bypass
```javascript
// Hook TrustManager
Java.perform(function() {
    var TrustManager = Java.use('javax.net.ssl.X509TrustManager');
    TrustManager.checkServerTrusted = function() {
        return [];
    };
});
```

## Database Analysis

### SQLite
```bash
# Extract database
adb pull /data/data/com.app/databases/app.db

# View with sqlite3
sqlite3 app.db
.schema
SELECT * FROM users;
```

### SharedPreferences
```bash
adb pull /data/data/com.app/shared_prefs/*.xml
cat preferences.xml
```

## Frida Scripting

### Basic Hook
```javascript
// Hook a method
Java.perform(function() {
    var Target = Java.use('com.example.Target');
    Target.method.implementation = function(arg) {
        console.log('Called:', arg);
        return this.method(arg);
    };
});
```

### Arguments/Return
```javascript
Java.perform(function() {
    var Target = Java.use('com.example.Target');
    Target.checkPassword.implementation = function(password) {
        console.log('Password:', password);
        var result = this.checkPassword(password);
        console.log('Result:', result);
        return result;
    };
});
```

### Native Functions
```javascript
// Hook native function
var lib = Module.findBaseAddress('libnative.so');
var func = Module.findExportByName('libnative.so', 'Java_com_example_check');

Interceptor.attach(func, {
    onEnter: function(args) {
        console.log('Arg0:', args[0]);
        console.log('Arg1:', Memory.readCString(args[1]));
    },
    onLeave: function(retval) {
        console.log('Return:', retval);
    }
});
```

## Automated Tools

### MobSF
```bash
# Docker
docker run -it -p 8000:8000 opensecurity/mobsf:latest

# Web UI at http://localhost:8000
# Upload APK for automatic analysis
```

### objection
```bash
# Connect to app
objection -g com.example.app explore

# Run commands
android hooking search classes
android hooking list classes
android hooking watch class com.example.Class
```

## Common Vulnerabilities

### Insecure Storage
```java
// Bad
SharedPreferences prefs = getSharedPreferences("data", MODE_PRIVATE);
prefs.edit().putString("token", token).apply();

// Good
EncryptedSharedPreferences
SecurityCrypto library
```

### Weak Crypto
```java
// Bad - MD5 for passwords
MessageDigest.getInstance("MD5");

// Bad - Hardcoded keys
SecretKey key = new SecretKeySpec("1234567890".getBytes(), "AES");

// Good
KeyStore + AndroidKeyStore
```

### WebView Issues
```java
// Vulnerable settings
webView.getSettings().setJavaScriptEnabled(true);
webView.getSettings().setAllowFileAccess(true);

// Expose interfaces
webView.addJavascriptInterface(new WebAppInterface(), "Android");
```

## CTF Mobile Challenges

### Common Patterns
```
1. Hardcoded flags in code
2. Flawed crypto implementations
3. Native library analysis
4. APK modification
5. Runtime manipulation
```
