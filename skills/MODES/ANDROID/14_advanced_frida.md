# ANDROID Skill: Advanced Frida Techniques

## Purpose
Advanced Frida scripting for complex Android analysis.

## Advanced Hooking

### Overload Resolution
```javascript
// Multiple overloads
Java.perform(function() {
    var File = Java.use('java.io.File');
    
    // Specific overload
    File.$init.overload('java.lang.String').implementation = function(path) {
        console.log('[*] File path: ' + path);
        return this.$init(path);
    };
    
    // All overloads
    File.exists.overload().implementation = function() {
        console.log('[*] exists() called');
        return this.exists();
    };
});
```

### Constructor Hooks
```javascript
Java.perform(function() {
    var MyClass = Java.use('com.example.MyClass');
    
    // Hook constructor
    MyClass.$init.overload('java.lang.String', 'int').implementation = function(str, num) {
        console.log('[*] Constructor: ' + str + ', ' + num);
        return this.$init(str, num);
    };
});
```

### Static Field Access
```javascript
Java.perform(function() {
    var MyClass = Java.use('com.example.MyClass');
    
    // Read static field
    console.log('[*] Static field: ' + MyClass.STATIC_FIELD.value);
    
    // Modify static field
    MyClass.STATIC_FIELD.value = 'modified';
});
```

## Memory Operations

### Read Memory Regions
```javascript
function dumpMemory(address, size) {
    var data = Memory.readByteArray(address, size);
    console.log('[*] Memory dump:');
    console.log(hexdump(data, {length: size}));
}

// Usage
var module = Process.findModuleByName('libnative.so');
dumpMemory(module.base, 0x1000);
```

### Write Memory
```javascript
// Write bytes
var ptr = Memory.alloc(16);
Memory.writeByteArray(ptr, [0x41, 0x42, 0x43, 0x44]);

// Write string
Memory.writeUtf8String(ptr, 'Hello');

// Write pointer
Memory.writePointer(ptr, anotherPtr);
```

### Search Memory
```javascript
// Find patterns
var ranges = Process.enumerateRanges('r--');

ranges.forEach(function(range) {
    var pattern = Memory.scanSync(range.start, range.size, '41 42 43 44');
    pattern.forEach(function(match) {
        console.log('[*] Found at: ' + match.address);
    });
});
```

## Stalker (Code Tracing)

### Basic Tracing
```javascript
var module = Process.findModuleByName('libnative.so');

Interceptor.attach(module.base, {
    onEnter: function(args) {
        // Called before function
        console.log('[*] Called from:');
        console.log(Thread.backtrace(this.context, Backtracer.ACCURATE)
            .map(DebugSymbol.fromAddress).join('\n'));
    }
});
```

### Stalker Trace
```javascript
var module = Process.findModuleByName('libnative.so');

// Create stalker
Stalker.follow(Process.getCurrentThreadId(), {
    events: {
        call: true,
        ret: true
    },
    onReceive: function(events) {
        parser.dump(events);
    },
    transform: function(iter) {
        var instruction;
        while ((instruction = iter.next()) !== null) {
            // Modify instructions
            iter.putLabel('label_' + iter.index);
            iter.next();
        }
    }
});
```

## Native Hooking

### Intercept Native Functions
```javascript
// Find function
var func = Module.findExportByName('libnative.so', 'checkFlag');

// Attach interceptor
Interceptor.attach(func, {
    onEnter: function(args) {
        console.log('[*] checkFlag called');
        console.log('[*] arg0 (JNI*): ' + args[0]);
        console.log('[*] arg1 (jobject): ' + args[1]);
        console.log('[*] arg2 (jstring): ' + Memory.readCString(args[2]));
    },
    onLeave: function(retval) {
        console.log('[*] Return value: ' + retval);
        // Modify return
        retval.replace(1);
    }
});
```

### Native String Manipulation
```javascript
var func = Module.findExportByName('libnative.so', 'process');

// JNI string handling
Interceptor.attach(func, {
    onEnter: function(args) {
        // Get JNI environment
        var env = args[0];
        
        // Get string length
        var length = env.GetStringLength(args[2]);
        
        // Read string
        var str = env.GetStringUTFChars(args[2], null);
        console.log('[*] Input: ' + str);
        
        // Release
        env.ReleaseStringUTFChars(args[2], str);
    }
});
```

## Frida Stalker + IDA

### Export Stalker Traces
```javascript
// Generate IDC script for IDA
Stalker.follow(Process.getCurrentThreadId(), {
    transform: function(iter) {
        var instr = iter.next();
        if (instr) {
            // Log to file
            console.log(instr.address + ' ' + instr.mnemonic + ' ' + instr.opStr);
        }
        iter.next();
    }
});
```

## Advanced Patterns

### Hook All Classes in Package
```javascript
Java.perform(function() {
    var classes = Java.enumerateLoadedClasses();
    
    classes.forEach(function(className) {
        if (className.startsWith('com.target.')) {
            try {
                var cls = Java.use(className);
                
                // Hook all methods
                var methods = Object.keys(cls);
                methods.forEach(function(methodName) {
                    if (methodName.includes('check') || methodName.includes('verify')) {
                        try {
                            cls[methodName].overloads.forEach(function(overload) {
                                overload.implementation = function() {
                                    console.log('[*] ' + className + '.' + methodName);
                                    return this[methodName].apply(this, arguments);
                                };
                            });
                        } catch(e) {}
                    }
                });
            } catch(e) {}
        }
    });
});
```

### Race Condition Exploitation
```javascript
// Timing attacks
var start = Date.now();
var result = targetFunction();
var end = Date.now();

console.log('[*] Execution time: ' + (end - start) + 'ms');

// Multiple calls for timing
var times = [];
for (var i = 0; i < 100; i++) {
    var start = Date.now();
    // call
    times.push(Date.now() - start);
}
```

### SSL Unpinning Advanced
```javascript
// Multi-method SSL bypass
Java.perform(function() {
    // ClearTrustManager
    var TrustManagerImpl = Java.use('javax.net.ssl.TrustManagerImpl');
    TrustManagerImpl.checkServerTrusted.implementation = function(chain, authType) {
        console.log('[*] TrustManager bypass');
    };
    
    // OkHttpCertificatePinner
    try {
        var Pinner = Java.use('okhttp3.CertificatePinner');
        Pinner.check.overload('java.lang.String', '[Ljava.security.cert.Certificate;').implementation = function(host, certs) {
            console.log('[*] CertificatePinner bypass for: ' + host);
        };
    } catch(e) {}
    
    // Apache HttpClient
    try {
        var SSL = Java.use('org.apache.http.conn.ssl.SSLSocketFactory');
        SSL.allowAllCertificates.implementation = function() {
            console.log('[*] Apache SSL bypass');
        };
    } catch(e) {}
});
```

## Persistence

### Frida Server Setup
```bash
# Start Frida server
adb push frida-server /data/local/tmp/
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "/data/local/tmp/frida-server -l 0.0.0.0:27042"

# Or on boot (root)
# Add to init script
```

### Spawn vs Attach
```javascript
// Spawn (before app starts)
frida -U -f com.example.app -l script.js --no-pause

// Attach (to running app)
frida -U com.example.app -l script.js

// Both combined
frida -U -f com.example.app -l script.js
```

## Performance Tips
```
- Use Stalker sparingly (expensive)
- Cache module lookups
- Minimize console.log in hot paths
- Use try/catch for error handling
- Avoid heavy string operations
```
