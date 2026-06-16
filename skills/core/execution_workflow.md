# EXECUTION: Workflow

Follow the strict operational workflow for all security testing activities. Do not skip any stages.

## Stages
1. **PLAN**: Analyze the target `{target}` and outline the exact scanning or reconnaissance commands. Explain the plan to the user.
2. **EXECUTE**: Run the tools using proper formatting. Capture standard outputs and exit codes.
3. **VERIFY**: Evaluate tool output logs. Cross-reference results with expected indicators. 
4. **STORE**: Save confirmed results and findings in memory and SQLite immediately.
5. **REPORT**: Compile findings into a structured final report based strictly on observed evidence.

## Completion Rules
- A task is **COMPLETE** if and only if:
  1. Tool execution finished successfully.
  2. Output was received.
  3. Findings were verified and stored.
- Otherwise, mark as:
  - **FAILED** (errors occurred, no outputs retrieved)
  - **PARTIAL** (some commands succeeded, further verification needed)
  - **BLOCKED** (out of scope, missing parameters, or execution prevented)
- Never report complete without concrete tool output.
