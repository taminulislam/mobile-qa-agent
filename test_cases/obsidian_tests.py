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

# Test Case 1: Verify Vault exists and enter it (Should PASS)
TEST_CREATE_VAULT = TestCase(
    name="test_create_vault",
    description="Open Obsidian, verify that a vault named 'InternVault' exists, and enter the vault to view its contents.",
    expected_result="The vault 'InternVault' should be accessible and the user should be inside the vault viewing its contents or empty vault screen.",
    should_pass=True,
    steps=[
        "Launch Obsidian app",
        "Look for 'InternVault' in the vault list or verify we are already inside it",
        "If vault list is shown, tap on 'InternVault' to enter it",
        "Verify that we are inside the vault (seeing notes list or empty vault)",
        "Report TEST_COMPLETE when inside the vault"
    ]
)

# Test Case 2: Create a new note (Should PASS)
TEST_CREATE_NOTE = TestCase(
    name="test_create_note",
    description="Create a new note titled 'Meeting Notes' and type the text 'Daily Standup' into the body.",
    expected_result="A new note titled 'Meeting Notes' should exist with 'Daily Standup' as its content.",
    should_pass=True,
    steps=[
        "Ensure we are inside a vault",
        "Look for new note button (usually '+' or 'New note')",
        "Tap to create new note",
        "Enter 'Meeting Notes' as the title",
        "Tap on the note body area",
        "Type 'Daily Standup'",
        "Verify the note content is visible"
    ]
)

# Test Case 3: Verify Appearance tab icon color (Should FAIL)
TEST_APPEARANCE_ICON_COLOR = TestCase(
    name="test_appearance_icon_red",
    description="Go to Settings and verify that the 'Appearance' tab icon is the color Red.",
    expected_result="The test should FAIL because the Appearance icon is monochrome/default theme color, NOT red.",
    should_pass=False,
    steps=[
        "Open Obsidian settings (gear icon or menu)",
        "Navigate to Settings",
        "Look for 'Appearance' option",
        "Examine the icon color of the Appearance tab",
        "Verify if the icon is RED colored",
        "Report FAIL because the icon is NOT red (it's monochrome)"
    ]
)

# Test Case 4: Find Print to PDF button (Should FAIL)
TEST_PRINT_TO_PDF = TestCase(
    name="test_print_to_pdf",
    description="Find and click the 'Print to PDF' button in the main file menu.",
    expected_result="The test should FAIL because 'Print to PDF' feature does not exist in the mobile version.",
    should_pass=False,
    steps=[
        "Open the main menu or file menu",
        "Look for 'Print to PDF' option",
        "Search through all available menu items",
        "Report FAIL when 'Print to PDF' is not found"
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
