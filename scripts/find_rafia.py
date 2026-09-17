"""
Find Rafia Siddiqui in Riaz Govt. Girls College 123 Passed Rolls
"""

import sys
import time
import requests

URL = "http://api.biekedu.com/search"
HEADERS = {
    "User-Agent": "Dart/3.4 (dart:io)",
    "Content-Type": "application/json"
}

def main():
    print("=" * 60)
    print("  Searching for RAFIA (Father: MUHAMMAD ZUBAIR)")
    print("  Target College: Riaz Govt. Girls College Liaquatabad No. 10")
    print("=" * 60)

    try:
        with open("rollNumbers/riaz_college_rolls.txt", "r") as f:
            rolls = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading rolls file: {e}")
        return

    print(f"Loaded {len(rolls)} rolls to check.\n")

    session = requests.Session()
    found = False

    for i, roll in enumerate(rolls, 1):
        payload = {
            "faculty": "sm",
            "value": "reg-p2-a-2026",
            "roll_no": roll
        }

        try:
            resp = session.post(URL, json=payload, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    student = data[0]
                    name = student.get("applicant_name", "").strip()
                    father = student.get("father_name", "").strip()
                    marks = student.get("total_marks", "N/A")
                    grade = student.get("grade", "N/A")
                    college = student.get("college_name", "N/A")

                    print(f"[{i}/{len(rolls)}] Roll {roll}: {name} d/o {father} -> {marks} ({grade})")

                    # Check for Rafia / Zubair
                    if "RAFIA" in name.upper() or "ZUBAIR" in father.upper():
                        print("\n" + "*" * 60)
                        print("  MATCH FOUND!")
                        print(f"  Roll Number: {roll}")
                        print(f"  Name:        {name}")
                        print(f"  Father Name: {father}")
                        print(f"  Total Marks: {marks}")
                        print(f"  Grade:       {grade}")
                        print(f"  College:     {college}")
                        print("*" * 60 + "\n")
                        found = True
                        break
                else:
                    print(f"[{i}/{len(rolls)}] Roll {roll}: No record found")
            else:
                print(f"[{i}/{len(rolls)}] Roll {roll}: Server status {resp.status_code}")

        except requests.exceptions.ConnectTimeout:
            print("\n[ERROR] Connection timed out!")
            print("Your current IP is still temporarily blocked by the BIEK server firewall.")
            print("To fix immediately: Turn on your phone's mobile hotspot and connect your PC to it.\n")
            return
        except Exception as e:
            print(f"[{i}/{len(rolls)}] Roll {roll}: Error ({e})")

        time.sleep(0.3)

    if not found:
        print("\nSearch finished across checked rolls.")

if __name__ == "__main__":
    main()
