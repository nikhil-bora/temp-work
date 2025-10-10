#!/usr/bin/env python3
"""
Basic test for Python FinOps Agent
"""

import sys
import os

print("Testing Python FinOps Agent...\n")

# Test 1: Import modules
print("Test 1: Importing modules...")
try:
    import anthropic
    import boto3
    from dotenv import load_dotenv
    from colorama import Fore
    print(f"{Fore.GREEN}✓ All imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Load environment
print("\nTest 2: Loading environment...")
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
api_key = os.getenv('ANTHROPIC_API_KEY')
aws_key = os.getenv('AWS_ACCESS_KEY_ID')

if api_key:
    print(f"{Fore.GREEN}✓ ANTHROPIC_API_KEY loaded ({api_key[:10]}...)")
else:
    print(f"{Fore.YELLOW}⚠ ANTHROPIC_API_KEY not found")

if aws_key:
    print(f"{Fore.GREEN}✓ AWS_ACCESS_KEY_ID loaded ({aws_key[:10]}...)")
else:
    print(f"{Fore.YELLOW}⚠ AWS_ACCESS_KEY_ID not found")

# Test 3: Import agent modules
print("\nTest 3: Importing agent modules...")
try:
    from agent import execute_athena_query, handle_tool_call, get_finops_system_prompt
    from tools import AVAILABLE_TOOLS
    print(f"{Fore.GREEN}✓ Agent modules imported")
    print(f"  - {len(AVAILABLE_TOOLS)} tools available")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 4: Check workspace directories
print("\nTest 4: Checking workspace directories...")
from pathlib import Path
workspace = Path(__file__).parent.parent / "workspace"
dirs = ["scripts", "workflows", "data"]
for d in dirs:
    dir_path = workspace / d
    if dir_path.exists():
        print(f"{Fore.GREEN}✓ {d}/ exists")
    else:
        print(f"{Fore.YELLOW}⚠ {d}/ not found")

# Test 5: Check CUR schema
print("\nTest 5: Checking CUR schema...")
from agent import CUR_SCHEMA
if CUR_SCHEMA:
    print(f"{Fore.GREEN}✓ CUR schema loaded ({CUR_SCHEMA['totalColumns']} columns)")
else:
    print(f"{Fore.YELLOW}⚠ CUR schema not loaded")

# Test 6: Test AWS boto3
print("\nTest 6: Testing AWS boto3...")
try:
    boto3.setup_default_session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'ap-south-1')
    )
    ec2 = boto3.client('ec2')
    print(f"{Fore.GREEN}✓ boto3 EC2 client created")
except Exception as e:
    print(f"{Fore.YELLOW}⚠ boto3 setup failed: {e}")

# Test 7: Test Anthropic client
print("\nTest 7: Testing Anthropic client...")
try:
    if api_key:
        client = anthropic.Anthropic(api_key=api_key)
        print(f"{Fore.GREEN}✓ Anthropic client created")
    else:
        print(f"{Fore.YELLOW}⚠ Skip - no API key")
except Exception as e:
    print(f"{Fore.YELLOW}⚠ Anthropic client failed: {e}")

print(f"\n{Fore.GREEN}{'='*50}")
print(f"{Fore.GREEN}All basic tests completed!")
print(f"{Fore.GREEN}{'='*50}\n")
print("Ready to run: python3 main.py")
