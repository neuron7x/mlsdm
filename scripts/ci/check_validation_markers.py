#!/usr/bin/env python3
"""
Check that all validation test files have the @pytest.mark.validation marker.

This prevents validation tests from being accidentally included in smoke test
runs due to pytest's test discovery mechanism.
"""

import sys
from pathlib import Path


def check_validation_markers():
    """Check that all validation test files have pytestmark = pytest.mark.validation."""
    repo_root = Path(__file__).parent.parent.parent
    validation_dir = repo_root / "tests" / "validation"
    
    if not validation_dir.exists():
        print(f"✓ No validation directory found at {validation_dir}")
        return True
    
    test_files = list(validation_dir.glob("test_*.py"))
    
    if not test_files:
        print(f"✓ No test files in {validation_dir}")
        return True
    
    unmarked_files = []
    
    for test_file in test_files:
        content = test_file.read_text()
        
        # Check for pytestmark = pytest.mark.validation
        if "pytestmark = pytest.mark.validation" not in content and \
           'pytestmark = [pytest.mark.validation' not in content:
            unmarked_files.append(test_file.relative_to(repo_root))
    
    if unmarked_files:
        print("❌ VALIDATION MARKER CHECK FAILED")
        print("\nThe following validation test files are missing the validation marker:")
        for file in unmarked_files:
            print(f"  - {file}")
        print("\nAdd this line after imports in each file:")
        print("  pytestmark = pytest.mark.validation")
        print("\nThis ensures validation tests are:")
        print("  1. Excluded from smoke test runs (which have 60s budget)")
        print("  2. Run in main CI test suite")
        print("  3. Properly marked for test filtering")
        return False
    
    print(f"✓ All {len(test_files)} validation test files have proper markers")
    return True


if __name__ == "__main__":
    success = check_validation_markers()
    sys.exit(0 if success else 1)
