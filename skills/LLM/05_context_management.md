# LLM Skill: Context Management

## Purpose
Manage LLM context effectively for RedForge.

## Context Window

### What It Is
```
Maximum tokens LLM can process
Includes: prompt + conversation + response
Typical: 4K - 128K tokens
```

### Token Counting
```python
# Rough estimate
def estimate_tokens(text):
    return len(text.split()) * 1.3  # Words to tokens

# Accurate counting
import tiktoken
encoder = tiktoken.get_encoding("cl100k_base")
tokens = len(encoder.encode(text))
```

## Context Optimization

### Prune Old Messages
```python
MAX_MESSAGES = 20

def manage_context(messages):
    if len(messages) > MAX_MESSAGES:
        # Keep recent, summarize old
        old = summarize_messages(messages[:-10])
        return old + messages[-10:]
    return messages
```

### Summarize Strategy
```python
def summarize_messages(messages):
    summary = llm.generate("""
        Summarize this conversation concisely:
        Include: main topics, key findings, pending tasks.
        Format as structured text.
    """)
    return [{"role": "system", "content": f"Summary: {summary}"}]
```

## Retrieval Augmented Generation

### RAG Pipeline
```python
# 1. Index documents
for doc in documents:
    chunks = split_into_chunks(doc)
    for chunk in chunks:
        vector = embed(chunk)
        vector_db.insert(vector, chunk)

# 2. Retrieve relevant
query = "SQL injection techniques"
vectors = vector_db.search(embed(query), top_k=5)

# 3. Augment prompt
context = "\n".join(vectors)
prompt = f"Context:\n{context}\n\nQuestion: {query}"
```

## Memory Management

### Short-Term (Working Memory)
```python
# Current session context
working_memory = {
    "task": "Analyze target.com",
    "phase": "Reconnaissance",
    "findings": [],
    "scope": ["example.com"]
}
```

### Long-Term (Persistent)
```python
# Cross-session knowledge
persistent_memory = {
    "target_info": {...},
    "vulnerability_history": [...],
    "lessons_learned": [...]
}
```

## RedForge Memory

### Commands
```bash
# View memory
redforge memory view

# Search memory
redforge memory search "SQL injection"

# Clear memory
redforge memory clear

# Export memory
redforge memory export > backup.json
```

## Skill Context

### Load Relevant Skills
```python
def get_skills_for_task(task):
    skills = []
    
    if "scan" in task or "recon" in task:
        skills.append(load_skill("recon"))
    
    if "web" in task:
        skills.append(load_skill("web_testing"))
    
    if "api" in task:
        skills.append(load_skill("api_testing"))
    
    return "\n\n".join(skills)
```

## Efficient Prompts

### Do
```
- Be specific about what you need
- Include output format
- Use examples
- Limit context to what's needed
```

### Don't
```
- Include entire files unless necessary
- Repeat information
- Use verbose explanations
- Include irrelevant details
```

## Message Management

### Structure
```python
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": first_task},
    {"role": "assistant", "content": first_response},
    # ... more exchanges ...
]
```

### Trim Strategy
```python
def trim_to_token_limit(messages, max_tokens=3000):
    total = sum_tokens(messages)
    
    while total > max_tokens and len(messages) > 2:
        # Remove oldest non-system message
        for i, msg in enumerate(messages):
            if msg["role"] != "system":
                messages.pop(i)
                break
        total = sum_tokens(messages)
    
    return messages
```

## Best Practices
```
1. Keep context focused
2. Use RAG for large knowledge
3. Summarize old context
4. Prune unnecessary messages
5. Load only relevant skills
6. Monitor token usage
7. Test with smaller context first
```
