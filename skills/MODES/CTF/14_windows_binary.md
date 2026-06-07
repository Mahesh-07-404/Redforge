# CTF Skill: Windows Binary Exploitation

## Purpose
Techniques for Windows binary challenges.

## Windows Basics

### Memory Layout
```
High Memory
+------------------+
|       Stack      |
+------------------+
|                   |
+------------------+
|       Heap       |
+------------------+
|    .data/.bss    |
+------------------+
|   .text (PE)     |
+------------------+
|       PEB/TEB    |
+------------------+
Low Memory
```

### Windows DLLs
```
kernel32.dll  - Core functions
ntdll.dll     - NT kernel interface
msvcrt.dll    - C runtime
user32.dll    - GUI functions
```

### Security
```bash
# Checksec equivalent
.\checksec --file=binary.exe

# ASLR, DEP, SafeSEH, SEHOP, CFG
```

## Windows Shellcode

### Basic Shellcode
```python
# x86 Windows shellcode
shellcode = asm('''
    push 0
    push 0x6578652e  # ".exe"
    push 0x636c6163  # "calc"
    mov eax, esp
    
    push 0
    mov esp, eax
    call 0x12345678  # addr of WinExec
''')
```

### Windows x64 Shellcode
```python
shellcode = asm('''
    sub rsp, 0x30
    
    # WinExec("calc", 1)
    lea rcx, [rip+calc_str]
    mov rdx, 1
    mov rax, 0x...
    call rax
    
    # ExitProcess(0)
    xor rcx, rcx
    mov rax, 0x...
    call rax
    
calc_str:
    .asciz "calc"
''')
```

## SEH Exploitation

### Structured Exception Handler
```python
# Overflow overwrites SEH
# SEH record: Next SEH -> Handler
# P overwrite: Next SEH pointer
# P+4 overwrite: Handler address

# Use pop pop ret gadget
# Jump to shellcode
```

### SafeSEH Bypass
```python
# Use non-SafeSEH modules
# Use ROP to disable SafeSEH
# Use heap spray
```

## Windows ROP

### Information Leak
```python
# Format string not common
# Use other leaks

# Heap spray for address leak
# VirtualAlloc spray
# PowerShell spray
```

### ROP Chain
```python
# Windows x86 ROP
# Use pwntools or mona

# Example: Call WinExec
rop = ROP(elf)
rop.win_exec(calc_cmd)

# Use mona
# !mona rop -m *.dll
```

## Heap Exploitation

### Windows Heap Internals
```python
# Lookaside, Freelist, LFH (Low Fragmentation Heap)
# Segment heap in Windows 8+

# Overflows still possible
# Use unlink on older systems
```

### Use After Free
```python
# Common pattern in Windows binaries
# Allocate, Free, Use (dangling pointer)
# Use after free gives code execution
```

## Windows Shellcode Techniques

### Egg Hunter
```python
# Find shellcode in memory
egg = b'w00t' * 2  # Egg marker
hunter = asm('''
    mov ebx, 0x0BADF00D  # Start address
search:
    inc ebx
    cmp [ebx], egg
    jne search
    jmp ebx
''')
```

### Staged Shellcode
```python
# First stage: download and execute
# Small shellcode downloads bigger payload

stage1 = asm('''
    # Download shellcode via URL
    call download
    
    # Execute
    jmp eax
''')
```

## DLL Hijacking

### Search Order
```python
# 1. Directory of exe
# 2. System32
# 3. Windows directory
# 4. Current directory
# 5. PATH directories
```

### Create Malicious DLL
```python
from ctypes import *

# Export original function
def GetLastError():
    return 0

# Shellcode execution
class ExportDLL:
    def DllMain(self):
        # Shellcode here
        return 1
```

## Windows-Specific Tools

### Mona
```python
# Immunity Debugger mona
# Find gadgets
!mona find -s "pop pop ret"

# Find modules
!mona modules

# Create rop chain
!mona rop -m *.dll
```

### WinDBG
```
# Breakpoints
bp 0x12345678
bl  # List breakpoints

# Examine
da address  # ASCII
du address  # Unicode
db address  # Bytes
dd address  # DWORDS

# Stepping
p  # Step over
t  # Step into
g  # Continue

# Memory
!heap -a
!peb
!teb
```

## Privilege Escalation

### Token Impersonation
```python
# SeImpersonatePrivilege
# Use Named Pipe
# Potato family exploits

# RottenPotato
# JuicyPotato
# SweetPotato
```

### Service Exploits
```powershell
# Create malicious service
sc create MaliciousService binPath= "C:\path\to\mal.exe"
sc start MaliciousService

# Modify existing service
sc config ServiceName binPath= "cmd /c ..."
```

## Common Patterns

### Format String
```
Less common on Windows
printf(user_input)  # Rare
wsprintf  # More common
```

### Integer Overflow
```c
// Same patterns as Linux
int size = user_input;
int total = size + header_size;
// Can overflow
```

## Checklist
```
[ ] Check security settings
[ ] Identify vulnerability
[ ] Find suitable exploit technique
[ ] Build exploit
[ ] Test
[ ] Get shell
```
