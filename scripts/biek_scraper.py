"""
BIEK Results Scraper
Board of Intermediate Education Karachi - Result Lookup (Part II 2026)

Usage:
    python scripts/biek_scraper.py --roll-numbers 607192 615380 --faculty sg
    python scripts/biek_scraper.py --file rollNumbers/sg_rolls.txt --faculty sg --output results/sg_results.csv
"""

import requests
import json
import csv
import argparse
import time
from typing import List, Dict, Optional

# API Configuration (Mobile App Production Endpoint)
API_URL = "http://api.biekedu.com/search"

# Faculty codes mapping (with display names)
FACULTY_CODES = {
    "pre-medical": "sm",
    "pre-engineering": "se",
    "science general": "sg",
    "humanities": "hmt",
    "commerce": "com"
}

# Faculty display names
FACULTY_NAMES = {
    "sm": "Pre-Medical",
    "se": "Pre-Engineering",
    "sg": "Science General",
    "hmt": "Humanities",
    "com": "Commerce"
}

# Exam type codes mapping (Regular Part II 2026 by default)
TYPE_CODES = {
    "regular part ii": "reg-p2-a-2026",
    "private part ii": "pvt-p2-a-2026"
}

# Default headers matching the mobile app
HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "User-Agent": "Dart/3.4 (dart:io)"
}


def search_result(
    roll_no: str,
    matric_roll_no: str,
    faculty: str = "sg",
    exam_type: str = "reg-p2-a-2026",
    delay: float = 0.5
) -> Dict:
    """
    Search for a single result.

    Args:
        roll_no: Intermediate roll number
        matric_roll_no: Matric roll number
        faculty: Faculty code (default: sg - Science General)
        exam_type: Exam type code (default: reg-p2-a-2026 - Regular Part II)
        delay: Delay in seconds between requests

    Returns:
        Dictionary with result data
    """
    payload = {
        "faculty": faculty,
        "value": exam_type,
        "roll_no": roll_no,
        "matric_roll_no": matric_roll_no
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
            return {
                "roll_no": roll_no,
                "matric_roll_no": matric_roll_no,
                "faculty": faculty,
                "status": "success",
                "data": data
            }
        else:
            return {
                "roll_no": roll_no,
                "matric_roll_no": matric_roll_no,
                "faculty": faculty,
                "status": "error",
                "error": f"HTTP {response.status_code}"
            }

    except Exception as e:
        return {
            "roll_no": roll_no,
            "matric_roll_no": matric_roll_no,
            "faculty": faculty,
            "status": "error",
            "error": str(e)
        }

    finally:
        time.sleep(delay)


def extract_student_info(result_data: Dict) -> Dict:
    """Extract student details from API response."""
    if result_data.get("status") != "success":
        return {
            "name": "N/A",
            "father_name": "N/A",
            "marks": "N/A",
            "grade": "N/A",
            "faculty": result_data.get("faculty", "N/A"),
            "status": result_data.get("status"),
            "error": result_data.get("error", "Unknown error")
        }

    try:
        data = result_data.get("data", {})
        detail = data.get("detail", {})
        
        # Check if student was actually found
        if not detail or not detail.get("applicant_name"):
            return {
                "name": "N/A",
                "father_name": "N/A",
                "marks": "N/A",
                "grade": "N/A",
                "faculty": FACULTY_NAMES.get(result_data.get("faculty", ""), result_data.get("faculty", "N/A")),
                "status": "NOT FOUND",
                "error": "No data found for this roll number"
            }

        grade_raw = detail.get("grade")
        grade = str(grade_raw).lower() if grade_raw is not None else ""

        # Determine pass/fail status based on grade
        if grade in ["pass", "a-1", "a", "b", "c", "d", "e"]:
            status = "PASS"
        elif grade in ["fail", "f"]:
            status = "FAIL"
        else:
            status = grade.upper() if grade else "UNKNOWN"

        faculty_code = result_data.get("faculty", "N/A")
        faculty_name = FACULTY_NAMES.get(faculty_code, faculty_code)

        return {
            "name": detail.get("applicant_name", "N/A"),
            "father_name": detail.get("father_name", "N/A"),
            "marks": str(detail.get("secured_total", "N/A")),
            "grade": detail.get("grade", "N/A"),
            "faculty": faculty_name,
            "status": status,
            "error": None
        }
    except Exception as e:
        return {
            "name": "N/A",
            "father_name": "N/A",
            "marks": "N/A",
            "grade": "N/A",
            "faculty": "N/A",
            "status": "error",
            "error": str(e)
        }


def search_across_all_faculties(
    roll_no: str,
    matric_roll_no: str,
    exam_type: str = "reg-p2-a-2026",
    delay: float = 0.5
) -> Dict:
    """
    Search for a roll number across all faculties until found.

    Args:
        roll_no: Intermediate roll number
        matric_roll_no: Matric roll number
        exam_type: Exam type code
        delay: Delay between requests (seconds)

    Returns:
        Dictionary with result data from the first faculty where found
    """
    faculties = ["sg", "sm", "se", "hmt", "com"]  # Order: sg first as it's most common

    for faculty in faculties:
        result = search_result(roll_no, matric_roll_no, faculty, exam_type, delay)

        # Check if we got a valid result (success with student data)
        if result.get("status") == "success":
            data = result.get("data", {})
            detail = data.get("detail", {})
            if detail.get("roll_no") and detail.get("applicant_name"):
                return result

        # If not found (empty detail), continue to next faculty
        # But don't retry if we got an HTTP error
        if result.get("status") == "error":
            continue

    return result


def bulk_search(
    roll_numbers: List[str],
    faculty: str = "sg",
    exam_type: str = "reg-p2-a-2026",
    delay: float = 0.5,
    output_file: Optional[str] = None,
    search_all_faculties: bool = False
) -> List[Dict]:
    """
    Search for multiple results.

    Args:
        roll_numbers: List of roll numbers to search
        faculty: Faculty code (default: sg)
        exam_type: Exam type code (default: reg-p2-a-2026)
        delay: Delay between requests (seconds)
        output_file: Optional CSV output file
        search_all_faculties: If True, search across all faculties until found

    Returns:
        List of result dictionaries
    """
    results = []

    if search_all_faculties:
        print(f"Searching {len(roll_numbers)} roll numbers across ALL faculties...")
    else:
        print(f"Searching {len(roll_numbers)} roll numbers...")
        print(f"Faculty: {faculty}, Exam Type: {exam_type}")

    print("-" * 50)

    for i, roll in enumerate(roll_numbers, 1):
        print(f"[{i}/{len(roll_numbers)}] Searching roll {roll}...", end=" ")

        if search_all_faculties:
            result = search_across_all_faculties(roll, roll, exam_type, delay)
        else:
            result = search_result(roll, roll, faculty, exam_type, delay)

        student_info = extract_student_info(result)

        if student_info.get("status") == "PASS":
            faculty_str = f" [{student_info.get('faculty', '')}]" if search_all_faculties else ""
            print(f"PASS{faculty_str} - {student_info.get('name', 'N/A')} ({student_info.get('marks', 'N/A')} marks)")
        elif student_info.get("status") == "FAIL":
            faculty_str = f" [{student_info.get('faculty', '')}]" if search_all_faculties else ""
            print(f"FAIL{faculty_str} - {student_info.get('name', 'N/A')}")
        else:
            print(f"ERROR - {student_info.get('error', 'Unknown')}")

        results.append({
            "roll_no": roll,
            **student_info
        })

    print("-" * 50)
    print(f"Completed! Found {len(results)} results.")

    # Save to CSV if output file specified
    if output_file:
        save_to_csv(results, output_file)
        print(f"Results saved to: {output_file}")

    return results


def save_to_csv(results: List[Dict], filename: str):
    """Save results to CSV file."""
    fieldnames = ["roll_no", "name", "father_name", "marks", "grade", "faculty", "status", "error"]

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def load_roll_numbers_from_file(filename: str) -> List[str]:
    """Load roll numbers from text file (one per line)."""
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]


