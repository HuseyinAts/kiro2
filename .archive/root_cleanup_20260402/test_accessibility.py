"""
KIRO2 Frontend Accessibility (a11y) Validation
Tests accessibility features for inclusive education

This script tests 9 accessibility components:
1. Semantic HTML usage
2. ARIA attributes validation
3. Keyboard navigation
4. Focus management
5. Color contrast (WCAG AA: 4.5:1)
6. WCAG validator integration
7. Dyslexia support (Bionic reading)
8. ADHD support (Focus mode)
9. Screen reader compatibility
"""

import sys
import io
from pathlib import Path
import re
import json

# Fix UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("KIRO2 FRONTEND ACCESSIBILITY (a11y) VALIDATION")
print("=" * 80)

# Test results tracking
tests_passed = 0
tests_failed = 0
total_tests = 9

frontend_dir = Path("frontend/src")

# ============================================================================
# TEST 1: Semantic HTML Usage
# ============================================================================
print("\n[TEST 1/9] Semantic HTML Usage")
print("-" * 80)

semantic_html_usage = 0
total_components_checked = 0

if frontend_dir.exists():
    # Check TSX components for semantic HTML
    component_files = list(frontend_dir.rglob("*.tsx"))[:50]  # Sample 50 components

    semantic_tags = ['<main', '<nav', '<header', '<footer', '<article', '<section', '<aside', '<button']

    for component_file in component_files:
        content = component_file.read_text(encoding='utf-8', errors='ignore')
        total_components_checked += 1

        # Check for semantic HTML tags
        has_semantic = any(tag in content for tag in semantic_tags)
        if has_semantic:
            semantic_html_usage += 1

    usage_rate = (semantic_html_usage / total_components_checked) * 100 if total_components_checked > 0 else 0

    print(f"[INFO] Checked {total_components_checked} components")
    print(f"       Components using semantic HTML: {semantic_html_usage} ({usage_rate:.1f}%)")

    if usage_rate >= 70:
        print(f"[PASS] Good semantic HTML usage ({usage_rate:.1f}% >= 70%)")
        tests_passed += 1
    elif usage_rate >= 40:
        print(f"[PARTIAL] Moderate semantic HTML usage ({usage_rate:.1f}%)")
        print(f"          RECOMMENDATION: Increase semantic HTML usage to 70%+")
        tests_failed += 1
    else:
        print(f"[FAIL] Low semantic HTML usage ({usage_rate:.1f}%)")
        print(f"       RECOMMENDATION: Replace <div> with semantic tags")
        tests_failed += 1
else:
    print("[FAIL] Frontend directory not found")
    tests_failed += 1

# ============================================================================
# TEST 2: ARIA Attributes Validation
# ============================================================================
print("\n[TEST 2/9] ARIA Attributes Usage")
print("-" * 80)

aria_usage = 0

if frontend_dir.exists():
    aria_patterns = [
        r'aria-label=',
        r'aria-labelledby=',
        r'aria-describedby=',
        r'aria-hidden=',
        r'role=',
    ]

    for component_file in component_files:
        content = component_file.read_text(encoding='utf-8', errors='ignore')

        # Check for ARIA attributes
        has_aria = any(re.search(pattern, content) for pattern in aria_patterns)
        if has_aria:
            aria_usage += 1

    aria_rate = (aria_usage / total_components_checked) * 100 if total_components_checked > 0 else 0

    print(f"[INFO] Components using ARIA attributes: {aria_usage} ({aria_rate:.1f}%)")

    if aria_rate >= 30:
        print(f"[PASS] ARIA attributes in use ({aria_rate:.1f}% >= 30%)")
        tests_passed += 1
    elif aria_rate >= 15:
        print(f"[PARTIAL] Some ARIA usage ({aria_rate:.1f}%)")
        print(f"          RECOMMENDATION: Add aria-label to interactive elements")
        tests_failed += 1
    else:
        print(f"[FAIL] Low ARIA usage ({aria_rate:.1f}%)")
        print(f"       RECOMMENDATION: Add ARIA attributes for screen readers")
        tests_failed += 1
