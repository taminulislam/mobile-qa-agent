"""
Planner Agent for Mobile QA Multi-Agent System

The Planner Agent is responsible for:
1. Analyzing the current screen state (screenshot)
2. Understanding the test case requirements
3. Deciding what action to take next
4. Breaking down complex tasks into actionable steps
"""

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
import google.generativeai as genai
from config.settings import GOOGLE_API_KEY, MODEL_NAME
from utils.logger import setup_logger
import base64
import json
import time
import re

logger = setup_logger("PlannerAgent")

# Rate limiting configuration
API_CALL_DELAY = 3  # 3 seconds between calls (ensures < 20 req/min)
MAX_RETRIES = 2     # Fewer retries needed since we won't hit limits often
INITIAL_RETRY_DELAY = 5  # Short retry if somehow rate limited

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

PLANNER_SYSTEM_PROMPT = """You are a Mobile QA Test Planner Agent. Your role is to analyze the current screen state of an Android mobile app and decide what action to take next to complete the given test case.

## Your Responsibilities:
1. Analyze the screenshot to understand the current UI state
2. Determine what elements are visible and interactive
3. Decide the next logical action to progress the test
4. Identify if the test goal has been achieved or if it's impossible

## Available Actions:
You must respond with ONE of these actions in JSON format:

1. TAP: Tap on a specific location
   {"action": "tap", "x": <int>, "y": <int>, "description": "<what you're tapping>"}

2. TYPE: Type text into a focused field
   {"action": "type_text", "text": "<text to type>", "description": "<what field>"}

3. SWIPE: Swipe/scroll the screen
   {"action": "swipe", "start_x": <int>, "start_y": <int>, "end_x": <int>, "end_y": <int>, "description": "<why swiping>"}

4. PRESS_BACK: Press the back button
   {"action": "press_back", "description": "<why pressing back>"}

5. PRESS_HOME: Press the home button
   {"action": "press_home", "description": "<why pressing home>"}

6. PRESS_ENTER: Press enter key
   {"action": "press_enter", "description": "<why pressing enter>"}

7. LAUNCH_APP: Launch an application
   {"action": "launch_app", "package_name": "<package>", "description": "<app name>"}

8. WAIT: Wait for UI to update
   {"action": "wait", "seconds": <float>, "description": "<what waiting for>"}

9. SCROLL_UP: Scroll up to see more content
   {"action": "scroll_up", "description": "<why scrolling up>"}

10. SCROLL_DOWN: Scroll down to see more content
    {"action": "scroll_down", "description": "<why scrolling down>"}

11. TEST_COMPLETE: The test objective has been achieved
    {"action": "test_complete", "result": "pass", "description": "<what was verified>"}

12. TEST_FAILED: The test has failed (element not found, wrong state, etc.)
    {"action": "test_failed", "result": "fail", "reason": "<why it failed>", "description": "<what went wrong>"}

13. TAP_BY_TEXT: Tap an element by its visible text (MOST RELIABLE for buttons - USE THIS FIRST!)
    {"action": "tap_by_text", "text": "<exact button text>", "description": "<what you're tapping>"}
    Examples: {"action": "tap_by_text", "text": "ALLOW", "description": "Tap ALLOW button"}
              {"action": "tap_by_text", "text": "Create a vault", "description": "Tap Create a vault button"}
              {"action": "tap_by_text", "text": "USE THIS FOLDER", "description": "Tap USE THIS FOLDER button"}

14. TAP_BY_HINT: Tap an input field by its placeholder/hint text (for text fields)
    {"action": "tap_by_hint", "hint": "<hint text>", "description": "<what field you're tapping>"}
    Example: {"action": "tap_by_hint", "hint": "My vault", "description": "Tap vault name input field"}

## Screen Coordinate Guidelines:
- Screen resolution: 1344 x 2992 pixels (Pixel 8 Pro)
- IMPORTANT: The screenshot shows the FULL screen. Estimate coordinates by percentage:
  - If button is 25% from top: y = 0.25 * 2992 = 748
  - If button is 40% from top: y = 0.40 * 2992 = 1197
  - If button is 50% from top: y = 0.50 * 2992 = 1496
  - If button is 60% from top: y = 0.60 * 2992 = 1795
- Horizontal center: x = 672 (half of 1344)
- For buttons in the middle-upper area (like "Create a vault" on welcome screen): y ≈ 1200-1400
- For buttons near bottom: y ≈ 2200-2600
- Always aim for the CENTER of buttons

## Important Rules:
1. PREFER TAP_BY_TEXT over TAP for buttons - it finds elements by text and is much more reliable
2. Use TAP_BY_TEXT for buttons like "ALLOW", "CANCEL", "Create a vault", "USE THIS FOLDER", "Appearance", etc.
3. Only use TAP with coordinates when the element has no visible text or TAP_BY_TEXT fails
4. Always analyze the screenshot CAREFULLY before deciding
5. If you tap wrong and end up on an unexpected screen, use PRESS_BACK to go back
6. If you can't find an element, try scrolling before giving up
7. If an element doesn't exist after thorough search, report TEST_FAILED
8. Provide clear descriptions for every action
9. Only report TEST_COMPLETE when you have VERIFIED the expected outcome
10. If screen looks wrong for current step, PRESS_BACK immediately

## Test-Specific Guidelines:
- For "should FAIL" tests: You MUST report TEST_FAILED when the expected element/feature is NOT found
- For color verification tests: Report TEST_FAILED if the color doesn't match (e.g., "Appearance accent color is purple, not red")
- For "Print to PDF" test: Look through the menu, and report TEST_FAILED because it doesn't exist on mobile
- For note creation: Type the exact title/content specified in the test description
- To navigate to Settings from note view: Tap the top-left icon to go back, then tap the gear icon in the vault view
- If you see 'InternVault' text, look for a gear/settings icon near it - tap x~570, y~140 area

Respond ONLY with valid JSON. No additional text or explanation outside the JSON.
"""


