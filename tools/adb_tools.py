"""
ADB Tools for Android Emulator Interaction

This module provides tools for interacting with the Android emulator
using ADB (Android Debug Bridge) commands.
"""

import subprocess
import base64
import time
from pathlib import Path
from typing import Optional, Tuple
from config.settings import (
    ADB_PATH, 
    EMULATOR_SERIAL, 
    SCREENSHOTS_DIR,
    SCREENSHOT_DELAY,
    ACTION_DELAY,
    SCREEN_WIDTH,
    SCREEN_HEIGHT
)
from utils.logger import setup_logger

logger = setup_logger("ADBTools")


class ADBTools:
    """
    A class providing ADB tools for Android emulator interaction.
    """
    
    def __init__(self, device_serial: str = None):
        """
        Initialize ADB Tools.
        
        Args:
            device_serial: The serial number of the target device/emulator
        """
        self.device_serial = device_serial or EMULATOR_SERIAL
        self.adb_prefix = [ADB_PATH, "-s", self.device_serial]
        self._verify_connection()
    
    def _verify_connection(self) -> bool:
        """Verify ADB connection to the device."""
        try:
            result = self._run_command(["devices"])
            if self.device_serial in result:
                logger.info(f"Connected to device: {self.device_serial}")
                return True
            else:
                logger.warning(f"Device {self.device_serial} not found in: {result}")
                return False
        except Exception as e:
            logger.error(f"Failed to verify ADB connection: {e}")
            return False
    
    def _run_command(self, args: list, use_prefix: bool = True) -> str:
        """
        Run an ADB command and return the output.
        
        Args:
            args: Command arguments
            use_prefix: Whether to use the device-specific prefix
            
        Returns:
            Command output as string
        """
        cmd = self.adb_prefix + args if use_prefix else [ADB_PATH] + args
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0 and result.stderr:
                logger.warning(f"Command stderr: {result.stderr}")
            return result.stdout
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(cmd)}")
            raise
        except Exception as e:
            logger.error(f"Command failed: {e}")
            raise
    
    def _run_shell_command(self, args: list) -> str:
        """Run an ADB shell command."""
        return self._run_command(["shell"] + args)
    
    # ==================== Screenshot Tools ====================
    
    def take_screenshot(self, filename: str = None) -> Tuple[str, bytes]:
        """
        Take a screenshot of the device screen.
        
        Args:
            filename: Optional filename for saving the screenshot
            
        Returns:
            Tuple of (filepath, image_bytes)
        """
        if filename is None:
            filename = f"screenshot_{int(time.time())}.png"
        
        filepath = SCREENSHOTS_DIR / filename
        
        try:
            # Use exec-out for direct binary output
            cmd = self.adb_prefix + ["exec-out", "screencap", "-p"]
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                image_bytes = result.stdout
                
                # Save to file
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
                
                logger.info(f"Screenshot saved: {filepath}")
                return str(filepath), image_bytes
            else:
                logger.error(f"Screenshot failed: {result.stderr}")
                raise Exception("Failed to capture screenshot")
                
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            raise
    
    def get_screenshot_base64(self) -> str:
        """
        Take a screenshot and return as base64 encoded string.
        
        Returns:
            Base64 encoded screenshot
        """
        _, image_bytes = self.take_screenshot()
        return base64.b64encode(image_bytes).decode('utf-8')
    
    # ==================== Touch/Tap Tools ====================
    
    def tap(self, x: int, y: int) -> str:
        """
        Tap at specific coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Result message
        """
        logger.info(f"Tapping at ({x}, {y})")
        self._run_shell_command(["input", "tap", str(x), str(y)])
        time.sleep(ACTION_DELAY)
        return f"Tapped at coordinates ({x}, {y})"
    
    def double_tap(self, x: int, y: int) -> str:
        """
        Double tap at specific coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Result message
        """
        logger.info(f"Double tapping at ({x}, {y})")
        self.tap(x, y)
        time.sleep(0.1)
        self.tap(x, y)
        return f"Double tapped at coordinates ({x}, {y})"
    
    def long_press(self, x: int, y: int, duration_ms: int = 1000) -> str:
        """
        Long press at specific coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration_ms: Press duration in milliseconds
            
        Returns:
            Result message
        """
        logger.info(f"Long pressing at ({x}, {y}) for {duration_ms}ms")
        self._run_shell_command([
            "input", "swipe", 
            str(x), str(y), str(x), str(y), str(duration_ms)
        ])
        time.sleep(ACTION_DELAY)
        return f"Long pressed at ({x}, {y}) for {duration_ms}ms"
    
    # ==================== Swipe/Scroll Tools ====================
    
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, 
              duration_ms: int = 300) -> str:
        """
        Swipe from one point to another.
        
        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            duration_ms: Swipe duration in milliseconds
            
        Returns:
            Result message
        """
        logger.info(f"Swiping from ({start_x}, {start_y}) to ({end_x}, {end_y})")
        self._run_shell_command([
            "input", "swipe",
            str(start_x), str(start_y),
            str(end_x), str(end_y),
            str(duration_ms)
        ])
        time.sleep(ACTION_DELAY)
        return f"Swiped from ({start_x}, {start_y}) to ({end_x}, {end_y})"
    
    def scroll_up(self) -> str:
        """Scroll up on the screen."""
        center_x = SCREEN_WIDTH // 2
        start_y = SCREEN_HEIGHT * 2 // 3
        end_y = SCREEN_HEIGHT // 3
        return self.swipe(center_x, start_y, center_x, end_y, 500)
    
    def scroll_down(self) -> str:
        """Scroll down on the screen."""
        center_x = SCREEN_WIDTH // 2
        start_y = SCREEN_HEIGHT // 3
        end_y = SCREEN_HEIGHT * 2 // 3
        return self.swipe(center_x, start_y, center_x, end_y, 500)
    
    # ==================== Text Input Tools ====================
    
    def type_text(self, text: str) -> str:
        """
        Type text into the focused field.
        
        Args:
            text: Text to type (spaces will be handled)
            
        Returns:
            Result message
        """
        # Replace spaces with %s for ADB
        escaped_text = text.replace(" ", "%s")
        # Escape special characters
        escaped_text = escaped_text.replace("'", "\\'")
        escaped_text = escaped_text.replace('"', '\\"')
        escaped_text = escaped_text.replace("&", "\\&")
        escaped_text = escaped_text.replace("<", "\\<")
        escaped_text = escaped_text.replace(">", "\\>")
        escaped_text = escaped_text.replace(";", "\\;")
        escaped_text = escaped_text.replace("(", "\\(")
        escaped_text = escaped_text.replace(")", "\\)")
        escaped_text = escaped_text.replace("|", "\\|")
        
        logger.info(f"Typing text: {text}")
        self._run_shell_command(["input", "text", escaped_text])
        time.sleep(ACTION_DELAY)
        return f"Typed text: {text}"
    
    def clear_text_field(self) -> str:
        """Clear the currently focused text field."""
        logger.info("Clearing text field")
        # Select all (Ctrl+A) and delete
        self._run_shell_command(["input", "keyevent", "123"])  # Move to end
        for _ in range(100):  # Delete up to 100 characters
            self._run_shell_command(["input", "keyevent", "67"])  # Backspace
        return "Cleared text field"
    
    # ==================== Key Event Tools ====================
    
    def press_key(self, keycode: int) -> str:
        """
        Press a specific key.
        
        Common keycodes:
        - 3: Home
        - 4: Back
        - 24: Volume Up
        - 25: Volume Down
        - 26: Power
        - 66: Enter
        - 67: Backspace
        - 82: Menu
        
        Args:
            keycode: Android keycode
            
        Returns:
            Result message
        """
        logger.info(f"Pressing key: {keycode}")
        self._run_shell_command(["input", "keyevent", str(keycode)])
        time.sleep(ACTION_DELAY)
        return f"Pressed key: {keycode}"
    
    def press_back(self) -> str:
        """Press the back button."""
        return self.press_key(4)
    
    def press_home(self) -> str:
        """Press the home button."""
        return self.press_key(3)
    
    def press_enter(self) -> str:
        """Press the enter key."""
        return self.press_key(66)
    
    def press_menu(self) -> str:
        """Press the menu button."""
        return self.press_key(82)
    
    # ==================== App Management Tools ====================
    
    def launch_app(self, package_name: str, activity: str = None) -> str:
        """
        Launch an application.
        
        Args:
            package_name: The app package name
            activity: Optional activity name
            
        Returns:
            Result message
        """
        logger.info(f"Launching app: {package_name}")
        
        if activity:
            component = f"{package_name}/{activity}"
            self._run_shell_command([
                "am", "start", "-n", component
            ])
        else:
            self._run_shell_command([
                "monkey", "-p", package_name, 
                "-c", "android.intent.category.LAUNCHER", "1"
            ])
        
        time.sleep(SCREENSHOT_DELAY)
        return f"Launched app: {package_name}"
    
    def close_app(self, package_name: str) -> str:
        """
        Force stop an application.
        
        Args:
            package_name: The app package name
            
        Returns:
            Result message
        """
        logger.info(f"Closing app: {package_name}")
        self._run_shell_command(["am", "force-stop", package_name])
        time.sleep(ACTION_DELAY)
        return f"Closed app: {package_name}"
    
    def get_current_activity(self) -> str:
        """Get the currently focused activity."""
        result = self._run_shell_command([
            "dumpsys", "activity", "activities", 
            "|", "grep", "mCurrentFocus"
        ])
        return result.strip()
    
    # ==================== Device Info Tools ====================
    
    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get the device screen size.
        
        Returns:
            Tuple of (width, height)
        """
        result = self._run_shell_command(["wm", "size"])
        # Parse "Physical size: 1344x2992"
        if "Physical size:" in result:
            size_str = result.split("Physical size:")[1].strip()
            width, height = map(int, size_str.split("x"))
            return width, height
        return SCREEN_WIDTH, SCREEN_HEIGHT
    
    def get_device_info(self) -> dict:
        """Get device information."""
        info = {
            "model": self._run_shell_command(["getprop", "ro.product.model"]).strip(),
            "android_version": self._run_shell_command(["getprop", "ro.build.version.release"]).strip(),
            "sdk_version": self._run_shell_command(["getprop", "ro.build.version.sdk"]).strip(),
        }
        return info
    
    # ==================== Utility Tools ====================
    
    def wait(self, seconds: float) -> str:
        """
        Wait for specified seconds.
        
        Args:
            seconds: Number of seconds to wait
            
        Returns:
            Result message
        """
        logger.info(f"Waiting for {seconds} seconds")
        time.sleep(seconds)
        return f"Waited for {seconds} seconds"
    
    def get_ui_hierarchy(self) -> str:
        """
        Dump the UI hierarchy (for debugging).
        
        Returns:
            UI hierarchy XML
        """
        self._run_shell_command(["uiautomator", "dump", "/sdcard/ui_dump.xml"])
        result = self._run_shell_command(["cat", "/sdcard/ui_dump.xml"])
        return result


# Create tool functions for ADK integration
def create_adb_tools(device_serial: str = None) -> dict:
    """
    Create a dictionary of ADB tool functions for agent use.
    
    Args:
        device_serial: Optional device serial
        
    Returns:
        Dictionary of tool functions
    """
    adb = ADBTools(device_serial)
    
    return {
        "take_screenshot": adb.take_screenshot,
        "get_screenshot_base64": adb.get_screenshot_base64,
        "tap": adb.tap,
        "double_tap": adb.double_tap,
        "long_press": adb.long_press,
        "swipe": adb.swipe,
        "scroll_up": adb.scroll_up,
        "scroll_down": adb.scroll_down,
        "type_text": adb.type_text,
        "clear_text_field": adb.clear_text_field,
        "press_back": adb.press_back,
        "press_home": adb.press_home,
        "press_enter": adb.press_enter,
        "press_menu": adb.press_menu,
        "launch_app": adb.launch_app,
        "close_app": adb.close_app,
        "wait": adb.wait,
    }
