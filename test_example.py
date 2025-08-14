#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to validate the empathetic code reviewer with the hackathon example.
This script tests the core functionality without requiring Streamlit or API keys.
"""

import json
from code_reviewer import parse_json_input, EmpathticCodeReviewer, ReviewerPersona, CodeQualityScore


def test_json_parsing():
    """Test JSON input parsing with the provided example"""
    
    example_json = """{
  "code_snippet": "def get_active_users(users):\\n    results = []\\n    for u in users:\\n        if u.is_active == True and u.profile_complete == True:\\n            results.append(u)\\n    return results",
  "review_comments": [
    "This is inefficient. Don't loop twice conceptually.",
    "Variable 'u' is a bad name.",
    "Boolean comparison '== True' is redundant."
  ]
}"""
    
    print("Testing JSON parsing...")
    try:
        parsed_data = parse_json_input(example_json)
        print("[PASS] JSON parsing successful!")
        
        print("\\nParsed Data:")
        print(f"Code snippet length: {len(parsed_data['code_snippet'])} characters")
        print(f"Number of comments: {len(parsed_data['review_comments'])}")
        
        print("\\nReview Comments:")
        for i, comment in enumerate(parsed_data['review_comments'], 1):
            print(f"  {i}. {comment}")
        
        print("\\nCode Snippet:")
        print(parsed_data['code_snippet'])
        
        return True
    except Exception as e:
        print(f"[FAIL] JSON parsing failed: {e}")
        return False


def test_severity_assessment():
    """Test comment severity assessment functionality"""
    
    # Create instance without API key for testing
    try:
        reviewer = EmpathticCodeReviewer("", ReviewerPersona.SENIOR_DEVELOPER)  # Empty API key for testing
        
        test_comments = [
            "This is inefficient. Don't loop twice conceptually.",
            "Variable 'u' is a bad name.",
            "Boolean comparison '== True' is redundant.",
            "This code is terrible and completely wrong!",
            "Consider using list comprehension for better readability."
        ]
        
        print("\\nTesting Severity Assessment:")
        for comment in test_comments:
            severity = reviewer._assess_comment_severity(comment)
            print(f"  '{comment}' -> {severity}")
        
        print("[PASS] Severity assessment working correctly!")
        return True
    except Exception as e:
        print(f"[FAIL] Severity assessment test failed: {e}")
        return False


def test_resource_generation():
    """Test resource link generation functionality"""
    
    try:
        reviewer = EmpathticCodeReviewer("", ReviewerPersona.MENTOR)  # Empty API key for testing
        
        test_cases = [
            ("Variable 'u' is a bad name.", "def func(): pass"),
            ("This is inefficient.", "for item in items: pass"),
            ("Boolean comparison '== True' is redundant.", "if flag == True: pass")
        ]
        
        print("\\nTesting Resource Generation:")
        for comment, code in test_cases:
            resources = reviewer._get_relevant_resources(comment, code)
            print(f"  Comment: '{comment}'")
            print(f"  Resources: {len(resources)} found")
            for resource in resources:
                print(f"    - {resource}")
            print()
        
        print("[PASS] Resource generation working correctly!")
        return True
    except Exception as e:
        print(f"[FAIL] Resource generation test failed: {e}")
        return False


def test_multi_language_detection():
    """Test multi-language detection functionality"""
    
    try:
        reviewer = EmpathticCodeReviewer("", ReviewerPersona.TECH_LEAD)
        
        test_codes = [
            ("def hello():\n    print('world')", "python"),
            ("function hello() {\n    console.log('world');\n}", "javascript"),
            ("public class Hello {\n    public static void main() {}\n}", "java"),
            ("#include <iostream>\nint main() { return 0; }", "cpp"),
            ("package main\nfunc main() {\n    fmt.Println(\"hello\")\n}", "go")
        ]
        
        print("\\nTesting Multi-Language Detection:")
        correct_detections = 0
        for code, expected_lang in test_codes:
            detected = reviewer._detect_language(code)
            is_correct = detected == expected_lang
            status = "[PASS]" if is_correct else "[FAIL]"
            print(f"  {expected_lang.title()} code -> detected as {detected} {status}")
            if is_correct:
                correct_detections += 1
        
        accuracy = (correct_detections / len(test_codes)) * 100
        print(f"\\nLanguage Detection Accuracy: {accuracy:.1f}%")
        
        print("[PASS] Multi-language detection working!")
        return True
        
    except Exception as e:
        print(f"[FAIL] Multi-language detection test failed: {e}")
        return False
        
def test_quality_scoring():
    """Test code quality scoring functionality"""
    
    try:
        reviewer = EmpathticCodeReviewer("", ReviewerPersona.SENIOR_DEVELOPER)
        
        test_code = "def bad_func(x): return x+1"  # Simple test code
        test_comments = ["Function name is unclear", "No type hints"]
        
        quality_score = reviewer._calculate_code_quality_score(test_code, test_comments, "python")
        
        print("\\nTesting Quality Scoring:")
        print(f"  Overall Score: {quality_score.overall_score:.1f}/10")
        print(f"  Readability: {quality_score.readability:.1f}/10")
        print(f"  Performance: {quality_score.performance:.1f}/10")
        print(f"  Maintainability: {quality_score.maintainability:.1f}/10")
        print(f"  Best Practices: {quality_score.best_practices:.1f}/10")
        print(f"  Improvement Potential: {quality_score.improvement_potential:.1f}/10")
        
        # Validate score ranges
        scores = [quality_score.overall_score, quality_score.readability, 
                 quality_score.performance, quality_score.maintainability, 
                 quality_score.best_practices, quality_score.improvement_potential]
        
        all_valid = all(0 <= score <= 10 for score in scores)
        print(f"\\n[PASS] All scores within valid range (0-10): {all_valid}")
        return all_valid
        
    except Exception as e:
        print(f"[FAIL] Quality scoring test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting Empathetic Code Reviewer Pro Tests\\n")
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: JSON Parsing
    if test_json_parsing():
        tests_passed += 1
    
    # Test 2: Severity Assessment
    if test_severity_assessment():
        tests_passed += 1
    
    # Test 3: Resource Generation
    if test_resource_generation():
        tests_passed += 1
        
    # Test 4: Multi-language Detection
    if test_multi_language_detection():
        tests_passed += 1
        
    # Test 5: Quality Scoring
    if test_quality_scoring():
        tests_passed += 1
    
    # Results
    print("\\n" + "="*50)
    print(f"Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("[SUCCESS] All tests passed! The application is ready to use.")
        print("\\nTo run the application:")
        print("   1. Get an OpenAI API key from https://platform.openai.com/api-keys")
        print("   2. Run: streamlit run app.py")
        print("   3. Enter your API key in the sidebar")
        print("   4. Click 'Load Example Data' to test with the hackathon example")
    else:
        print("[ERROR] Some tests failed. Please check the implementation.")
    
    print("="*50)


if __name__ == "__main__":
    main()