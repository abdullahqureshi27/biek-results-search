"""
BIEK Regular Part II 2026 Roll Number Search
Search roll numbers from a file across specific or all faculties

Usage:
    # Search SG rolls in SG faculty only (fast, specific)
    python bulk_search_all.py --file rollNumbers/sg_rolls.txt --faculty sg --output results/sg_results.csv --workers 20

    # Search PM rolls in SM (Pre-Medical) faculty only
    python bulk_search_all.py --file rollNumbers/pm_rolls.txt --faculty sm --output results/pm_results.csv --workers 20

    # Search across ALL faculties (slower but comprehensive)
    python bulk_search_all.py --file rollNumbers/sg_rolls.txt --output results/sg_results.csv --workers 20

    # Search by range with specific faculty
    python bulk_search_all.py --start 700000 --end 700100 --faculty sg --output test.csv --workers 5
"""

import os
import requests
import csv
import time
import argparse
import concurrent.futures
from threading import Lock
from typing import List, Dict, Optional
from datetime import datetime

# API Configuration (Mobile App Production Endpoint)
API_URL = "http://api.biekedu.com/search"
HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "User-Agent": "Dart/3.4 (dart:io)"
}

# All faculties (ordered by most common)
FACULTIES = [
    ("sg", "Science General"),
    ("sm", "Pre-Medical"),
    ("se", "Pre-Engineering"),
    ("hmt", "Humanities"),
    ("com", "Commerce")
]

# All exam types - Regular Part II 2026 by default
EXAM_TYPES = [
    "reg-p2-a-2026",  # Regular Part II 2026 (PRIMARY)
]

# Progress tracking
progress_lock = Lock()
progress = {
    "checked": 0,
    "found": 0,
    "start_time": None,
    "last_roll": 0
}


def search_roll(roll_no: str, faculty: str, exam_type: str, delay: float = 0.05) -> Optional[Dict]:
    """Search for a roll number with specific faculty and exam type."""
    payload = {
        "faculty": faculty,
        "value": exam_type,
        "roll_no": roll_no,
        "matric_roll_no": roll_no
    }

    try:
        response = requests.post(
            API_URL,
            json=payload,
            headers=HEADERS,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            detail = data.get("detail", {})

            if detail.get("roll_no") and detail.get("applicant_name"):
                return {
                    "roll_no": roll_no,
                    "faculty": faculty,
                    "exam_type": exam_type,
                    "name": detail.get("applicant_name"),
                    "father_name": detail.get("father_name"),
                    "marks": detail.get("secured_total", 0),
                    "grade": detail.get("grade", ""),
                }

        time.sleep(delay)
        return None

    except Exception:
        time.sleep(delay)
        return None


def search_roll_all_combinations(roll_no: str, delay: float = 0.05, specific_faculty: Optional[str] = None) -> Optional[Dict]:
    """
    Search a roll number across faculties and exam types.
    Stops as soon as a match is found.

    Args:
        roll_no: Roll number to search
        delay: Delay between requests
        specific_faculty: If provided, only search this faculty code (e.g., 'sg', 'sm')
    """
    # Filter faculties if specific one is requested
    faculties_to_search = FACULTIES
    if specific_faculty:
        faculties_to_search = [(code, name) for code, name in FACULTIES if code == specific_faculty]
        if not faculties_to_search:
            return None

    # Try each exam type, then each faculty, until a match is found
    for exam_type in EXAM_TYPES:
        # Try each faculty for this exam type
        for faculty_code, faculty_name in faculties_to_search:
            result = search_roll(roll_no, faculty_code, exam_type, delay)
            if result:
                result["faculty_name"] = faculty_name
                return result
    return None


def worker(roll_no: str, output_file: str, delay: float = 0.05, specific_faculty: Optional[str] = None) -> Optional[Dict]:
    """Worker function for concurrent search."""
    result = search_roll_all_combinations(roll_no, delay, specific_faculty)

    with progress_lock:
        progress["checked"] += 1
        progress["last_roll"] = roll_no
        if result:
            progress["found"] += 1
            # Save immediately
            with open(output_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "roll_no", "name", "father_name", "marks", "grade",
                    "faculty", "faculty_name", "exam_type"
                ])
                writer.writerow(result)

    return result


def get_eta(completed: int, total: int, elapsed_seconds: float) -> str:
    """Calculate estimated time remaining."""
    if completed == 0:
        return "Unknown"
    rate = completed / elapsed_seconds
    remaining = total - completed
    seconds = remaining / rate
    minutes = seconds / 60
    if minutes > 60:
        return f"{minutes/60:.1f} hours"
    return f"{minutes:.1f} minutes"


def load_roll_numbers_from_file(filename: str) -> List[str]:
    """Load roll numbers from text file (one per line)."""
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]


