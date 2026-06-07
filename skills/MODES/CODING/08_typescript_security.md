# CODING Skill: TypeScript Security

## Purpose
Secure TypeScript coding practices.

## Input Validation

### Zod Validation
```typescript
import { z } from 'zod';

const UserSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).regex(/[A-Z]/),
  age: z.number().min(18).max(120)
});

type User = z.infer<typeof UserSchema>;

function createUser(data: unknown): User {
  return UserSchema.parse(data);  // Throws if invalid
}
```

### Type Guards
```typescript
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function sanitizeInput(input: unknown): string {
  if (!isString(input)) {
    throw new Error('Invalid input type');
  }
  return input.trim();
}
```

## SQL Injection Prevention

### Prisma
```typescript
// Safe - parameterized
const user = await prisma.user.findFirst({
  where: {
    email: userInput  // Automatically parameterized
  }
});

// Unsafe - raw interpolation
const users = await prisma.$queryRaw`SELECT * FROM users WHERE email = ${userInput}`;
```

### Knex
```typescript
// Safe
const users = await knex('users')
  .where('email', userInput);  // Parameterized

// Unsafe
const users = await knex.raw(
  `SELECT * FROM users WHERE email = '${userInput}'`
);
```

## XSS Prevention

### React
```typescript
// Safe - auto-escaped by default
function SafeComponent({ userInput }: { userInput: string }) {
  return <div>{userInput}</div>;  // Escaped
}

// Dangerous - dangerouslySetInnerHTML
function DangerousComponent({ html }: { html: string }) {
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}
```

### DOM Manipulation
```typescript
// Safe
element.textContent = userInput;

// Dangerous
element.innerHTML = userInput;  // XSS!
```

## Authentication

### JWT Verification
```typescript
import jwt from 'jsonwebtoken';

interface TokenPayload {
  userId: string;
  role: string;
}

function verifyToken(token: string): TokenPayload {
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET!) as TokenPayload;
    return decoded;
  } catch {
    throw new Error('Invalid token');
  }
}

// Strict typing
const payload = verifyToken(req.headers.authorization);
if (payload.role !== 'admin') {
  throw new Error('Unauthorized');
}
```

## Authorization

### RBAC Middleware
```typescript
type Permission = 'read' | 'write' | 'delete';

const permissions: Record<string, Permission[]> = {
  admin: ['read', 'write', 'delete'],
  editor: ['read', 'write'],
  viewer: ['read']
};

function requirePermission(permission: Permission) {
  return (req: Request, res: Response, next: NextFunction) => {
    const userRole = req.user?.role;
    if (!userRole || !permissions[userRole]?.includes(permission)) {
      return res.status(403).json({ error: 'Forbidden' });
    }
    next();
  };
}

// Usage
router.delete('/posts/:id', 
  authenticate, 
  requirePermission('delete'), 
  deletePost
);
```

## Command Injection Prevention

### Node.js
```typescript
import { execFile } from 'child_process';

// Safe - explicit arguments
execFile('ls', ['-la', safePath], (error, stdout) => {
  // safePath is treated as single argument
});

// Unsafe - shell interpolation
exec(`ls -la ${userInput}`);  // Command injection!
```

## SSRF Prevention

```typescript
import { URL } from 'url';

function isAllowedUrl(inputUrl: string): boolean {
  try {
    const url = new URL(inputUrl);
    
    // Block private IPs
    if (url.hostname === 'localhost' || 
        url.hostname.startsWith('192.168.') ||
        url.hostname.startsWith('10.') ||
        url.hostname.startsWith('172.16.')) {
      return false;
    }
    
    return url.protocol === 'https:';
  } catch {
    return false;
  }
}

async function fetchUrl(inputUrl: string): Promise<string> {
  if (!isAllowedUrl(inputUrl)) {
    throw new Error('URL not allowed');
  }
  return fetch(inputUrl).then(r => r.text());
}
```

## Type-Safe Crypto

```typescript
import { createHash, randomBytes, createCipheriv, createDecipheriv } from 'crypto';

function hashPassword(password: string, salt: string): string {
  return createHash('sha256')
    .update(password + salt)
    .digest('hex');
}

function encrypt(data: string, key: Buffer): { iv: string; encrypted: string } {
  const iv = randomBytes(16);
  const cipher = createCipheriv('aes-256-gcm', key, iv);
  
  let encrypted = cipher.update(data, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  
  const authTag = cipher.getAuthTag();
  
  return {
    iv: iv.toString('hex'),
    encrypted,
    authTag: authTag.toString('hex')
  };
}
```

## Rate Limiting

```typescript
import rateLimit from 'express-rate-limit';

const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per window
  message: 'Too many requests',
  standardHeaders: true,
  legacyHeaders: false,
});

// Apply to routes
app.use('/api/', apiLimiter);

// Strict limiter for auth
const authLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 5,
  skipSuccessfulRequests: true
});

app.post('/login', authLimiter, loginHandler);
```

## Secure Headers

```typescript
import helmet from 'helmet';

// Apply security headers
app.use(helmet());

// Strict CSP
app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'"],
    styleSrc: ["'self'"],
    imgSrc: ["'self'", 'https:'],
    connectSrc: ["'self'"],
    fontSrc: ["'self'"],
    objectSrc: ["'none'"],
    mediaSrc: ["'self'"],
    frameSrc: ["'none'"]
  }
}));
```

## Error Handling

```typescript
// Safe error handling - don't leak info
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error({
    message: err.message,
    stack: err.stack,
    path: req.path,
    timestamp: new Date().toISOString()
  });
  
  // Generic message to client
  res.status(500).json({ 
    error: 'Internal server error',
    requestId: req.headers['x-request-id']
  });
});
```

## Environment Variables

```typescript
import { z } from 'zod';

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
  PORT: z.string().transform(Number).pipe(z.number().min(1)),
  NODE_ENV: z.enum(['development', 'production'])
});

const env = envSchema.parse(process.env);

export const config = {
  database: {
    url: env.DATABASE_URL
  },
  jwt: {
    secret: env.JWT_SECRET
  },
  port: env.PORT,
  isProduction: env.NODE_ENV === 'production'
};
```
