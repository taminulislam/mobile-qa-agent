"""
ADB Tools for Android Emulator Interaction

This module provides tools for interacting with the Android emulator
using ADB (Android Debug Bridge) commands.
"""

import subprocess
import base64
import time
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Tuple, Dict, List
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
    
    # ==================== UI Automator Tools ====================
    
    def _get_ui_xml(self) -> str:
        """
        Dump UI hierarchy and return as XML string.
        
        Returns:
            UI hierarchy XML string
        """
        self._run_shell_command(["uiautomator", "dump", "/sdcard/ui_dump.xml"])
        result = self._run_shell_command(["cat", "/sdcard/ui_dump.xml"])
        return result
    
    def _parse_bounds(self, bounds_str: str) -> Tuple[int, int, int, int]:
        """
        Parse bounds string like "[0,0][1344,2992]" into (x1, y1, x2, y2).
        
        Args:
            bounds_str: Bounds string in format "[x1,y1][x2,y2]"
            
        Returns:
            Tuple of (x1, y1, x2, y2)
        """
        match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
        if len(match) == 2:
            x1, y1 = int(match[0][0]), int(match[0][1])
            x2, y2 = int(match[1][0]), int(match[1][1])
            return x1, y1, x2, y2
        raise ValueError(f"Could not parse bounds: {bounds_str}")
    
    def _get_center(self, bounds: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """
        Calculate center coordinates from bounds.
        
        Args:
            bounds: Tuple of (x1, y1, x2, y2)
            
        Returns:
            Tuple of (center_x, center_y)
        """
        x1, y1, x2, y2 = bounds
        return (x1 + x2) // 2, (y1 + y2) // 2
    
    def find_element_by_text(self, text: str) -> Optional[Dict]:
        """
        Find element by exact text match using UI Automator.
        
        Args:
            text: Exact text to search for
            
        Returns:
            Dict with element info (bounds, center_x, center_y) or None if not found
        """
        logger.info(f"Finding element by text: '{text}'")
        xml_str = self._get_ui_xml()
        
        # Search for node elements with matching text and bounds attributes
        # The attributes may not be adjacent, so we need to match the whole node
        node_pattern = r'<node[^>]+text="([^"]*)"[^>]+bounds="(\[[^\]]+\]\[[^\]]+\])"[^>]*/?>|<node[^>]+bounds="(\[[^\]]+\]\[[^\]]+\])"[^>]+text="([^"]*)"[^>]*/?>'
        
        for match in re.finditer(node_pattern, xml_str):
            # Handle both orderings of text and bounds attributes
            if match.group(1) is not None:
                found_text = match.group(1)
                bounds_str = match.group(2)
            else:
                found_text = match.group(4)
                bounds_str = match.group(3)
            
            if found_text == text:
                try:
                    bounds = self._parse_bounds(bounds_str)
                    center_x, center_y = self._get_center(bounds)
                    logger.info(f"Found element '{text}' at center ({center_x}, {center_y})")
                    return {
                        "text": text,
                        "bounds": bounds,
                        "bounds_str": bounds_str,
                        "center_x": center_x,
                        "center_y": center_y
                    }
                except ValueError as e:
                    logger.warning(f"Failed to parse bounds: {e}")
        
        logger.warning(f"Element with text '{text}' not found")
        return None
    
    def find_element_by_text_contains(self, text: str) -> Optional[Dict]:
        """
        Find element by partial text match using UI Automator.
        
        Args:
            text: Partial text to search for
            
        Returns:
            Dict with element info (bounds, center_x, center_y) or None if not found
        """
        logger.info(f"Finding element containing text: '{text}'")
        xml_str = self._get_ui_xml()
        
        # Search for node elements with text containing search string
        node_pattern = r'<node[^>]+text="([^"]*)"[^>]+bounds="(\[[^\]]+\]\[[^\]]+\])"[^>]*/?>|<node[^>]+bounds="(\[[^\]]+\]\[[^\]]+\])"[^>]+text="([^"]*)"[^>]*/?>'
        
        for match in re.finditer(node_pattern, xml_str):
            # Handle both orderings of text and bounds attributes
            if match.group(1) is not None:
                found_text = match.group(1)
                bounds_str = match.group(2)
            else:
                found_text = match.group(4)
                bounds_str = match.group(3)
            
            if found_text and text.lower() in found_text.lower():
                try:
                    bounds = self._parse_bounds(bounds_str)
                    center_x, center_y = self._get_center(bounds)
                    logger.info(f"Found element '{found_text}' at center ({center_x}, {center_y})")
                    return {
                        "text": found_text,
                        "bounds": bounds,
                        "bounds_str": bounds_str,
                        "center_x": center_x,
                        "center_y": center_y
                    }
                except ValueError as e:
                    logger.warning(f"Failed to parse bounds: {e}")
        
        logger.warning(f"Element containing text '{text}' not found")
        return None
    
    def find_element_by_resource_id(self, resource_id: str) -> Optional[Dict]:
        """
        Find element by resource-id using UI Automator.
        
        Args:
            resource_id: Resource ID to search for (can be partial)
            
        Returns:
            Dict with element info or None if not found
        """
        logger.info(f"Finding element by resource-id: '{resource_id}'")
        xml_str = self._get_ui_xml()
        
        # Search for node elements with matching resource-id
        node_pattern = r'<node[^>]+resource-id="([^"]*)"[^>]+bounds="(\[[^\]]+\]\[[^\]]+\])"[^>]*/?>|<node[^>]+bounds="(\[[^\]]+\]\[[^\]]+\])"[^>]+resource-id="([^"]*)"[^>]*/?>'
        
        for match in re.finditer(node_pattern, xml_str):
            if match.group(1) is not None:
                found_id = match.group(1)
                bounds_str = match.group(2)
            else:
                found_id = match.group(4)
                bounds_str = match.group(3)
            
            if found_id and resource_id in found_id:
                try:
                    bounds = self._parse_bounds(bounds_str)
                    center_x, center_y = self._get_center(bounds)
                    logger.info(f"Found element with id '{found_id}' at center ({center_x}, {center_y})")
                    return {
                        "resource_id": found_id,
                        "bounds": bounds,
                        "bounds_str": bounds_str,
                        "center_x": center_x,
                        "center_y": center_y
                    }
                except ValueError as e:
                    logger.warning(f"Failed to parse bounds: {e}")
        
        logger.warning(f"Element with resource-id '{resource_id}' not found")
        return None
    
    def tap_element_by_text(self, text: str, exact_match: bool = True) -> str:
        """
        Find element by text and tap its center.
        
        Args:
            text: Text to search for
            exact_match: If True, requires exact match; if False, partial match
            
        Returns:
            Result message
        """
        if exact_match:
            element = self.find_element_by_text(text)
        else:
            element = self.find_element_by_text_contains(text)
        
        if element:
            return self.tap(element["center_x"], element["center_y"])
        else:
            error_msg = f"Could not find element with text '{text}'"
            logger.error(error_msg)
            return error_msg
    
    def tap_element_by_text_contains(self, text: str) -> str:
        """
        Find element by partial text match and tap its center.
        
        Args:
            text: Partial text to search for
            
        Returns:
            Result message
        """
        element = self.find_element_by_text_contains(text)
        
        if element:
            return self.tap(element["center_x"], element["center_y"])
        else:
            error_msg = f"Could not find element containing text '{text}'"
            logger.error(error_msg)
            return error_msg
    
    def find_element_by_hint(self, hint: str) -> Optional[Dict]:
        """
        Find element by hint (placeholder) text using UI Automator.
        
        Args:
            hint: Hint text to search for
            
        Returns:
            Dict with element info or None if not found
        """
        logger.info(f"Finding element by hint: '{hint}'")
        xml_str = self._get_ui_xml()
        
        # Search for node elements with matching hint
        node_pattern = r'<node[^>]+hint="([^"]*)"[^>]+bounds="(\[[^\]]+\]\[[^\]]+\])"[^>]*/?>|<node[^>]+bounds="(\[[^\]]+\]\[[^\]]+\])"[^>]+hint="([^"]*)"[^>]*/?>'
        
        for match in re.finditer(node_pattern, xml_str):
            if match.group(1) is not None:
                found_hint = match.group(1)
                bounds_str = match.group(2)
            else:
                found_hint = match.group(4)
                bounds_str = match.group(3)
            
            if found_hint and hint.lower() in found_hint.lower():
                try:
                    bounds = self._parse_bounds(bounds_str)
                    center_x, center_y = self._get_center(bounds)
                    logger.info(f"Found element with hint '{found_hint}' at center ({center_x}, {center_y})")
                    return {
                        "hint": found_hint,
                        "bounds": bounds,
                        "bounds_str": bounds_str,
                        "center_x": center_x,
                        "center_y": center_y
                    }
                except ValueError as e:
                    logger.warning(f"Failed to parse bounds: {e}")
        
        logger.warning(f"Element with hint '{hint}' not found")
        return None
    
    def tap_element_by_hint(self, hint: str) -> str:
        """
        Find element by hint and tap its center.
        
        Args:
            hint: Hint text to search for
            
        Returns:
            Result message
        """
        element = self.find_element_by_hint(hint)
        
        if element:
            return self.tap(element["center_x"], element["center_y"])
        else:
            error_msg = f"Could not find element with hint '{hint}'"
            logger.error(error_msg)
            return error_msg
    
    def tap_element_by_resource_id(self, resource_id: str) -> str:
        """
        Find element by resource-id and tap its center.
        
        Args:
            resource_id: Resource ID to search for
            
        Returns:
            Result message
        """
        element = self.find_element_by_resource_id(resource_id)
        
        if element:
            return self.tap(element["center_x"], element["center_y"])
        else:
            error_msg = f"Could not find element with resource-id '{resource_id}'"
            logger.error(error_msg)
            return error_msg


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
        # UI Automator tools
        "find_element_by_text": adb.find_element_by_text,
        "find_element_by_text_contains": adb.find_element_by_text_contains,
        "find_element_by_resource_id": adb.find_element_by_resource_id,
        "tap_element_by_text": adb.tap_element_by_text,
        "tap_element_by_resource_id": adb.tap_element_by_resource_id,
    }
