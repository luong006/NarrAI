"""
Unified Test Runner for NarrAI E2E & Resilience Test Track
Executes comprehensive test suites across:
1. Core Track (111 tests):
   - R1: Adaptive Open-Ontology & 3 Narrative Modes (test_e2e_ontology_modes.py)
   - R3: Bank-Grade Currency Engine & Anti-Clone Guard (test_e2e_banking_security.py)
   - R2: Next-Gen Recommender Engine & Open Messenger (test_e2e_recommender_messenger.py)
   - Banking Concurrency & Adversarial Empirical (test_banking_adversarial_empirical.py)
   - Adversarial Narrative & Recommender (test_adversarial_narrative_recommender.py)
   - Backend Router Integration Gen2 (test_backend_integration_gen2.py)
2. Round 5 Track (71 tests):
   - 5-Target Copilot Manuscript Surgery & Feed (test_e2e_round5_surgery_feed.py)
   - Adversarial Surgery Stress & Invariant Resilience (test_adversarial_round5_resilience.py)
3. Round 7 Track:
   - Backend AI Dual-Matrix Resilience & Q&A Interview Refiner (test_round7_qa_resilience.py)

Usage:
    python backend/tests/run_all_tests.py
"""

import os
import sys
import time
import unittest

# Ensure backend root and backend/tests are on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
tests_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)

# Ensure dummy keys for agent initialization across test runners
os.environ.setdefault("GROQ_API_KEY", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_COPILOT", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_BIBLE", "gsk_test_dummy_key_for_unit_tests")


def build_e2e_suite() -> unittest.TestSuite:
    """Builds test suite incorporating all Core (111) + Round 5 (71) + Round 7 resilience test modules."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Core Track Modules (111 tests)
    core_modules = [
        "test_e2e_ontology_modes",
        "test_e2e_banking_security",
        "test_e2e_recommender_messenger",
        "test_banking_adversarial_empirical",
        "test_adversarial_narrative_recommender",
        "test_backend_integration_gen2",
    ]

    # Round 5 Track Modules (71 tests)
    round5_modules = [
        "test_e2e_round5_surgery_feed",
        "test_adversarial_round5_resilience",
    ]

    # Round 7 Track Modules (Resilience tests)
    round7_modules = [
        "test_round7_qa_resilience",
    ]

    all_modules = core_modules + round5_modules + round7_modules

    for mod_name in all_modules:
        mod = None
        # Try importing from tests package first, then directly
        try:
            mod = __import__(f"tests.{mod_name}", fromlist=[mod_name])
        except ImportError:
            try:
                mod = __import__(mod_name)
            except ImportError as e:
                print(f"Warning: Could not import {mod_name}: {e}")
                continue

        if mod:
            tests = loader.loadTestsFromModule(mod)
            suite.addTests(tests)

    return suite


def main():
    print("=" * 80)
    print(" " * 20 + "NARRAI COMPREHENSIVE E2E & RESILIENCE TEST RUNNER")
    print(" " * 15 + "Verification across Core (111) + Round 5 (71) + Round 7 Suites")
    print("=" * 80)

    start_time = time.time()
    suite = build_e2e_suite()
    total_tests = suite.countTestCases()
    print(f"Discovered {total_tests} test cases across Core, Round 5, and Round 7 tracks.")
    print("-" * 80)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    elapsed = time.time() - start_time
    passed = total_tests - len(result.failures) - len(result.errors) - len(result.skipped)

    print("\n" + "=" * 80)
    print(" " * 30 + "TEST EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total Tests Executed : {total_tests}")
    print(f"Passed               : {passed} ({(passed/total_tests*100) if total_tests else 0:.1f}%)")
    print(f"Failures             : {len(result.failures)}")
    print(f"Errors               : {len(result.errors)}")
    print(f"Skipped              : {len(result.skipped)}")
    print(f"Total Time           : {elapsed:.2f} seconds")
    print("-" * 80)

    if result.wasSuccessful():
        print(">>> ALL TEST SUITES PASSED CLEANLY (100% SUCCESS) <<<")
        sys.exit(0)
    else:
        print(">>> TEST FAILURES DETECTED <<<")
        sys.exit(1)


if __name__ == "__main__":
    main()
