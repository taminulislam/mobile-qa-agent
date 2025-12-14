"""
Executor Agent for Mobile QA Multi-Agent System

The Executor Agent is responsible for:
1. Taking planned actions from the Planner
2. Executing them via ADB commands
3. Capturing the results and new screen state
4. Reporting execution status back to the Supervisor
"""

from typing import Tuple, Optional
from tools.adb_tools import ADBTools
from config.settings import SCREENSHOT_DELAY
from utils.logger import setup_logger
import time

logger = setup_logger("ExecutorAgent")


class ExecutorAgent:
    """
    Executor Agent that executes actions on the Android emulator.
    """
    
    def __init__(self, device_serial: str = None):
        """
        Initialize the Executor Agent.
        
        Args:
            device_serial: Optional device serial for ADB connection
        """
        self.adb = ADBTools(device_serial)
        self.last_action = None
        self.action_count = 0
        logger.info("ExecutorAgent initialized")
    
    def execute(self, action: dict) -> Tuple[bool, str, Optional[str]]:
        """
        Execute a planned action.
        
        Args:
            action: Dictionary containing action details from Planner
            
        Returns:
            Tuple of (success: bool, message: str, screenshot_base64: Optional[str])
        """
        action_type = action.get("action", "").lower()
        description = action.get("description", "No description")
        
        logger.info(f"Executing action: {action_type} - {description}")
        self.action_count += 1
        
        try:
            result_message = ""
            
            # Execute based on action type
            if action_type == "tap":
                x = action.get("x", 0)
                y = action.get("y", 0)
                result_message = self.adb.tap(x, y)
                
            elif action_type == "double_tap":
                x = action.get("x", 0)
                y = action.get("y", 0)
                result_message = self.adb.double_tap(x, y)
                
            elif action_type == "long_press":
                x = action.get("x", 0)
                y = action.get("y", 0)
                duration = action.get("duration_ms", 1000)
                result_message = self.adb.long_press(x, y, duration)
                
            elif action_type == "type_text":
                text = action.get("text", "")
                result_message = self.adb.type_text(text)
                
            elif action_type == "swipe":
                start_x = action.get("start_x", 0)
                start_y = action.get("start_y", 0)
                end_x = action.get("end_x", 0)
                end_y = action.get("end_y", 0)
                duration = action.get("duration_ms", 300)
                result_message = self.adb.swipe(start_x, start_y, end_x, end_y, duration)
                
            elif action_type == "scroll_up":
                result_message = self.adb.scroll_up()
                
            elif action_type == "scroll_down":
                result_message = self.adb.scroll_down()
                
            elif action_type == "press_back":
                result_message = self.adb.press_back()
                
            elif action_type == "press_home":
                result_message = self.adb.press_home()
                
            elif action_type == "press_enter":
                result_message = self.adb.press_enter()
                
            elif action_type == "press_menu":
                result_message = self.adb.press_menu()
                
            elif action_type == "launch_app":
                package_name = action.get("package_name", "")
                result_message = self.adb.launch_app(package_name)
                
            elif action_type == "close_app":
                package_name = action.get("package_name", "")
                result_message = self.adb.close_app(package_name)
                
            elif action_type == "wait":
                seconds = action.get("seconds", 1)
                result_message = self.adb.wait(seconds)
                
            elif action_type == "clear_text":
                result_message = self.adb.clear_text_field()
            
            elif action_type == "tap_by_text":
                text = action.get("text", "")
                exact_match = action.get("exact_match", True)
                result_message = self.adb.tap_element_by_text(text, exact_match)
                if "Could not find" in result_message:
                    logger.warning(f"Element not found: {text}")
                    return False, result_message, self.adb.get_screenshot_base64()
            
            elif action_type == "tap_by_resource_id":
                resource_id = action.get("resource_id", "")
                result_message = self.adb.tap_element_by_resource_id(resource_id)
                if "Could not find" in result_message:
                    logger.warning(f"Element not found: {resource_id}")
                    return False, result_message, self.adb.get_screenshot_base64()
            
            elif action_type == "tap_by_hint":
                hint = action.get("hint", "")
                result_message = self.adb.tap_element_by_hint(hint)
                if "Could not find" in result_message:
                    logger.warning(f"Element not found by hint: {hint}")
                    return False, result_message, self.adb.get_screenshot_base64()
                
            elif action_type == "test_complete":
                result = action.get("result", "pass")
                result_message = f"Test completed with result: {result}"
                logger.info(f"TEST COMPLETE: {description}")
                # Take final screenshot
                time.sleep(SCREENSHOT_DELAY)
                screenshot_b64 = self.adb.get_screenshot_base64()
                return True, result_message, screenshot_b64
                
            elif action_type == "test_failed":
                reason = action.get("reason", "Unknown reason")
                result_message = f"Test failed: {reason}"
                logger.warning(f"TEST FAILED: {reason} - {description}")
                # Take final screenshot
                time.sleep(SCREENSHOT_DELAY)
                screenshot_b64 = self.adb.get_screenshot_base64()
                return True, result_message, screenshot_b64
                
            else:
                logger.warning(f"Unknown action type: {action_type}")
                result_message = f"Unknown action type: {action_type}"
                return False, result_message, None
            
            # Wait for UI to update and take screenshot
            time.sleep(SCREENSHOT_DELAY)
            screenshot_b64 = self.adb.get_screenshot_base64()
            
            self.last_action = action
            logger.info(f"Action executed successfully: {result_message}")
            
            return True, result_message, screenshot_b64
            
        except Exception as e:
            error_msg = f"Execution error: {str(e)}"
            logger.error(error_msg)
            
            # Try to get screenshot even after error
            try:
                screenshot_b64 = self.adb.get_screenshot_base64()
            except:
                screenshot_b64 = None
                
            return False, error_msg, screenshot_b64
    
    def get_current_screenshot(self) -> str:
        """
        Get the current screen state as base64 encoded image.
        
        Returns:
            Base64 encoded screenshot
        """
        return self.adb.get_screenshot_base64()
    
    def get_action_count(self) -> int:
        """Get the total number of actions executed."""
        return self.action_count
    
    def reset(self):
        """Reset the executor state for a new test."""
        self.last_action = None
        self.action_count = 0
        logger.info("ExecutorAgent reset")
    
    def prepare_for_test(self, launch_obsidian: bool = True):
        """
        Prepare the emulator for a new test.
        This closes any running apps, returns to home screen, and optionally launches Obsidian.
        
        Args:
            launch_obsidian: If True, launch Obsidian app after preparation
        """
        logger.info("Preparing emulator for test")
        
        # Press home to ensure we start from home screen
        self.adb.press_home()
        time.sleep(1)
        
        # Close Obsidian if running
        try:
            self.adb.close_app("md.obsidian")
            time.sleep(0.5)
        except:
            pass
        
        # Launch Obsidian app for the test
        if launch_obsidian:
            logger.info("Launching Obsidian for test")
            self.adb.launch_app("md.obsidian")
            time.sleep(2)  # Wait for app to fully load
        
        logger.info("Emulator prepared for test")
