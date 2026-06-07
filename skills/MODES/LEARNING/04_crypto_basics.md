# LEARNING Skill: Cryptography Basics

## Purpose
Fundamental cryptographic concepts.

## Types of Encryption

### Symmetric
```
Same key for encrypt/decrypt
Examples: AES, DES, 3DES, ChaCha20

Pros: Fast, efficient
Cons: Key distribution problem
```

### Asymmetric
```
Public key for encrypt, private key for decrypt
Examples: RSA, ECC, Diffie-Hellman

Pros: Solves key distribution
Cons: Slow, computationally expensive
```

## Hash Functions

### Properties
```
One-way: Cannot reverse
Deterministic: Same input = Same output
Collision resistance: Hard to find same hash
Avalanche: Small change = Big hash difference
```

### Common Hashes
```
MD5     - 128-bit, broken
SHA-1   - 160-bit, deprecated
SHA-256 - 256-bit, widely used
SHA-512 - 512-bit, high security
BLAKE2  - Fast, secure
```

## Encoding vs Encryption
```
Encoding: Not security (Base64, Hex)
Encryption: Provides security (AES, RSA)
```

## AES

### Modes
```
ECB   - Electronic Codebook (weak)
CBC   - Cipher Block Chaining
CTR   - Counter mode
GCM   - Galois/Counter Mode (authenticated)
```

### Key Sizes
```
AES-128 - 128-bit key
AES-192 - 192-bit key
AES-256 - 256-bit key
```

## RSA

### Key Generation
```
1. Pick two primes p, q
2. n = p * q
3. phi(n) = (p-1)(q-1)
4. Pick e (usually 65537)
5. d = e^-1 mod phi(n)
```

### Security
```
Based on factoring large numbers
n should be 2048+ bits
e is usually small (65537)
d should be large
```

## Digital Signatures

### Process
```
1. Hash message
2. Encrypt hash with private key
3. Send message + signature
4. Decrypt signature with public key
5. Compare hash
```

## TLS/SSL

### Handshake (Simplified)
```
1. Client hello (supported ciphers)
2. Server hello (chosen cipher, cert)
3. Client verifies certificate
4. Key exchange (DH or RSA)
5. Encrypted communication
```

## Password Storage

### Best Practice
```python
# Never store plain text
# Use bcrypt, scrypt, or Argon2

import bcrypt
hashed = bcrypt.hashpw(password, bcrypt.gensalt())
bcrypt.checkpw(password, hashed)
```

## Common Mistakes
```
- MD5 for passwords
- ECB mode for multiple blocks
- Predictable IVs
- Hardcoded keys
- No HMAC for integrity
- Custom crypto
```
