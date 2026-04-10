#!/usr/bin/env python3
"""
Complete Pipeline Wrapper for OpenSourceScribes
Runs Phase 1 (parsing) + Phase 2 (Prefect video production) in one command.

Usage:
    python run_pipeline.py                      # Use github_urls.txt
    python run_pipeline.py --input my_repos.txt
    python run_pipeline.py --date 04-01        # Custom delivery folder
    python run_pipeline.py --skip-parse       # Skip Phase 1, use existing posts_data.json

Dependencies:
    - Python 3.x
    - simple_parser.py must exist
    - run_with_prefect.sh must be executable
    - Prefect server should be running
"""

import sys
import subprocess
import json
import argparse
import os
from datetime import datetime
from pathlib import Path

# Color codes for terminal output
class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title):
    """Print a formatted header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title.center(70)}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 70}{Colors.END}\n")

def print_step(step_num, description):
    """Print a step indicator"""
    print(f"{Colors.PURPLE}{Colors.BOLD}[{step_num}]{Colors.END} {description}")

def print_success(message):
    """Print a success message"""
    print(f"{Colors.GREEN}{Colors.BOLD}✓{Colors.END} {message}")

def print_error(message):
    """Print an error message"""
    print(f"{Colors.RED}{Colors.BOLD}✗{Colors.END} {message}")

def print_warning(message):
    """Print a warning message"""
    print(f"{Colors.YELLOW}{Colors.BOLD}⚠{Colors.END} {message}")

def run_phase_1(input_file):
    """
    Run simple_parser.py to generate posts_data.json
    
    Args:
        input_file: Path to input file with GitHub URLs
        
    Returns:
        True if successful, False otherwise
    """
    print_step("PHASE 1", f"Parsing {input_file}...")
    print(f"   Running: python3 simple_parser.py {input_file}")
    
    result = subprocess.run(
        ["python3", "simple_parser.py", input_file],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    
    if result.returncode != 0:
        print_error("Phase 1 failed")
        print(f"\n{Colors.RED}Error output:{Colors.END}")
        print(result.stderr)
        return False
    
    # Show output if verbose
    if "Processing" in result.stdout or "Done" in result.stdout:
        output_lines = result.stdout.strip().split('\n')
        if output_lines:
            print(f"   {output_lines[-1]}")
    
    print_success("Phase 1 complete - posts_data.json generated")
    return True

def validate_phase_1_output(expected_project_count=None):
    """
    Validate posts_data.json exists and contains valid data
    
    Args:
        expected_project_count: Optional expected number of projects
        
    Returns:
        Number of projects found, or None if validation fails
    """
    print_step("VALIDATION", "Checking posts_data.json...")
    
    posts_data_path = Path(__file__).parent / "posts_data.json"
    
    if not posts_data_path.exists():
        print_error("posts_data.json not found")
        return None
    
    try:
        with open(posts_data_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"posts_data.json has invalid JSON: {e}")
        return None
    
    if not data:
        print_error("posts_data.json is empty")
        return None
    
    project_count = len(data)
    print_success(f"Validation passed: {project_count} projects parsed")
    
    # Check expected count if provided
    if expected_project_count is not None:
        input_urls_path = Path(__file__).parent / "github_urls.txt"
        if input_urls_path.exists():
            with open(input_urls_path) as f:
                actual_urls = len([line for line in f if line.strip() and line.startswith('https://github.com/')])
            print(f"   Input: {actual_urls} URLs → Parsed: {project_count} projects")
            if project_count < actual_urls:
                print_warning(f"⚠  Parsed count ({project_count}) < Input count ({actual_urls}) - some repos may have failed")
    
    return project_count

def check_prefect_server():
    """
    Check if Prefect server is running
    
    Returns:
        True if server appears to be running, False otherwise
    """
    print_step("CHECK", "Prefect server status...")
    
    try:
        # Try to check Prefect status
        result = subprocess.run(
            ["npx", "prefect", "status"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 or "running" in result.stdout.lower():
            print_success("Prefect server appears to be running")
            return True
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        pass
    except Exception as e:
        pass
    
    print_warning("Prefect server status unknown - will proceed anyway")
    return True

def run_phase_2(project_count):
    """
    Run Prefect orchestration (Phase 2)
    
    Args:
        project_count: Number of projects being processed
        
    Returns:
        True if successful, False otherwise
    """
    print_step("PHASE 2", f"Video production for {project_count} projects...")
    print(f"   Running: ./run_with_prefect.sh orchestration")
    
    script_path = Path(__file__).parent / "run_with_prefect.sh"
    
    if not script_path.exists():
        print_error(f"Script not found: {script_path}")
        return False
    
    # Make executable if not already
    try:
        if not os.access(script_path, os.X_OK):
            os.chmod(script_path, 0o755)
    except Exception as e:
        print_warning(f"Could not make script executable: {e}")
    
    result = subprocess.run(
        ["bash", str(script_path), "orchestration"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    
    if result.returncode != 0:
        print_error("Phase 2 failed")
        print(f"\n{Colors.RED}Error output:{Colors.END}")
        print(result.stderr)
        return False
    
    print_success("Phase 2 complete - videos generated")
    return True

def count_input_urls(input_file):
    """
    Count GitHub URLs in input file
    
    Args:
        input_file: Path to input file
        
    Returns:
        Number of GitHub URLs found
    """
    input_path = Path(__file__).parent / input_file
    
    if not input_path.exists():
        return 0
    
    with open(input_path) as f:
        urls = [line for line in f if line.strip() and line.startswith('https://github.com/')]
    
    return len(urls)

def show_summary(start_time, input_file, delivery_date):
    """
    Display pipeline completion summary
    
    Args:
        start_time: Timestamp when pipeline started
        input_file: Input file used
        delivery_date: Delivery folder date
    """
    elapsed = datetime.now() - start_time
    delivery_folder = Path(__file__).parent / "deliveries" / delivery_date
    
    print_header("🎉 PIPELINE COMPLETE")
    
    print(f"{Colors.WHITE}{Colors.BOLD}Summary:{Colors.END}")
    print(f"   Input file:      {input_file}")
    print(f"   Delivery folder: {delivery_folder}")
    print(f"   Total time:     {elapsed.total_seconds():.1f}s")
    
    if delivery_folder.exists():
        print(f"\n{Colors.GREEN}{Colors.BOLD}Location:{Colors.END}")
        print(f"   {delivery_folder.absolute()}")
        
        # List files
        mp4_files = list(delivery_folder.glob("*.mp4"))
        if mp4_files:
            print(f"\n{Colors.WHITE}{Colors.BOLD}Video files created:{Colors.END} {len(mp4_files)}")
    else:
        print_warning(f"   Delivery folder not found at expected location")

def main():
    """Main pipeline execution"""
    
    parser = argparse.ArgumentParser(
        description="OpenSourceScribes Complete Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard run with github_urls.txt
  python run_pipeline.py
  
  # Custom input file
  python run_pipeline.py --input my_repos.txt
  
  # Skip parsing, use existing posts_data.json
  python run_pipeline.py --skip-parse
  
  # Custom delivery date prefix
  python run_pipeline.py --date 04-01
  
  # Dry run (test validation without running)
  python run_pipeline.py --dry-run
        """
    )
    
    parser.add_argument(
        "--input",
        default="github_urls.txt",
        help="Input file with GitHub URLs (default: github_urls.txt)"
    )
    
    parser.add_argument(
        "--date",
        default=None,
        help="Delivery folder date prefix (default: MM-DD from today)"
    )
    
    parser.add_argument(
        "--skip-parse",
        action="store_true",
        help="Skip Phase 1 (parsing), use existing posts_data.json"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate files without running pipeline"
    )
    
    args = parser.parse_args()
    
    # Set delivery date
    if args.date:
        delivery_date = args.date
    else:
        delivery_date = datetime.now().strftime("%m-%d")
    
    start_time = datetime.now()
    
    print_header("🚀 OPENSOURCESCRIBES: PIPELINE")
    
    print(f"{Colors.WHITE}{Colors.BOLD}Configuration:{Colors.END}")
    print(f"   Input file:     {args.input}")
    print(f"   Delivery date:  {delivery_date}")
    print(f"   Skip Phase 1:   {args.skip_parse}")
    print(f"   Dry run:        {args.dry_run}")
    
    # Count input URLs
    url_count = count_input_urls(args.input)
    if url_count > 0:
        print(f"   Repos to parse: {url_count}")
    
    # Set delivery date environment variable for Prefect
    os.environ["DELIVERY_DATE"] = delivery_date
    
    # Check input file exists
    input_path = Path(__file__).parent / args.input
    if not args.skip_parse and not input_path.exists():
        print_error(f"Input file not found: {args.input}")
        print(f"\n{Colors.YELLOW}Hint:{Colors.END} Create {args.input} with GitHub URLs, one per line")
        print(f"   Example:")
        print(f"   https://github.com/owner/repo1")
        print(f"   https://github.com/owner/repo2")
        sys.exit(1)
    
    # Dry run - just validate
    if args.dry_run:
        print_header("🧪 DRY RUN MODE")
        
        if not args.skip_parse:
            print_step("CHECK", "simple_parser.py exists")
            parser_path = Path(__file__).parent / "simple_parser.py"
            if not parser_path.exists():
                print_error(f"Not found: {parser_path}")
                sys.exit(1)
            print_success("simple_parser.py found")
        
        print_step("CHECK", "run_with_prefect.sh exists")
        prefect_script = Path(__file__).parent / "run_with_prefect.sh"
        if not prefect_script.exists():
            print_error(f"Not found: {prefect_script}")
            sys.exit(1)
        print_success("run_with_prefect.sh found")
        
        print_step("CHECK", "Prefect server status")
        check_prefect_server()
        
        print_success("All checks passed - ready to run")
        print(f"\n{Colors.YELLOW}Run without --dry-run to execute the pipeline{Colors.END}")
        sys.exit(0)
    
    # ===== START PIPELINE =====
    
    # Phase 1: Parse repos
    project_count = None
    
    if not args.skip_parse:
        if not run_phase_1(args.input):
            sys.exit(1)
        
        project_count = validate_phase_1_output(url_count)
        if project_count is None:
            sys.exit(1)
    else:
        print_step("PHASE 1", "Skipped (--skip-parse flag)")
        
        # Validate existing posts_data.json
        project_count = validate_phase_1_output(url_count)
        if project_count is None:
            sys.exit(1)
    
    # Check Prefect server
    check_prefect_server()
    
    # Phase 2: Video production
    if not run_phase_2(project_count):
        sys.exit(1)
    
    # Show summary
    show_summary(start_time, args.input, delivery_date)
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Pipeline finished successfully!{Colors.END}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Pipeline interrupted by user{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error:{Colors.END} {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
