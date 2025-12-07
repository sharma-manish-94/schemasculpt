#!/usr/bin/env python3
"""
Phase 1 Implementation Validation Script
Validates that all Phase 1 components are properly implemented
"""

import os
import json
import re
import sys
from pathlib import Path

def print_status(message, status="INFO"):
    colors = {
        "INFO": "\033[94m",
        "PASS": "\033[92m",
        "FAIL": "\033[91m",
        "WARN": "\033[93m"
    }
    print(f"{colors.get(status, '')}{status}: {message}\033[0m")

def check_file_exists(filepath, description):
    """Check if a file exists and report status"""
    if os.path.exists(filepath):
        print_status(f"✅ {description}: {os.path.basename(filepath)}", "PASS")
        return True
    else:
        print_status(f"❌ Missing {description}: {filepath}", "FAIL")
        return False

def check_java_file_content(filepath, patterns, description):
    """Check if Java file contains required patterns"""
    if not os.path.exists(filepath):
        print_status(f"❌ File not found: {filepath}", "FAIL")
        return False

    try:
        with open(filepath, 'r') as f:
            content = f.read()

        results = []
        for pattern_desc, pattern in patterns.items():
            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                results.append(f"✅ {pattern_desc}")
            else:
                results.append(f"❌ Missing: {pattern_desc}")

        if all("✅" in result for result in results):
            print_status(f"✅ {description}: All patterns found", "PASS")
            return True
        else:
            print_status(f"⚠️ {description}: Some issues found", "WARN")
            for result in results:
                print(f"  {result}")
            return False

    except Exception as e:
        print_status(f"❌ Error reading {filepath}: {e}", "FAIL")
        return False

def check_javascript_file_content(filepath, patterns, description):
    """Check if JavaScript file contains required patterns"""
    if not os.path.exists(filepath):
        print_status(f"❌ File not found: {filepath}", "FAIL")
        return False

    try:
        with open(filepath, 'r') as f:
            content = f.read()

        results = []
        for pattern_desc, pattern in patterns.items():
            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                results.append(f"✅ {pattern_desc}")
            else:
                results.append(f"❌ Missing: {pattern_desc}")

        if all("✅" in result for result in results):
            print_status(f"✅ {description}: All patterns found", "PASS")
            return True
        else:
            print_status(f"⚠️ {description}: Some issues found", "WARN")
            for result in results:
                print(f"  {result}")
            return False

    except Exception as e:
        print_status(f"❌ Error reading {filepath}: {e}", "FAIL")
        return False

