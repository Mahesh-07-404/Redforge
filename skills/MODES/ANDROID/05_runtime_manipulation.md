# ANDROID Skill: Runtime Manipulation

## Purpose
Master runtime manipulation for Android testing.

## Objection

### Installation
```bash
pip install objection
```

### Connect
```bash
# By package name
objection -g com.example.app explore

# By process name
objection -n "com.example.app" explore
```

### Commands
```bash
# List classes
android hooking list classes

# Search classes
android hooking search classes password
android hooking search classes crypto

# Watch class
android hooking watch class com.example.utils.Crypto

# Watch method
android hooking watch class_method com.example.utils.Crypto.decrypt --dump-args --dump-return

# Disable SSL pinning
android sslpinning disable

# Bypass root detection
android root disable
```

## Memory Analysis

### Dump Memory
```bash
# Dump process memory
memory dump all /data/local/tmp/memory.dump

# Dump specific region
memory dump from_allocations com.example.Class
```

### Search Memory
```bash
# Search for string
memory search "password" --string

# Search for bytes
memory search "\\x41\\x42\\x43"
```

## Frida Scripts

### Basic Script Template
```javascript
// script.js
setTimeout(function() {
    Java.perform(function() {
        console.log('[*] Script loaded');
        
        // Hook code here
        var Target = Java.use('com.example.Target');
        Target.method.implementation = function(arg) {
            console.log('[*] Called:', arg);
            return this.method(arg);
        };
    });
}, 0);
```

### Run Script
```bash
frida -U -f com.example.app -l script.js --no-pause
```

## Common Hooks

### Hook All Exceptions
```javascript
Java.perform(function() {
    var Thread = Java.use('java.lang.Thread');
    Thread.setDefaultUncaughtExceptionHandler(Java.use('java.lang.Thread$UncaughtExceptionHandler').$new({
        uncaughtException: function(t, e) {
            console.log('[*] Exception:', e);
        }
    }));
});
```

### Hook Input/Output Streams
```javascript
Java.perform(function() {
    var FileInputStream = Java.use('java.io.FileInputStream');
    FileInputStream.read.overload().implementation = function() {
        var data = this.read();
        if (data !== -1) {
            console.log('[*] Read byte:', data);
        }
        return data;
    };
});
```

### Hook File Operations
```javascript
Java.perform(function() {
    var File = Java.use('java.io.File');
    File.$init.overload('java.lang.String').implementation = function(path) {
        console.log('[*] File access:', path);
        return this.$init(path);
    };
});
```

## WebView Manipulation

### Enable Debugging
```javascript
Java.perform(function() {
    var WebView = Java.use('android.webkit.WebView');
    WebView.setWebContentsDebuggingEnabled(Java.use('java.lang.Boolean').TRUE);
});
```

### Intercept JavaScript
```javascript
Java.perform(function() {
    var WebView = Java.use('android.webkit.WebView');
    var JavascriptInterface = Java.use('android.webkit.JavascriptInterface');
    
    // Find injected interface
    var interfaces = this.getClass().getDeclaredFields();
    // ...
});
```

## Encrypted Data

### Hook Key Derivation
```javascript
Java.perform(function() {
    var SecretKeySpec = Java.use('javax.crypto.spec.SecretKeySpec');
    SecretKeySpec.$init.overload('[B', 'java.lang.String').implementation = function(key, algo) {
        console.log('[*] Key derivation:', algo);
        console.log('[*] Key:', Java.use('android.util.Base64').encodeToString(key, 0));
        return this.$init(key, algo);
    };
});
```

### Hook Cipher
```javascript
Java.perform(function() {
    var Cipher = Java.use('javax.crypto.Cipher');
    Cipher.doFinal.overload('[B').implementation = function(data) {
        console.log('[*] Plaintext:', Java.use('android.util.Base64').encodeToString(data, 0));
        var result = this.doFinal(data);
        console.log('[*] Ciphertext:', Java.use('android.util.Base64').encodeToString(result, 0));
        return result;
    };
});
```

## Database Manipulation

### Hook SQLite
```javascript
Java.perform(function() {
    var SQLiteDatabase = Java.use('android.database.sqlite.SQLiteDatabase');
    SQLiteDatabase.execSQL.overload('java.lang.String').implementation = function(sql) {
        console.log('[*] SQL:', sql);
        return this.execSQL(sql);
    };
});
```

### Dump Database
```bash
# Copy database
adb shell "run-as com.example.app cat databases/app.db" > app.db

# With Objection
android root set
file dump /data/data/com.example.app/databases/app.db /data/local/tmp/app.db
```

## Network Interception

### Hook HttpURLConnection
```javascript
Java.perform(function() {
    var HttpURLConnection = Java.use('java.net.HttpURLConnection');
    HttpURLConnection.getInputStream.implementation = function() {
        console.log('[*] URL:', this.getURL());
        return this.getInputStream();
    };
});
```

### Hook OkHttp
```javascript
Java.perform(function() {
    Java.perform(function() {
        var Interceptor = Java.use('okhttp3.Interceptor');
        var Interceptor_Chain = Java.use('okhttp3.Interceptor$Chain');
        
        Interceptor.intercept.implementation = function(chain) {
            var request = chain.request();
            console.log('[*] Request URL:', request.url());
            console.log('[*] Request Headers:', request.headers());
            
            var response = this.intercept(chain);
            console.log('[*] Response:', response);
            return response;
        };
    });
});
```

## Preferences Manipulation

### Read SharedPreferences
```bash
# With Objection
android hooking list classes SharedPreferences
```

### Write Preferences
```javascript
Java.perform(function() {
    var SharedPreferences = Java.use('android.content.SharedPreferences');
    var Editor = Java.use('android.content.SharedPreferences$Editor');
    
    // Hook to modify values
    Editor.putString.implementation = function(key, value) {
        console.log('[*] Setting:', key, '=', value);
        return this.putString(key, value);
    };
});
```

## Device State Manipulation

### Mock Location
```javascript
Java.perform(function() {
    var LocationManager = Java.use('android.location.LocationManager');
    LocationManager.getLastKnownLocation.implementation = function(provider) {
        var mockLocation = Java.use('android.location.Location').$new('gps');
        mockLocation.setLatitude(Java.use('java.lang.Double').parseDouble('37.7749'));
        mockLocation.setLongitude(Java.use('java.lang.Double').parseDouble('-122.4194'));
        return mockLocation;
    };
});
```

### Device Info Spoofing
```javascript
Java.perform(function() {
    var Build = Java.use('android.os.Build');
    Build.MODEL.value = 'Pixel 4';
    Build.MANUFACTURER.value = 'Google';
    Build.DEVICE.value = 'flame';
});
```

## Tips
```
- Use --no-pause to auto-start app
- Use objection for quick analysis
- Save useful scripts for reuse
- Check Objection's android commands
```
