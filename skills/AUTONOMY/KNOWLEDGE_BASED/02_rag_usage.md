# RAG (Retrieval-Augmented Generation) Usage

## RAG Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Query     │────▶│  Retrieval    │────▶│  Generation  │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  Knowledge    │
                    │    Base       │
                    └──────────────┘
```

## RAG Process

### 1. Indexing (Offline)
```python
for doc in documents:
    chunks = split(doc, chunk_size=500)
    embeddings = embed(chunks)
    store(chunks, embeddings)
```

### 2. Retrieval (Online)
```python
query_embedding = embed(query)
results = search(
    collection=knowledge_base,
    query_vector=query_embedding,
    top_k=5
)
```

### 3. Generation
```python
context = format_context(results)
prompt = f"Query: {query}\n\nContext: {context}\n\nAnswer:"
response = llm.generate(prompt)
```

## Context Formatting

### Concatenation
```python
context = "\n\n".join([r.content for r in results])
```

### Summary with Links
```python
context = "Relevant information:\n"
for i, r in enumerate(results, 1):
    context += f"{i}. {r.summary}\n[Source: {r.source}]\n"
```

## RAG Optimization

### Chunk Size
- Too small: Missing context
- Too large: Noise, token limits
- Recommended: 500-1000 tokens

### Retrieval Parameters
```python
results = search(
    query_embedding,
    top_k=5,           # Number of results
    similarity_threshold=0.7,  # Minimum relevance
    max_distance=1.0
)
```

### Hybrid Approach
```python
semantic_results = semantic_search(query, k=3)
keyword_results = keyword_search(query, k=3)
combined = merge_by_score(semantic_results, keyword_results)
```

## RedForge RAG Integration

```python
class RedForgeRAG:
    def __init__(self):
        self.vector_store = create_vector_store()
        self.skill_loader = SkillIndexer()
    
    def retrieve_context(self, query, mode):
        # Get relevant skills
        skill_results = self.skill_loader.search(query, mode=mode)
        
        # Get workspace memory
        memory_results = self.workspace_memory.search(query)
        
        # Get global knowledge
        global_results = self.global_memory.search(query)
        
        # Combine and rank
        return self.combine_results([
            skill_results,
            memory_results,
            global_results
        ])
```
