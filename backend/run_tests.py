#!/usr/bin/env python3
"""
Test runner for the AI Website Navigator Backend
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=False)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED (exit code: {e.returncode})")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run AI Website Navigator Backend Tests")
    parser.add_argument('--type', choices=['unit', 'integration', 'performance', 'edge', 'all'], 
                       default='all', help='Type of tests to run')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', '-c', action='store_true', help='Run with coverage report')
    parser.add_argument('--parallel', '-p', action='store_true', help='Run tests in parallel')
    parser.add_argument('--stress', action='store_true', help='Include stress tests (slow)')
    parser.add_argument('--file', '-f', help='Run specific test file')
    parser.add_argument('--test', '-t', help='Run specific test function')
    
    args = parser.parse_args()
    
    # Change to backend directory if not already there
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    print("🤖 AI Website Navigator Backend Test Suite")
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Check if pytest is available
    try:
        subprocess.run(['python', '-c', 'import pytest'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ pytest not found. Installing...")
        subprocess.run(['pip', 'install', 'pytest', 'pytest-asyncio', 'pytest-cov'], check=True)
    
    # Build base command
    base_cmd = "python -m pytest"
    
    if args.verbose:
        base_cmd += " -v"
    else:
        base_cmd += " -q"
    
    if args.coverage:
        base_cmd += " --cov=. --cov-report=html --cov-report=term"
    
    if args.parallel:
        base_cmd += " -n auto"  # Requires pytest-xdist
    
    success_count = 0
    total_tests = 0
    
    # Specific file or test
    if args.file:
        test_path = f"tests/{args.file}" if not args.file.startswith('tests/') else args.file
        if args.test:
            cmd = f"{base_cmd} {test_path}::{args.test}"
            description = f"Running specific test: {args.test}"
        else:
            cmd = f"{base_cmd} {test_path}"
            description = f"Running test file: {args.file}"
        
        if run_command(cmd, description):
            success_count += 1
        total_tests += 1
    
    # Run test categories
    elif args.type == 'all' or args.type == 'unit':
        total_tests += 1
        if run_command(f"{base_cmd} tests/test_api_endpoints.py", "API Endpoint Tests"):
            success_count += 1
        
        total_tests += 1
        if run_command(f"{base_cmd} tests/test_ai_engine.py", "AI Engine Tests"):
            success_count += 1
        
        total_tests += 1
        if run_command(f"{base_cmd} tests/test_rag_system.py", "RAG System Tests"):
            success_count += 1
    
    if args.type == 'all' or args.type == 'integration':
        total_tests += 1
        if run_command(f"{base_cmd} tests/test_integration.py", "Integration Tests"):
            success_count += 1
    
    if args.type == 'all' or args.type == 'performance':
        # Skip stress tests unless explicitly requested
        stress_filter = "" if args.stress else " -m 'not stress'"
        total_tests += 1
        if run_command(f"{base_cmd} tests/test_performance.py{stress_filter}", "Performance Tests"):
            success_count += 1
    
    if args.type == 'all' or args.type == 'edge':
        total_tests += 1
        if run_command(f"{base_cmd} tests/test_edge_cases.py", "Edge Case Tests"):
            success_count += 1
    
    # Additional comprehensive test if running all
    if args.type == 'all' and not args.file:
        total_tests += 1
        if run_command(f"{base_cmd} tests/", "All Tests (Comprehensive)"):
            success_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {success_count}/{total_tests}")
    print(f"❌ Failed: {total_tests - success_count}/{total_tests}")
    
    if success_count == total_tests:
        print(f"🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"💥 {total_tests - success_count} TEST SUITE(S) FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
