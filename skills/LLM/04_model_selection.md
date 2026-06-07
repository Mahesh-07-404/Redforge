# LLM Skill: Model Selection

## Purpose
Choose the right LLM for each task.

## Model Categories

### Fast/ Cheap
```
- Gemini Flash
- GPT-3.5-Turbo
- Claude Haiku
- Llama 3.2 (small)
```

### Balanced
```
- GPT-4o-Mini
- Claude Sonnet
- Gemini Pro
- Llama 3.1 (medium)
```

### Capable
```
- GPT-4
- Claude Opus
- Gemini Ultra
- Llama 3.1 (large)
```

## Task Mapping

### Reconnaissance
```
Model: Fast
Examples:
- nmap result parsing
- Subdomain enumeration
- Technology detection

Recommended: Gemini Flash, GPT-3.5
```

### Vulnerability Analysis
```
Model: Balanced
Examples:
- Code review
- Vulnerability classification
- Impact assessment

Recommended: GPT-4o, Claude Sonnet
```

### Exploitation
```
Model: Capable
Examples:
- Writing exploits
- Complex payload generation
- Bypass techniques

Recommended: GPT-4, Claude Opus
```

### Report Writing
```
Model: Balanced
Examples:
- Finding documentation
- Executive summaries
- Remediation suggestions

Recommended: GPT-4o, Claude Sonnet
```

## RedForge Configuration

### config.yaml Examples
```yaml
llm:
  provider: ollama
  model: llama3.2
  
  # Or cloud
  provider: openai
  model: gpt-4o-mini

llm_tasks:
  recon:
    model: llama3.2  # Fast
  analysis:
    model: gpt-4o    # Balanced
  exploit:
    model: gpt-4     # Capable
  report:
    model: gpt-4o    # Balanced
```

## Local vs Cloud

### Local (Ollama)
```
Pros:
- Free
- Private
- No rate limits
- Offline capable

Cons:
- Slower
- Less capable
- Resource intensive

Use for:
- Development/testing
- Learning
- Simple tasks
```

### Cloud (OpenAI, etc.)
```
Pros:
- Fast
- Capable
- Reliable

Cons:
- Costs money
- Privacy concerns
- Rate limits

Use for:
- Production
- Complex tasks
- Time-sensitive
```

## Cost Optimization

### Minimize Token Usage
```python
# Use smaller models for simple tasks
if is_simple_task(query):
    model = "gpt-3.5-turbo"
else:
    model = "gpt-4"
```

### Batch Similar Tasks
```python
# Instead of many small calls
batch_prompt = "\n".join([f"{i}: {task}" for i, task in enumerate(tasks)])
response = llm.generate(batch_prompt)
results = parse_batch_response(response)
```

## Model Switching

### RedForge Commands
```bash
# Set model
redforge config set llm.model gpt-4o

# Task-specific
redforge analyze --model fast
redforge exploit --model powerful
```

## Context Window

### Size Considerations
```
4K tokens:  Simple tasks, short code
16K tokens: Standard analysis
32K tokens: Large codebases
128K+:     Full applications
```

### Optimize Context
```python
# Truncate old messages
if len(messages) > 10:
    messages = summarize_old_messages(messages[:5]) + messages[5:]

# Use retrieval for context
context = vector_db.similarity_search(query, top_k=5)
```

## Benchmarking

### Test Tasks
```python
tasks = [
    "Parse nmap output",
    "Find SQL injection",
    "Write XSS payload",
    "Generate report"
]

for task in tasks:
    for model in models:
        start = time.time()
        result = model.generate(task)
        duration = time.time() - start
        quality = evaluate(result)
        print(f"{model}: {duration:.2f}s, quality={quality}")
```

## Recommendations

### By Task Type
```
Simple/Low Risk:  Use fast/cheap models
Standard Tasks:   Use balanced models
Complex/Critical: Use capable models
```

### By Budget
```
Free only:        Ollama + Llama
Low budget:       Mix of local + GPT-3.5
Medium budget:    GPT-4o-mini
No budget limit:  Claude Opus / GPT-4
```

## Checklist
```
[ ] Identify task complexity
[ ] Assess required capabilities
[ ] Consider privacy needs
[ ] Check budget constraints
[ ] Test with sample task
[ ] Monitor costs/quality
```
