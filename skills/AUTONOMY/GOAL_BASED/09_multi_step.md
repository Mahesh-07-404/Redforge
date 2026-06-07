# Multi-Step Task Coordination

## Coordination Patterns

### Sequential Coordination
Tasks execute in order, each completion triggers next.
```
A → B → C → D
```

### Parallel Coordination
Independent tasks execute simultaneously.
```
A ─┬─→ D
B ─┬─→ D
C ─┬─→ D
```

### Pipeline Coordination
Output of one feeds into next.
```
A → B → C → D
  ↓
  results_B → C
```

### Master-Worker Coordination
One coordinates, many execute.
```
Master
  ├─→ Worker A
  ├─→ Worker B
  └─→ Worker C
```

## Task Dependencies

### Dependency Types
```python
# Must complete before
depends_on(task_B, task_A)  # B needs A

# Must not run simultaneously
excludes(task_A, task_B)

# Should run together
together(task_A, task_B)

# Must run after condition
after(condition, task_A)
```

### Dependency Resolution
```python
def resolve_order(tasks):
    # Topological sort
    sorted_tasks = []
    remaining = tasks.copy()
    
    while remaining:
        ready = [t for t in remaining if all_deps_done(t, sorted_tasks)]
        if not ready:
            raise CircularDependencyError()
        sorted_tasks.extend(ready)
        remaining -= ready
    
    return sorted_tasks
```

## Coordination Commands

### Batch Execution
```bash
# Sequential
for task in tasks; do execute "$task"; done

# Parallel with wait
(execute task1 &) && (execute task2 &) && wait
```

### Tool Coordination
```bash
# Pass output between tools
nmap -oX scan.xml target.com
grep "open" scan.xml | ffuf -mc FF,200
```

## State Synchronization

### Shared State
```python
shared_state = {
    "findings": [],
    "completed": set(),
    "current": None
}

# Thread-safe updates
with lock:
    shared_state["findings"].append(new_finding)
```

### Event-Based
```python
events.on("task_complete", handle_completion)
events.on("task_failed", handle_failure)
```

## Best Practices

1. **Clear Dependencies**: Document what each task needs
2. **Idempotent Tasks**: Safe to run multiple times
3. **Independent Tasks**: Minimize dependencies
4. **Timeout Management**: Don't wait forever
5. **Error Propagation**: Report failures up
