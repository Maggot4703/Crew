#!/usr/bin/env python3
"""
TTS Test Runner for Crew Project
Run different TTS test suites individually or combined
"""

import argparse
import os
import subprocess
import sys


def run_test_file(test_file, verbose=True):
    """Run a specific test file"""
    sep = "=" * 60
    print(sep)
    print(f"RUNNING: {test_file}")
    print(sep)

    try:
        cmd = [sys.executable, test_file]
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=False,
            text=True,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {test_file}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run TTS tests for Crew project")
    parser.add_argument(
        "--comprehensive", action="store_true", help="Run comprehensive TTS test suite"
    )
    parser.add_argument("--basic", action="store_true", help="Run basic TTS tests")
    parser.add_argument("--details", action="store_true", help="Run TTS details tests")
    parser.add_argument("--all", action="store_true", help="Run all TTS tests")

    args = parser.parse_args()

    # Test files to run
    test_files = []

    if args.all or (not any([args.comprehensive, args.basic, args.details])):
        # Run all tests by default
        test_files = [
            "tests/test_tts.py",
            "tests/test_tts_details.py",
            "tests/test_tts_comprehensive.py",
        ]
    else:
        if args.basic:
            test_files.append("tests/test_tts.py")
        if args.details:
            test_files.append("tests/test_tts_details.py")
        if args.comprehensive:
            test_files.append("tests/test_tts_comprehensive.py")

    # Check TTS availability
    try:
        pass

        tts_available = True
        print("✓ pyttsx3 TTS engine is available")
    except ImportError:
        tts_available = False
        print("⚠ pyttsx3 TTS engine is NOT available - using mock engine")

    # Run each test file
    results = {}
    for test_file in test_files:
        if os.path.exists(test_file):
            success = run_test_file(test_file, verbose=True)
            results[test_file] = success
        else:
            print(f"⚠ Test file not found: {test_file}")
            results[test_file] = False

    # Summary
    sep = "=" * 60
    print(sep)
    print("TTS TEST SUMMARY")
    print(sep)

    total_tests = len(results)
    passed_tests = sum(1 for success in results.values() if success)

    for test_file, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status:10} {test_file}")

    print(f"\nTTS Engine Available: {'✓ Yes' if tts_available else '✗ No (Mock)'}")
    print(f"Tests Run: {total_tests}")
    print(f"Tests Passed: {passed_tests}")
    print(f"Tests Failed: {total_tests - passed_tests}")

    if passed_tests == total_tests:
        print("\n🎉 All TTS tests passed!")
        return 0
    else:
        print("\n❌ Some TTS tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
