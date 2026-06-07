# CODING Skill: Vulnerable Rust Patterns

## Purpose
Understand common vulnerable Rust patterns.

## SQL Injection

### Vulnerable
```rust
// String concatenation
let query = format!("SELECT * FROM users WHERE name='{}'", name);
conn.query(&query, &[])?;
```

### Secure
```rust
// Parameterized query
let query = "SELECT * FROM users WHERE name = $1";
conn.query(query, &[&name])?;
```

## Command Injection

### Vulnerable
```rust
use std::process::Command;

// User input in command
let output = Command::new("ls")
    .arg(&user_input)  // Might be safe
    .output()?;

// Shell true - DANGEROUS
let output = Command::new("bash")
    .arg("-c")
    .arg(&format!("ls {}", user_input))  // Vulnerable!
    .output()?;
```

### Secure
```rust
use std::process::Command;

// Explicit arguments only
let output = Command::new("ls")
    .arg("-la")
    .arg("/safe/path")
    .output()?;

// Validation
fn is_safe_path(path: &str) -> bool {
    !path.contains(|c| c == ';' || c == '|' || c == '&')
}
```

## Buffer Overflow

### Vulnerable
```rust
// Unsafe code without bounds checking
unsafe {
    let mut buffer = [0u8; 64];
    std::ptr::copy_nonoverlapping(user_data.as_ptr(), buffer.as_mut_ptr(), 128); // Overflow!
}
```

### Secure
```rust
use std::io::Read;

// Safe file reading
let mut file = std::fs::File::open(path)?;
let mut buffer = Vec::new();
file.read_to_end(&mut buffer)?;

// Or with explicit size
if user_data.len() <= 64 {
    let mut buffer = [0u8; 64];
    buffer[..user_data.len()].copy_from_slice(&user_data);
}
```

## Memory Safety

### Vulnerable
```rust
use std::ptr;

// Use after free
let boxed = Box::new(42);
let raw = Box::into_raw(boxed);
drop(Box::from_raw(raw));
unsafe { println!("{}", *raw); }  // Use after free!
```

### Secure
```rust
// Always validate pointers
let boxed = Box::new(42);
let raw = Box::into_raw(boxed);
// Keep one reference alive
let _ref = unsafe { Box::from_raw(raw) };
// Safe to use
println!("{}", boxed);
```

## Hardcoded Secrets

### Bad
```rust
const API_KEY: &str = "sk_live_1234567890";
let password = "secret123";
```

### Good
```rust
use std::env;

// Environment variable
let api_key = env::var("API_KEY")
    .expect("API_KEY must be set");

// Or from config file
#[derive(serde::Deserialize)]
struct Config {
    api_key: String,
}
```

## Weak Crypto

### Bad
```rust
use md5::{Md5, Digest};

let mut hasher = Md5::new();
hasher.update(&password);
let result = hasher.finalize();
// MD5 is broken for security purposes
```

### Good
```rust
use argon2::{Argon2, PasswordHasher};
use argon2::password_hash::rand_core::OsRng;

// For passwords
let hash = Argon2::default()
    .hash_password(password.as_bytes(), &mut OsRng)?;

if hash.verify_password(password.as_bytes(), &hash).is_ok() {
    // Valid password
}

// For hashing (non-password)
use sha2::{Sha256, Digest};
let mut hasher = Sha256::new();
hasher.update(&data);
let result = hasher.finalize();
```

## Panics

### Vulnerable
```rust
fn get_user(id: u32) -> User {
    let users = get_all_users();
    users[id as usize]  // Panic if id out of bounds!
}
```

### Secure
```rust
fn get_user(id: u32) -> Option<User> {
    let users = get_all_users();
    users.get(id as usize).cloned()
}

// Or with proper error handling
fn get_user(id: u32) -> Result<User, Error> {
    let users = get_all_users();
    users.get(id as usize)
        .cloned()
        .ok_or_else(|| Error::UserNotFound(id))
}
```

## Integer Overflow

### Vulnerable
```rust
let a: u32 = 4294967295;
let b: u32 = 1;
let sum = a.wrapping_add(b);  // Wraps silently, or panics in debug

// In loops
for i in 0.. {
    // Might overflow if running too long
    let size = i * 1000;  // Integer overflow!
}
```

### Secure
```rust
// Explicit overflow checking
let a: u32 = 4294967295;
let b: u32 = 1;

// Check before operation
let sum = a.checked_add(b)
    .ok_or_else(|| Error::IntegerOverflow)?;

// Or saturating arithmetic
let sum = a.saturating_add(b);

// Use checked operations
for i in 0.. {
    let size = i.checked_mul(1000)
        .ok_or_else(|| Error::SizeOverflow)?;
}
```

## Race Conditions

### Vulnerable
```rust
use std::sync::Mutex;

static COUNTER: Mutex<i32> = Mutex::new(0);

fn increment() {
    let mut counter = COUNTER.lock().unwrap();
    *counter += 1;  // Race if called concurrently
}
```

### Secure
```rust
use std::sync::{Mutex, Arc};
use std::sync::atomic::{AtomicU32, Ordering};

// Atomic for simple counters
static COUNTER: AtomicU32 = AtomicU32::new(0);

fn increment() {
    COUNTER.fetch_add(1, Ordering::SeqCst);
}

// Or Mutex for complex operations
static COUNTER: Mutex<Counter> = Mutex::new(Counter::new());

fn increment() -> Result<(), PoisonError<MutexGuard<Counter>>> {
    let mut counter = COUNTER.lock()?;
    counter.value += 1;
    Ok(())
}
```

## Input Validation

### Bad
```rust
fn handler(port: String) {
    let _ = port.parse::<u16>();  // No validation
}
```

### Good
```rust
use std::net::SocketAddr;

fn parse_address(input: &str) -> Result<SocketAddr, ParseError> {
    input.parse::<SocketAddr>()
}

fn validate_port(port: u16) -> Result<(), Error> {
    if port < 1024 {
        return Err(Error::PrivilegedPort);
    }
    if port > 65535 {
        return Err(Error::InvalidPort);
    }
    Ok(())
}
```

## Error Handling

### Bad
```rust
fn read_file(path: &str) -> String {
    std::fs::read_to_string(path).unwrap()  // Panics on error!
}

fn process() {
    let data = read_file("config.txt");
    // ...
}
```

### Secure
```rust
use std::io;

fn read_file(path: &str) -> Result<String, io::Error> {
    std::fs::read_to_string(path)
}

fn process() -> Result<(), Box<dyn std::error::Error>> {
    let data = read_file("config.txt")?;
    // ...
    Ok(())
}
```

## Async Race Conditions

### Vulnerable
```rust
use std::sync::Mutex;

static DATA: Mutex<Option<String>> = Mutex::new(None);

async fn update(data: String) {
    let mut guard = DATA.lock().unwrap();
    *guard = Some(data);  // Lock held across await!
    some_async_operation().await;
    guard.drop();  // Released too late!
}
```

### Secure
```rust
use tokio::sync::Mutex;

static DATA: tokio::sync::Mutex<Option<String>> = tokio::sync::Mutex::new(None);

async fn update(data: String) {
    // Lock only during critical section
    {
        let mut guard = DATA.lock().await;
        *guard = Some(data);
    }
    // Safe to await here
    some_async_operation().await;
}
```