def validate_phase1_implementation():
    """Main validation function"""
    print("🧪 Phase 1 Implementation Validation")
    print("=" * 50)

    passed_tests = 0
    total_tests = 0

    # Test 1: Check ValidationSuggestion DTO
    total_tests += 1
    validation_suggestion_patterns = {
        "Has severity field": r"String\s+severity",
        "Has category field": r"String\s+category",
        "Has explainable field": r"boolean\s+explainable",
        "Has 6-parameter constructor": r"ValidationSuggestion\([^)]*String\s+message[^)]*String\s+ruleId[^)]*String\s+severity[^)]*String\s+category[^)]*Map<String,\s*Object>\s+context[^)]*boolean\s+explainable[^)]*\)"
    }

    if check_java_file_content(
        "api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/dto/ValidationSuggestion.java",
        validation_suggestion_patterns,
        "ValidationSuggestion DTO"
    ):
        passed_tests += 1

    # Test 2: Check Explanation DTOs
    total_tests += 1
    explanation_files = [
        ("api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/dto/ExplanationRequest.java", "ExplanationRequest DTO"),
        ("api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/dto/ExplanationResponse.java", "ExplanationResponse DTO")
    ]

    explanation_success = True
    for filepath, desc in explanation_files:
        if not check_file_exists(filepath, desc):
            explanation_success = False

    if explanation_success:
        passed_tests += 1

    # Test 3: Check Hardening Service
    total_tests += 1
    hardening_patterns = {
        "OAuth2 security method": r"applyOAuth2Security",
        "Rate limiting method": r"applyRateLimiting",
        "Caching method": r"applyCaching",
        "Idempotency method": r"applyIdempotency",
        "Validation method": r"applyValidation",
        "Error handling method": r"applyErrorHandling"
    }

    if check_java_file_content(
        "api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/service/HardeningService.java",
        hardening_patterns,
        "HardeningService"
    ):
        passed_tests += 1

    # Test 4: Check AI Service endpoints
    total_tests += 1
    ai_endpoint_patterns = {
        "Explain endpoint": r"@router\.post\(\"/ai/explain\"\)",
        "Test case generation": r"@router\.post\(\"/ai/test-cases/generate\"\)",
        "Test suite generation": r"@router\.post\(\"/ai/test-suite/generate\"\)",
        "RAG integration": r"rag_service\."
    }

    if check_javascript_file_content(
        "ai_service/app/api/endpoints.py",
        ai_endpoint_patterns,
        "AI Service endpoints"
    ):
        passed_tests += 1

    # Test 5: Check Frontend ValidationSuggestion component
    total_tests += 1
    validation_ui_patterns = {
        "Why button": r"Why\?",
        "Explanation state": r"explanation.*useState",
        "Loading state": r"isLoadingExplanation",
        "Severity styling": r"getSeverityClass",
        "API call": r"explainValidationIssue"
    }

    if check_javascript_file_content(
        "ui/src/components/validation/ValidationSuggestion.js",
        validation_ui_patterns,
        "ValidationSuggestion Frontend Component"
    ):
        passed_tests += 1

    # Test 6: Check Demo Component
    total_tests += 1
    demo_patterns = {
        "Phase1Demo component": r"const Phase1Demo",
        "Why button demo": r"renderWhyButtonDemo",
        "Hardening demo": r"renderHardeningDemo",
        "Test generation demo": r"renderTestGenerationDemo",
        "Tab switching": r"activeDemo.*setActiveDemo"
    }

    if check_javascript_file_content(
        "ui/src/components/demo/Phase1Demo.js",
        demo_patterns,
        "Phase1Demo Component"
    ):
        passed_tests += 1

    # Test 7: Check Frontend API services
    total_tests += 1
    api_service_patterns = {
        "Explanation service": r"explainValidationIssue",
        "Hardening services": r"hardenOperation",
        "Test generation": r"generateTestCases",
        "OAuth2 hardening": r"addOAuth2Security",
        "Rate limiting": r"addRateLimiting"
    }

    if check_javascript_file_content(
        "ui/src/api/validationService.js",
        api_service_patterns,
        "Frontend API Services"
    ):
        passed_tests += 1

    # Test 8: Check updated linter rules use new ValidationSuggestion format
    total_tests += 1
    linter_success = True
    linter_files = [
        "api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/service/linter/MissingSummaryRule.java",
        "api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/service/linter/SecurityRequirementsRule.java",
        "api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/service/linter/MissingOperationIdRule.java"
    ]

    for linter_file in linter_files:
        if os.path.exists(linter_file):
            with open(linter_file, 'r') as f:
                content = f.read()

            # Look for ValidationSuggestion constructor calls (handle multi-line constructors)
            constructor_matches = re.findall(r'new ValidationSuggestion\s*\([^;]*?\);', content, re.MULTILINE | re.DOTALL)

            # Check if any constructor has 6 parameters (5 commas + 1)
            has_six_param_constructor = False
            for match in constructor_matches:
                # Count commas in the constructor call
                comma_count = match.count(',')
                if comma_count >= 5:  # 6 parameters = 5 commas
                    has_six_param_constructor = True
                    break

            if not has_six_param_constructor:
                print_status(f"⚠️ {os.path.basename(linter_file)}: Still using old ValidationSuggestion constructor", "WARN")
                linter_success = False
        else:
            linter_success = False

    if linter_success:
        print_status("✅ Linter Rules: Updated to new ValidationSuggestion format", "PASS")
        passed_tests += 1
    else:
        print_status("⚠️ Linter Rules: Some files need constructor updates", "WARN")

    # Summary
    print("\n" + "=" * 50)
    print(f"🧪 Validation Summary: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print_status("🎉 All Phase 1 components implemented correctly!", "PASS")
        return True
    else:
        print_status(f"⚠️ {total_tests - passed_tests} issues found - review above", "WARN")
        return False

if __name__ == "__main__":
    success = validate_phase1_implementation()
    sys.exit(0 if success else 1)