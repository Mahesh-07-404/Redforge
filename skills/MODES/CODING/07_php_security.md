# CODING Skill: PHP Security

## Purpose
Secure PHP coding practices.

## SQL Injection

### Vulnerable
```php
// String concatenation
$query = "SELECT * FROM users WHERE name='" . $_GET['name'] . "'";
$result = mysqli_query($conn, $query);

// Prepared statement without params
$stmt = $pdo->prepare($query);
$stmt->execute();
```

### Secure
```php
// Prepared statements
$stmt = $pdo->prepare("SELECT * FROM users WHERE name = ?");
$stmt->execute([$name]);

// Named parameters
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = :id");
$stmt->execute(['id' => $id]);
```

## XSS

### Vulnerable
```php
// Direct output
echo $_GET['name'];

// innerHTML
echo "<div>" . $_POST['comment'] . "</div>";
```

### Secure
```php
// HTML entities
echo htmlspecialchars($_GET['name'], ENT_QUOTES, 'UTF-8');

// Content Security Policy
header("Content-Security-Policy: default-src 'self'");

// Purifier for rich content
require_once 'HTMLPurifier.auto.php';
$config = HTMLPurifier_Config::createDefault();
$purifier = new HTMLPurifier($config);
$clean_html = $purifier->purify($_POST['comment']);
```

## CSRF

### Vulnerable
```php
// No CSRF protection
if (isset($_POST['delete'])) {
    deleteAccount($_POST['id']);
}
```

### Secure
```php
// Generate token
session_start();
if (empty($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}

// Verify token
if (!hash_equals($_SESSION['csrf_token'], $_POST['csrf_token'])) {
    die('CSRF validation failed');
}

// Form
echo '<input type="hidden" name="csrf_token" value="' . $_SESSION['csrf_token'] . '">';
```

## Password Hashing

### Vulnerable
```php
// MD5/SHA1
$hash = md5($password);
$hash = sha1($password);
```

### Secure
```php
// Password hashing
$hash = password_hash($password, PASSWORD_DEFAULT);

// Verify
if (password_verify($password, $stored_hash)) {
    // Login successful
}

// Argon2 (PHP 7.2+)
$hash = password_hash($password, PASSWORD_ARGON2ID);
```

## File Upload

### Vulnerable
```php
// No validation
move_uploaded_file($_FILES['file']['tmp_name'], 
                  '/uploads/' . $_FILES['file']['name']);
```

### Secure
```php
// Validate upload
$allowed_types = ['image/jpeg', 'image/png', 'image/gif'];
$max_size = 5 * 1024 * 1024; // 5MB

if (!in_array($_FILES['file']['type'], $allowed_types)) {
    die('Invalid file type');
}

if ($_FILES['file']['size'] > $max_size) {
    die('File too large');
}

// Verify magic bytes
$finfo = finfo_open(FILEINFO_MIME_TYPE);
$mime = finfo_file($finfo, $_FILES['file']['tmp_name']);
finfo_close($finfo);

if (!in_array($mime, $allowed_types)) {
    die('Invalid file content');
}

// Generate safe filename
$ext = pathinfo($_FILES['file']['name'], PATHINFO_EXTENSION);
$filename = bin2hex(random_bytes(16)) . '.' . $ext;

// Store outside webroot
$upload_dir = '/var/www/uploads/';
move_uploaded_file($_FILES['file']['tmp_name'], 
                  $upload_dir . $filename);
```

## Session Security

### Vulnerable
```php
// No session hardening
session_start();
```

### Secure
```php
// Secure session
session_start([
    'cookie_httponly' => true,
    'cookie_secure' => true,  // HTTPS only
    'cookie_samesite' => 'Strict',
    'use_strict_mode' => true,
]);

// Regenerate after login
session_regenerate_id(true);

// Set timeout
if (isset($_SESSION['last_activity']) && 
    (time() - $_SESSION['last_activity'] > 1800)) {
    session_destroy();
    session_start();
}
$_SESSION['last_activity'] = time();
```

## Headers

### Security Headers
```php
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('X-XSS-Protection: 1; mode=block');
header('Referrer-Policy: strict-origin-when-cross-origin');
header("Content-Security-Policy: default-src 'self'");

// HSTS
header('Strict-Transport-Security: max-age=31536000; includeSubDomains');
```

## Input Validation

### Validation Functions
```php
// Sanitize input
function sanitize_input($data) {
    $data = trim($data);
    $data = stripslashes($data);
    $data = htmlspecialchars($data, ENT_QUOTES, 'UTF-8');
    return $data;
}

// Validate email
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    die('Invalid email');
}

// Validate URL
if (!filter_var($url, FILTER_VALIDATE_URL)) {
    die('Invalid URL');
}

// Whitelist validation
$allowed = ['red', 'green', 'blue'];
if (!in_array($color, $allowed)) {
    die('Invalid color');
}
```

## Command Injection

### Vulnerable
```php
// User input in shell
system("ls " . $_GET['dir']);
shell_exec("grep " . $_GET['pattern'] . " file.txt");
```

### Secure
```php
// Escape shell arguments
$dir = escapeshellarg($_GET['dir']);
system("ls " . $dir);

// Or avoid shell entirely
$safe_dir = basename($_GET['dir']);
if (strpos($safe_dir, '..') !== false) {
    die('Directory traversal detected');
}
```

## Deserialization

### Vulnerable
```php
// Unserialize user input
$object = unserialize($_COOKIE['data']);
```

### Secure
```php
// JSON instead of serialize
$data = json_decode($_COOKIE['data'], true);
if (json_last_error() !== JSON_ERROR_NONE) {
    die('Invalid JSON');
}

// If you must use unserialize
if (class_exists('MyClass')) {
    $object = unserialize($data, ['allowed_classes' => ['MyClass']]);
}
```

## Error Handling

### Vulnerable
```php
// Show all errors
ini_set('display_errors', 1);
error_reporting(E_ALL);
```

### Secure
```php
// Production settings
ini_set('display_errors', 0);
error_reporting(E_ALL);
ini_set('log_errors', 1);
ini_set('error_log', '/var/log/php_errors.log');

// Custom error handler
set_error_handler(function($level, $message, $file, $line) {
    if (error_reporting() & $level) {
        error_log("[$level] $message in $file:$line");
    }
    return false;
});
```
