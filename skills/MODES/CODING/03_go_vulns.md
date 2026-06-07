# CODING Skill: Vulnerable Go Patterns

## Purpose
Understand common vulnerable Go patterns.

## SQL Injection

### Vulnerable
```go
// String concatenation
query := "SELECT * FROM users WHERE name='" + name + "'"
db.Query(query)

// Sprintf injection
query := fmt.Sprintf("SELECT * FROM users WHERE id=%s", id)
```

### Secure
```go
// Parameterized query
query := "SELECT * FROM users WHERE name = ?"
row := db.QueryRow(query, name)

// Multiple parameters
query := "SELECT * FROM users WHERE name = ? AND age > ?"
rows, err := db.Query(query, name, age)
```

## Command Injection

### Vulnerable
```go
import "os/exec"

// exec.Command with user input
cmd := exec.Command("ls", "-la", userInput)

// Shell true with user input
cmd := exec.Command("bash", "-c", "ls "+userInput)
```

### Secure
```go
// No shell, explicit arguments
cmd := exec.Command("ls", "-la", "/safe/path")

// Validation
if !isValidPath(userInput) {
    return errors.New("invalid path")
}
cmd := exec.Command("ls", userInput)
```

## Path Traversal

### Vulnerable
```go
// Direct file access
func handler(w http.ResponseWriter, r *http.Request) {
    file := r.URL.Query().Get("file")
    content, _ := os.ReadFile(file)
    w.Write(content)
}
```

### Secure
```go
import "path/filepath"

func secureHandler(w http.ResponseWriter, r *http.Request) {
    file := r.URL.Query().Get("file")
    
    // Resolve and validate
    resolved := filepath.Join("/safe/base", file)
    if !strings.HasPrefix(resolved, "/safe/base/") {
        http.Error(w, "Forbidden", 403)
        return
    }
    
    content, err := os.ReadFile(resolved)
    if err != nil {
        http.Error(w, "Not found", 404)
        return
    }
    w.Write(content)
}
```

## XSS

### Vulnerable
```go
// Direct HTML output
func handler(w http.ResponseWriter, r *http.Request) {
    name := r.URL.Query().Get("name")
    fmt.Fprintf(w, "Hello %s", name)
}
```

### Secure
```go
import "html/template"

func safeHandler(w http.ResponseWriter, r *http.Request) {
    name := r.URL.Query().Get("name")
    t := template.Must(template.ParseFiles("template.html"))
    t.Execute(w, map[string]string{"Name": name})
}

// template.html: {{.Name}} auto-escapes
```

## SSRF

### Vulnerable
```go
func handler(w http.ResponseWriter, r *http.Request) {
    url := r.URL.Query().Get("url")
    resp, _ := http.Get(url)
    defer resp.Body.Close()
    io.Copy(w, resp.Body)
}
```

### Secure
```go
import "net/url"

func safeHandler(w http.ResponseWriter, r *http.Request) {
    inputURL := r.URL.Query().Get("url")
    
    parsed, err := url.Parse(inputURL)
    if err != nil {
        http.Error(w, "Invalid URL", 400)
        return
    }
    
    // Whitelist allowed hosts
    allowed := map[string]bool{"api.example.com": true}
    if !allowed[parsed.Host] {
        http.Error(w, "Forbidden", 403)
        return
    }
    
    // Only allow HTTP(S)
    if parsed.Scheme != "http" && parsed.Scheme != "https" {
        http.Error(w, "Invalid scheme", 400)
        return
    }
    
    resp, err := http.Get(inputURL)
    // ...
}
```

## Hardcoded Secrets

### Bad
```go
const APIKey = "sk_live_1234567890"
var Password = "secret123"
```

### Good
```go
import "os"

// Environment variable
apiKey := os.Getenv("API_KEY")

// Validation
if apiKey == "" {
    log.Fatal("API_KEY not set")
}

// Or configuration
type Config struct {
    APIKey string
}
cfg := loadConfig() // Load from env/file
```

## Weak Crypto

### Bad
```go
import (
    "crypto/md5"
    "crypto/sha1"
)

// MD5 for passwords
hash := md5.Sum([]byte(password))

// Weak hashing
sha := sha1.Sum([]byte(data))
```

### Good
```go
import (
    "golang.org/x/crypto/bcrypt"
    "crypto/sha256"
)

// bcrypt for passwords
hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
err = bcrypt.CompareHashAndPassword(hash, []byte(password))

// SHA256 for checksums
hash := sha256.Sum256([]byte(data))
```

## JWT Vulnerabilities

### Vulnerable
```go
import "github.com/golang-jwt/jwt"

// None algorithm
token := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
    return nil, nil
})

// No verification
token := jwt.Parse(tokenString, func(token *jwt.Token) ([]byte, error) {
    return []byte("any-secret"), nil
})
```

### Secure
```go
import "github.com/golang-jwt/jwt"

// Always verify
token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
    if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
        return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
    }
    return []byte(os.Getenv("JWT_SECRET")), nil
})

if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
    // Use claims
}
```

## Integer Overflow

### Vulnerable
```go
func process(data []byte) {
    length := int(len(data))
    // Integer overflow check missing
    buffer := make([]byte, length+1)
}
```

### Secure
```go
func safeProcess(data []byte) error {
    length := len(data)
    if length > maxSize {
        return errors.New("data too large")
    }
    buffer := make([]byte, length+1)
    // Safe processing
    return nil
}
```

## Nil Pointer Dereference

### Vulnerable
```go
type Config struct {
    DB *sql.DB
}

func (c *Config) Query(sql string) {
    // No nil check
    rows, _ := c.DB.Query(sql)
    defer rows.Close()
}
```

### Secure
```go
func (c *Config) Query(sql string) error {
    if c.DB == nil {
        return errors.New("database not initialized")
    }
    rows, err := c.DB.Query(sql)
    if err != nil {
        return err
    }
    defer rows.Close()
    return nil
}
```

## Race Conditions

### Vulnerable
```go
var counter int

func increment() {
    counter++  // Race condition
}
```

### Secure
```go
import "sync"

var (
    counter int
    mu      sync.Mutex
)

func increment() {
    mu.Lock()
    defer mu.Unlock()
    counter++
}

// Or use atomic
import "sync/atomic"
var counter int64

func increment() {
    atomic.AddInt64(&counter, 1)
}
```

## Input Validation

### Bad
```go
func handler(w http.ResponseWriter, r *http.Request) {
    age := r.URL.Query().Get("age")
    // No validation
    fmt.Fprintf(w, "Age: %s", age)
}
```

### Good
```go
import "strconv"

func handler(w http.ResponseWriter, r *http.Request) {
    ageStr := r.URL.Query().Get("age")
    age, err := strconv.Atoi(ageStr)
    if err != nil || age < 0 || age > 150 {
        http.Error(w, "Invalid age", 400)
        return
    }
    fmt.Fprintf(w, "Age: %d", age)
}
```