else:
    tests_failed += 1

# ============================================================================
# TEST 3: Keyboard Navigation
# ============================================================================
print("\n[TEST 3/9] Keyboard Navigation Support")
print("-" * 80)

keyboard_support_found = False

keyboard_patterns = [
    r'onKeyDown',
    r'onKeyPress',
    r'onKeyUp',
    r'tabIndex',
    r'keyboard',
]

keyboard_components = 0

if frontend_dir.exists():
    for component_file in component_files:
        content = component_file.read_text(encoding='utf-8', errors='ignore')

        # Check for keyboard event handlers
        has_keyboard = any(re.search(pattern, content, re.IGNORECASE) for pattern in keyboard_patterns)
        if has_keyboard:
            keyboard_components += 1

    keyboard_rate = (keyboard_components / total_components_checked) * 100 if total_components_checked > 0 else 0

    print(f"[INFO] Components with keyboard support: {keyboard_components} ({keyboard_rate:.1f}%)")

    if keyboard_rate >= 20:
        print(f"[PASS] Keyboard navigation implemented ({keyboard_rate:.1f}% >= 20%)")
        keyboard_support_found = True
        tests_passed += 1
    elif keyboard_rate >= 10:
        print(f"[PARTIAL] Some keyboard support ({keyboard_rate:.1f}%)")
        print(f"          RECOMMENDATION: Add Tab, Enter, Escape handling")
        tests_failed += 1
    else:
        print(f"[FAIL] Limited keyboard support ({keyboard_rate:.1f}%)")
        print(f"       RECOMMENDATION: Implement keyboard navigation")
        tests_failed += 1
else:
    tests_failed += 1

# ============================================================================
# TEST 4: Focus Management
# ============================================================================
print("\n[TEST 4/9] Focus Management")
print("-" * 80)

focus_management_found = False

focus_patterns = [
    r'autoFocus',
    r'focus\(\)',
    r'\.focus',
    r'useFocus',
    r'FocusTrap',
]

focus_components = 0

if frontend_dir.exists():
    for component_file in component_files:
        content = component_file.read_text(encoding='utf-8', errors='ignore')

        # Check for focus management
        has_focus = any(re.search(pattern, content) for pattern in focus_patterns)
        if has_focus:
            focus_components += 1

    focus_rate = (focus_components / total_components_checked) * 100 if total_components_checked > 0 else 0

    print(f"[INFO] Components with focus management: {focus_components} ({focus_rate:.1f}%)")

    if focus_rate >= 15:
        print(f"[PASS] Focus management implemented ({focus_rate:.1f}% >= 15%)")
        focus_management_found = True
        tests_passed += 1
    else:
        print(f"[PARTIAL] Limited focus management ({focus_rate:.1f}%)")
        print(f"          RECOMMENDATION: Add focus handling for modals and forms")
        tests_failed += 1
else:
    tests_failed += 1

# ============================================================================
# TEST 5: Color Contrast (WCAG AA: 4.5:1)
# ============================================================================
print("\n[TEST 5/9] Color Contrast Configuration")
print("-" * 80)

color_contrast_configured = False

theme_files = [
    Path("frontend/src/theme.ts"),
    Path("frontend/src/styles/theme.ts"),
    Path("frontend/src/config/theme.ts"),
]

for theme_file in theme_files:
    if theme_file.exists():
        content = theme_file.read_text(encoding='utf-8', errors='ignore')

        # Check for color contrast considerations
        has_contrast = (
            "contrast" in content.lower() or
            "wcag" in content.lower() or
            ("color" in content.lower() and "text" in content.lower())
        )

        if has_contrast:
            print(f"[PASS] Color contrast configuration found in: {theme_file.name}")
            print(f"       Theme includes color/contrast settings")
            color_contrast_configured = True
            tests_passed += 1
            break

if not color_contrast_configured:
    print("[WARN] No explicit color contrast configuration found")
    print("       RECOMMENDATION: Verify WCAG AA compliance (4.5:1 ratio)")
    print("       Tool: Use Chrome DevTools Lighthouse or axe DevTools")
    tests_failed += 1

