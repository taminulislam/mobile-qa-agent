"""
Mobile QA Multi-Agent System - Main Entry Point

This is the main entry point for running the Mobile QA Multi-Agent System.
It orchestrates the Supervisor, Planner, and Executor agents to run
automated QA tests on the Obsidian mobile app.

Usage:
    python main.py                    # Run all tests
    python main.py --test test_name   # Run specific test
    python main.py --list             # List available tests
"""

import argparse
import sys
from datetime import datetime

from agents.supervisor import SupervisorAgent
from test_cases.obsidian_tests import (
    ALL_TEST_CASES, 
    get_test_case_by_name,
    get_passing_tests,
    get_failing_tests
)
from config.settings import GOOGLE_API_KEY
from utils.logger import setup_logger

logger = setup_logger("Main")


def check_prerequisites():
    """Check that all prerequisites are met."""
    errors = []
    
    # Check API key
    if not GOOGLE_API_KEY:
        errors.append("GOOGLE_API_KEY not set in .env file")
    
    # Check ADB connection
    try:
        import subprocess
        result = subprocess.run(
            ["adb", "devices"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        if "emulator" not in result.stdout and "device" not in result.stdout:
            errors.append("No Android emulator/device connected. Run: adb devices")
    except FileNotFoundError:
        errors.append("ADB not found in PATH. Make sure Android SDK platform-tools is in PATH")
    except Exception as e:
        errors.append(f"ADB check failed: {e}")
    
    if errors:
        logger.error("Prerequisites check failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    logger.info("Prerequisites check passed ✅")
    return True


def list_tests():
    """List all available test cases."""
    print("\n" + "=" * 60)
    print("AVAILABLE TEST CASES")
    print("=" * 60)
    
    print("\n📗 Tests Expected to PASS:")
    print("-" * 40)
    for tc in get_passing_tests():
        print(f"  • {tc.name}")
        print(f"    {tc.description[:60]}...")
    
    print("\n📕 Tests Expected to FAIL:")
    print("-" * 40)
    for tc in get_failing_tests():
        print(f"  • {tc.name}")
        print(f"    {tc.description[:60]}...")
    
    print("\n" + "=" * 60)
    print(f"Total: {len(ALL_TEST_CASES)} tests")
    print("=" * 60 + "\n")


def run_specific_test(test_name: str):
    """Run a specific test by name."""
    test_case = get_test_case_by_name(test_name)
    
    if test_case is None:
        logger.error(f"Test '{test_name}' not found.")
        logger.info("Available tests:")
        for tc in ALL_TEST_CASES:
            logger.info(f"  - {tc.name}")
        return None
    
    supervisor = SupervisorAgent()
    result = supervisor.run_test(test_case)
    supervisor.export_results()
    
    return result


def run_all_tests():
    """Run all available tests."""
    supervisor = SupervisorAgent()
    results = supervisor.run_all_tests(ALL_TEST_CASES)
    supervisor.export_results()
    
    return results


def run_demo_tests():
    """Run a smaller demo set of tests (2 pass, 2 fail)."""
    demo_tests = [
        get_test_case_by_name("test_create_vault"),      # Should PASS
        get_test_case_by_name("test_create_note"),       # Should PASS
        get_test_case_by_name("test_appearance_icon_red"), # Should FAIL
        get_test_case_by_name("test_print_to_pdf"),      # Should FAIL
    ]
    
    supervisor = SupervisorAgent()
    results = supervisor.run_all_tests(demo_tests)
    supervisor.export_results()
    
    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Mobile QA Multi-Agent System for Obsidian App Testing"
    )
    parser.add_argument(
        "--test", "-t",
        type=str,
        help="Run a specific test by name"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available tests"
    )
    parser.add_argument(
        "--demo", "-d",
        action="store_true",
        help="Run demo tests (4 tests: 2 pass, 2 fail)"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all tests"
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip prerequisite checks"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print("\n" + "=" * 60)
    print("🤖 MOBILE QA MULTI-AGENT SYSTEM")
    print("   Powered by Google ADK + Gemini")
    print("=" * 60 + "\n")
    
    # Handle list command
    if args.list:
        list_tests()
        return 0
    
    # Check prerequisites
    if not args.skip_checks:
        if not check_prerequisites():
            return 1
    
    # Determine what to run
    try:
        if args.test:
            logger.info(f"Running specific test: {args.test}")
            result = run_specific_test(args.test)
            if result is None:
                return 1
                
        elif args.demo:
            logger.info("Running demo tests (4 tests)")
            results = run_demo_tests()
            
        elif args.all:
            logger.info("Running all tests")
            results = run_all_tests()
            
        else:
            # Default: run demo
            logger.info("No option specified. Running demo tests.")
            logger.info("Use --help for more options.")
            results = run_demo_tests()
        
        logger.info("\n✅ Test execution completed!")
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Test execution interrupted by user")
        return 130
        
    except Exception as e:
        logger.error(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
