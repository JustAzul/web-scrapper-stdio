import sys
import pytest
import os

def main():
    """
    Run tests for specific domains only.
    
    Usage: python run_domain_tests.py domain1 [domain2 ...]
    Example: python run_domain_tests.py dev.to dmnews.com
    """
    if len(sys.argv) < 2:
        print("Usage: python run_domain_tests.py domain1 [domain2 ...]")
        print("Example: python run_domain_tests.py dev.to dmnews.com")
        sys.exit(1)
    
    # Get domains from command line arguments
    domains = sys.argv[1:]
    print(f"Running tests only for domains: {', '.join(domains)}")
    
    # Construct the expression for domain filtering
    domain_expr = ' or '.join([f"domain_info[0] == '{domain}'" for domain in domains])
    
    # Build the pytest command to run only tests with the specified domains
    pytest_args = [
        "-v",  # Verbose output
        "--capture=no",  # Show print statements
        f"-k \"({domain_expr})\"",  # Filter for tests with these domains
    ]
    
    # Run pytest with the constructed arguments
    sys.exit(pytest.main(pytest_args))

if __name__ == "__main__":
    main() 