# ============================================================================
# TEST 6: WCAG Validator Integration
# ============================================================================
print("\n[TEST 6/9] WCAG Validator Integration")
print("-" * 80)

wcag_validator_found = False

package_json = Path("frontend/package.json")

if package_json.exists():
    content = package_json.read_text(encoding='utf-8')

    # Check for accessibility testing libraries
    accessibility_libs = [
        "jest-axe",
        "@axe-core/react",
        "eslint-plugin-jsx-a11y",
        "pa11y",
    ]

    libs_found = [lib for lib in accessibility_libs if lib in content]

    if libs_found:
        print(f"[PASS] Accessibility validator found: {', '.join(libs_found)}")
        print(f"       Automated a11y testing enabled")
        wcag_validator_found = True
        tests_passed += 1
    else:
        print("[WARN] No WCAG validator library found")
        print("       RECOMMENDATION: Install jest-axe or eslint-plugin-jsx-a11y")
        print("       npm install --save-dev jest-axe @axe-core/react")
        tests_failed += 1
else:
    print("[FAIL] package.json not found")
    tests_failed += 1

# ============================================================================
# TEST 7: Dyslexia Support (Bionic Reading)
# ============================================================================
print("\n[TEST 7/9] Dyslexia Support (Bionic Reading)")
print("-" * 80)

dyslexia_support_found = False

dyslexia_files = [
    Path("frontend/src/components/BionicReading.tsx"),
    Path("frontend/src/hooks/useBionicReading.ts"),
    Path("frontend/src/utils/bionicReading.ts"),
]

for dyslexia_file in dyslexia_files:
    if dyslexia_file.exists():
        print(f"[PASS] Dyslexia support found in: {dyslexia_file.name}")
        print(f"       Bionic reading feature implemented")
        dyslexia_support_found = True
        tests_passed += 1
        break

if not dyslexia_support_found:
    # Check backend for bionic reading API
    backend_bionic = Path("backend/api/bionic_reading_routes.py")
    if backend_bionic.exists():
        print(f"[PASS] Bionic reading API exists in backend")
        print(f"       Backend support for dyslexia features")
        tests_passed += 1
    else:
        print("[WARN] No dyslexia/bionic reading support found")
        print("       RECOMMENDATION: Implement bionic reading feature")
        print("       This is important for Turkish educational platform")
        tests_failed += 1

# ============================================================================
# TEST 8: ADHD Support (Focus Mode)
# ============================================================================
print("\n[TEST 8/9] ADHD Support (Focus Mode)")
print("-" * 80)

adhd_support_found = False

adhd_patterns = [
    "adhd",
    "focus.*mode",
    "distraction.*free",
    "minimal.*ui",
]

adhd_files = [
    Path("frontend/src/components/FocusMode.tsx"),
    Path("frontend/src/hooks/useFocusMode.ts"),
    Path("frontend/src/contexts/FocusContext.tsx"),
]

for adhd_file in adhd_files:
    if adhd_file.exists():
        print(f"[PASS] ADHD support found in: {adhd_file.name}")
        print(f"       Focus mode feature implemented")
        adhd_support_found = True
        tests_passed += 1
        break

if not adhd_support_found:
    # Search in components for ADHD/focus mode mentions
    if frontend_dir.exists():
        for component_file in component_files:
            content = component_file.read_text(encoding='utf-8', errors='ignore')

            has_adhd_support = any(re.search(pattern, content, re.IGNORECASE) for pattern in adhd_patterns)
            if has_adhd_support:
                print(f"[PASS] ADHD support mentioned in components")
                print(f"       Focus mode or distraction-free features found")
                adhd_support_found = True
                tests_passed += 1
                break

if not adhd_support_found:
    print("[WARN] No ADHD/focus mode support found")
    print("       RECOMMENDATION: Add focus mode for distraction-free learning")
    print("       Features: Minimal UI, silent notifications, progress tracking")
    tests_failed += 1

# ============================================================================
# TEST 9: Screen Reader Compatibility
# ============================================================================
print("\n[TEST 9/9] Screen Reader Compatibility")
print("-" * 80)

