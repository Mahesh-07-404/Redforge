# CTF Skill: Cryptography

## Purpose
Solve cryptographic challenges in CTF competitions.

## Encoding Detection

### Base Family
```
Base16: 0-9, A-F (hex)
Base32: A-Z, 2-7 (uppercase only)
Base58: Bitcoin addresses (no 0, O, I, l)
Base64: A-Z, a-z, 0-9, +, /, =
Base85: Adobe (z85), more efficient
Base94: Visible ASCII characters
```

### Detection Order
```
1. Hex (0-9, a-f only)
2. Base64 (check for = padding)
3. Base32 (A-Z, 2-7)
4. Custom alphabet analysis
```

## Classic Ciphers

### Caesar/Rot
```python
# ROT13
import codecs
codecs.decode(ciphertext, 'rot13')

# Brute force Caesar
for shift in range(26):
    plaintext = ''
    for c in ciphertext:
        if c.isalpha():
            base = ord('a') if c.islower() else ord('A')
            plaintext += chr((ord(c) - base + shift) % 26 + base)
        else:
            plaintext += c
    print(shift, plaintext)
```

### Vigenere
```python
# Kasiski examination for key length
# Frequency analysis for decryption

# Known key
def vigenere_decrypt(ciphertext, key):
    result = []
    key_len = len(key)
    for i, c in enumerate(ciphertext):
        if c.isalpha():
            base = ord('a') if c.islower() else ord('A')
            key_char = key[i % key_len].lower()
            shift = ord(key_char) - ord('a')
            result.append(chr((ord(c.lower()) - ord('a') - shift) % 26 + ord('a')))
        else:
            result.append(c)
    return ''.join(result)
```

### Atbash
```python
def atbash(ciphertext):
    result = []
    for c in ciphertext:
        if c.isalpha():
            base = ord('a') if c.islower() else ord('A')
            result.append(chr(25 - (ord(c) - base) + base))
        else:
            result.append(c)
    return ''.join(result)
```

## Modern Crypto

### RSA

#### Factorization
```python
# Small primes
from sympy import factorint
factors = factorint(n)  # Returns {p: exp, q: exp}

# fermat.py for near-perfect squares
# cado-nfs for large numbers
# factordb.com lookup
```

#### Common Attacks
```python
# d when e is small
d = pow(e, -1, phi(n))

# e=3 small message attack
c = pow(m, 3, n)  # m^3 < n
m = round(pow(c, 1/3))

# Hastad's broadcast attack
# Chinese Remainder Theorem
from sympy import crt

# Wiener attack (d < n^0.25)
# Use sage or wiener.py

# Bleichenbaker attack (padding oracle)
```

#### RSA Math
```python
# Given p, q, e
phi = (p-1)*(q-1)
d = pow(e, -1, phi)
m = pow(c, d, n)

# n = p*q
# phi = (p-1)*(q-1) = n - p - q + 1
# d = e^-1 mod phi
```

### AES

#### Modes
```
ECB: Electronic Codebook (weak)
CBC: Cipher Block Chaining
CTR: Counter mode
GCM: Galois/Counter Mode
```

#### CBC Attacks
```python
# Padding oracle
# Modify last byte of previous block
# XOR with guess to get plaintext byte

# Bit flipping
# XOR modify IV to control first block
```

#### CTR Mode
```python
# Nonce + Counter = keystream
# ciphertext XOR keystream = plaintext
# Modify nonce for arbitrary plaintext control
```

## Hash Functions

### Collision Attacks
```python
# MD5 fast collision
# Use fastcoll

# Length extension
#适用于 MAC = hash(secret || message)
# 可计算 hash(secret || message || padding || extension)
```

### HMAC
```python
import hmac
import hashlib

# Verify HMAC
hmac.new(key, message, hashlib.sha256).hexdigest()

# Weak key attacks
# If key is known or guessable
```

## Python Crypto Libraries
```python
from Crypto.Cipher import AES, DES, RC4, PKCS1_v1_5
from Crypto.Util.number import getPrime, inverse, bytes_to_long
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import gmpy2
```

## Tools
```bash
# Online
- dcode.fr (classical ciphers)
- cryptii.com
- boxentriq.com
- factordb.com
- crt.sh (certificates)

# CLI
openssl enc -d -aes-256-cbc -in file.enc -k password
openssl rsautl -decrypt -inkey private.pem -in encrypted

# Python
sage -c "..."  # For math-heavy crypto
```

## Common CTF Patterns
```
1. Small n = factorable
2. Small e = small d attack
3. Shared p or q
4. Weak random numbers
5. Custom S-boxes
6. Oracle vulnerabilities
7. ASCII-only output
8. Time-based leaks
```

## AES-ECB Patterns
```python
# Detect ECB (repeating blocks)
from itertools import combinations

def find_ecb_iv(ciphertext, blocksize=16):
    blocks = [ciphertext[i:i+blocksize] 
              for i in range(0, len(ciphertext), blocksize)]
    for a, b in combinations(blocks, 2):
        if a == b:
            return True
    return False
```

## Key Derivation
```python
import hashlib

def derive_key(password, salt, iterations=100000):
    key = password + salt
    for _ in range(iterations):
        key = hashlib.sha256(key).digest()
    return key

# PBKDF2
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
```

## CTF Checklist
```
[ ] Identify encoding
[ ] Try common ciphers
[ ] Check if text is hex/ascii
[ ] Analyze frequency
[ ] Look for patterns
[ ] Try online decoders first
[ ] Check for weak crypto
[ ] Look for implementation bugs
[ ] Check key management
[ ] Consider side channels
```
