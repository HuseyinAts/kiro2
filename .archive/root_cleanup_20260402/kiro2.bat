@echo off
REM KIRO2 Orchestrator - Quick Launcher
REM Usage: kiro2 "your task here"
REM        kiro2 --dry-run "test routing"
REM        kiro2 --stats

python "%~dp0kiro2-orchestrator\kiro2-orchestrator\scripts\kiro2_orchestrator.py" %*
