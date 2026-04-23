#!/usr/bin/env python3
"""
CLI interface for Reward Hacking Prevention.

Usage:
    python -m backend.hooks.reward_hacking.cli [OPTIONS] FILES...

Examples:
    python -m backend.hooks.reward_hacking.cli tests/test_user.py
    python -m backend.hooks.reward_hacking.cli --verbose src/
    python -m backend.hooks.reward_hacking.cli --json --config custom.yaml src/
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .hook_manager import HookManager
from .models.detection_result import GlobalConfig


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="reward-hacking-check",
        description="Detect reward hacking patterns in code files",
        epilog="Exit codes: 0=clean, 1=warning, 2=critical (blocks commit)"
    )

    parser.add_argument(
        "files",
        nargs="+",
        help="Files or directories to analyze"
    )

    parser.add_argument(
        "-c", "--config",
        type=str,
        default=None,
        help="Path to custom configuration file (YAML/JSON)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON"
    )

    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit with code 2 on warnings (not just critical)"
    )

    parser.add_argument(
        "--disable",
        type=str,
        action="append",
        default=[],
        help="Disable specific detector(s) by name"
    )

    parser.add_argument(
        "--enable-only",
        type=str,
        action="append",
        default=[],
        help="Enable only specific detector(s)"
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout per file in seconds (default: 30)"
    )

    parser.add_argument(
        "--max-files",
        type=int,
        default=100,
        help="Maximum number of files to analyze (default: 100)"
    )

    parser.add_argument(
        "--list-detectors",
        action="store_true",
        help="List all available detectors and exit"
    )

    return parser.parse_args(argv)


def collect_files(paths: list[str]) -> list[str]:
    """
    Collect all files from given paths.

    Args:
        paths: List of file/directory paths

    Returns:
        List of file paths
    """
    files: list[str] = []

    for path_str in paths:
        path = Path(path_str)

        if path.is_file():
            files.append(str(path.absolute()))
        elif path.is_dir():
            # Recursively find supported files
            for ext in HookManager.SUPPORTED_EXTENSIONS:
                for file in path.rglob(f"*{ext}"):
                    # Skip common excluded directories
                    if any(part.startswith('.') or part in ('node_modules', '__pycache__', 'venv', '.venv')
                           for part in file.parts):
                        continue
                    files.append(str(file.absolute()))

    return files


def load_config(config_path: str | None) -> GlobalConfig:
    """
    Load configuration from file.

    Args:
        config_path: Path to config file

    Returns:
        GlobalConfig instance
    """
    if config_path is None:
        return GlobalConfig()

    path = Path(config_path)
    if not path.exists():
        print(f"Warning: Config file not found: {config_path}", file=sys.stderr)
        return GlobalConfig()

    try:
        content = path.read_text()

        if path.suffix in ('.yml', '.yaml'):
            import yaml
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)

        return GlobalConfig(**data)

    except Exception as e:
        print(f"Warning: Failed to load config: {e}", file=sys.stderr)
        return GlobalConfig()


async def main_async(args: argparse.Namespace) -> int:
    """
    Async main function.

    Args:
        args: Parsed arguments

    Returns:
        Exit code
    """
    # Handle --list-detectors
    if args.list_detectors:
        manager = HookManager()
        print("Available detectors:")
        for name in manager.get_detector_names():
            print(f"  - {name}")
        return 0

    # Collect files
    files = collect_files(args.files)

    if not files:
        print("No files to analyze", file=sys.stderr)
        return 0

    if args.verbose:
        print(f"Analyzing {len(files)} file(s)...")

    # Load configuration
    config = load_config(args.config)
    config.fail_on_warning = args.fail_on_warning
    config.timeout_seconds = args.timeout
    config.max_files = args.max_files

    # Create manager
    manager = HookManager(config=config)

    # Handle --disable
    for detector_name in args.disable:
        if not manager.disable_detector(detector_name):
            print(f"Warning: Unknown detector: {detector_name}", file=sys.stderr)

    # Handle --enable-only
    if args.enable_only:
        # Disable all first
        for detector in manager.detectors:
            detector.config.enabled = False
        # Enable specified ones
        for detector_name in args.enable_only:
            if not manager.enable_detector(detector_name):
                print(f"Warning: Unknown detector: {detector_name}", file=sys.stderr)

    # Run detection
    result = await manager.run_hooks(files)

    # Output results
    if args.json_output:
        output = {
            "exit_code": result.exit_code,
            "total_detections": result.total_detections,
            "critical_count": result.critical_count,
            "warning_count": result.warning_count,
            "info_count": result.info_count,
            "files_analyzed": result.files_analyzed,
            "execution_time_ms": result.execution_time_ms,
            "results": [
                {
                    "detector": r.detector_name,
                    "pattern_type": r.pattern_type,
                    "severity": r.severity,
                    "file": r.file_path,
                    "line": r.line_number,
                    "code": r.code_snippet,
                    "message": r.message,
                    "remediation": r.remediation,
                    "confidence": r.confidence,
                }
                for r in result.results
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        print(result.summary)

        if args.verbose:
            print(f"\nExecution time: {result.execution_time_ms:.2f}ms")
            print(f"Files analyzed: {result.files_analyzed}")

    return result.exit_code


def main(argv: list[str] | None = None) -> int:
    """
    Main entry point.

    Args:
        argv: Command line arguments

    Returns:
        Exit code
    """
    args = parse_args(argv)

    try:
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
