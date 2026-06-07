# CTF Skill: Reverse Engineering

## Purpose
Techniques for analyzing and reverse engineering binaries.

## Static Analysis

### Basic Tools
```bash
# Disassembler
objdump -d binary | less
objdump -M intel -d binary

# Symbol analysis
nm binary  # Symbols
readelf -s binary  # Full symbol info
strings binary | grep flag

# ELF analysis
readelf -h binary  # Header
readelf -l binary  # Program headers
readelf -S binary  # Section headers
```

### Disassembly
```bash
# Interactive disassembler
radare2 binary
# Commands:
# aaa - analyze all
# afl - list functions
# pdf - disassemble function
# s sym.main - seek to main
# px - hexdump

# Ghidra (GUI)
ghidraRun

# IDA (if available)
ida64 binary
```

### Pattern Recognition
```c
// Common function signatures
main()
fork()
execve()
system()
popen()
socket()
connect()
recv()

// Crypto patterns
MD5_Update()
SHA256_Update()
AES_encrypt()
RSA_public_decrypt()
```

## Dynamic Analysis

### Debugging
```bash
# Basic debugging
gdb binary
gdb -q binary

# With pwntools
gdb.attach(proc, '''
    break *0x0804856c
    continue
''')
```

### GDB Commands
```
break *0x0804856c    # Break at address
break main           # Break at function
info breakpoints    # List breakpoints
delete 1            # Delete breakpoint
run                  # Start execution
continue             # Continue execution
nexti / ni          # Next instruction
stepi / si          # Step into call
print $reg          # Print register
x/10x $sp           # Examine memory (hex)
x/s $ebp-8          # Examine as string
x/10i $pc           # Examine as instructions
backtrace / bt      # Stack trace
info registers      # All registers
```

### GEF (GDB Enhancement)
```bash
# Install
wget -q -O- https://github.com/hugsy/gef/releases/download/20231011/gef.sh | sh

# Features
gef➤  pdisass $pc          # Pretty disassemble
gef➤  heap chunks           # Heap analysis
gef➤  got                  # GOT table
gef➤  vmmap                # Memory map
gef➤  checksec             # Security checks
```

## Binary Formats

### ELF Structure
```
Header
  - Entry point
  - Program headers
  - Section headers

Sections (.text, .data, .bss, .rodata, .got, .plt)

Segments (LOAD, INTERP, DYNAMIC)
```

### Executable Analysis
```bash
# Checksec
checksec --file=binary
# Output:
# Arch:     amd64
# Stack:    Canary found
# NX:       NX enabled
# PIE:      No PIE
# Relro:    Partial
```

### PLT/GOT Analysis
```bash
# GOT/PLT entries
objdump -d -j .plt binary
objdump -d -j .got binary

# What calls what
readelf -r binary
```

## Decompilation

### Ghidra Scripts
```java
// Basic decompile
Listing.decompile(getFirstFunction());

// Find strings
import java.util.Arrays;
StringSearcher searcher = new StringSearcher();
searcher.search();

// Find references
import ghidra.app.script.GhidraScript;
findReferencesTo(address);
```

### Pseudocode Analysis
```c
// Common decompiled patterns

// Buffer allocation
char buffer[256];
char *buffer = malloc(256);

// String operations
strcpy(dst, src);
strcat(dst, src);
sprintf(buf, "%s", input);
scanf("%s", buf);

// Loop patterns
for (int i = 0; i < n; i++) { }

// Conditional
if (x > y) { /* ... */ }
```

## Crackme Solving

### Basic Pattern
```
1. Find password check function
2. Understand validation logic
3. Either:
   - Find hardcoded password
   - Reverse algorithm
   - Patch binary
   - Bruteforce
```

### Common Approaches
```python
# Patch binary
with open('binary', 'rb') as f:
    data = bytearray(f.read())

# NOP out check
data[0x1234:0x1236] = b'\x90\x90\x90'

# Change conditional
data[0x1234] = 0x75  # jne -> je

with open('binary_patched', 'wb') as f:
    f.write(data)
```

## Scripting Analysis

### Automate with pwntools
```python
from pwn import *

binary = ELF('./crackme')
print(f"Entry point: {hex(binary.entry)}")
print(f"Functions: {binary.symbols.keys()}")

# Find password function
for name, addr in binary.symbols.items():
    if 'check' in name or 'pass' in name or 'valid' in name:
        print(f"{name}: {hex(addr)}")
```

### ROP Chain Builder
```python
from pwn import *

elf = ELF('./rop binary')
rop = ROP(elf)

# Build ROP chain
rop.call(elf.symbols['win_function'])
print(rop.dump())
```

## Android APK Analysis

### Static Analysis
```bash
# Extract APK
apktool d target.apk -o output/

# Decompile
jadx -d output source.apk

# Find secrets
grep -r "password" output/
grep -r "api_key" output/
```

### Dynamic Analysis
```bash
# Frida hooking
frida -U -f com.target.app -l script.js

# script.js
Java.perform(function() {
    var TargetClass = Java.use('com.target.Class');
    TargetClass.method.implementation = function(arg) {
        console.log('Arg:', arg);
        return this.method(arg);
    };
});
```

## Checklist
```
[ ] Run checksec
[ ] Identify binary type
[ ] Check symbols/strings
[ ] Analyze entry point
[ ] Find interesting functions
[ ] Trace execution flow
[ ] Identify crypto/encoding
[ ] Look for anti-debug
[ ] Build exploit
```
