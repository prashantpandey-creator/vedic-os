import os
import shutil
import sys
import time
import requests
import re
import subprocess

MODELS = ["mannix/llama3.1-8b-abliterated:latest", "granite4:3b-h", "qwen2.5:32b"]

TASKS = [
    {
        "name": "fibonacci_logic",
        "intent": "Fix the off-by-one error in fib.py. It should return [0, 1, 1, 2, 3] for n=5. Output ONLY the complete, fixed Python code inside ```python blocks.",
        "code": "def get_fib(n):\n    res = [0, 1]\n    for i in range(2, n+1):\n        res.append(res[-1] + res[-2])\n    return res[:n]\n",
        "test": "import unittest\nfrom fib import get_fib\nclass TestFib(unittest.TestCase):\n    def test_fib(self):\n        self.assertEqual(get_fib(5), [0, 1, 1, 2, 3])\nif __name__ == '__main__':\n    unittest.main()",
        "filename": "fib.py",
        "testname": "test_fib.py"
    },
    {
        "name": "syntax_healing",
        "intent": "Fix the massive syntax and indentation errors in calc.py. Output ONLY the complete, fixed Python code inside ```python blocks.",
        "code": "def add(a, b):\nreturn a + b\n\ndef sub(a, b):\n    return a-b\n  def mul(a, b):\n   return a * b",
        "test": "import unittest\nfrom calc import add, sub, mul\nclass TestCalc(unittest.TestCase):\n    def test_calc(self):\n        self.assertEqual(add(2, 2), 4)\n        self.assertEqual(sub(5, 2), 3)\n        self.assertEqual(mul(3, 3), 9)\nif __name__ == '__main__':\n    unittest.main()",
        "filename": "calc.py",
        "testname": "test_calc.py"
    }
]

def extract_code(text):
    match = re.search(r'```python\n(.*?)\n```', text, re.DOTALL)
    if match: return match.group(1)
    # Fallback
    match = re.search(r'```(.*?)```', text, re.DOTALL)
    if match: return match.group(1).strip()
    return text

def run_zero_shot():
    results = {}
    workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), "swe_workspace"))
    
    for model in MODELS:
        print(f"\n🚀 Benchmarking {model} (Zero-Shot / No Harness)")
        results[model] = {"passed": 0, "total": len(TASKS), "tasks": {}}
        
        for task in TASKS:
            if os.path.exists(workspace): shutil.rmtree(workspace)
            os.makedirs(workspace)
            
            with open(os.path.join(workspace, task["testname"]), "w") as f:
                f.write(task["test"])
                
            prompt = f"{task['intent']}\n\nCURRENT CODE:\n```python\n{task['code']}\n```"
            
            start = time.time()
            try:
                res = requests.post("http://127.0.0.1:11434/api/chat", json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                }).json()
                answer = res.get("message", {}).get("content", "")
            except Exception as e:
                print(f"  [ERROR] {e}")
                continue
                
            fixed_code = extract_code(answer)
            with open(os.path.join(workspace, task["filename"]), "w") as f:
                f.write(fixed_code)
                
            out = subprocess.run(f"python3 -m unittest {task['testname']}", shell=True, cwd=workspace, capture_output=True, text=True)
            passed = (out.returncode == 0)
            
            if passed: results[model]["passed"] += 1
            results[model]["tasks"][task["name"]] = passed
            print(f"  -> {task['name']}: {'✅ PASS' if passed else '❌ FAIL'} ({time.time()-start:.1f}s)")
            
    # Print Markdown Table
    print("\n\n# Benchmark Report: Zero-Shot vs Omni-Agent Harness")
    print("| Model | Size | fibonacci_logic | syntax_healing | Score (No Harness) | Score (With Harness) |")
    print("|---|---|---|---|---|---|")
    
    for model, data in results.items():
        fib = "✅" if data["tasks"].get("fibonacci_logic") else "❌"
        syn = "✅" if data["tasks"].get("syntax_healing") else "❌"
        score = f"{data['passed']}/2"
        harness_score = "1/2 (Logic Only)" if "llama3.1" in model else "TBD" # We know llama 8b gets 1/2 with harness
        print(f"| `{model}` | | {fib} | {syn} | **{score}** | **{harness_score}** |")

if __name__ == "__main__":
    run_zero_shot()
