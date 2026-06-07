# ANDROID Skill: Rooting & Root Detection Bypass

## Purpose
Understand rooting and bypass root detection in Android apps.

## What is Root?

### Root Access
```
- Full system access (su binary)
- Superuser management (Magisk, SuperSU)
- System-level modifications
```

### Why Apps Detect Root
```
- Security compliance
- Banking apps
- Gaming apps
- DRM content
```

## Root Detection Methods

### 1. File-Based
```java
// Check for su binary
new File("/system/app/Superuser.apk").exists()
new File("/system/xbin/su").exists()
new File("/system/bin/su").exists()

// Check for Magisk
new File("/sbin/.magisk").exists()
new File("/data/adb/magisk").exists()
```

### 2. Command-Based
```java
// Run su command
Runtime.getRuntime().exec("su -c id");

// Check for root apps
Runtime.getRuntime().exec("pm list packages | grep superuser");
```

### 3. Build Info
```java
// Check build tags
Build.TAGS.contains("test-keys")

// Check for SU binaries
String[] paths = {
    "/system/app/Superuser.apk",
    "/sbin/su",
    "/system/bin/su",
    "/system/xbin/su",
    "/data/local/xbin/su"
};
```

### 4. Native Detection
```c
// Native library checking
// Usually in lib/ directory
// Uses stat() or access()
```

## Frida Bypass Scripts

### Universal Root Bypass
```javascript
Java.perform(function() {
    // Hook File.exists()
    var File = Java.use('java.io.File');
    File.exists.implementation = function() {
        var path = this.getAbsolutePath();
        if (path.contains('su') || path.contains('magisk')) {
            console.log('[*] Blocking root check for: ' + path);
            return false;
        }
        return this.exists();
    };
    
    // Hook Runtime.exec()
    var Runtime = Java.use('java.lang.Runtime');
    Runtime.exec.overload('java.lang.String').implementation = function(cmd) {
        if (cmd.includes('su') || cmd.includes('Superuser')) {
            console.log('[*] Blocking exec: ' + cmd);
            return null;
        }
        return this.exec(cmd);
    };
    
    // Hook Build.TAGS
    var Build = Java.use('android.os.Build');
    Build.TAGS.value = "release-keys";
});
```

### Complete Bypass Script
```javascript
setTimeout(function() {
    Java.perform(function() {
        var PackageManager = Java.use('android.content.pm.PackageManager');
        
        // Hide Magisk
        try {
            var native = Module.findExportByName("libc.so", "stat");
            Interceptor.attach(native, {
                onEnter: function(args) {
                    var path = Memory.readCString(args[0]);
                    if (path.includes('/data/adb/magisk') || path.includes('.magisk')) {
                        Memory.writeUtf8String(args[0], '/non-existent-path');
                    }
                }
            });
        } catch(e) {
            console.log('[*] Native hook failed: ' + e);
        }
        
        console.log('[+] Root bypass loaded');
    });
}, 0);
```

## Objection Commands

```bash
# Disable root detection
objection -g com.example.app explore
android root disable

# Or specific bypass
android hooking set root_detection disable
```

## Magisk Specific

### MagiskHide
```
- Magisk has built-in hiding
- Enable MagiskHide in settings
- Select apps to hide from
```

### Zygisk
```
- New Magisk implementation
- Uses Zygote injection
- More effective hiding
```

### Shamiko
```
- Additional hiding module
- Works with Zygisk
- Hides root from more apps
```

## Common Libraries

### RootBeer
```java
// Popular root detection library
RootBeer rootBeer = new RootBeer(context);

if (rootBeer.isRooted()) {
    // App detects root
}

// Methods
rootBeer.isRootedWithoutApps()
rootBeer.detectRootManagementApps()
rootBeer.detectPotentiallyDangerousApps()
rootBeer.checkForBinary("su")
```

### SafetyNet/Play Integrity

### Attestation
```java
// Google Play Services SafetyNet
// Now replaced by Play Integrity API

// Check device integrity
// Includes root detection
// Hardware attestation
```

## Hiding Root from Apps

### Magisk Modules
```
- Zygisk
- Shamiko
- Play Integrity Fix
- Universal SafetyNet Fix
```

### Configuration
```
# Magisk app settings
- Enable Zygisk
- Enable Shamiko
- Configure denylist
- Add target app to denylist
```

## Frida Objection

### Objection Bypass
```bash
# Launch app with bypass
objection -g com.example.app explore --startup-script bypass.js

# bypass.js
if (Java.available) {
    Java.perform(function() {
        // Root bypass code
    });
}
```

## Checklist
```
[ ] Identify detection method
[ ] Choose bypass approach
[ ] Use Frida/Objection
[ ] Test app functionality
[ ] Consider Magisk modules
```

## Detection Bypass Priority

1. **Frida first** - Most flexible
2. **Objection** - Quick testing
3. **Magisk modules** - Permanent solution
4. **Repatch APK** - For distribution
