# Pattern: Safe Variable Initialization in Parallel Nodes

## Context
Use this when implementing multi-agent workflows (e.g., LangGraph) where nodes execute in parallel and share state, specifically when using nested dictionary access or external engine calls.

## Problem
In parallel execution environments, if a node fails early or an exception is caught silently, subsequent loggers or return statements might reference variables that were never initialized, causing `UnboundLocalError` or `NameError` which can crash the entire workflow.

## Solution
Always initialize critical variables (like `analysis` or `response`) at the start of the node function, and use safe `.get()` defaults for structured data.

### 1. Anti-Pattern (Unsafe)
```python
def agent_node(state):
    try:
        data = engine.process(state) # If this fails, 'data' is undefined
        response = f"Result: {data['value']}"
    except:
        response = "Error occurred"
    
    logger.info(f"Log: {data['status']}") # CRASH: NameError: name 'data' is not defined
    return {"view": response}
```

### 2. Pattern (Safe)
```python
def agent_node(state):
    # 1. Initialize with defaults
    data = {}
    response = "No data processed"
    
    try:
        data = engine.process(state)
        response = f"Result: {data.get('value', 'N/A')}"
    except Exception as e:
        response = f"Error: {e}"
    
    # 2. Use safe access with defaults
    logger.info(f"Log: {data.get('status', 'unknown')}")
    return {"view": response}
```

## Gotchas
- **Logger Crashes**: Loggers are common places for these errors. Always ensure variables passed to loggers are initialized even in failure paths.
- **Empty Dicts**: Initializing to `{}` is usually safer than `None` if you plan to use `.get()`.
- **Try/Except Scope**: Keep the try/except block narrow around the risky call, but ensure variables needed for the return statement exist outside that scope.
