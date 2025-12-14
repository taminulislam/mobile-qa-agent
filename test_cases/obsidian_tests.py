"""
QA Test Cases for Obsidian Mobile App

This module defines the test cases to be executed by the multi-agent system.
Each test case includes:
- name: Unique identifier
- description: Natural language description of what to test
- expected_result: What should happen if the test passes
- should_pass: Whether the test is expected to pass or fail
"""

from dataclasses import dataclass
from typing import List
from enum import Enum


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


@dataclass
class TestCase:
    """Represents a single QA test case"""
    name: str
    description: str
    expected_result: str
    should_pass: bool
    steps: List[str] = None  # Optional detailed steps
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []


@dataclass
class TestResult:
    """Represents the result of a test execution"""
    test_case: TestCase
    status: TestStatus
    actual_result: str
    steps_executed: List[str]
    error_message: str = None
    screenshots: List[str] = None
    
    def __post_init__(self):
        if self.screenshots is None:
            self.screenshots = []
    
    @property
    def is_correct(self) -> bool:
        """Check if the test result matches expected outcome"""
        if self.test_case.should_pass:
            return self.status == TestStatus.PASSED
        else:
            return self.status == TestStatus.FAILED


# ==================== Obsidian Test Cases ====================

OBSIDIAN_PACKAGE = "md.obsidian"

# Test Case 1: Create a new Vault (Should PASS)
TEST_CREATE_VAULT = TestCase(
    name="test_create_vault",
    description="Create vault: 1) Tap purple 'Create a vault' 2) Tap purple 'Continue without sync' 3) Clear vault name field, type 'InternVault' 4) Tap purple 'Create a vault' 5) Tap blue 'USE THIS FOLDER' 6) Tap 'ALLOW'. Then verify main vault interface.",
    expected_result="Vault 'InternVault' created and main Obsidian interface visible (New tab or notes list).",
    should_pass=True,
    steps=[
        "Tap purple 'Create a vault' button",
        "Tap purple 'Continue without sync' button",
        "Tap vault name field and clear it",
        "Type 'InternVault'",
        "Tap purple 'Create a vault' button",
        "Tap blue 'USE THIS FOLDER' button",
        "Tap 'ALLOW' button",
        "Report TEST_COMPLETE when vault interface visible"
    ]
)

# Test Case 2: Create a new note (Should PASS)
TEST_CREATE_NOTE = TestCase(
    name="test_create_note",
    description="Create a new note titled 'Meeting Notes' with body text 'Daily Standup'. Steps: 1) Tap 'Create new note' or the + icon 2) Type 'Meeting Notes' as the title (first line) 3) Press Enter 4) Type 'Daily Standup' as the body content. Report TEST_COMPLETE when done.",
    expected_result="A note titled 'Meeting Notes' with body 'Daily Standup' should be created. Report TEST_COMPLETE once the text is typed.",
    should_pass=True,
    steps=[
        "Tap the 'Create new note' button or + icon in the vault interface",
        "Type 'Meeting Notes' as the note title (first line)",
        "Press Enter to move to the body",
        "Type 'Daily Standup' as the body content",
        "Report TEST_COMPLETE when text has been entered"
    ]
)

# Test Case 3: Verify Appearance tab icon color (Should FAIL)
TEST_APPEARANCE_ICON_COLOR = TestCase(
    name="test_appearance_icon_red",
    description="Verify Appearance accent color is RED. Steps: 1) Tap top-left icon (x=112, y=240) to go back to file browser 2) Tap the settings gear icon at EXACT coordinates (x=1138, y=280) - this is the purple gear in top-right 3) Tap 'Appearance' text 4) Check 'Accent color' - it is PURPLE, not RED. Report TEST_FAILED.",
    expected_result="The test should FAIL because the Appearance accent color is purple, NOT red.",
    should_pass=False,
    steps=[
        "Tap top-left icon at (x=112, y=240) to go back to file browser",
        "Tap settings gear icon at EXACT (x=1138, y=280)",
        "Tap 'Appearance' in Settings menu",
        "Look at 'Accent color' - it is PURPLE, not RED",
        "Report TEST_FAILED because accent color is NOT red"
    ]
)

# Test Case 4: Find Print to PDF button (Should FAIL)
TEST_PRINT_TO_PDF = TestCase(
    name="test_print_to_pdf",
    description="Find and click the 'Print to PDF' button in the main file menu. Steps: 1) Tap the hamburger menu (3 horizontal lines) at bottom right 2) Look through the menu options for 'Print to PDF' 3) It does NOT exist in mobile - report TEST_FAILED.",
    expected_result="The test should FAIL because 'Print to PDF' feature does not exist in the mobile version's menu.",
    should_pass=False,
    steps=[
        "Tap the hamburger menu icon (3 horizontal lines) at the bottom right of the screen",
        "Look through all menu options for 'Print to PDF'",
        "The option does NOT exist in the mobile version",
        "Report TEST_FAILED because 'Print to PDF' was not found in the menu"
    ]
)

# Test Case 5: Search functionality (Should PASS)
TEST_SEARCH_FUNCTIONALITY = TestCase(
    name="test_search_functionality",
    description="Use the search feature to search for 'Meeting' and verify search results appear.",
    expected_result="Search results should display any notes containing 'Meeting' in their title or content.",
    should_pass=True,
    steps=[
        "Ensure we have at least one note with 'Meeting' in it",
        "Find and tap the search icon",
        "Type 'Meeting' in the search field",
        "Verify that search results are displayed"
    ]
)

# Test Case 6: Toggle dark mode (Should PASS)
TEST_TOGGLE_DARK_MODE = TestCase(
    name="test_toggle_dark_mode",
    description="Go to Settings > Appearance and toggle the dark/light mode theme.",
    expected_result="The app theme should visibly change between dark and light mode.",
    should_pass=True,
    steps=[
        "Open Settings",
        "Navigate to Appearance settings",
        "Find theme or dark mode toggle",
        "Toggle the theme setting",
        "Verify the visual change in the app"
    ]
)

# Test Case 7: Non-existent plugin (Should FAIL)
TEST_NONEXISTENT_PLUGIN = TestCase(
    name="test_enable_calendar_plugin",
    description="Enable the 'Calendar View' core plugin from the settings.",
    expected_result="The test should FAIL because 'Calendar View' is not a core plugin in Obsidian mobile.",
    should_pass=False,
    steps=[
        "Open Settings",
        "Navigate to Core plugins section",
        "Look for 'Calendar View' plugin",
        "Report FAIL when plugin is not found"
    ]
)


# Collection of all test cases
ALL_TEST_CASES = [
    TEST_CREATE_VAULT,
    TEST_CREATE_NOTE,
    TEST_APPEARANCE_ICON_COLOR,
    TEST_PRINT_TO_PDF,
    TEST_SEARCH_FUNCTIONALITY,
    TEST_TOGGLE_DARK_MODE,
    TEST_NONEXISTENT_PLUGIN,
]


def get_test_case_by_name(name: str) -> TestCase:
    """Get a test case by its name."""
    for tc in ALL_TEST_CASES:
        if tc.name == name:
            return tc
    return None


def get_passing_tests() -> List[TestCase]:
    """Get all test cases that should pass."""
    return [tc for tc in ALL_TEST_CASES if tc.should_pass]


def get_failing_tests() -> List[TestCase]:
    """Get all test cases that should fail."""
    return [tc for tc in ALL_TEST_CASES if not tc.should_pass]
