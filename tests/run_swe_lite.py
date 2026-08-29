import os
import shutil
import sys
import time
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.checkpoint import clear_checkpoints
from core.terminal_engine import TerminalEngine
from core.tool_registry import ToolRegistry
from agents.omni_state_machine import init_omni_loop, generate_next_thought, parse_action

# Fixtures for our SWE-Bench Lite Simulation
TASKS = [
    {
        "name": "fibonacci_off_by_one",
        "intent": "Fix the off-by-one error in fib.py. It should return [0, 1, 1, 2, 3] for n=5. Run python3 -m unittest test_fib.py to verify.",
        "code": "def get_fib(n):\n    res = [0, 1]\n    for i in range(2, n+1):\n        res.append(res[-1] + res[-2])\n    return res[:n]\n",
        "test": "import unittest\nfrom fib import get_fib\nclass TestFib(unittest.TestCase):\n    def test_fib(self):\n        self.assertEqual(get_fib(5), [0, 1, 1, 2, 3])\nif __name__ == '__main__':\n    unittest.main()",
        "filename": "fib.py",
        "testname": "test_fib.py"
    },
    {
        "name": "syntax_error_healing",
        "intent": "Fix the massive syntax and indentation errors in calc.py. Make sure python3 -m unittest test_calc.py passes.",
        "code": "def add(a, b):\nreturn a + b\n\ndef sub(a, b):\n    return a-b\n  def mul(a, b):\n   return a * b",
        "test": "import unittest\nfrom calc import add, sub, mul\nclass TestCalc(unittest.TestCase):\n    def test_calc(self):\n        self.assertEqual(add(2, 2), 4)\n        self.assertEqual(sub(5, 2), 3)\n        self.assertEqual(mul(3, 3), 9)\nif __name__ == '__main__':\n    unittest.main()",
        "filename": "calc.py",
        "testname": "test_calc.py"
    }
]

def run_benchmark():
    results = []
    workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), "swe_workspace"))
    coder_model = "llama3.1:8b"
    
    print("🚀 Starting Omni-Agent SWE-Bench (Lite) Evaluation")
    print("=" * 60)
    
    # Pre-pull the model just in case
    requests.post("http://127.0.0.1:11434/api/pull", json={"name": coder_model})
    
    for task in TASKS:
        print(f"\n[Task]: {task['name']}")
        
        # Setup workspace
        if os.path.exists(workspace):
            shutil.rmtree(workspace)
        os.makedirs(workspace)
        
        with open(os.path.join(workspace, task["filename"]), "w") as f:
            f.write(task["code"])
        with open(os.path.join(workspace, task["testname"]), "w") as f:
            f.write(task["test"])
            
        clear_checkpoints(workspace)
        
        terminal = TerminalEngine(workspace_dir=workspace)
        registry = ToolRegistry(workspace, terminal)
        
        # Init State Machine
        messages, blueprint = init_omni_loop(task["intent"], "qwen2.5:0.5b", coder_model, workspace_dir=workspace, status_container=None)
        
        steps_taken = 0
        success = False
        start_time = time.time()
        
        for step in range(1, 15): # Max 15 steps
            print(f"  Step {step}... ", end="", flush=True)
            try:
                raw_response = generate_next_thought(coder_model, messages, step_placeholder=None)
                messages.append({"role": "assistant", "content": raw_response})
                
                action_data = parse_action(raw_response)
                if not action_data:
                    print("[MALFORMED JSON] Retrying...")
                    messages.append({"role": "user", "content": "Error: Your JSON block was malformed. Fix it."})
                    continue
                    
                print(f"[{action_data.get('action')}]")
                if action_data.get("action") == "error":
                    print(f"    Raw: {raw_response[:200]}...")
                
                if action_data.get("action") == "done":
                    success = True
                    break
                    
                tool_result = registry.execute_tool(action_data)
                messages.append({"role": "user", "content": f"Tool Execution Result:\n```\n{tool_result.get('msg', tool_result)}\n```"})
                
            except Exception as e:
                print(f"[FATAL ERROR] {e}")
                break
                
            steps_taken += 1
                
        duration = time.time() - start_time
        
        # Final Verification
        import subprocess
        res = subprocess.run(f"python3 -m unittest {task['testname']}", shell=True, cwd=workspace, capture_output=True, text=True)
        tests_passed = (res.returncode == 0)
        
        results.append({
            "task": task["name"],
            "success": success and tests_passed,
            "steps": steps_taken,
            "time": duration
        })
        print(f"  -> Result: {'✅ PASS' if tests_passed else '❌ FAIL'} (Steps: {steps_taken}, Time: {duration:.1f}s)")
        
    print("\n" + "=" * 60)
    print("🏆 FINAL BENCHMARK RESULTS")
    print("=" * 60)
    
    report = "# 🏆 Omni-Agent Benchmark Results (SWE-Bench Lite)\n\n"
    report += "| Task | Solved? | Autonomous Steps | Time (s) |\n"
    report += "|------|---------|------------------|----------|\n"
    
    passed = 0
    for r in results:
        icon = "✅" if r['success'] else "❌"
        report += f"| {r['task']} | {icon} | {r['steps']} | {r['time']:.1f}s |\n"
        if r['success']: passed += 1
        
    report += f"\n**Final Score:** {passed}/{len(TASKS)} ({(passed/len(TASKS))*100:.1f}%)\n"
    report += "> Note: This benchmarks the agent's ability to read tracebacks, self-heal AST errors, and iteratively run Python unittests completely autonomously.\n"
    
    with open(os.path.join(os.path.dirname(__file__), "..", "artifacts", "benchmark_swe_results.md"), "w") as f:
        f.write(report)
        
    print(report)

if __name__ == "__main__":
    run_benchmark()
