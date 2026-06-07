# Semantic Search Techniques

## Semantic vs Keyword

| Aspect | Keyword Search | Semantic Search |
|--------|----------------|-----------------|
| Matching | Exact words | Meaning |
| Synonyms | No | Yes |
| Context | No | Yes |
| Speed | Faster | Slower |
| Precision | High (when keywords match) | High (when meaning matches) |

## Embedding Models

### Popular Models
- `all-MiniLM-L6-v2` (Fast, good quality)
- `all-mpnet-base-v2` (Higher quality)
- `BAAI/bge-large` (State of art)

### Model Selection
```python
models = {
    "fast": "sentence-transformers/all-MiniLM-L6-v2",
    "balanced": "sentence-transformers/all-mpnet-base-v2",
    "quality": "BAAI/bge-large-en-v1.5"
}
```

## Search Techniques

### 1. Cosine Similarity
```python
def cosine_similarity(a, b):
    return dot(a, b) / (norm(a) * norm(b))
```

### 2. ANN (Approximate Nearest Neighbor)
```python
# For large datasets
index = AnnoyIndex(embedding_dim)
index.add_items(embeddings, ids)
index.build(n_trees=10)
results = index.get_nns_by_vector(query, n=5)
```

### 3. Hybrid Search
```python
def hybrid_search(query, collection, k=5):
    # Get keyword scores
    keyword_scores = bm25(query, collection)
    
    # Get semantic scores
    semantic_scores = vector_similarity(embed(query), collection)
    
    # Combine scores
    combined = 0.3 * normalize(keyword_scores) + 0.7 * normalize(semantic_scores)
    return top_k(combined, k)
```

## Search Optimization

### Pre-filtering
```python
# Filter before search
filtered = [d for d in documents if d.metadata["category"] == target]
results = search(filtered, query)
```

### Post-filtering
```python
results = search(documents, query)
filtered = [r for r in results if r.metadata["category"] == target]
```

### Re-ranking
```python
# Initial retrieval (fast)
candidates = fast_search(query, k=100)

# Re-rank with cross-encoder (accurate)
reranked = cross_encoder_rerank(query, candidates, k=10)
```

## Best Practices

1. **Normalize embeddings**: Ensure consistent similarity
2. **Filter early**: Reduce search space
3. **Re-rank**: Improve final results
4. **Monitor latency**: Balance speed and quality
5. **Update index**: Keep embeddings fresh
