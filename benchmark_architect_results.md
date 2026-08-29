# Architect Ingestion Benchmark

### architect-compiler:latest
- **Time**: 8.04s
- **Speed**: 8.1 tokens/sec
- **Output**: - 100 classes, each named ModuleX, from 0 to 99.  
- Each class has an `execute` method returning a sequential integer.  
- All modules are standalone...

### granite4:3b-h
- **Time**: 9.91s
- **Speed**: 14.3 tokens/sec
- **Output**: - The codebase consists of a `main.py` file containing 50 classes named `Module0` to `Module49`.
- Each class implements an `execute()` method that re...

### mannix/llama3.1-8b-abliterated:latest
- **Time**: 24.93s
- **Speed**: 4.0 tokens/sec
- **Output**: **Summary:**

* The codebase consists of 99 modules, each with a single method `execute()` that returns an integer value from 0 to 98.
* No complex lo...
