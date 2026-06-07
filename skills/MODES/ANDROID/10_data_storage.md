# ANDROID Skill: Data Storage Analysis

## Purpose
Analyze data storage mechanisms in Android apps.

## Storage Types

### Internal Storage
```java
// app-private directory
getFilesDir();        // /data/data/com.example/files/
getCacheDir();        // /data/data/com.example/cache/
getDir("name", MODE_PRIVATE);  // /data/data/com.example/files/name/
```

### External Storage
```java
// Shared storage
Environment.getExternalStorageDirectory();  // /sdcard/
getExternalFilesDir(null);  // /storage/emulated/0/Android/data/com.example/files/
```

### SharedPreferences
```java
// XML-based key-value storage
SharedPreferences prefs = getSharedPreferences("data", Context.MODE_PRIVATE);

// Read
String token = prefs.getString("auth_token", "");

// Write
prefs.edit().putString("auth_token", token).apply();
```

### SQLite Database
```java
// /data/data/com.example/databases/
SQLiteDatabase db = openOrCreateDatabase("app.db", MODE_PRIVATE, null);

// Create table
db.execSQL("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)");
```

## Extracting Data

### From Emulator/Device
```bash
# List databases
adb shell "run-as com.example ls databases/"

# Copy database
adb shell "run-as com.example cat databases/app.db" > app.db

# SharedPreferences
adb shell "run-as com.example cat shared_prefs/prefs.xml"
```

### Using Objection
```bash
objection -g com.example.app explore

# List storage
android storage list

# Dump files
file dump /data/data/com.example/shared_prefs/prefs.xml
```

## Frida Extraction

### Dump SharedPreferences
```javascript
Java.perform(function() {
    var SharedPreferencesImpl = Java.use('android.app.SharedPreferencesImpl');
    var File = Java.use('java.io.File');
    
    // Hook SharedPreferences
    SharedPreferencesImpl.getString.overload('java.lang.String', 'java.lang.String').implementation = function(key, defValue) {
        var result = this.getString(key, defValue);
        console.log('[*] SharedPref[' + key + '] = ' + result);
        return result;
    };
});
```

### Dump SQLite
```javascript
Java.perform(function() {
    var SQLiteDatabase = Java.use('android.database.sqlite.SQLiteDatabase');
    
    SQLiteDatabase.execSQL.overload('java.lang.String').implementation = function(sql) {
        console.log('[*] SQL: ' + sql);
        return this.execSQL(sql);
    };
    
    SQLiteDatabase.rawQuery.overload('java.lang.String', '[Ljava.lang.String;').implementation = function(sql, args) {
        console.log('[*] Query: ' + sql);
        console.log('[*] Args: ' + args);
        return this.rawQuery(sql, args);
    };
});
```

## Common Vulnerabilities

### 1. Hardcoded Credentials
```java
// Bad
SharedPreferences prefs = getSharedPreferences("data", MODE_PRIVATE);
prefs.edit().putString("api_key", "sk_live_12345").apply();
```

### 2. Insecure Storage
```java
// Storing sensitive data without encryption
prefs.edit().putString("password", password).apply();

// Should use EncryptedSharedPreferences
```

### 3. World-Readable Files
```java
// Bad - MODE_WORLD_READABLE
openFileOutput("data.txt", Context.MODE_WORLD_READABLE);
```

## Secure Storage

### EncryptedSharedPreferences
```java
import androidx.security.crypto.EncryptedSharedPreferences;
import androidx.security.crypto.MasterKey;

MasterKey masterKey = new MasterKey.Builder(context)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
    .build();

EncryptedSharedPreferences sharedPreferences = 
    EncryptedSharedPreferences.create(
        context,
        "secure_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    );

// Now safe to store sensitive data
sharedPreferences.edit().putString("token", authToken).apply();
```

### Android Keystore
```java
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;

// Generate key in hardware-backed keystore
KeyGenParameterSpec spec = new KeyGenParameterSpec.Builder(
    "my_key_alias",
    KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
    .setKeySize(256)
    .build();
```

## Database Analysis

### SQLite Viewer
```bash
# Copy database
adb pull /data/data/com.example/databases/app.db

# View with sqlite3
sqlite3 app.db
sqlite> .tables
sqlite> .schema users
sqlite> SELECT * FROM users;
```

### SQLCipher (Encrypted DB)
```java
// If app uses SQLCipher
// May need key extraction via Frida

Java.perform(function() {
    var SQLCipher = Java.use('net.sqlcipher.database.SQLiteDatabase');
    // Hook database operations
});
```

## File System Analysis

### Common Locations
```
/data/data/com.example/files/       # Internal files
/data/data/com.example/databases/  # SQLite databases
/data/data/com.example/shared_prefs/  # SharedPreferences
/data/data/com.example/cache/      # Cache files
/data/data/com.example/no_backup/  # not backed up files
```

### Backup Analysis
```xml
<!-- AndroidManifest.xml -->
<application android:allowBackup="true">
```

```bash
# Backup app data (requires root or special APK)
abd backup -apk com.example.app -f backup.ab

# Extract backup
java -jar abe.jar unpack backup.ab backup.tar
```

## Frida File Hooks

### Monitor File Operations
```javascript
Java.perform(function() {
    var FileInputStream = Java.use('java.io.FileInputStream');
    var FileOutputStream = Java.use('java.io.FileOutputStream');
    
    FileInputStream.read.overload().implementation = function() {
        var data = this.read();
        console.log('[*] File read: ' + bytesToString(data));
        return data;
    };
});
```

### Dump File Content
```javascript
Java.perform(function() {
    var File = Java.use('java.io.File');
    
    File.$init.overload('java.lang.String').implementation = function(path) {
        console.log('[*] File opened: ' + path);
        return this.$init(path);
    };
});
```

## Checklist
```
[ ] List all storage locations
[ ] Check SharedPreferences for secrets
[ ] Analyze SQLite databases
[ ] Look for encryption
[ ] Test backup feature
[ ] Check file permissions
```

## Secure Storage Best Practices
```
1. Use EncryptedSharedPreferences
2. Use Android Keystore
3. Never store passwords in plaintext
4. Disable allowBackup if sensitive
5. Clear cache on logout
```
