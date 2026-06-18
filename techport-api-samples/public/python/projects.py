"""
TechPort API - Projects
=======================
NOTE: For simplicity, requests below show only required fields and responses are summarized, not shown in full. See the README's "A Note on These Examples" section for details.

Examples showing how to use the two main project endpoints:

  1. GET /api/projects
     Returns a list of project IDs. You can optionally filter by
     last-updated date. This is the starting point for browsing projects.

  2. GET /api/projects/{projectId}
     Returns the full details for one specific project — title, status,
     TRL, contacts, program, lead organization, and more.

No login or API key needed.
"""

import re
import requests

BASE_URL = "https://techport.nasa.gov"
HEADERS    = {"User-Agent": "Mozilla/5.0 (compatible; TechPortAPIClient/1.0)"}

# Set to False for dev VPC environments with self-signed SSL certificates.
# Set to True for production (techport.nasa.gov uses a valid certificate).
VERIFY_SSL = True   # Change to False if testing against the internal dev VPC


def remove_html_tags(text):
    """Strip HTML tags from text. Descriptions often contain tags like <p> and <br>."""
    if not text:
        return ""
    return re.sub(r"<[^>]+>", " ", text).strip()


# ENDPOINT: GET /api/projects
def list_projects(updated_since=None):
    """
    Returns a list of project IDs from TechPort.

    If you pass an updated_since date (formatted as "YYYY-MM-DD"), only
    projects updated on or after that date are included. This is useful
    for syncing or monitoring recent changes.

    Without a date filter, all ~20,000+ project IDs are returned.
    Each item in the list is a small dict containing just the projectId
    (and a few other lightweight fields). Use get_project() to get full details.

    Examples:
        # All projects updated this year
        projects = list_projects(updated_since="2024-01-01")

        # Every project in TechPort (large list)
        all_projects = list_projects()
    """
    url    = f"{BASE_URL}/api/projects"
    params = {}
    if updated_since:
        params["updatedSince"] = updated_since

    response = requests.get(url, params=params, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json().get("projects", [])


# ENDPOINT: GET /api/projects/{projectId}
def get_project(project_id):
    """
    Returns the full details for one project, looked up by its numeric ID.

    The returned dictionary contains all the project's fields. Key ones:
        projectId       - The unique ID number
        title           - Project name
        status          - "Active", "Completed", "Planned", or "Canceled"
        trlBegin        - Technology Readiness Level at start (1-9)
        trlCurrent      - Current TRL
        trlEnd          - Target TRL when the project finishes
        startYear/Month - When the project started
        endYear/Month   - When it's expected to end (or ended)
        description     - What the project does (may contain HTML)
        program         - The NASA program it belongs to
        responsibleMd   - The NASA Mission Directorate overseeing it
        leadOrganization - The main org doing the work
        projectContacts - List of people to contact, with their roles
        technologyOutcomes - What happened to the technology after the project
        libraryItems    - Attached documents and links
        viewCount       - How many times this project page has been viewed

    Example:
        project = get_project(184674)
        print(project["title"])   # "ISRU Power Architecture Study"
    """
    url      = f"{BASE_URL}/api/projects/{project_id}"
    response = requests.get(url, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json().get("project", {})


def print_project(project):
    """
    Prints a readable summary of a project to the terminal.
    Pass in the dictionary returned by get_project().
    """
    # Each of these nested fields may be absent on some projects,
    # so we default to an empty dict to avoid KeyError crashes
    program  = project.get("program") or {}
    md       = project.get("responsibleMd") or {}
    lead_org = project.get("leadOrganization") or {}
    contacts = project.get("projectContacts") or []
    outcomes = project.get("technologyOutcomes") or []
    library  = project.get("libraryItems") or []
    dest     = project.get("destinationType") or []

    # State is nested one level deeper inside stateTerritory
    state_info = lead_org.get("stateTerritory") or {}
    state      = state_info.get("abbreviation", "N/A")

    # Build a comma-separated list of destination types (e.g. "Mars, Moon and Cislunar")
    destinations = ", ".join(d for d in dest if d) if dest else "N/A"

    # Strip HTML from the description and trim it
    description = remove_html_tags(project.get("description", ""))
    if len(description) > 300:
        description = description[:300] + "..."

    print(f"  ID            : {project.get('projectId')}")
    print(f"  Title         : {project.get('title')}")
    print(f"  Acronym       : {project.get('acronym', 'N/A')}")
    print(f"  Status        : {project.get('status')} | Release: {project.get('releaseStatus')}")
    print(f"  Last Updated  : {project.get('lastUpdated')}")
    print(f"  Duration      : {project.get('startMonth')}/{project.get('startYear')} - {project.get('endMonth')}/{project.get('endYear')}")
    print(f"  TRL           : {project.get('trlBegin')} -> {project.get('trlCurrent')} -> {project.get('trlEnd')}  (begin / current / end)")
    print(f"  Program       : [{program.get('programId')}] {program.get('title')} ({program.get('acronym')})")
    print(f"  Directorate   : {md.get('organizationName')} ({md.get('acronym')})")
    print(f"  Lead Org      : {lead_org.get('organizationName')} ({lead_org.get('organizationType')}) - {lead_org.get('city', 'N/A')}, {state}")
    print(f"  Destinations  : {destinations}")
    print(f"  Views         : {project.get('viewCount', 0):,}")
    print(f"  Tech Outcomes : {len(outcomes)}")
    print(f"  Library Items : {len(library)}")

    # Print each contact with their role and email
    if contacts:
        print(f"  Contacts:")
        for c in contacts:
            print(f"    - {c.get('fullName')} ({c.get('projectContactRolePretty')}) - {c.get('email', 'N/A')}")

    # Print up to 3 library items
    if library:
        print(f"  Library Items:")
        for item in library[:3]:
            link = item.get("url") or "(file attachment — no URL)"
            print(f"    - {item.get('title')} [{item.get('libraryItemType', 'N/A')}] - {link}")

    # Print up to 3 technology outcomes
    if outcomes:
        print(f"  Technology Outcomes:")
        for o in outcomes[:3]:
            path = o.get("technology_outcome_path") or o.get("technologyOutcomePath", "N/A")
            date = o.get("technology_outcome_date") or o.get("technologyOutcomeDate", "N/A")
            print(f"    - {path} ({date})")

    if description:
        print(f"  Description   : {description}")


# ── Examples ──────────────────────────────────────────────────────────────────
# The code below runs when you execute this file directly: python projects.py
# It won't run if you import this file from another script.

if __name__ == "__main__":

    # Example 1: List projects updated recently
    print("=== Projects updated since 2024-01-01 ===")
    projects = list_projects(updated_since="2024-01-01")
    print(f"Total: {len(projects):,}")
    print(f"First 5 IDs: {[p.get('projectId') for p in projects[:5]]}")
    print()

    # Example 2: Count all projects in TechPort
    print("=== Total projects in TechPort ===")
    all_projects = list_projects()
    print(f"Total: {len(all_projects):,}")
    print()

    # Example 3: Get full details for a specific project
    print("=== Full detail: project 184674 (ISRU Power Architecture Study) ===")
    project = get_project(184674)
    print_project(project)
    print()

    # Example 4: Get the most recently updated project
    if projects:
        latest_id = projects[0].get("projectId")
        print(f"=== Most recently updated project (ID: {latest_id}) ===")
        latest = get_project(latest_id)
        print_project(latest)
