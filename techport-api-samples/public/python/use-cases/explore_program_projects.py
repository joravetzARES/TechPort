"""
TechPort API - Use Case: Explore Projects by Program
=====================================================
NOTE: For simplicity, requests below show only required fields and responses are summarized, not shown in full. See the README's "A Note on These Examples" section for details.

A realistic multi-step workflow that demonstrates how to:
  1. List all active NASA programs
  2. Let the user pick one
  3. Fetch a sample of recent projects and filter to the chosen program
  4. Enrich matches with full project details
  5. Print a summary table and export a CSV

No authentication required.

NOTE ON FILTERING:
  The public API does not support filtering projects by program directly.
  This script fetches recently updated project IDs in batches and checks
  each one's programId against the chosen program. It stops once it has
  found enough matches or has scanned a reasonable number of projects.
  For full filtered access, use the internal search endpoint with an API key.

Run:
    python explore_program_projects.py
"""

import csv
import requests

BASE_URL    = "https://techport.nasa.gov"
HEADERS     = {"User-Agent": "Mozilla/5.0 (compatible; TechPortAPIClient/1.0)"}
OUTPUT_FILE = "program_projects.csv"

# How many matching projects to collect and how many IDs to scan at most
TARGET_MATCHES = 10
MAX_SCAN       = 500


# ENDPOINT: GET /api/programs
def get_programs(active_only=True):
    """Fetch all NASA programs."""
    response = requests.get(
        f"{BASE_URL}/api/programs",
        params={"activeOnly": str(active_only).lower()},
        headers=HEADERS,
    )
    response.raise_for_status()
    return response.json().get("programs", [])


# ENDPOINT: GET /api/projects
def get_project_ids(updated_since="2020-01-01"):
    """
    Fetch project IDs updated since a given date.
    Returns a list of dicts with at minimum a projectId field.
    """
    response = requests.get(
        f"{BASE_URL}/api/projects",
        params={"updatedSince": updated_since},
        headers=HEADERS,
    )
    response.raise_for_status()
    return response.json().get("projects", [])


# ENDPOINT: GET /api/projects/{projectId}
def get_project_detail(project_id):
    """Fetch full details for a single project."""
    response = requests.get(
        f"{BASE_URL}/api/projects/{project_id}",
        headers=HEADERS,
    )
    response.raise_for_status()
    return response.json().get("project", {})


def export_to_csv(projects, output_path):
    """Export a list of project dicts to a CSV file."""
    if not projects:
        print("No projects to export.")
        return

    fields = ["projectId", "title", "status", "trlCurrent",
              "startYear", "endYear", "program", "responsibleMd"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for p in projects:
            writer.writerow({
                "projectId":     p.get("projectId"),
                "title":         p.get("title"),
                "status":        p.get("status"),
                "trlCurrent":    p.get("trlCurrent"),
                "startYear":     p.get("startYear"),
                "endYear":       p.get("endYear"),
                "program":       (p.get("program") or {}).get("title", ""),
                "responsibleMd": (p.get("responsibleMd") or {}).get("organizationName", ""),
            })
    print(f"\nExported {len(projects)} project(s) to: {output_path}")


def main():
    # ── Step 1: List all programs and let user pick by ID ────────────────────
    print("Fetching active NASA programs...\n")
    programs   = get_programs(active_only=True)
    id_to_prog = {p.get("programId"): p for p in programs}

    # Group by mission directorate for readability
    by_md = {}
    for p in programs:
        md = (p.get("responsibleMd") or {}).get("acronym", "Unknown")
        by_md.setdefault(md, []).append(p)

    print(f"{'ID':<8} {'Title'}")
    print("-" * 70)
    for md in sorted(by_md):
        print(f"  [{md}]")
        for p in by_md[md]:
            print(f"  {p.get('programId'):<8} {p.get('title')}")
    print(f"\nTotal: {len(programs)} active programs")

    # ── Step 2: Ask for a program ID ─────────────────────────────────────────
    print()
    while True:
        raw = input("Enter a Program ID from the list above: ").strip()
        if not raw.isdigit():
            print("  Please enter a numeric ID.")
            continue
        program_id = int(raw)
        if program_id not in id_to_prog:
            print(f"  ID {program_id} not found in the list. Please try again.")
            continue
        break

    chosen = id_to_prog[program_id]
    print(f"\nSelected: [{program_id}] {chosen.get('title')}")

    # ── Step 2: Fetch recent project IDs ────────────────────────────────────
    print(f"\nFetching recently updated project IDs (since 2020-01-01)...")
    all_ids = get_project_ids(updated_since="2020-01-01")
    print(f"Total IDs to scan: {len(all_ids):,} (will stop after {TARGET_MATCHES} matches "
          f"or {MAX_SCAN} scanned)")

    # ── Step 3: Scan projects and collect those matching the program ──────────
    print(f"\nScanning projects for program {program_id}...")
    detailed = []
    scanned  = 0

    for entry in all_ids[:MAX_SCAN]:
        pid = entry.get("projectId")
        try:
            project = get_project_detail(pid)
            scanned += 1
            proj_program_id = (project.get("program") or {}).get("programId")

            if proj_program_id == program_id:
                detailed.append(project)
                print(f"  Match {len(detailed)}: [{pid}] {project.get('title')}")
                if len(detailed) >= TARGET_MATCHES:
                    print(f"  Reached target of {TARGET_MATCHES} matches — stopping scan.")
                    break
            elif scanned % 50 == 0:
                print(f"  Scanned {scanned}/{min(MAX_SCAN, len(all_ids))}... "
                      f"({len(detailed)} matches so far)")

        except requests.HTTPError as e:
            print(f"  Error fetching {pid}: {e}")

    print(f"\nScan complete. Scanned {scanned} projects, found {len(detailed)} in program.")

    if not detailed:
        print("No matching projects found. Try a different program or increase MAX_SCAN.")
        return

    # ── Step 4: Print summary table ──────────────────────────────────────────
    print(f"\n{'ID':<10} {'TRL':<5} {'Status':<12} {'Title'}")
    print("-" * 72)
    for p in detailed:
        trl   = str(p.get("trlCurrent", "?"))
        title = (p.get("title") or "")[:42]
        print(f"{p.get('projectId'):<10} {trl:<5} {p.get('status', 'N/A'):<12} {title}")

    # ── Step 5: Export to CSV ────────────────────────────────────────────────
    export_to_csv(detailed, OUTPUT_FILE)


if __name__ == "__main__":
    main()
