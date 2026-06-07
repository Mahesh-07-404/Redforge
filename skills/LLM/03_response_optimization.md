# LLM Skill: Response Optimization

## Purpose
Optimize LLM responses for RedForge tasks.

## Prompt Optimization

### Be Specific
```markdown
# Bad
"Find vulnerabilities"

# Good
"Find SQL injection vulnerabilities in the /api/users endpoint.
Check for: UNION-based, Boolean-based, Time-based blind SQLi.
Report severity (CVSS) and simple PoC."
```

### Include Context
```markdown
# Bad
"What's this?"

# Good
"Given this Python code that handles user authentication:
[code]
Identify if it's vulnerable to SQL injection and suggest fixes."
```

### Define Output Format
```markdown
# Bad
"Tell me about XSS"

# Good
"Explain XSS as a structured response:
1. Definition (1 sentence)
2. Types: Reflected, Stored, DOM
3. Example payload
4. Prevention method"
```

## Response Parsing

### Structured Outputs
```python
import json

# Ask for JSON
prompt = """
Analyze this code for vulnerabilities.
Return JSON with:
{"vulnerabilities": [{"type": "", "severity": "", "line": 0}]}
"""

response = llm.generate(prompt)
data = json.loads(response)
```

### Regex Extraction
```python
import re

# Extract CVEs
response = llm.generate(prompt)
cves = re.findall(r'CVE-\d{4}-\d{4,}', response)
```

## Token Management

### Minimize Context
```python
# Only include relevant code
code_snippet = get_relevant_function(code, target_line)

prompt = f"""
Analyze this function for vulnerabilities:
```python
{code_snippet}
```
"""
```

### Summarize Old Context
```python
# Before adding to context
summary = llm.generate(f"Summarize: {old_context}")
context = summary + new_information
```

### Use Smaller Models
```python
# Use appropriate model
if task == "simple_classification":
    model = "gpt-3.5-turbo"  # Fast, cheap
elif task == "complex_analysis":
    model = "gpt-4"  # More capable
```

## Chain of Thought

### Enable Reasoning
```markdown
"Analyze this vulnerability step by step:
1. What type of vulnerability is this?
2. What are the attack vectors?
3. What is the potential impact?
4. How severe is it (1-10)?
5. Suggest remediation.

Then provide your final answer in this format:
Type: [answer]
Severity: [answer]
```

## Few-Shot Examples

### Improve Accuracy
```markdown
"""Analyze this code vulnerability.

Example 1:
Code: query = "SELECT * FROM users WHERE id=" + id
Analysis: SQL Injection in 'id' parameter
Severity: High

Example 2:
Code: os.system("ls " + user_input)
Analysis: Command Injection in 'user_input'
Severity: Critical

Now analyze:
Code: {user_code}
Analysis:"""
```

## Temperature/Temperature Settings

### Use Cases
```python
# Creative tasks (higher)
temperature = 0.8  # Story writing, brainstorming

# Factual tasks (lower)
temperature = 0.3  # Vulnerability analysis

# Code generation (low)
temperature = 0.2  # Deterministic, correct output

# Balanced
temperature = 0.5  # General use
```

## Caching

### Reduce Costs
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_analysis(prompt_hash):
    return llm.generate(prompt)
```

### Smart Caching
```python
# Cache skill content
skills_cache = {}

def get_skill(skill_name):
    if skill_name not in skills_cache:
        skills_cache[skill_name] = load_skill(skill_name)
    return skills_cache[skill_name]
```

## Error Handling

### Retry Logic
```python
def generate_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return llm.generate(prompt)
        except RateLimitError:
            wait = 2 ** attempt
            time.sleep(wait)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(1)
```

### Fallback
```python
def generate(prompt):
    try:
        return primary_llm.generate(prompt)
    except:
        return fallback_llm.generate(prompt)
```

## Parallel Processing

### Batch Tasks
```python
# Instead of sequential
for item in items:
    result = llm.analyze(item)

# Parallel
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(llm.analyze, items))
```

## Quality Checks

### Validate Output
```python
def validate_response(response):
    required_fields = ["severity", "type", "recommendation"]
    for field in required_fields:
        if field not in response.lower():
            return False, f"Missing: {field}"
    return True, "Valid"
```

### Self-Correction
```python
initial = llm.generate(prompt)

# Verify
is_valid, issues = validate_response(initial)

if not is_valid:
    fixed = llm.generate(f"""
        Previous response was incomplete.
        Missing: {issues}
        Please provide complete response.
    """)
```

## Best Practices
```
1. Be specific and concise
2. Include output format
3. Use examples
4. Enable reasoning for complex tasks
5. Adjust temperature for use case
6. Cache repeated content
7. Handle errors gracefully
8. Validate outputs
9. Use appropriate model size
10. Monitor token usage
```
