#!/usr/bin/env python3
"""
Comprehensive test runner for Financial AI Agents system.

This script provides various test execution options including:
- Unit tests
- Integration tests  
- Performance tests
- Coverage reporting
- Test result analysis
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any


class TestRunner:
    """Comprehensive test runner with multiple execution modes."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_dir = self.project_root / "tests"
        self.coverage_dir = self.project_root / "htmlcov"
        
    def setup_environment(self):
        """Set up test environment variables."""
        test_env = {
            "GROQ_API_KEY": "test-groq-key-12345",
            "PHI_API_KEY": "test-phi-key-67890",
            "ENVIRONMENT": "test",
            "LOG_LEVEL": "WARNING",
            "PYTHONPATH": str(self.project_root)
        }
        
        for key, value in test_env.items():
            os.environ[key] = value
        
        print("✓ Test environment configured")
    
    def run_unit_tests(self, verbose: bool = False) -> bool:
        """Run unit tests."""
        print("\n🧪 Running Unit Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "unit"),
            "-m", "not slow",
            "--cov=app",
            "--cov-report=term-missing"
        ]
        
        if verbose:
            cmd.append("-v")
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        if success:
            print("✓ Unit tests passed")
        else:
            print("✗ Unit tests failed")
        
        return success
    
    def run_integration_tests(self, verbose: bool = False) -> bool:
        """Run integration tests."""
        print("\n🔗 Running Integration Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "integration"),
            "-m", "not slow",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        if success:
            print("✓ Integration tests passed")
        else:
            print("✗ Integration tests failed")
        
        return success
    
    def run_performance_tests(self, verbose: bool = False) -> bool:
        """Run performance tests."""
        print("\n⚡ Running Performance Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "performance"),
            "--timeout=300",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        if success:
            print("✓ Performance tests passed")
        else:
            print("✗ Performance tests failed")
        
        return success
    
    def run_all_tests(self, verbose: bool = False) -> Dict[str, bool]:
        """Run all test suites."""
        print("\n🚀 Running Complete Test Suite...")
        
        results = {}
        
        # Run unit tests
        results["unit"] = self.run_unit_tests(verbose)
        
        # Run integration tests
        results["integration"] = self.run_integration_tests(verbose)
        
        # Run performance tests (only if other tests pass)
        if results["unit"] and results["integration"]:
            results["performance"] = self.run_performance_tests(verbose)
        else:
            print("⚠️  Skipping performance tests due to failures in basic tests")
            results["performance"] = False
        
        return results
    
    def run_coverage_report(self) -> bool:
        """Generate comprehensive coverage report."""
        print("\n📊 Generating Coverage Report...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "unit"),
            str(self.test_dir / "integration"),
            "--cov=app",
            "--cov-report=html",
            "--cov-report=xml",
            "--cov-report=term",
            "--cov-fail-under=80"
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        if success:
            print(f"✓ Coverage report generated: {self.coverage_dir}/index.html")
        else:
            print("✗ Coverage report generation failed")
        
        return success
    
    def run_quick_tests(self) -> bool:
        """Run quick test suite for development."""
        print("\n⚡ Running Quick Test Suite...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "unit"),
            "-m", "not slow",
            "--tb=line",
            "-q"
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        if success:
            print("✓ Quick tests passed")
        else:
            print("✗ Quick tests failed")
        
        return success
    
    def run_specific_test(self, test_path: str, verbose: bool = False) -> bool:
        """Run a specific test file or test function."""
        print(f"\n🎯 Running Specific Test: {test_path}")
        
        cmd = [
            "python", "-m", "pytest",
            test_path,
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        if success:
            print(f"✓ Test {test_path} passed")
        else:
            print(f"✗ Test {test_path} failed")
        
        return success
    
    def run_parallel_tests(self, workers: int = 4) -> bool:
        """Run tests in parallel for faster execution."""
        print(f"\n🔄 Running Tests in Parallel ({workers} workers)...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "unit"),
            str(self.test_dir / "integration"),
            f"-n{workers}",
            "--tb=short"
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        success = result.returncode == 0
        
        if success:
            print("✓ Parallel tests passed")
        else:
            print("✗ Parallel tests failed")
        
        return success
    
    def analyze_test_results(self, results: Dict[str, bool]):
        """Analyze and display test results summary."""
        print("\n" + "="*60)
        print("📋 TEST RESULTS SUMMARY")
        print("="*60)
        
        total_suites = len(results)
        passed_suites = sum(1 for success in results.values() if success)
        
        for suite_name, success in results.items():
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"{suite_name.upper():15} {status}")
        
        print("-"*60)
        print(f"TOTAL: {passed_suites}/{total_suites} test suites passed")
        
        if passed_suites == total_suites:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. Please review the output above.")
            return False
    
    def check_dependencies(self) -> bool:
        """Check if all required test dependencies are installed."""
        print("🔍 Checking test dependencies...")
        
        required_packages = [
            "pytest",
            "pytest-asyncio", 
            "pytest-cov",
            "pytest-timeout",
            "psutil"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"✗ Missing packages: {', '.join(missing_packages)}")
            print("Install with: pip install -r requirements.txt")
            return False
        
        print("✓ All test dependencies available")
        return True


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(description="Financial AI Agents Test Runner")
    
    parser.add_argument(
        "mode",
        choices=["unit", "integration", "performance", "all", "coverage", "quick", "parallel"],
        help="Test execution mode"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--test", "-t",
        type=str,
        help="Run specific test file or function"
    )
    
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=4,
        help="Number of parallel workers (for parallel mode)"
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner()
    
    # Check dependencies
    if not runner.check_dependencies():
        sys.exit(1)
    
    # Set up environment
    runner.setup_environment()
    
    # Execute tests based on mode
    start_time = time.time()
    
    try:
        if args.test:
            success = runner.run_specific_test(args.test, args.verbose)
        elif args.mode == "unit":
            success = runner.run_unit_tests(args.verbose)
        elif args.mode == "integration":
            success = runner.run_integration_tests(args.verbose)
        elif args.mode == "performance":
            success = runner.run_performance_tests(args.verbose)
        elif args.mode == "coverage":
            success = runner.run_coverage_report()
        elif args.mode == "quick":
            success = runner.run_quick_tests()
        elif args.mode == "parallel":
            success = runner.run_parallel_tests(args.workers)
        elif args.mode == "all":
            results = runner.run_all_tests(args.verbose)
            success = runner.analyze_test_results(results)
        else:
            print(f"Unknown mode: {args.mode}")
            sys.exit(1)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️  Total execution time: {duration:.2f} seconds")
        
        if success:
            print("🎉 Test execution completed successfully!")
            sys.exit(0)
        else:
            print("❌ Test execution failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()