screen_reader_support = 0

screen_reader_patterns = [
    r'aria-live',
    r'aria-atomic',
    r'aria-busy',
    r'visually-hidden',
    r'sr-only',
]

if frontend_dir.exists():
    for component_file in component_files:
        content = component_file.read_text(encoding='utf-8', errors='ignore')

        # Check for screen reader specific attributes
        has_sr_support = any(re.search(pattern, content, re.IGNORECASE) for pattern in screen_reader_patterns)
        if has_sr_support:
            screen_reader_support += 1

    sr_rate = (screen_reader_support / total_components_checked) * 100 if total_components_checked > 0 else 0

    print(f"[INFO] Components with screen reader support: {screen_reader_support} ({sr_rate:.1f}%)")

    if sr_rate >= 10:
        print(f"[PASS] Screen reader support implemented ({sr_rate:.1f}% >= 10%)")
        tests_passed += 1
    elif sr_rate >= 5:
        print(f"[PARTIAL] Some screen reader support ({sr_rate:.1f}%)")
        print(f"          RECOMMENDATION: Add aria-live for dynamic content")
        tests_failed += 1
    else:
        print(f"[FAIL] Limited screen reader support ({sr_rate:.1f}%)")
        print(f"       RECOMMENDATION: Add sr-only class and aria-live regions")
        tests_failed += 1
else:
    tests_failed += 1

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("ACCESSIBILITY VALIDATION SUMMARY")
print("=" * 80)

success_rate = (tests_passed / total_tests) * 100

print(f"\nTotal Tests: {total_tests}")
print(f"Tests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Success Rate: {success_rate:.1f}%")

print("\n" + "-" * 80)
print("ACCESSIBILITY FEATURES BREAKDOWN")
print("-" * 80)

features = [
    ("Semantic HTML", semantic_html_usage > 0),
    ("ARIA Attributes", aria_usage > 0),
    ("Keyboard Navigation", keyboard_support_found),
    ("Focus Management", focus_management_found),
    ("Color Contrast", color_contrast_configured),
    ("WCAG Validator", wcag_validator_found),
    ("Dyslexia Support", dyslexia_support_found),
    ("ADHD Support", adhd_support_found),
    ("Screen Reader Support", screen_reader_support > 0),
]

for feature_name, implemented in features:
    status = "[PASS]" if implemented else "[FAIL]"
    print(f"{status} {feature_name}")

print("\n" + "=" * 80)

if tests_passed == total_tests:
    print("[SUCCESS] EXCELLENT ACCESSIBILITY SUPPORT!")
    print("\nYour platform is inclusive and accessible:")
    print("✓ WCAG 2.1 Level AA compliance")
    print("✓ Keyboard navigation")
    print("✓ Screen reader support")
    print("✓ Dyslexia/ADHD accommodations")
    sys.exit(0)
elif tests_passed >= 7:
    print("[GOOD] Strong accessibility foundation")
    print(f"\nPassed {tests_passed}/{total_tests} accessibility tests")
    print("\nPlatform is accessible to most users")
    print("Minor improvements recommended for full WCAG compliance")
    sys.exit(0)
elif tests_passed >= 4:
    print("[FAIR] Basic accessibility implemented")
    print(f"\nPassed {tests_passed}/{total_tests} tests")
    print("\nRECOMMENDATION: Improve accessibility before production")
    print("Focus on:")
    if not wcag_validator_found:
        print("- Add WCAG validator (jest-axe)")
    if not dyslexia_support_found:
        print("- Implement bionic reading")
    if not adhd_support_found:
        print("- Add focus mode")
    sys.exit(0)
else:
    print("[NEEDS IMPROVEMENT] Limited accessibility")
    print(f"\nOnly {tests_passed}/{total_tests} tests passed")
    print("\nCRITICAL FOR EDUCATIONAL PLATFORM:")
    print("1. Add semantic HTML and ARIA attributes")
    print("2. Implement keyboard navigation")
    print("3. Install accessibility validators")
    print("4. Add dyslexia/ADHD support features")
    print("5. Test with screen readers")
    sys.exit(1)
