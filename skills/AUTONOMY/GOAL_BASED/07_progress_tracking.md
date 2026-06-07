# Progress Tracking

## Progress Metrics

### Quantitative Metrics
- Tasks completed / Total tasks
- Findings discovered
- Tools executed
- Time elapsed / Time remaining
- Lines of output processed

### Qualitative Metrics
- Goal proximity
- Coverage completeness
- Confidence level

## Progress Reporting

```python
class ProgressTracker:
    def __init__(self, total_tasks):
        self.total = total_tasks
        self.completed = 0
        self.failed = 0
        self.current = None
    
    def update(self, task_id, status):
        if status == 'completed':
            self.completed += 1
        elif status == 'failed':
            self.failed += 1
    
    def report(self):
        return f"{self.completed}/{self.total} tasks completed"
```

## Progress Display

### Progress Bar
```
[████████████████████░░░░] 80% - Task 8/10
```

### Status Report
```
[+] Completed: Reconnaissance
[+] Completed: Port Scanning  
[-] In Progress: Vulnerability Scan
[ ] Pending: Exploitation
[ ] Pending: Documentation
```

## Milestone Tracking

### Key Milestones
1. Initial recon complete
2. Attack surface identified
3. High-priority vulns found
4. Exploitation successful
5. Documentation complete

### Milestone Checkpoints
```python
milestones = [
    {"name": "Recon", "tasks": [1, 2, 3]},
    {"name": "Scan", "tasks": [4, 5, 6]},
    {"name": "Exploit", "tasks": [7, 8, 9]},
    {"name": "Report", "tasks": [10]}
]

for milestone in milestones:
    if all(tasks_complete(t) for t in milestone["tasks"]):
        notify(f"Milestone: {milestone['name']}")
```

## Progress Estimation

### Time Estimation
```python
# Based on historical data
avg_time_per_task = total_time / completed_tasks
remaining_tasks = total_tasks - completed_tasks
estimated_remaining = avg_time_per_task * remaining_tasks
```

### Coverage Estimation
```python
# Subdomains discovered / Subdomains in scope
subdomain_coverage = discovered / in_scope

# Ports scanned / Total ports
port_coverage = scanned / total_ports

# Endpoints discovered / Total endpoints
endpoint_coverage = discovered / total
```

## Progress Persistence

Save progress for recovery:
```python
progress = {
    "completed_tasks": [...],
    "failed_tasks": [...],
    "findings": [...],
    "current_task": "vuln_scan",
    "timestamp": now()
}
save_progress(progress)
```
