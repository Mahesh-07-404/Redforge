# ANDROID Skill: Android Internals

## Purpose
Deep understanding of Android internals for security research.

## Android Architecture

```
┌─────────────────────────────────────────────┐
│              Applications                   │
│   (System Apps, User Apps)                  │
├─────────────────────────────────────────────┤
│              Application Framework          │
│  (Activity Manager, Package Manager,        │
│   Window Manager, Content Providers, etc.)   │
├─────────────────────────────────────────────┤
│         Android Runtime (ART/Dalvik)        │
│     (DEX bytecode execution, GC)            │
├─────────────────────────────────────────────┤
│            Native Libraries                 │
│   (OpenGL, SSL, SQLite, WebKit, etc.)      │
├─────────────────────────────────────────────┤
│              HAL (Hardware Abstraction)     │
├─────────────────────────────────────────────┤
│              Linux Kernel                   │
│   (Security, Memory, Process, Drivers)       │
└─────────────────────────────────────────────┘
```

## Application Lifecycle

### Component Types
```
Activity      - Single screen UI
Service      - Background operation
BroadcastReceiver - Event listener
ContentProvider - Data sharing
```

### Process Model
```
Zygote process
    ├── system_server
    ├── com.android.phone
    ├── com.android.browser
    └── com.example.app (isolated)
```

## ART/Dalvik

### DEX Format
```
DEX File Structure:
- Header
- String IDs
- Type IDs
- Proto IDs
- Field IDs
- Method IDs
- Class Definitions
- Data
```

### Bytecode
```java
// Java source
if (x > 0) {
    doSomething();
}

// DEX bytecode (simplified)
if-gtz v0, :cond_0
invoke-virtual {p0}, LMyClass;.doSomething()V
:cond_0
```

### OAT Files
```
- Compiled DEX to native code
- Located in /data/app/<pkg>/oat/
- ARM, ARM64, x86, x86_64
```

## IPC/Binder

### Binder Mechanism
```
Client Process                 Server Process
     │                              │
     │  Binder Driver               │
     ├──────────────────────────────┤
     │                             │
IPC invocations ─────────────►  Handle
     │◄────────────── Reply ───────┘
```

### AIDL
```java
// Interface definition
interface IRemoteService {
    String getData();
    void setData(String data);
}

// Auto-generated Binder code
```

## Security Model

### User IDs
```
Each app gets unique UID
/apps/uid_<uid>/
/data/data/<pkg>/
```

### Permissions Model
```
Install time permissions
Runtime permissions (Android 6+)
Permission groups
```

### SELinux
```
Enforcing/Permissive modes
Contexts: u:object_r:app_data_file:s0
Policy rules
```

## File System

### Key Directories
```
/data/                    - App data
/data/data/<pkg>/         - App private storage
/data/app/<pkg>/          - APK files
/data/local/tmp/          - World-writable
/system/app/              - System apps
/system/framework/        - Framework JARs
```

### Permissions
```
drwxrwx---   - rwx for owner only
drwxrwxrwx   - rwx for everyone (world-writable)
```

## Memory Layout

### Process Memory
```
High Addresses
┌─────────────┐
│   Native    │  (malloc, JNI)
├─────────────┤
│  Java Heap │  (ART managed)
├─────────────┤
│  Code      │  (Native + DEX)
├─────────────┤
│  Stack     │  (Thread stacks)
├─────────────┤
│ Low Addresses
```

### ASLR
```
- PIE enabled
- Stack canaries
- Randomized heap
```

## System Services

### Key Services
```
ActivityManagerService  - App lifecycle
PackageManagerService   - App installation
WindowManagerService    - UI management
ContentService          - Data providers
```

### Service Communication
```
Intent ──────────► Component
AIDL ────────────► Binder IPC
Messenger ───────► Handler
```

## Debugging Internals

### Debugfs
```bash
# View binder info
cat /sys/kernel/debug/binder/stats
cat /sys/kernel/debug/binder/transactions

# View process info
cat /proc/<pid>/maps
cat /proc/<pid>/status
```

### systrace
```bash
# Capture system traces
systrace.py -o trace.html sched gfx view wm am app
```

### Perf
```bash
# Profile app
perf record -p <pid> -g
perf report
```

## Vulnerability Classes

### 1. Component Attacks
```
- Exported activities
- Exported services
- Exported broadcast receivers
- Exported content providers
```

### 2. WebView Vulnerabilities
```
- JavaScript interface
- File access
- URL loading
```

### 3. Intent Injection
```
- Unprotected broadcasts
- Scheme handling
- Deep links
```

### 4. Memory Issues
```
- Use after free
- Heap overflow
- Race conditions
```

## Reverse Engineering

### DEX Structure
```bash
# View DEX header
xxd app.apk | head -20

# dexdump
dexdump -d classes.dex
```

### OAT Analysis
```bash
# List oat files
ls /data/app/*/oat/*/*.oat

# oatdump
oatdump --oat-file=/path/to/app.oat
```

### ART Internals
```
- Class linking
- Method inlining
- GC roots
- JIT compilation
```

## Resources
```
- AOSP Source Code
- Android Developers Documentation
- Android Security Reports
- Google Project Zero Blog
- NTT Security Research
```
