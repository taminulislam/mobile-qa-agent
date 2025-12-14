"""
Supervisor Agent for Mobile QA Multi-Agent System

The Supervisor Agent is responsible for:
1. Orchestrating the Planner and Executor agents
2. Managing test execution flow
3. Verifying state transitions
4. Logging and reporting final results (Pass/Fail)
5. Distinguishing between step failures and test assertion failures
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import time

from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from test_cases.obsidian_tests import TestCase, TestResult, TestStatus
from config.settings import MAX_STEPS, SCREENSHOTS_DIR
from utils.logger import setup_logger

logger = setup_logger("SupervisorAgent")


@dataclass
class StepRecord:
    """Record of a single execution step"""
    step_number: int
    action: dict
    success: bool
    message: str
    screenshot_path: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SupervisorAgent:
    """
    Supervisor Agent that orchestrates the QA testing process.
    """
    
    def __init__(self, device_serial: str = None):
        """
        Initialize the Supervisor Agent.
        
        Args:
            device_serial: Optional device serial for ADB connection
        """
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent(device_serial)
        self.current_test: Optional[TestCase] = None
        self.step_records: List[StepRecord] = []
        self.test_results: List[TestResult] = []
        logger.info("SupervisorAgent initialized")
    
    def run_test(self, test_case: TestCase) -> TestResult:
        """
        Run a single test case.
        
        Args:
            test_case: The test case to execute
            
        Returns:
            TestResult object containing the outcome
        """
        logger.info("=" * 60)
        logger.info(f"STARTING TEST: {test_case.name}")
        logger.info(f"Description: {test_case.description}")
        logger.info(f"Expected to {'PASS' if test_case.should_pass else 'FAIL'}")
        logger.info("=" * 60)
        
        # Reset agents for new test
        self.planner.reset()
        self.executor.reset()
        self.current_test = test_case
        self.step_records = []
        
        # Prepare emulator
        self.executor.prepare_for_test()
        time.sleep(1)
        
        # Get initial screenshot
        try:
            initial_screenshot = self.executor.get_current_screenshot()
        except Exception as e:
            logger.error(f"Failed to get initial screenshot: {e}")
            return self._create_error_result(test_case, f"Failed to get initial screenshot: {e}")
        
        # Execute test steps
        current_screenshot = initial_screenshot
        previous_actions = []
        final_status = TestStatus.RUNNING
        final_message = ""
        
        for step in range(1, MAX_STEPS + 1):
            logger.info(f"\n--- Step {step}/{MAX_STEPS} ---")
            
            # 1. Planner decides next action
            action = self.planner.analyze_and_plan(
                screenshot_base64=current_screenshot,
                test_description=test_case.description,
                expected_result=test_case.expected_result,
                should_pass=test_case.should_pass,
                previous_actions=previous_actions,
                current_step=step,
                max_steps=MAX_STEPS
            )
            
            # 2. Check for terminal actions
            action_type = action.get("action", "")
            
            if action_type == "test_complete":
                logger.info(f"✅ TEST COMPLETED: {action.get('description', '')}")
                final_status = TestStatus.PASSED
                final_message = action.get("description", "Test completed successfully")
                
                # Execute to get final screenshot
                success, message, screenshot = self.executor.execute(action)
                self._record_step(step, action, success, message, screenshot)
                break
                
            elif action_type == "test_failed":
                reason = action.get("reason", "Unknown reason")
                logger.warning(f"❌ TEST FAILED: {reason}")
                final_status = TestStatus.FAILED
                final_message = reason
                
                # Execute to get final screenshot
                success, message, screenshot = self.executor.execute(action)
                self._record_step(step, action, success, message, screenshot)
                break
            
            # 3. Executor performs the action
            success, message, new_screenshot = self.executor.execute(action)
            
            # 4. Record the step
            self._record_step(step, action, success, message, new_screenshot)
            
            # 5. Handle execution failures (step failure vs test failure)
            if not success:
                logger.warning(f"Step execution failed: {message}")
                # This is a STEP failure, not necessarily a test failure
                # We continue and let the planner decide what to do
            
            # 6. Update state for next iteration
            if new_screenshot:
                current_screenshot = new_screenshot
            previous_actions.append({
                "step": step,
                "action": action_type,
                "description": action.get("description", ""),
                "success": success
            })
        
        else:
            # Max steps reached without conclusion
            logger.warning(f"Max steps ({MAX_STEPS}) reached without test conclusion")
            final_status = TestStatus.ERROR
            final_message = f"Test did not complete within {MAX_STEPS} steps"
        
        # Create and store result
        result = self._create_result(test_case, final_status, final_message)
        self.test_results.append(result)
        
        # Log final result
        self._log_test_result(result)
        
        return result
    
    def run_all_tests(self, test_cases: List[TestCase]) -> List[TestResult]:
        """
        Run multiple test cases sequentially.
        
        Args:
            test_cases: List of test cases to execute
            
        Returns:
            List of TestResult objects
        """
        logger.info(f"\n{'#' * 60}")
        logger.info(f"STARTING TEST SUITE: {len(test_cases)} tests")
        logger.info(f"{'#' * 60}\n")
        
        results = []
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n[{i}/{len(test_cases)}] Running: {test_case.name}")
            result = self.run_test(test_case)
            results.append(result)
            
            # Brief pause between tests
            time.sleep(2)
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _record_step(self, step: int, action: dict, success: bool, 
                     message: str, screenshot_b64: str = None):
        """Record a test step."""
        screenshot_path = None
        if screenshot_b64:
            # Save screenshot
            filename = f"{self.current_test.name}_step_{step}.png"
            screenshot_path = str(SCREENSHOTS_DIR / filename)
            try:
                import base64
                with open(screenshot_path, 'wb') as f:
                    f.write(base64.b64decode(screenshot_b64))
            except Exception as e:
                logger.warning(f"Failed to save screenshot: {e}")
                screenshot_path = None
        
        record = StepRecord(
            step_number=step,
            action=action,
            success=success,
            message=message,
            screenshot_path=screenshot_path
        )
        self.step_records.append(record)
    
    def _create_result(self, test_case: TestCase, status: TestStatus, 
                       message: str) -> TestResult:
        """Create a TestResult object."""
        steps_executed = [
            f"Step {r.step_number}: {r.action.get('action', 'unknown')} - {r.action.get('description', '')}"
            for r in self.step_records
        ]
        
        screenshots = [r.screenshot_path for r in self.step_records if r.screenshot_path]
        
        return TestResult(
            test_case=test_case,
            status=status,
            actual_result=message,
            steps_executed=steps_executed,
            screenshots=screenshots
        )
    
    def _create_error_result(self, test_case: TestCase, error_message: str) -> TestResult:
        """Create an error TestResult."""
        return TestResult(
            test_case=test_case,
            status=TestStatus.ERROR,
            actual_result=error_message,
            steps_executed=[],
            error_message=error_message
        )
    
    def _log_test_result(self, result: TestResult):
        """Log the test result with clear formatting."""
        logger.info("\n" + "=" * 60)
        logger.info(f"TEST: {result.test_case.name}")
        logger.info(f"STATUS: {result.status.value.upper()}")
        logger.info(f"EXPECTED TO PASS: {result.test_case.should_pass}")
        logger.info(f"ACTUAL RESULT: {result.actual_result}")
        logger.info(f"CORRECT BEHAVIOR: {'✅ YES' if result.is_correct else '❌ NO'}")
        logger.info(f"STEPS EXECUTED: {len(result.steps_executed)}")
        logger.info("=" * 60 + "\n")
    
    def _print_summary(self, results: List[TestResult]):
        """Print a summary of all test results."""
        total = len(results)
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in results if r.status == TestStatus.ERROR)
        correct = sum(1 for r in results if r.is_correct)
        
        logger.info("\n" + "#" * 60)
        logger.info("TEST SUITE SUMMARY")
        logger.info("#" * 60)
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Errors: {errors}")
        logger.info(f"Correct Behavior: {correct}/{total} ({100*correct/total:.1f}%)")
        logger.info("#" * 60)
        
        # Detailed breakdown
        logger.info("\nDetailed Results:")
        logger.info("-" * 60)
        for result in results:
            status_icon = "✅" if result.is_correct else "❌"
            expected = "PASS" if result.test_case.should_pass else "FAIL"
            actual = result.status.value.upper()
            logger.info(f"{status_icon} {result.test_case.name}")
            logger.info(f"   Expected: {expected} | Actual: {actual}")
        logger.info("-" * 60)
    
    def export_results(self, filepath: str = None) -> str:
        """
        Export test results to a JSON file.
        
        Args:
            filepath: Optional output file path
            
        Returns:
            Path to the exported file
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = str(SCREENSHOTS_DIR.parent / f"test_results_{timestamp}.json")
        
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.test_results),
            "results": [
                {
                    "test_name": r.test_case.name,
                    "description": r.test_case.description,
                    "expected_to_pass": r.test_case.should_pass,
                    "status": r.status.value,
                    "actual_result": r.actual_result,
                    "is_correct": r.is_correct,
                    "steps_executed": r.steps_executed,
                    "screenshots": r.screenshots
                }
                for r in self.test_results
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Results exported to: {filepath}")
        return filepath