class PlannerAgent:
    """
    Planner Agent that analyzes screenshots and decides next actions.
    Includes rate limiting and retry logic for API quota management.
    """
    
    def __init__(self):
        """Initialize the Planner Agent."""
        self.model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=PLANNER_SYSTEM_PROMPT
        )
        self.history = []
        self.last_api_call_time = 0  # Track last API call for rate limiting
        logger.info("PlannerAgent initialized")
    
    def _wait_for_rate_limit(self):
        """Wait between API calls for smooth execution."""
        elapsed = time.time() - self.last_api_call_time
        if elapsed < API_CALL_DELAY:
            wait_time = API_CALL_DELAY - elapsed
            time.sleep(wait_time)
    
    def _extract_retry_delay(self, error_message: str) -> float:
        """Extract retry delay from error message if present."""
        # Try to extract "retry in Xs" or "retry_delay { seconds: X }"
        match = re.search(r'retry in (\d+\.?\d*)s', str(error_message))
        if match:
            return float(match.group(1)) + 1  # Add small buffer
        
        # Try to extract from "seconds: X" format
        match = re.search(r'seconds:\s*(\d+)', str(error_message))
        if match:
            return float(match.group(1)) + 1
        
        return INITIAL_RETRY_DELAY
    
    def analyze_and_plan(
        self, 
        screenshot_base64: str, 
        test_description: str,
        expected_result: str,
        should_pass: bool,
        previous_actions: list = None,
        current_step: int = 1,
        max_steps: int = 20
    ) -> dict:
        """
        Analyze the current screen and plan the next action.
        
        Args:
            screenshot_base64: Base64 encoded screenshot
            test_description: The test case description
            expected_result: Expected outcome of the test
            should_pass: Whether the test is expected to pass
            previous_actions: List of previously executed actions
            current_step: Current step number
            max_steps: Maximum allowed steps
            
        Returns:
            Dictionary containing the planned action
        """
        logger.info(f"Planning step {current_step}/{max_steps}")
        
        # Build context message
        context = f"""
## Current Test Case:
**Description:** {test_description}
**Expected Result:** {expected_result}
**Should Pass:** {"Yes" if should_pass else "No (this test is expected to FAIL - look for missing/wrong elements)"}

## Progress:
- Current Step: {current_step} of {max_steps}
- Previous Actions: {json.dumps(previous_actions or [], indent=2)}

## Task:
Analyze the screenshot and decide the next action to progress this test.
If the test expects to FAIL (should_pass=No), you should look for the element/feature that is supposed to be missing or incorrect, and report TEST_FAILED when you confirm it's not there.

What is your next action? Respond with JSON only.
"""
        
        # Create the image part
        image_part = {
            "mime_type": "image/png",
            "data": screenshot_base64
        }
        
        # Retry loop with exponential backoff for rate limiting
        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                # Wait for rate limit before making API call
                self._wait_for_rate_limit()
                
                # Record the API call time
                self.last_api_call_time = time.time()
                
                # Generate response
                response = self.model.generate_content([
                    context,
                    image_part
                ])
                
                response_text = response.text.strip()
                logger.debug(f"Raw planner response: {response_text}")
                
                # Parse JSON response
                # Handle potential markdown code blocks
                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                    response_text = response_text.strip()
                
                action = json.loads(response_text)
                logger.info(f"Planned action: {action.get('action')} - {action.get('description', '')}")
                
                return action
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse planner response as JSON: {e}")
                logger.error(f"Response was: {response_text}")
                # Return a safe default action
                return {
                    "action": "wait",
                    "seconds": 1,
                    "description": "Waiting due to planning error, will retry"
                }
            except Exception as e:
                error_str = str(e)
                last_error = e
                
                # Check if it's a rate limit error (429)
                if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                    if attempt < MAX_RETRIES:
                        retry_delay = self._extract_retry_delay(error_str)
                        logger.warning(f"Rate limit hit (attempt {attempt + 1}/{MAX_RETRIES + 1}). Waiting {retry_delay:.1f}s before retry...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {MAX_RETRIES + 1} attempts")
                else:
                    # Non-rate-limit error, don't retry
                    logger.error(f"Planner error: {e}")
                    break
        
        # All retries exhausted or non-retryable error
        return {
            "action": "test_failed",
            "result": "fail",
            "reason": f"Planner error after retries: {str(last_error)}",
            "description": "Internal planner error"
        }
    
    def reset(self):
        """Reset the planner state for a new test."""
        self.history = []
        logger.info("PlannerAgent reset")
