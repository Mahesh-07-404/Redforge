# ANDROID Skill: Native Library Analysis

## Purpose
Analyze native (JNI) code in Android apps.

## Native Libraries

### Common Locations
```
lib/arm64-v8a/libnative.so
lib/armeabi-v7a/libnative.so
lib/x86/libnative.so
lib/x86_64/libnative.so
```

### Why Native Code?
```
Performance critical code
Legacy code reuse
Obffuscation
Hardware access
Hidden functionality
```

## Extracting Libraries

### From APK
```bash
unzip app.apk lib/armeabi-v7a/libnative.so
```

### From Device
```bash
adb pull /data/app/com.example/lib/arm64-v8a/libnative.so ./
```

## Analysis Tools

### Static
```bash
# Strings
strings libnative.so | head -100
strings libnative.so | grep -i flag

# Symbols
nm libnative.so              # List symbols
readelf -s libnative.so      # Detailed symbols
objdump -d libnative.so       # Disassemble

# File info
file libnative.so
readelf -h libnative.so
```

### Dynamic Analysis
```bash
# GDB
gdb -q libnative.so
(gdb) disassemble main

# radare2
r2 libnative.so
[0x00001000]> aaa    # Analyze
[0x00001000]> afl    # List functions
[0x00001000]> pdf    # Disassemble function
```

### IDA/Ghidra
```bash
# IDA
ida64 libnative.so

# Ghidra
ghidraRun
# Import binary, select ARM64
```

## JNI Functions

### Common JNI Calls
```c
// Find class
jclass cls = (*env)->FindClass(env, "com/example/Target");

// Get method ID
jmethodID method = (*env)->GetMethodID(env, cls, "methodName", "(I)V");

// Call method
(*env)->CallVoidMethod(env, obj, method, arg);
```

### Native Function Naming
```
Java_com_example_MainActivity_checkFlag
Java_<package>_<class>_<method>

// With signature
Java_com_example_MainActivity_nativeMethod(JNIEnv *env, jobject obj, jstring input)
```

## Common Vulnerabilities

### Hardcoded Strings
```c
// Look for strings in binary
strings libnative.so

// Common patterns
"flag{"
"password"
"token"
"secret"
```

### Weak Crypto
```c
// Custom crypto implementations
// Simple XOR
for (i = 0; i < len; i++) {
    output[i] = input[i] ^ key[i % keylen];
}
```

### Buffer Overflow
```c
// strcpy without length check
char buf[64];
strcpy(buf, user_input);  // Vulnerable!
```

### Command Injection
```c
// system() with user input
system(user_input);  // Vulnerable!
```

## Frida Hooking Native

### Hook Native Function
```javascript
var funcName = 'Java_com_example_MainActivity_checkFlag';
Interceptor.attach(Module.findExportByName('libnative.so', funcName), {
    onEnter: function(args) {
        console.log('[*] checkFlag called');
        console.log('[*] Arg:', Memory.readCString(args[2]));
    },
    onLeave: function(retval) {
        console.log('[*] Return:', retval);
    }
});
```

### Find Function Address
```javascript
var lib = Module.findBaseAddress('libnative.so');
console.log('[*] Base:', lib);

// Find by name
var func = Module.findExportByName('libnative.so', 'checkFlag');
console.log('[*] checkFlag:', func);
```

### Read/Write Memory
```javascript
// Read string from argument
var inputStr = Memory.readCString(args[2]);
console.log('[*] Input:', inputStr);

// Write to return value
Memory.writeInt(retval, 1);  // Return 1 (true)
```

## ARM Assembly Basics

### Registers
```
x0-x7: Arguments (also return for functions returning structs)
x30: Link Register (return address)
sp: Stack Pointer
pc: Program Counter
```

### Common Instructions
```
LDR  - Load register
STR  - Store register
MOV  - Move value
ADD  - Add
SUB  - Subtract
CMP  - Compare
B/BL - Branch/Branch with Link
BLR  - Branch to Register
RET  - Return
```

### Function Prologue
```asm
push   {fp, lr}
add    fp, sp, #4
sub    sp, sp, #0x10
```

## Frida + ARM

### Trace Execution
```javascript
var func = Module.findExportByName('libnative.so', 'processInput');

Interceptor.attach(func, {
    onEnter: function(args) {
        console.log('[*] processInput called');
        console.log('[*] Args:');
        for (var i = 0; i < 4; i++) {
            console.log('    x' + i + ':', this.context['x' + i]);
        }
    },
    onLeave: function(retval) {
        console.log('[*] Return:', retval);
    }
});
```

### Modify Control Flow
```javascript
Interceptor.attach(func, {
    onLeave: function(retval) {
        console.log('[*] Original return:', retval);
        retval.replace(1);  // Force return 1
    }
});
```

## CTF Native Challenges

### Approach
```
1. Extract native library
2. Find function of interest
3. Analyze with IDA/Ghidra
4. Identify vulnerability
5. Write Frida script or patch
```

### Common Patterns
```c
// Flag check
if (checkFlag(input)) {
    printf("Correct!\n");
}

// Hidden function
void hidden() {
    printf("flag{...}\n");
}

// Encrypted flag
char encrypted[] = {0x41, 0x42, 0x43};
decode(encrypted);
```

## Patching Native Binaries

### With Radare2
```bash
r2 -w libnative.so   # Write mode

[0x00001000]> s sym.checkFlag
[0x00001000]> pdf     # Disassemble
[0x00001000]> wa mov r0, #1  # Write: return 1
[0x00001000]> wa nop        # NOP
```

### With IDA
```
Edit -> Patch program -> Assemble
Edit -> Patch program -> Apply patches
```

## Automated Analysis

### FLARE
```
https://github.com/fireeye/flare-ida_plugins
# Native librarie analysis
```

### BinCAT
```
# Native code analysis plugin
```

## Checklist
```
[ ] Extract library
[ ] Identify architecture
[ ] Find JNI functions
[ ] Analyze strings
[ ] Find interesting functions
[ ] Hook with Frida
[ ] Identify vulnerability
[ ] Exploit/patch
```
