#!/usr/bin/env python3
# Shebang tells Unix-like systems how to execute the file (useful if you make it executable).

"""Gradebook Manager
Simple command-line gradebook that stores student records in a CSV file.
Features: add student, delete student by id, list students, show average/high/low.
This file is heavily commented so each line's purpose and rationale is clear.
"""

# --- Imports: bring in modules we need and why ---
import csv                      # csv module - read/write CSV files in a structured way
import os                       # os module - check for file existence and work with filesystem
from typing import List, Dict   # typing - help indicate expected data shapes (List, Dict) for clarity
from statistics import mean     # mean function - compute average grade easily and correctly
import sys                      # sys - used to exit program cleanly if needed

# --- Constants: configuration you can change later ---
CSV_FILE = "grades.csv"         # filename where student data will be stored
FIELDNAMES = ["id", "name", "subject", "grade"]  # CSV header columns and their order

# --- Utility: ensure CSV file exists with header ---
def ensure_file():
    """Create CSV_FILE with header if it doesn't exist yet."""
    if not os.path.exists(CSV_FILE):                    # check if the file already exists
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
            # open file in write mode; newline="" prevents extra blank lines on Windows
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            # create a DictWriter tied to our FIELDNAMES so writes are consistent
            writer.writeheader()                        # write CSV header so file has column names

# --- Load students: read CSV rows and normalize types ---
def load_students() -> List[Dict]:
    """
    Read CSV_FILE and return a list of student dicts with types:
    - id: int
    - name: str
    - subject: str
    - grade: int (0-100) or None if invalid
    """
    ensure_file()                                      # make sure file exists before trying to open
    students: List[Dict] = []                          # prepare empty list to collect rows
    with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)                     # DictReader yields each row as a dict (keys = header)
        for row in reader:
            # defensive: skip empty rows (if any)
            if not row or not row.get("id"):
                continue
            # parse id to integer (if invalid, skip row)
            try:
                sid = int(row["id"])
            except (ValueError, TypeError):
                continue
            # parse grade to integer if possible; if not, set None
            grade_raw = row.get("grade", "").strip()
            try:
                grade_val = int(grade_raw) if grade_raw != "" else None
            except ValueError:
                grade_val = None
            # build normalized dict and append to list
            students.append({
                "id": sid,
                "name": row.get("name", "").strip(),
                "subject": row.get("subject", "").strip(),
                "grade": grade_val
            })
    return students                                     # return the list to caller

# --- Save students: write the list of dicts back to CSV ---
def save_students(students: List[Dict]):
    """Write students list to CSV_FILE, converting values to strings."""
    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()                            # write header first
        for s in students:
            # convert types to strings (CSV stores text)
            writer.writerow({
                "id": str(s["id"]),
                "name": s.get("name", ""),
                "subject": s.get("subject", ""),
                "grade": "" if s.get("grade") is None else str(s["grade"])
            })

# --- Utility: compute next available id ---
def next_id(students: List[Dict]) -> int:
    """Return next numeric id for a new student (1-based)."""
    if not students:
        return 1
    # compute max id and add 1 — ensures uniqueness even if rows were deleted
    return max(s["id"] for s in students) + 1

# --- Feature: add a new student interactively ---
def add_student():
    """Prompt user for student details, validate input, save new student to CSV."""
    students = load_students()                          # load existing students
    sid = next_id(students)                            # decide id for new student

    # Name input: require non-empty name
    name = input("Student name: ").strip()
    if not name:
        print("Name cannot be empty. Cancelled.")
        return

    # Subject input: allow empty but trim whitespace
    subject = input("Subject (e.g., Math): ").strip() or "General"

    # Grade input: must be integer between 0 and 100
    grade_raw = input("Grade (0-100): ").strip()
    try:
        grade_val = int(grade_raw)
        if grade_val < 0 or grade_val > 100:
            print("Grade must be between 0 and 100. Cancelled.")
            return
    except ValueError:
        print("Invalid grade. Use an integer between 0 and 100. Cancelled.")
        return

    # Build student dict and append to list, then save
    new_student = {"id": sid, "name": name, "subject": subject, "grade": grade_val}
    students.append(new_student)
    save_students(students)
    print(f"Added student id={sid}: {name} ({subject}) grade={grade_val}")

