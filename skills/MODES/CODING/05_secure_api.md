# CODING Skill: Secure API Design

## Purpose
Design secure APIs.

## Authentication

### Token-Based
```python
# JWT tokens
import jwt
from datetime import datetime, timedelta

def create_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
```

### OAuth 2.0
```python
# Authorization code flow
# 1. Redirect to /oauth/authorize
# 2. User grants permission
# 3. Receive authorization code
# 4. Exchange for access token
# 5. Use access token
```

## Authorization

### RBAC (Role-Based)
```python
# Decorator approach
def require_role(role):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.role != role:
                abort(403)
            return func(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/admin')
@require_role('admin')
def admin_panel():
    return "Admin area"
```

### Permission Checks
```python
def check_permission(user, resource, action):
    # Check specific permissions
    return user.has_permission(resource, action)
```

## Input Validation

### Schema Validation
```python
from pydantic import BaseModel, validator

class UserCreate(BaseModel):
    email: str
    password: str
    age: int
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password too short')
        return v
```

## Rate Limiting

### Implementation
```python
from functools import wraps
from redis import Redis

redis = Redis()

def rate_limit(max_requests, window):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"rate:{func.__name__}:{request.ip}"
            current = redis.get(key)
            
            if current and int(current) >= max_requests:
                abort(429)
            
            pipe = redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            pipe.execute()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

## Security Headers

### Flask
```python
from flask import Flask
from flask_talisman import Talisman

app = Flask(__name__)
Talisman(app, content_security_policy={
    'default-src': "'self'",
    'script-src': "'self'",
})
```

### FastAPI
```python
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com"]
)
```

## Error Handling

### Don't Leak Information
```python
# Bad - Information leakage
@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({
        'error': str(e),
        'stack': traceback.format_exc()  # LEAK!
    })

# Good - Generic error
@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({
        'error': 'An error occurred',
        'request_id': request.id
    })
```

## SQL Injection Prevention

### ORM Usage
```python
# SQLAlchemy
user = db.query(User).filter(User.id == user_id).first()

# Parameterized queries
db.execute(
    "SELECT * FROM users WHERE id = ?",
    (user_id,)
)
```

## XSS Prevention

### Output Encoding
```python
from markupsafe import escape

# HTML template
template = "<p>Hello {{ name }}</p>"
# Safe: markupsafe auto-escapes

# API response
return jsonify({
    'message': escape(user_input)
})
```

## CSRF Prevention

### Flask-WTF
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# Forms auto-include CSRF tokens
# AJAX needs header
headers = {'X-CSRFToken': get_csrf_token()}
```

## File Upload Security

### Validation
```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'gif'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def secure_filename(filename):
    # Remove path components
    name = os.path.basename(filename)
    # Remove special characters
    return re.sub(r'[^\w.]', '', name)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        abort(400)
    
    file = request.files['file']
    if file.filename == '':
        abort(400)
    
    if not allowed_file(file.filename):
        abort(400)
    
    if file.content_length > MAX_FILE_SIZE:
        abort(400)
    
    # Verify magic bytes
    magic = file.read(1024)
    if not is_safe_magic(magic):
        abort(400)
    
    # Save securely
    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_DIR, filename))
```

## API Documentation

### OpenAPI/Swagger
```yaml
openapi: 3.0.0
info:
  title: Secure API
  version: 1.0.0
paths:
  /users:
    post:
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/User'
```
