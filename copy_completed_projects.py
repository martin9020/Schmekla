#!/usr/bin/env python3
"""
Copy completed Clovis Canopy projects to D:\Completed-Projects
A completed project = has PDF files in its structure
Canceled projects = empty folders or only quotes/no PDFs
"""

import os
import shutil
from pathlib import Path
from typing import List, Tuple
import argparse


def long_path(path: Path) -> str:
    """Convert path to Windows long path format (handles paths > 260 chars)"""
    path_str = str(path.resolve())
    if not path_str.startswith("\\\\?\\"):
        return "\\\\?\\" + path_str
    return path_str


def copy_with_long_paths(src: Path, dst: Path):
    """Copy directory tree handling Windows long paths"""
    src_long = long_path(src)
    dst_long = long_path(dst)

    # Create destination
    os.makedirs(dst_long, exist_ok=True)

    errors = []

    for root, dirs, files in os.walk(src_long):
        # Calculate relative path from source
        rel_path = os.path.relpath(root, src_long)
        dest_dir = os.path.join(dst_long, rel_path) if rel_path != "." else dst_long

        # Create subdirectories
        for d in dirs:
            dir_path = os.path.join(dest_dir, d)
            try:
                os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                errors.append((os.path.join(root, d), dir_path, str(e)))

        # Copy files
        for f in files:
            src_file = os.path.join(root, f)
            dst_file = os.path.join(dest_dir, f)
            try:
                shutil.copy2(src_file, dst_file)
            except Exception as e:
                errors.append((src_file, dst_file, str(e)))

    return errors

def find_projects_with_pdfs(base_path: Path) -> List[Tuple[Path, str, int]]:
    """
    Find all projects that contain PDF files.
    
    Returns:
        List of tuples: (project_path, letter, job_number)
    """
    completed_projects = []
    
    if not base_path.exists():
        print(f"ERROR: Base path does not exist: {base_path}")
        return completed_projects
    
    print(f"Scanning: {base_path}")
    
    # Iterate through letter folders (A-Z)
    for letter_folder in sorted(base_path.iterdir()):
        if not letter_folder.is_dir() or len(letter_folder.name) != 1 or not letter_folder.name.isalpha():
            continue
            
        print(f"\nScanning letter folder: {letter_folder.name}")
        
        # Iterate through project folders in each letter folder
        for project_folder in sorted(letter_folder.iterdir()):
            if not project_folder.is_dir():
                continue
                
            # Look for job number subfolder (numeric)
            job_folder = None
            for subfolder in project_folder.iterdir():
                if subfolder.is_dir() and subfolder.name.isdigit():
                    job_folder = subfolder
                    break
            
            if not job_folder:
                continue
                
            job_number = int(job_folder.name)
            
            # Check if this project contains PDF files
            has_pdfs = False
            for pdf_file in job_folder.rglob("*.pdf"):
                if pdf_file.is_file():
                    has_pdfs = True
                    break
            
            if has_pdfs:
                completed_projects.append((job_folder, letter_folder.name, job_number))
                print(f"  * Found: {project_folder.name} (Job #{job_number})")
    
    return completed_projects

def copy_project_structure(project_path: Path, letter: str, job_number: int, dest_base: Path, dry_run: bool = False, force: bool = False) -> str:
    """
    Copy entire project structure maintaining organization.
    Returns: "success", "skipped", or "error"
    """
    project_name = project_path.parent.name
    dest_path = dest_base / letter / project_name / str(job_number)

    print(f" {'[DRY RUN] ' if dry_run else ''}Copying:")
    print(f"  From: {project_path}")
    print(f"  To:   {dest_path}")

    if dry_run:
        return "success"

    # Check if destination already exists
    dest_long = long_path(dest_path)
    if os.path.exists(dest_long):
        if force:
            print(f"  Destination exists, removing for re-copy (--force)...")
            try:
                shutil.rmtree(dest_long)
            except Exception as e:
                print(f"  ERROR: Could not remove existing folder - {e}")
                return "error"
        else:
            print(f"  Skipping (already exists)")
            return "skipped"

    # Copy entire folder content using long path handling
    errors = copy_with_long_paths(project_path, dest_path)

    if errors:
        print(f"  WARNING: {len(errors)} file(s) failed to copy:")
        for src, dst, err in errors[:5]:  # Show first 5 errors
            print(f"    - {os.path.basename(src)}: {err}")
        if len(errors) > 5:
            print(f"    ... and {len(errors) - 5} more")

    # Count copied files
    try:
        file_count = sum(1 for _ in Path(dest_long).rglob("*") if _.is_file())
        pdf_count = sum(1 for _ in Path(dest_long).rglob("*.pdf") if _.is_file())
        print(f"  * Copied: {file_count} files ({pdf_count} PDFs)")
    except Exception:
        print(f"  * Copied (could not count files)")

    return "success" if not errors else "error"

def main():
    parser = argparse.ArgumentParser(description="Copy completed Clovis Canopy projects")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied without actually copying")
    parser.add_argument("--force", action="store_true", help="Re-copy even if destination exists (deletes and re-copies)")
    parser.add_argument("--source", default=r"D:\Clovis Canopies\Clovis Canopies Team Site - Documents\Customer",
                       help="Source customer folder")
    parser.add_argument("--dest", default=r"D:\Completed-Projects",
                       help="Destination folder for completed projects")
    parser.add_argument("--letter", help="Only process specific letter (A-Z)")
    
    args = parser.parse_args()
    
    source_path = Path(args.source)
    dest_path = Path(args.dest)
    
    print("=" * 60)
    print("Clovis Canopies - Completed Projects Copy Tool")
    print("=" * 60)
    
    # Find all projects with PDFs
    completed_projects = find_projects_with_pdfs(source_path)
    
    # Filter by letter if specified
    if args.letter:
        completed_projects = [(p, l, j) for p, l, j in completed_projects if l.upper() == args.letter.upper()]
    
    print(f"\n{'=' * 60}")
    print(f"Found {len(completed_projects)} completed projects")
    print(f"{'=' * 60}")
    
    if not completed_projects:
        print("No completed projects found!")
        return
    
    # Group by letter for summary
    by_letter = {}
    for _, letter, _ in completed_projects:
        by_letter[letter] = by_letter.get(letter, 0) + 1
    
    print("Projects by letter:")
    for letter in sorted(by_letter.keys()):
        print(f"  {letter}: {by_letter[letter]} projects")
    
    # Copy projects
    print(f"\n{'=' * 60}")
    if args.dry_run:
        print("DRY RUN MODE - No files will be copied")
    if args.force:
        print("FORCE MODE - Will re-copy existing folders")
    print(f"{'=' * 60}")

    success_count = 0
    skip_count = 0
    error_count = 0

    for i, (project_path, letter, job_number) in enumerate(completed_projects, 1):
        print(f"\n[{i}/{len(completed_projects)}]", end="")
        result = copy_project_structure(project_path, letter, job_number, dest_path, args.dry_run, args.force)
        if result == "success":
            success_count += 1
        elif result == "skipped":
            skip_count += 1
        else:
            error_count += 1

    print(f"\n{'=' * 60}")
    print(f"Completed! {'(Dry run - no files copied)' if args.dry_run else ''}")
    print(f"  Copied: {success_count}")
    print(f"  Skipped: {skip_count}")
    print(f"  Errors: {error_count}")
    print(f"Destination: {dest_path}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()