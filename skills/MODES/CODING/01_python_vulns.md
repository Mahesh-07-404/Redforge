# CODING Skill: Vulnerable Python Patterns

## Purpose
Understand common vulnerable Python patterns for security testing.

## SQL Injection

### Vulnerable
```python
# String concatenation
query = "SELECT * FROM users WHERE name='" + name + "'"
cursor.execute(query)

# .format() injection
query = "SELECT * FROM users WHERE id={}".format(user_id)
cursor.execute(query)

# % formatting
query = "SELECT * FROM users WHERE name='%s'" % name
cursor.execute(query)
```

### Secure
```python
# Parameterized
query = "SELECT * FROM users WHERE name = ?"
cursor.execute(query, (name,))

# Named parameters
query = "SELECT * FROM users WHERE name = :name"
cursor.execute(query, {"name": name})
```

## Command Injection

### Vulnerable
```python
import os

# os.system
os.system("ls " + user_input)

# subprocess with shell=True
subprocess.run("ls " + user_input, shell=True)

# eval
result = eval(user_input)

# exec
exec(user_input)
```

### Secure
```python
import subprocess

# Without shell
subprocess.run(["ls", user_input])

# For complex commands, use lists
subprocess.run(["ls", "-la", "/tmp"])
```

## Path Traversal

### Vulnerable
```python
# Direct file access
filepath = "/var/www/" + user_filename
with open(filepath) as f:
    content = f.read()

# os.path.join bypass
# User sends "../../../etc/passwd"
```

### Secure
```python
from pathlib import Path
import os

base = Path("/var/www/uploads").resolve()
filepath = (base / user_filename).resolve()

# Verify it's within base
if not str(filepath).startswith(str(base)):
    raise ValueError("Invalid path")

with open(filepath) as f:
    content = f.read()
```

## Code Injection

### Vulnerable
```python
# Pickle from untrusted source
import pickle
data = pickle.loads(untrusted_data)

# YAML load
import yaml
data = yaml.load(user_yaml)

# marshal
import marshal
code = marshal.loads(user_data)
```

### Secure
```python
import pickle
# Use a custom unpickler that restricts classes
class SafeUnpickler(pickle.Unpickler):
    ALLOWED_CLASSES = {'MyClass'}
    def find_class(self, name):
        if name not in self.ALLOWED_CLASSES:
            raise pickle.UnpicklingError("Disallowed class")
        return super().find_class(name)

# For YAML, use safe_load
import yaml
data = yaml.safe_load(user_yaml)
```

## XXE (XML External Entity)

### Vulnerable
```python
from xml.etree import ElementTree as ET

# Default parser is vulnerable
tree = ET.parse(user_xml)
```

### Secure
```python
from xml.etree import ElementTree as ET

# Disable entity expansion
parser = ET.XMLParser()
parser.feed('<root></root>')
tree = ET.parse(user_xml, parser)
```

## SSRF

### Vulnerable
```python
import requests

# User controls URL
response = requests.get(user_url)
```

### Secure
```python
import requests
from urllib.parse import urlparse

ALLOWED_HOSTS = ['api.trusted.com', 'cdn.example.com']

def is_safe_url(url):
    parsed = urlparse(url)
    return parsed.hostname in ALLOWED_HOSTS

if is_safe_url(user_url):
    response = requests.get(user_url)
```

## Insecure Deserialization

### Vulnerable
```python
import pickle, json

# Pickle
obj = pickle.loads(user_data)

# JSON with eval
obj = eval(user_json)
```

### Secure
```python
import json
import dataclasses

# Use json for data
obj = json.loads(user_json)

# For objects, use typed validation
@dataclass
class User:
    name: str
    age: int
    def __post_init__(self):
        if not isinstance(self.name, str):
            raise ValueError("name must be string")
```

## Hardcoded Secrets

### Bad
```python
API_KEY = "sk_live_1234567890"
DB_PASSWORD = "secret123"
JWT_SECRET = "hardcoded-secret"
```

### Good
```python
import os

API_KEY = os.environ.get('API_KEY')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

# Or use a secrets manager
from keyring import get_password
password = get_password('service', 'username')
```

## Weak Crypto

### Bad
```python
import hashlib

# MD5 for passwords
password_hash = hashlib.md5(password).hexdigest()

# No salt
```

### Good
```python
import bcrypt
import hashlib

# bcrypt for passwords
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# SHA256 with salt for non-password
salt = os.urandom(32)
password_hash = hashlib.sha256(salt + password.encode()).hexdigest()
```

## Input Validation

### Bad
```python
age = int(user_input)  # Can crash
files = os.listdir(user_path)  # Can Traverse
```

### Good
```python
# Validate type and range
try:
    age = int(user_input)
    if not 0 <= age <= 150:
        raise ValueError("Invalid age")
except ValueError:
    raise ValidationError("Age must be a number")

# Validate path
if not os.path.exists(safe_path):
    raise ValueError("Path does not exist")
```

## Race Conditions

### Vulnerable
```python
# TOCTOU (Time of Check to Time of Use)
if os.path.exists(filename):
    # Race window here
    open(filename)
```

### Secure
```python
import fcntl

# Use file locking
with open(filename, 'r') as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    # Safe access
    content = f.read()
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```
