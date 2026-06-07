# LEARNING Skill: Python for Security

## Purpose
Python skills for security testing.

## Socket Programming

### TCP Client
```python
from socket import *

s = socket(AF_INET, SOCK_STREAM)
s.connect(('target', port))

s.send(b'Hello')
data = s.recv(1024)
s.close()
```

### TCP Server
```python
from socket import *

s = socket(AF_INET, SOCK_STREAM)
s.bind(('0.0.0.0', 4444))
s.listen(5)

while True:
    conn, addr = s.accept()
    data = conn.recv(1024)
    conn.send(data)
    conn.close()
```

## HTTP Requests
```python
import requests

# GET
r = requests.get('https://example.com')

# POST
r = requests.post('https://example.com/api', 
                  data={'key': 'value'})

# With headers
r = requests.get('https://example.com',
                 headers={'Authorization': 'Bearer token'})

print(r.text)
print(r.json())
```

## File Operations
```python
# Read
with open('file.txt', 'r') as f:
    data = f.read()

# Write
with open('output.txt', 'w') as f:
    f.write(data)

# Binary
with open('binary.bin', 'rb') as f:
    data = f.read()
```

## Regular Expressions
```python
import re

# Find patterns
matches = re.findall(r'flag\{[^}]+\}', data)

# Match start
if re.match(r'flag\{', data):
    print('Found')

# Search
result = re.search(r'password:\s*(\w+)', data)
if result:
    print(result.group(1))
```

## Threading
```python
import threading

def worker(arg):
    print(f'Thread {arg}')

threads = []
for i in range(5):
    t = threading.Thread(target=worker, args=(i,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()
```

## Subprocess
```python
import subprocess

# Run command
result = subprocess.run(['ls', '-la'], capture_output=True, text=True)
print(result.stdout)

# Shell command
result = subprocess.run('ls -la', shell=True, capture_output=True)
```

## JSON
```python
import json

# Parse
data = json.loads('{"key": "value"}')

# Create
obj = {'key': 'value', 'list': [1, 2, 3]}
json_str = json.dumps(obj)

# Pretty print
print(json.dumps(obj, indent=2))
```

## Cryptography
```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib
import base64

# Hash
h = hashlib.sha256(b'data').hexdigest()

# AES encrypt
key = b'0123456789abcdef'  # 16 bytes
cipher = AES.new(key, AES.MODE_CBC, iv)
ct = cipher.encrypt(pad(b'data', 16))
```

## Scapy
```python
from scapy.all import *

# Send packet
send(IP(dst='target')/TCP(dport=80)/'GET / HTTP/1.1\r\n\r\n')

# Sniff
packets = sniff(filter='tcp port 80', count=10)

# Analyze
for pkt in packets:
    if pkt.haslayer(IP):
        print(pkt[IP].src, '->', pkt[IP].dst)
```

## Collections
```python
from collections import Counter

# Count occurrences
text = 'aaabbbccc'
cnt = Counter(text)
print(cnt.most_common())

# Default dict
from collections import defaultdict
d = defaultdict(list)
```

## Base64
```python
import base64

# Encode
encoded = base64.b64encode(b'data')

# Decode
decoded = base64.b64decode(encoded)
```

## argparse
```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--target', required=True)
parser.add_argument('-p', '--port', type=int, default=80)
args = parser.parse_args()

print(args.target, args.port)
```
