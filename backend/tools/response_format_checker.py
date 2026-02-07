#!/usr/bin/env python3
"""
Response Format Checker Tool
Command-line utility for validating API response format compliance
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.response_validators import (
    ResponseTester,
    ResponseValidator,
    run_response_validation_tests,
)


class ResponseFormatChecker:
    """Command-line tool for checking API response formats"""

    def __init__(self):
        self.validator = ResponseValidator(strict_validation=False)
        self.tester = ResponseTester()

    def check_file(self, file_path: str) -> Dict[str, Any]:
        """
        Check response format from JSON file

        Args:
            file_path: Path to JSON file containing response data

        Returns:
            Dict containing validation results
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                response_data = json.load(f)

            return self._validate_response_data(response_data, f"file:{file_path}")

        except FileNotFoundError:
            return {
                "source": f"file:{file_path}",
                "error": f"File not found: {file_path}",
                "validation_passed": False,
            }
        except json.JSONDecodeError as e:
            return {
                "source": f"file:{file_path}",
                "error": f"Invalid JSON: {str(e)}",
                "validation_passed": False,
            }
        except Exception as e:
            return {
                "source": f"file:{file_path}",
                "error": f"Unexpected error: {str(e)}",
                "validation_passed": False,
            }

    def check_url(
        self, url: str, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Check response format from API endpoint

        Args:
            url: API endpoint URL
            headers: Optional HTTP headers

        Returns:
            Dict containing validation results
        """
        try:
            response = requests.get(url, headers=headers or {}, timeout=30)
            response_data = response.json()

            result = self._validate_response_data(response_data, f"url:{url}")
            result["http_status"] = response.status_code
            result["response_time_ms"] = response.elapsed.total_seconds() * 1000

            return result

        except requests.exceptions.RequestException as e:
            return {
                "source": f"url:{url}",
                "error": f"Request failed: {str(e)}",
                "validation_passed": False,
            }
        except json.JSONDecodeError as e:
            return {
                "source": f"url:{url}",
                "error": f"Response is not valid JSON: {str(e)}",
                "validation_passed": False,
            }
        except Exception as e:
            return {
                "source": f"url:{url}",
                "error": f"Unexpected error: {str(e)}",
                "validation_passed": False,
            }

    def check_json_string(self, json_string: str) -> Dict[str, Any]:
        """
        Check response format from JSON string

        Args:
            json_string: JSON string containing response data

        Returns:
            Dict containing validation results
        """
        try:
            response_data = json.loads(json_string)
            return self._validate_response_data(response_data, "json_string")

        except json.JSONDecodeError as e:
            return {
                "source": "json_string",
                "error": f"Invalid JSON: {str(e)}",
                "validation_passed": False,
            }
        except Exception as e:
            return {
                "source": "json_string",
                "error": f"Unexpected error: {str(e)}",
                "validation_passed": False,
            }

    def _validate_response_data(
        self, response_data: Dict[str, Any], source: str
    ) -> Dict[str, Any]:
        """Internal method to validate response data"""
        result = {
            "source": source,
            "validation_passed": False,
            "errors": [],
            "warnings": [],
            "response_type": "unknown",
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Basic structure validation
            if not self.validator.validate_response_structure(response_data):
                result["errors"].append("Basic response structure validation failed")

            # Determine response type
            if response_data.get("success") == True:
                if "pagination" in response_data:
                    result["response_type"] = "paginated_success"
                    failures = self.tester.assert_paginated_response(response_data)
                else:
                    result["response_type"] = "success"
                    failures = self.tester.assert_success_response(response_data)
            elif response_data.get("success") == False:
                result["response_type"] = "error"
                failures = self.tester.assert_error_response(response_data)
            else:
                result["response_type"] = "invalid"
                failures = ["Response does not have valid 'success' field"]

            result["errors"].extend(failures)

            # Additional checks
            self._add_quality_warnings(response_data, result)

            # Determine if validation passed
            result["validation_passed"] = len(result["errors"]) == 0

        except Exception as e:
            result["errors"].append(f"Validation exception: {str(e)}")

        return result

    def _add_quality_warnings(
        self, response_data: Dict[str, Any], result: Dict[str, Any]
    ):
        """Add quality warnings to validation result"""
        warnings = []

        # Check for empty messages
        if response_data.get("message") == "":
            warnings.append("Response message is empty")

        # Check for missing meta fields
        meta = response_data.get("meta", {})
        if not meta.get("request_id"):
            warnings.append("Missing request_id in meta")
        if not meta.get("api_version"):
            warnings.append("Missing api_version in meta")
        if not meta.get("processing_time_ms"):
            warnings.append("Missing processing_time_ms in meta")

        # Check for Turkish message format
        message = response_data.get("message", "")
        if message and not any(
            turkish_char in message.lower() for turkish_char in "çğıöşü"
        ):
            warnings.append("Message appears to be in English rather than Turkish")

        # Check pagination completeness
        if "pagination" in response_data:
            pagination = response_data["pagination"]
            if pagination.get("total_items", 0) == 0 and response_data.get("data"):
                warnings.append("Pagination shows 0 total_items but data is present")

        # Check error details completeness
        if response_data.get("errors"):
            for i, error in enumerate(response_data["errors"]):
                if not error.get("code"):
                    warnings.append(f"Error {i} missing error code")
                if not error.get("message"):
                    warnings.append(f"Error {i} missing error message")

        result["warnings"] = warnings

    def bulk_check(
        self, sources: List[str], source_type: str = "auto"
    ) -> List[Dict[str, Any]]:
        """
        Check multiple sources

        Args:
            sources: List of file paths, URLs, or JSON strings
            source_type: Type of sources (auto, file, url, json)

        Returns:
            List of validation results
        """
        results = []

        for source in sources:
            if source_type == "auto":
                # Auto-detect source type
                if source.startswith(("http://", "https://")):
                    result = self.check_url(source)
                elif source.startswith("{") and source.endswith("}"):
                    result = self.check_json_string(source)
                else:
                    result = self.check_file(source)
            elif source_type == "file":
                result = self.check_file(source)
            elif source_type == "url":
                result = self.check_url(source)
            elif source_type == "json":
                result = self.check_json_string(source)
            else:
                result = {
                    "source": source,
                    "error": f"Unknown source type: {source_type}",
                    "validation_passed": False,
                }

            results.append(result)

        return results

    def generate_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary report from validation results"""
        total_sources = len(results)
        passed_sources = len([r for r in results if r.get("validation_passed")])
        failed_sources = len([r for r in results if not r.get("validation_passed")])

        # Count by response type
        response_types = {}
        for result in results:
            response_type = result.get("response_type", "unknown")
            response_types[response_type] = response_types.get(response_type, 0) + 1

        # Collect common errors
        all_errors = []
        for result in results:
            all_errors.extend(result.get("errors", []))

        error_counts = {}
        for error in all_errors:
            error_counts[error] = error_counts.get(error, 0) + 1

        common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]

        # Collect common warnings
        all_warnings = []
        for result in results:
            all_warnings.extend(result.get("warnings", []))

        warning_counts = {}
        for warning in all_warnings:
            warning_counts[warning] = warning_counts.get(warning, 0) + 1

        common_warnings = sorted(
            warning_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return {
            "summary": {
                "total_sources": total_sources,
                "passed": passed_sources,
                "failed": failed_sources,
                "success_rate": f"{(passed_sources/total_sources)*100:.1f}%"
                if total_sources > 0
                else "0%",
            },
            "response_types": response_types,
            "common_errors": [
                {"error": error, "count": count} for error, count in common_errors
            ],
            "common_warnings": [
                {"warning": warning, "count": count}
                for warning, count in common_warnings
            ],
            "details": results,
        }


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Response Format Checker - Validate API response format compliance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check a single JSON file
  python response_format_checker.py --file response.json
  
  # Check multiple files
  python response_format_checker.py --file file1.json file2.json file3.json
  
  # Check API endpoint
  python response_format_checker.py --url https://api.example.com/users
  
  # Check multiple endpoints
  python response_format_checker.py --url https://api.example.com/users https://api.example.com/posts
  
  # Check JSON string
  python response_format_checker.py --json '{"success": true, "status": "success", "message": "OK"}'
  
  # Generate test examples
  python response_format_checker.py --generate-tests
  
  # Verbose output with warnings
  python response_format_checker.py --file response.json --verbose
  
  # Output as JSON
  python response_format_checker.py --file response.json --output json
        """,
    )

    # Input options
    parser.add_argument("--file", "-f", nargs="+", help="JSON file(s) to validate")

    parser.add_argument(
        "--url", "-u", nargs="+", help="API endpoint URL(s) to validate"
    )

    parser.add_argument("--json", "-j", nargs="+", help="JSON string(s) to validate")

    # Options
    parser.add_argument("--headers", help="HTTP headers for URL requests (JSON format)")

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output including warnings",
    )

    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (text or json)",
    )

    parser.add_argument(
        "--generate-tests",
        action="store_true",
        help="Generate test examples and run validation tests",
    )

    args = parser.parse_args()

    if args.generate_tests:
        print("Generating test examples and running validation tests...")
        report = run_response_validation_tests()

        if args.output == "json":
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print("\\n[CHART] Test Results Summary:")
            print(f"Test Case: {report['test_case_name']}")
            print(f"Total Tests: {report['summary']['total']}")
            print(f"Passed: {report['summary']['passed']}")
            print(f"Failed: {report['summary']['failed']}")
            print(f"Success Rate: {report['summary']['success_rate']}")

            if args.verbose:
                print("\\n[MEMO] Detailed Results:")
                for result in report["results"]:
                    status_emoji = (
                        "[CHECK]"
                        if result["status"] == "PASS"
                        else "[X]"
                        if result["status"] == "FAIL"
                        else "⚠️"
                    )
                    print(f"  {status_emoji} {result['test_name']}: {result['status']}")
                    if result["status"] == "FAIL" and "failures" in result:
                        for failure in result["failures"]:
                            print(f"    - {failure}")
        return

    if not args.file and not args.url and not args.json:
        parser.print_help()
        return

    checker = ResponseFormatChecker()

    # Parse headers if provided
    headers = None
    if args.headers:
        try:
            headers = json.loads(args.headers)
        except json.JSONDecodeError:
            print("[X] Error: Invalid JSON format for headers")
            return

    all_results = []

    # Check files
    if args.file:
        for file_path in args.file:
            result = checker.check_file(file_path)
            all_results.append(result)

    # Check URLs
    if args.url:
        for url in args.url:
            result = checker.check_url(url, headers)
            all_results.append(result)

    # Check JSON strings
    if args.json:
        for json_string in args.json:
            result = checker.check_json_string(json_string)
            all_results.append(result)

    # Generate and display report
    report = checker.generate_report(all_results)

    if args.output == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        # Text output
        print("[MAG] Response Format Validation Report")
        print("=" * 50)

        # Summary
        summary = report["summary"]
        print("[CHART] Summary:")
        print(f"  Total Sources: {summary['total_sources']}")
        print(f"  [CHECK] Passed: {summary['passed']}")
        print(f"  [X] Failed: {summary['failed']}")
        print(f"  Success Rate: {summary['success_rate']}")

        # Response types
        if report["response_types"]:
            print("\\n[CLIPBOARD] Response Types:")
            for response_type, count in report["response_types"].items():
                print(f"  {response_type}: {count}")

        # Common errors
        if report["common_errors"]:
            print("\\n[ALERT] Most Common Errors:")
            for error_info in report["common_errors"][:5]:
                print(f"  [{error_info['count']}x] {error_info['error']}")

        # Common warnings
        if report["common_warnings"] and args.verbose:
            print("\\n⚠️ Most Common Warnings:")
            for warning_info in report["common_warnings"][:5]:
                print(f"  [{warning_info['count']}x] {warning_info['warning']}")

        # Detailed results
        print("\\n[MEMO] Detailed Results:")
        for result in all_results:
            status_emoji = "[CHECK]" if result["validation_passed"] else "[X]"
            print(
                f"\\n{status_emoji} {result['source']} ({result.get('response_type', 'unknown')})"
            )

            if not result["validation_passed"]:
                if "error" in result:
                    print(f"    Error: {result['error']}")
                if result.get("errors"):
                    for error in result["errors"]:
                        print(f"    - {error}")

            if args.verbose and result.get("warnings"):
                for warning in result["warnings"]:
                    print(f"    ⚠️ {warning}")

            # Show additional info for URL checks
            if "http_status" in result:
                print(f"    HTTP Status: {result['http_status']}")
                print(f"    Response Time: {result.get('response_time_ms', 0):.1f}ms")


if __name__ == "__main__":
    main()
