# CTF Skill: Crypto Advanced

## Purpose
Advanced cryptographic attack techniques.

## RSA Attacks

### Wiener's Attack
```python
# When d < n^0.25
from fractions import Fraction

def wiener(e, n):
    # Continued fraction expansion
    # Find convergent with smallest |Ed - k*phi| < 1/3 * sqrt(n)
    pass

# Use sage
sage: e = ...
sage: n = ...
sage: d = pow(e, -1, euler_phi(n))  # This won't work, use wiener
```

### Boneh-Durfee Attack
```python
# When d < n^0.292
# Use sage implementation
sage: load('boneh_durfee.sage')
sage: d = boneh_durfee(e, n)
```

### Hastad's Broadcast Attack
```python
# Same message, different e (coprime)
# Using Chinese Remainder Theorem

from sympy import CRT

def hastad(c_list, n_list, e):
    # CRT to combine ciphertexts
    c = CRT([c % n for c, n in zip(c_list, n_list)])
    # Find e-th root
    m = round(pow(c, 1/e, n_product))
    return m
```

### Franklin-Reiter Attack
```python
# RSA with related messages: f(m1), f(m2)
# where m1 = a*m2 + b

# Use gcd
def franklin_reiter(f, g, n):
    # gcd(f(x) - g(x), n) reveals relationship
    pass
```

### Coppersmith's Theorem
```python
# Find small root of polynomial modulo n
# Small e with partial d leak
# Use sage
sage: P.<x> = PolynomialMod(n, Integer(e))
sage: f = ...  # polynomial
sage: f.monic().small_roots(beta=0.5)
```

## Elliptic Curve Crypto

### ECDSA
```python
# Weak nonce leads to key recovery
# If k is known: d = (s^-1 * (z + r*d)) mod n
# If k is reused: d = (s1*z2 - s2*z1) / (r2*s1 - r1*s2)

# Low randomness
# Same k reveals d
```

### Curve Weaknesses
```python
# Find curve parameters
# Check for weak curves
# Anomalous curve: #E(p) = p
# Smart's attack: E(p) = p

# Find curve order
# Should be prime or smooth
```

## AES Side Channels

### Timing Attacks
```python
# Measure execution time
# Correlate with key byte guesses
# Use statistical analysis
```

### Power Analysis
```python
# Differential Power Analysis (DPA)
# Measure power consumption
# Correlate with intermediate values
```

## Hash Length Extension
```python
# For MD5, SHA1, SHA256 with key=secret||message
# Can compute hash(secret||message||padding||extension)

import hashlib
import hmac

def length_extension(original_msg, original_mac, secret_len, extension):
    # Find padding
    # Append extension
    # Compute new MAC
    pass
```

## Diffie-Hellman

### Small Subgroup
```python
# DH with small q
# Find order of public key
# Use to recover other party's private key

# If q is small, can enumerate all possible shared secrets
```

### Logjam Attack
```python
# Group 1 (512-bit) DH broken by NFS
# Precompute discrete log for common primes
# Use in real-time attack
```

## Lattice Attacks

### LLL Algorithm
```python
# Use sage or fpylll
from sage.all import *

# CVP, SVP problems
# Can break RSA with high bits known
```

## Padding Oracle

### CBC Mode
```python
# Modify ciphertext blocks
# Observe padding error

def padding_oracle(c1, c2, oracle):
    # c1 is previous block, c2 is target
    # Byte-by-byte decryption
    
    for i in range(16, 0, -1):
        for guess in range(256):
            # Craft IV with guess at position i
            # Query oracle
            # If valid padding, guess is correct
```

## RC4 Attacks

### Biases
```python
# Fluhrer-McGrew biases
# Specific output bytes biased

# Recover key stream from ciphertext
# Use statistical analysis
```

## ECBCAC

### IV Prediction
```python
# If IV is predictable
# Precompute IV' = f(seed)
# Encrypt with known IV
# Attacker can control first block
```

## Oracle Attacks

### Bleichenbaker
```python
# PKCS#1 v1.5 padding oracle
# RSA decryption must reveal padding errors

# Use Bletchley's or other tools
```

## Tools
```bash
# RsaCtfTool
python3 RsaCtfTool.py --attack <attack> --n <n> --e <e> --c <c>

# Wiener's attack
# Hastad attack
# Boneh-Durfee
# LLL
# Factorization

# SageMath
sage crypto.sage

# CTF crypto tools
pip install gmpy2 sympy pycryptodome
```

## Checklist
```
[ ] Factor n if possible
[ ] Check for small e
[ ] Check for small d
[ ] Look for weak keys
[ ] Analyze padding
[ ] Check for oracle
[ ] Use appropriate attack
```