def main():
    parser = argparse.ArgumentParser(
        description="BIEK Results Bulk Search Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search individual roll numbers
  python biek_scraper.py --roll-numbers 716937 716938 716939

  # Search from file
  python biek_scraper.py --file roll_numbers.txt

  # Search with specific faculty and exam type (Part II 2026 is the default)
  python biek_scraper.py --roll-numbers 716937 --faculty pm --exam-type reg-p2-a-2026

  # Search across ALL faculties automatically (finds students in any group)
  python biek_scraper.py --roll-numbers 716937 716938 --all-faculties

  # Save results to CSV
  python biek_scraper.py --roll-numbers 716937 716938 --output results.csv
        """
    )

    parser.add_argument(
        "--roll-numbers",
        nargs="+",
        help="Roll numbers to search (space-separated)"
    )

    parser.add_argument(
        "--file",
        help="File containing roll numbers (one per line)"
    )

    parser.add_argument(
        "--output",
        help="Output CSV file path"
    )

    parser.add_argument(
        "--faculty",
        default="sg",
        choices=list(FACULTY_CODES.values()),
        help="Faculty code (default: sg)"
    )

    parser.add_argument(
        "--exam-type",
        default="reg-p2-a-2026",
        choices=list(TYPE_CODES.values()),
        help="Exam type code (default: reg-p2-a-2026 - Regular Part II 2026)"
    )

    parser.add_argument(
        "--all-faculties",
        action="store_true",
        help="Search across all faculties until student is found"
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between requests in seconds (default: 0.5)"
    )

    args = parser.parse_args()

    # Collect roll numbers
    roll_numbers = []

    if args.roll_numbers:
        roll_numbers.extend(args.roll_numbers)

    if args.file:
        roll_numbers.extend(load_roll_numbers_from_file(args.file))

    if not roll_numbers:
        parser.error("Please provide --roll-numbers or --file")

    # Remove duplicates while preserving order
    roll_numbers = list(dict.fromkeys(roll_numbers))

    # Convert all to strings
    roll_numbers = [str(r) for r in roll_numbers]

    # Run bulk search
    bulk_search(
        roll_numbers,
        faculty=args.faculty,
        exam_type=args.exam_type,
        delay=args.delay,
        output_file=args.output,
        search_all_faculties=args.all_faculties
    )


if __name__ == "__main__":
    main()
