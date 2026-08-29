"""
pytest config for tests/.

Not everything under tests/ is a pytest test. Several files are scripts that were
named test_* and are meant to be run directly — they execute at import time and
some call sys.exit() at module level, which crashes pytest during COLLECTION
(not during a test), taking the whole run down with an INTERNALERROR.

Rather than pretend they are tests, they are listed here with the reason. Run
them the way they were written to be run:

    python3 tests/test_long_running.py

`pytest -q` then collects the 7 real tests and passes.
"""

collect_ignore = [
    # Calls sys.exit(1) at module level — crashes collection outright.
    "test_long_running.py",
    "accuracy_test.py",
    "test_token_lifecycle.py",
    # Real, but they drive live models and take minutes. Not suitable for a bare
    # `pytest` run; both have their own CLI.
    #   python3 tests/test_agent_completes_task.py --task fix_bug
    #   python3 tests/bench_ssm_vs_transformer.py
    "test_agent_completes_task.py",
    "bench_ssm_vs_transformer.py",
    # test_json_output_reliability(model, n_trials=5) takes a required arg, which
    # pytest reads as a fixture request ("fixture 'model' not found"). It is a
    # live-model reliability benchmark with its own CLI, not a unit test.
    "test_output_path.py",
    # Benchmarks, not assertions.
    "benchmark.py",
    "coder_benchmark.py",
    "zero_shot_benchmark.py",
    "run_swe_lite.py",
    "test_omni.py",
    # Fixture workspace used BY a test, not a test itself.
    "swe_workspace",
]
