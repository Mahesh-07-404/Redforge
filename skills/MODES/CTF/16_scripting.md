# CTF Skill: Scripting & Automation

## Purpose
Python scripting for solving CTF challenges efficiently.

## Common Patterns

### Brute Force
```python
#!/usr/bin/env python3
from itertools import product
import string

def bruteforce(charset, length):
    for attempt in product(charset, repeat=length):
        yield ''.join(attempt)

# Usage
for attempt in bruteforce(string.ascii_lowercase, 4):
    if check(attempt):
        print(f"Found: {attempt}")
        break
```

### Dictionary Attack
```python
def dict_attack(wordlist, check_func):
    with open(wordlist) as f:
        for line in f:
            word = line.strip()
            if check_func(word):
                return word
    return None
```

## Network Scripts

### TCP Client
```python
from socket import *

def send_hex(s, data):
    s.send(bytes.fromhex(data))

def recv_until(s, delim):
    data = b''
    while delim not in data:
        data += s.recv(1)
    return data

# Usage
s = socket(AF_INET, SOCK_STREAM)
s.connect(('host', port))
```

### HTTP Client
```python
import urllib.request
import urllib.parse

def post(url, data):
    data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=data)
    return urllib.request.urlopen(req).read()

def get(url, headers={}):
    req = urllib.request.Request(url, headers=headers)
    return urllib.request.urlopen(req).read()
```

## Crypto Scripts

### XOR
```python
def xor(data, key):
    if isinstance(key, int):
        key = bytes([key])
    result = []
    for i, b in enumerate(data):
        result.append(b ^ key[i % len(key)])
    return bytes(result)

# Encrypt/decrypt
cipher = xor(plaintext, key)
decrypted = xor(cipher, key)
```

### Frequency Analysis
```python
from collections import Counter

def frequency_analysis(text):
    return Counter(text)

def chi_squared(text, expected):
    observed = Counter(text)
    return sum((o - e)**2 / e for c, o in observed.items() for e in [expected.get(c, 0)])
```

### RSA Tools
```python
from Crypto.Util.number import getPrime, inverse, bytes_to_long

def rsa_encrypt(m, e, n):
    return pow(bytes_to_long(m), e, n)

def rsa_decrypt(c, d, n):
    return long_to_bytes(pow(c, d, n))
```

## File Analysis

### Extract Strings
```python
import re

def extract_strings(data, min_len=4):
    pattern = re.compile(rb'[\x20-\x7e]{%d,}' % min_len)
    return pattern.findall(data)

def extract_pattern(data, pattern):
    return re.findall(pattern.encode(), data)
```

### File Carving
```python
def carve_file(data, signature, name):
    start = data.find(signature)
    if start == -1:
        return None
    
    # Find end marker or use heuristic
    end = find_end(data, start, name)
    
    return data[start:end]

def find_end(data, start, name):
    if 'zip' in name:
        return data.find(b'PK\x05\x06', start)
    return start + 1000000  # Fallback
```

## Binary Exploitation

### Pwntools Basic
```python
from pwn import *

context.arch = 'amd64'
context.log_level = 'debug'

io = process('./binary')
# io = remote('host', port)

# Interactive
io.interactive()

# Send/Receive
io.send(b'payload')
io.sendline(b'input')
response = io.recvline()
```

### Exploit Template
```python
#!/usr/bin/env python3
from pwn import *

HOST = 'host'
PORT = port

def exploit():
    io = remote(HOST, PORT) if not LOCAL else process('./binary')
    
    # Build payload
    offset = 64
    payload = b'A' * offset
    payload += p64(0xdeadbeef)
    
    io.sendline(payload)
    io.interactive()

if __name__ == '__main__':
    exploit()
```

## Automation

### Multiprocessing
```python
from multiprocessing import Pool, cpu_count

def check_worker(args):
    value, target = args
    return value if check(value, target) else None

def parallel_check(items, target, workers=4):
    with Pool(workers) as pool:
        results = pool.map(check_worker, [(i, target) for i in items])
    return [r for r in results if r]
```

### Async
```python
import asyncio

async def check(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()

async def main(urls):
    tasks = [check(url) for url in urls]
    return await asyncio.gather(*tasks)
```

## Regex Patterns

### Flag Pattern
```python
import re

def find_flags(data):
    patterns = [
        r'flag\{[^}]+\}',
        r'FLAG\{[^}]+\}',
        r'pctf\{[^}]+\}',
        r'hxp\{[^}]+\}',
    ]
    
    for pattern in patterns:
        yield from re.findall(pattern, data)
```

### Hash Patterns
```python
patterns = {
    'md5': r'[a-f0-9]{32}',
    'sha1': r'[a-f0-9]{40}',
    'sha256': r'[a-f0-9]{64}',
    'base64': r'[A-Za-z0-9+/]+={0,2}',
}
```

## Checklist
```
[ ] Identify problem type
[ ] Choose approach
[ ] Write efficient solution
[ ] Test locally
[ ] Run on remote
[ ] Get flag
```