# --- Feature: delete a student by id ---
def delete_student():
    """List students, ask for id to delete, confirm, then remove & save."""
    students = load_students()
    if not students:
        print("No students found.")
        return

    list_students(students, limit=50)                   # show students so user sees ids

    # Prompt for id and validate
    try:
        sid = int(input("Enter student id to delete: ").strip())
    except (ValueError, TypeError):
        print("Invalid id. Cancelled.")
        return

    # Find the student to delete (if any)
    target = next((s for s in students if s["id"] == sid), None)
    if not target:
        print("No student with that id. Nothing deleted.")
        return

    # Confirm deletion
    confirm = input(f"Delete {target['name']} (id={sid})? Type 'yes' to confirm: ").strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        return

    # Filter out the chosen student and save
    students = [s for s in students if s["id"] != sid]
    save_students(students)
    print(f"Deleted student id={sid}.")

# --- Feature: list students in table form ---
def list_students(students: List[Dict] = None, limit: int = 20):
    """
    Print students table. If students is None, load from CSV.
    limit controls how many rows to show (most recent ids first).
    """
    if students is None:
        students = load_students()
    if not students:
        print("No students to list.")
        return

    # Sort by id descending so newest entries show first; stable and simple
    students_sorted = sorted(students, key=lambda x: x["id"], reverse=True)

    # Print a simple table header
    print(f"{'id':<4} {'name':<20} {'subject':<15} {'grade':>6}")
    print("-" * 50)
    # Print each student up to the limit
    for s in students_sorted[:limit]:
        grade_str = "" if s.get("grade") is None else str(s["grade"])
        print(f"{s['id']:<4} {s['name'][:20]:<20} {s.get('subject','')[:15]:<15} {grade_str:>6}")

# --- Feature: compute class statistics ---
def show_stats(subject_filter: str = None):
    """
    Compute and print average, highest, and lowest grades.
    If subject_filter is provided, compute stats only for that subject.
    """
    students = load_students()
    if not students:
        print("No students to compute statistics.")
        return

    # Optionally filter by subject (case-insensitive)
    if subject_filter:
        filtered = [s for s in students if s.get("subject","").lower() == subject_filter.lower() and s.get("grade") is not None]
        title = f"Statistics for subject: {subject_filter}"
    else:
        filtered = [s for s in students if s.get("grade") is not None]
        title = "Statistics (all students)"

    if not filtered:
        print("No graded students found for this selection.")
        return

    grades = [s["grade"] for s in filtered]            # extract list of integer grades
    avg = mean(grades)                                 # compute mean using statistics.mean
    highest = max(grades)                              # max grade
    lowest = min(grades)                               # min grade

    # Print results with clear labels
    print(title)
    print(f" - Count: {len(grades)}")
    print(f" - Average grade: {avg:.2f}")
    print(f" - Highest grade: {highest}")
    print(f" - Lowest grade: {lowest}")

# --- Main interactive loop: menu-driven CLI ---
def main():
    """Run the command-line menu loop until the user quits."""
    ensure_file()                                      # ensure file exists before interacting
    print("Gradebook Manager — commands: add, delete, list, stats, quit")
    while True:
        cmd = input("\nEnter command (add/list/delete/stats/quit): ").strip().lower()
        if not cmd:
            continue                                  # empty input -> reprompt
        if cmd in ("add", "a"):
            add_student()                             # add new student
        elif cmd in ("delete", "del", "d"):
            delete_student()                          # delete by id
        elif cmd in ("list", "l"):
            list_students()                           # list students
        elif cmd in ("stats", "s"):
            subj = input("Enter subject to filter or press Enter for all: ").strip()
            show_stats(subj or None)                  # show stats, maybe filtered
        elif cmd in ("quit", "q", "exit"):
            print("Goodbye.")
            sys.exit(0)                              # exit program cleanly
        else:
            print("Unknown command. Try: add, list, delete, stats, quit")

# Standard Python entry point guard so functions run only when script executed directly
if __name__ == "__main__":
    main()
