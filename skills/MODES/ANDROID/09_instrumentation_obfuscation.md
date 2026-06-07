# ANDROID Skill: Instrumentation & Obfuscation

## Purpose
Understand Android instrumentation and obfuscation techniques.

## Instrumentation

### What is Instrumentation?
```
- Modifying app behavior at runtime
- Hooking method calls
- Changing return values
- Injecting code
```

### Use Cases
```
- Security testing
- App analysis
- Automation
- Debugging
```

## Obfuscation Types

### 1. Name Obfuscation
```java
// Before
public class LoginActivity {
    public void validatePassword(String password) {}
}

// After (ProGuard/R8)
public class a {
    public void a(String b) {}
}
```

### 2. String Encryption
```java
// Plain text in code
String apiKey = "sk_live_1234567890";

// Obfuscated
String apiKey = DecryptHelper.decrypt(new byte[]{0x41, 0x42, 0x43});
```

### 3. Control Flow
```java
// Before
if (condition) {
    doA();
} else {
    doB();
}

// After (opaque predicates)
while (Math.random() > 0.5) {}
doA();
```

### 4. Reflection
```java
// Using reflection to hide method names
Class<?> clazz = Class.forName("com.example.Utils");
Method method = clazz.getMethod("a", String.class);
method.invoke(null, "input");
```

## Common Obfuscators

### ProGuard/R8
```gradle
android {
    buildTypes {
        release {
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

### DashO
```
- Commercial obfuscator
- Stronger protection
- Native code support
```

### DexGuard
```
- Enhanced ProGuard
- DEX encryption
- Asset protection
```

### GuardSquare
```
- iOS and Android
- Code virtualization
- String encryption
```

## Analyzing Obfuscated Code

### Dynamic Analysis
```javascript
// Hook to see actual values
Java.perform(function() {
    var MyClass = Java.use('com.example.a');
    
    // Hook the deobfuscated method
    MyClass.b.implementation = function(str) {
        console.log('[*] Decrypted: ' + str);
        return this.b(str);
    };
});
```

### Frida Tracing
```javascript
// Trace all method calls
Java.perform(function() {
    var classes = Java.enumerateLoadedClasses();
    classes.forEach(function(className) {
        if (className.includes('com.target.')) {
            console.log('[*] Found: ' + className);
        }
    });
});
```

## String Deobfuscation

### Automatic Deobfuscation
```javascript
// Hook decryption methods
Java.perform(function() {
    var Utils = Java.use('com.example.Utils');
    
    Utils.decryptString.overload('java.lang.String').implementation = function(encrypted) {
        var result = this.decryptString(encrypted);
        console.log('[*] Decrypted: ' + result);
        return result;
    };
});
```

### Native String Decryption
```javascript
// Hook native functions
var native = Module.findExportByName('libnative.so', 'decrypt');

Interceptor.attach(native, {
    onLeave: function(retval) {
        console.log('[*] Decrypted: ' + Memory.readCString(retval));
    }
});
```

## Reflection Analysis

### Find Reflection Targets
```javascript
Java.perform(function() {
    var Class = Java.use('java.lang.Class');
    var Method = Java.use('java.lang.reflect.Method');
    
    // Hook Class.forName
    Class.forName.overload('java.lang.String').implementation = function(name) {
        console.log('[*] Class.forName: ' + name);
        return this.forName(name);
    };
});
```

### Call Original Methods
```javascript
Java.perform(function() {
    var Utils = Java.use('com.example.Utils');
    
    // Get method via reflection
    var method = Java.use('java.lang.Class').getMethod(
        Java.use('java.lang.String').class
    );
    
    // Call
    var result = method.invoke(utilsInstance, "arg");
});
```

## DEX Analysis

### dex2jar + JD-GUI
```bash
# Convert DEX to JAR
d2j-dex2jar app.apk -o output.jar

# Analyze with JD-GUI
jd-gui output.jar
```

### CFR/Procyon
```bash
# Better decompilers
java -jar cfr.jar app.apk --outputdir output/
java -jar procyon.jar app.apk -o output/
```

## Obfuscation Patterns

### Enum Obfuscation
```java
// Before
enum Level { LOW, MEDIUM, HIGH }

// After (integer constants)
public static final int LEVEL_LOW = 0;
public static final int LEVEL_MEDIUM = 1;
```

### Class Obfuscation
```java
// Map obfuscated names
public class a {
    public int a(int b, int c) {
        return b + c;
    }
}
```

## Defeating Obfuscation

### FRIDA-STRINGS
```bash
# Extract strings from native
frida-strings -p <pid>
```

### frida-crypto
```javascript
// Hook crypto operations
Java.perform(function() {
    var Cipher = Java.use('javax.crypto.Cipher');
    Cipher.doFinal.overload('[B').implementation = function(data) {
        console.log('[*] Cipher input: ' + bytesToHex(data));
        var result = this.doFinal(data);
        console.log('[*] Cipher output: ' + bytesToHex(result));
        return result;
    };
});
```

## Best Practices

### For Developers
```
1. Use R8/ProGuard
2. Enable string encryption
3. Use reflection sparingly
4. Add root checks
5. Use certificate pinning
```

### For Security Testers
```
1. Use dynamic analysis
2. Hook at critical points
3. Be patient with obfuscation
4. Use native analysis tools
```

## Checklist
```
[ ] Identify obfuscation type
[ ] Use appropriate deobfuscator
[ ] Hook decryption methods
[ ] Trace execution flow
[ ] Document findings
```
