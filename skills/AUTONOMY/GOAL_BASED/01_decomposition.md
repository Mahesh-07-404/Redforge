# Goal Decomposition

Breaking complex goals into manageable subtasks.

## Decomposition Principles

1. **Atomic Tasks**: Each subtask should be self-contained
2. **Clear Outcomes**: Define expected results for each subtask
3. **Logical Order**: Arrange subtasks in execution sequence
4. **Dependency Mapping**: Identify which tasks depend on others

## Decomposition Steps

### Step 1: Goal Analysis
```
Input: "Find SQL injection in example.com"
↓
Identify: Target, Attack Surface, Testing Approach
```

### Step 2: Subtask Generation
```
Main Goal → Recon → Enumerate → Test → Verify → Report
```

### Step 3: Task Refinement
```
"Find SQL injection"
  ├─ "Gather target information"
  │   ├─ WHOIS lookup
  │   ├─ DNS enumeration
  │   └─ Technology detection
  ├─ "Identify attack surface"
  │   ├─ Crawl website
  │   └─ Find input points
  └─ "Test for SQL injection"
      ├─ Test login forms
      ├─ Test search parameters
      └─ Test API endpoints
```

### Step 4: Dependency Resolution
```
Order tasks by dependencies:
1. Recon (no dependencies)
2. Enumerate (depends on recon)
3. Test (depends on enumerate)
4. Verify (depends on test)
```

## Patterns

### Linear Decomposition
For sequential processes:
```
A → B → C → D
```

### Parallel Decomposition
For independent tasks:
```
    → B →
A →      → D
    → C →
```

### Hierarchical Decomposition
For complex systems:
```
Goal
├── Subgoal A
│   ├── Task A1
│   └── Task A2
└── Subgoal B
    ├── Task B1
    └── Task B2
```

## Best Practices

- Keep subtasks atomic (1-3 steps each)
- Define clear success criteria
- Identify potential blockers early
- Plan for failure recovery
- Maintain flexibility for adaptation