def run_search(output_file: str, workers: int = 10, delay: float = 0.05,
               roll_file: Optional[str] = None, start_roll: Optional[int] = None,
               end_roll: Optional[int] = None, specific_faculty: Optional[str] = None):
    """Run concurrent search across all roll numbers."""
    # Load roll numbers from file or generate from range
    if roll_file:
        roll_numbers = load_roll_numbers_from_file(roll_file)
        total = len(roll_numbers)
        range_str = f"File: {roll_file}"
    else:
        if start_roll is None or end_roll is None:
            raise ValueError("Either --file or both --start and --end must be provided")
        total = end_roll - start_roll + 1
        roll_numbers = [str(r) for r in range(start_roll, end_roll + 1)]
        range_str = f"Range: {start_roll:,} to {end_roll:,}"

    # Initialize output file with header
    out_dir = os.path.dirname(output_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "roll_no", "name", "father_name", "marks", "grade",
            "faculty", "faculty_name", "exam_type"
        ])
        writer.writeheader()

    progress["start_time"] = time.time()
    progress["checked"] = 0
    progress["found"] = 0

    # Determine faculty search info
    if specific_faculty:
        faculty_name = dict(FACULTIES).get(specific_faculty, specific_faculty)
        faculty_info = f"Faculty: {specific_faculty} ({faculty_name}) only"
    else:
        faculty_info = "Faculties: All 5 (sg -> sm -> se -> hmt -> com)"

    print(f"BIEK Regular Part II 2026 Roll Search")
    print(f"=" * 60)
    print(f"{range_str}")
    print(f"Total: {total:,} roll numbers")
    print(f"Workers: {workers}")
    print(f"Exam: Regular Part II 2026")
    print(f"{faculty_info}")
    print(f"Output: {output_file}")
    print()

    start_time = time.time()
    found_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(worker, roll, output_file, delay, specific_faculty): roll
            for roll in roll_numbers
        }

        completed = 0
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            result = future.result()

            if result and result.get("name"):
                found_count += 1
                # Print found students
                print(f"  FOUND: {result['roll_no']} | {result['name'][:30]} | {result['faculty_name']} | {result['exam_type']}")

            # Progress update every 500
            if completed % 500 == 0:
                elapsed = time.time() - start_time
                eta = get_eta(completed, total, elapsed)
                rate = completed / elapsed * 60
                print(f"[{completed:,}/{total:,}] Found: {found_count:,} | Rate: {rate:.0f}/min | ETA: {eta}")

    elapsed = time.time() - start_time
    print()
    print(f"=" * 60)
    print(f"COMPLETED!")
    print(f"Roll numbers checked: {total:,}")
    print(f"Students found: {found_count:,}")
    print(f"Total time: {elapsed/60:.1f} minutes")
    print(f"Average rate: {total/elapsed*60:.0f} rolls/minute")
    print(f"Results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="BIEK Regular Part II 2026 Roll Search - Search rolls from file or range across all faculties",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search from SG rolls file
  python bulk_search_all.py --file rollNumbers/sg_rolls.txt --output results/sg_results.csv --workers 20

  # Search from PM rolls file
  python bulk_search_all.py --file rollNumbers/pm_rolls.txt --output results/pm_results.csv --workers 20

  # Search by range (fallback)
  python bulk_search_all.py --start 700000 --end 700100 --workers 5 --output test.csv
        """
    )

    parser.add_argument(
        "--file",
        help="File containing roll numbers (one per line)"
    )

    parser.add_argument(
        "--start",
        type=int,
        help="Starting roll number (used if --file not provided)"
    )

    parser.add_argument(
        "--end",
        type=int,
        help="Ending roll number (used if --file not provided)"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Number of concurrent workers (default: 10)"
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.05,
        help="Delay between requests (default: 0.05)"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output CSV file"
    )

    parser.add_argument(
        "--faculty",
        choices=["sg", "sm", "se", "hmt", "com"],
        help="Search only in specific faculty (sg=Science General, sm=Pre-Medical, se=Pre-Engineering, hmt=Humanities, com=Commerce). If not specified, searches all faculties."
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.file and (args.start is None or args.end is None):
        parser.error("Either --file or both --start and --end must be provided")

    # Calculate total rolls for warning
    if args.file:
        with open(args.file, 'r') as f:
            total_rolls = sum(1 for line in f if line.strip())
    else:
        total_rolls = args.end - args.start + 1

    # Calculate API calls based on faculty filter
    if args.faculty:
        api_calls = total_rolls * 1  # Only 1 faculty
        faculty_info = f"1 faculty ({args.faculty})"
    else:
        api_calls = total_rolls * 5  # All 5 faculties
        faculty_info = "5 faculties"

    print(f"WARNING: This will search {total_rolls:,} roll numbers")
    print(f"Each roll requires up to {faculty_info} x 1 exam type")
    print(f"Estimated API calls: ~{api_calls:,}")
    print()

    run_search(
        output_file=args.output,
        workers=args.workers,
        delay=args.delay,
        roll_file=args.file,
        start_roll=args.start,
        end_roll=args.end,
        specific_faculty=args.faculty
    )


if __name__ == "__main__":
    main()
