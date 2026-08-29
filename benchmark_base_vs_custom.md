# Base Model vs Custom Architecture Benchmark

### qwen3:4b-instruct-2507-q4_K_M
- **Time**: 6.31s
- **Speed**: 10.9 tokens/sec
- **Output**: - 120 service classes defined, each with a `start()` method returning `True`.  
- All services are identical in structure and behavior.  
- No dependencies, configuration, or interaction between services.  
- Each service is standalone and self-contained.  
- Architecture is monolithic and repetitiv...

### architect-compiler:latest
- **Time**: 1.86s
- **Speed**: 37.1 tokens/sec
- **Output**: - 120 service classes defined, each with a `start()` method returning `True`.  
- All services are identical in implementation and behavior.  
- No dependencies, communication, or coordination between services.  
- Each service is standalone and self-contained.  
- Architecture is monolithic and rep...
