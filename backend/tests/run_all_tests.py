"""
Unified Test Runner for NarrAI E2E Test Track
Executes comprehensive 4-Tier test suites across:
1. R1: Adaptive Open-Ontology & 3 Narrative Modes (test_e2e_ontology_modes.py)
2. R3: Bank-Grade Currency Engine & Anti-Clone Guard (test_e2e_banking_security.py)
3. R2: Next-Gen Recommender Engine & Open Messenger (test_e2e_recommender_messenger.py)

Usage:
    python backend/tests/run_all_tests.py
"""

import os
import sys
import time
import unittest

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


def build_e2e_suite() -> unittest.TestSuite:
    """Builds test suite incorporating all 3 E2E test modules."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    from tests import test_e2e_ontology_modes
    from tests import test_e2e_banking_security
    from tests import test_e2e_recommender_messenger
    from tests import test_banking_adversarial_empirical
    from tests import test_adversarial_narrative_recommender
    from tests import test_backend_integration_gen2

    suite.addTests(loader.loadTestsFromModule(test_e2e_ontology_modes))
    suite.addTests(loader.loadTestsFromModule(test_e2e_banking_security))
    suite.addTests(loader.loadTestsFromModule(test_e2e_recommender_messenger))
    suite.addTests(loader.loadTestsFromModule(test_banking_adversarial_empirical))
    suite.addTests(loader.loadTestsFromModule(test_adversarial_narrative_recommender))
    suite.addTests(loader.loadTestsFromModule(test_backend_integration_gen2))

    return suite


def main():
    print("=" * 80)
    print(" " * 20 + "NARRAI COMPREHENSIVE E2E TEST RUNNER")
    print(" " * 18 + "Tiers 1-4 Verification across R1, R2, R3")
    print("=" * 80)

    start_time = time.time()
    suite = build_e2e_suite()
    total_tests = suite.countTestCases()
    print(f"Discovered {total_tests} test cases across 3 E2E tracks.")
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
        print(">>> ALL E2E TEST SUITES PASSED CLEANLY (100% SUCCESS) <<<")
        sys.exit(0)
    else:
        print(">>> E2E TEST FAILURES DETECTED <<<")
        sys.exit(1)


if __name__ == "__main__":
    main()
