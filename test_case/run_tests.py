#!/usr/bin/env python3
"""
Simple runner script for the endpoint test suite.
This script can be run independently to test all endpoints.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import the test suite
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_case.endpoint_test_suite import main

if __name__ == "__main__":
    print("🚀 Starting Workspace Management Service Endpoint Tests")
    print("=" * 60)
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
