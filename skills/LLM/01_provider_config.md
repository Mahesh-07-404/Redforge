# LLM Skill: Provider Configuration

## Purpose
Configure and optimize LLM providers in RedForge.

## Supported Providers

### Local
```
- Ollama (Recommended)
- LM Studio
- LocalAI
- llama.cpp
```

### Cloud
```
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- Groq (Fast inference)
```

## Ollama Setup

### Installation
```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Verify
ollama --version

# Start server
ollama serve
```

### Model Management
```bash
# Pull models
ollama pull llama3.2
ollama pull mistral
ollama pull codellama

# List models
ollama list

# Remove model
ollama rm model-name
```

### Configuration
```yaml
# config.yaml
llm:
  provider: ollama
  model: llama3.2
  base_url: http://localhost:11434
  options:
    temperature: 0.7
    num_ctx: 4096
```

### Performance
```bash
# Recommended settings
ollama pull llama3.2:latest

# For security tasks
ollama pull mixtral:8x7b-instruct-v0.1-q4_K_M

# Memory requirements
# llama3.2: 8GB RAM
# mixtral: 32GB RAM
```

## OpenAI Setup

### API Key
```yaml
llm:
  provider: openai
  model: gpt-4o
  api_key: sk-proj-...
```

### Models
```
- gpt-4o (Latest, recommended)
- gpt-4-turbo
- gpt-3.5-turbo (Fast, cheaper)
```

### Cost Management
```yaml
llm:
  provider: openai
  model: gpt-4o-mini  # Cheaper option
  max_tokens: 2000
  temperature: 0.5
```

## Anthropic Setup

### API Key
```yaml
llm:
  provider: anthropic
  model: claude-3-5-sonnet
  api_key: sk-ant-...
```

### Models
```
- claude-3-5-sonnet (Recommended)
- claude-3-opus (Most capable)
- claude-3-haiku (Fast, cheap)
```

## Google Gemini Setup

### API Key
```yaml
llm:
  provider: gemini
  model: gemini-2.0-flash
  api_key: YOUR_API_KEY
```

### Models
```
- gemini-2.0-flash (Latest, fast)
- gemini-1.5-pro (Long context)
- gemini-1.5-flash (Balanced)
```

## Groq Setup

### API Key
```yaml
llm:
  provider: groq
  model: llama-3.1-70b-versatile
  api_key: gsk_...
```

### Models
```
- llama-3.1-70b-versatile (Fast)
- llama-3.1-8b-instant (Very fast)
- mixtral-8x7b-32768 (Fast)
```

## RedForge Configuration

### Quick Setup
```bash
# Interactive setup
redforge config setup

# Set provider
redforge config set llm.provider ollama

# Set model
redforge config set llm.model llama3.2
```

### Verify Connection
```bash
# Test connection
redforge llm test

# Should output: "Connection successful"
```

## Provider Comparison

### Speed
```
Fastest:     Groq, Gemini
Fast:        Ollama (local), Claude
Moderate:    OpenAI GPT-4
Slow:        Claude Opus (large context)
```

### Cost
```
Free:        Ollama (local)
Cheapest:    Groq, Gemini
Moderate:    OpenAI GPT-3.5
Expensive:   Claude Opus, GPT-4
```

### Security
```
Most Private: Ollama (local)
Cloud:        Depends on policy
```

### Recommended Use Cases
```
Local Testing:    Ollama
Bug Bounty:       Groq/Gemini (fast)
CTF:              Ollama (free)
Learning:         Ollama (free)
Complex Analysis: Claude/GPT-4
```

## Troubleshooting

### Ollama Issues
```bash
# Server not running
ollama serve

# Model not found
ollama pull model-name

# Memory issues
# Reduce num_ctx in config
```

### API Issues
```bash
# Verify key
echo $OPENAI_API_KEY

# Test rate limits
redforge llm status
```

## Optimization

### Token Management
```yaml
llm:
  max_tokens: 4000
  context_window: 8192
```

### Caching
```yaml
llm:
  cache: true
  cache_ttl: 3600
```

### Fallback
```yaml
llm:
  primary: openai
  fallback: ollama
```

## Best Practices
```
1. Start with Ollama for free testing
2. Use Groq/Gemini for speed
3. Use Claude/GPT-4 for complex tasks
4. Set appropriate token limits
5. Enable caching for repeated queries
```
