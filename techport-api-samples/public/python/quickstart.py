"""
TechPort API - Quickstart
=========================
NOTE: For simplicity, requests below show only required fields and responses are summarized, not shown in full. See the README's "A Note on These Examples" section for details.

The best place to start. This script:
  1. Fetches a list of recently updated NASA technology projects
  2. Gets the full details for the first 5
  3. Prints a readable summary of each one

No login or API key needed. Just run it:
    python quickstart.py

You'll need the 'requests' library if you don't have it:
    pip install requests
"""

import re
import requests

# The base URL for all TechPort API calls
BASE_URL = "https://techport.nasa.gov"

# We include a User-Agent header so the server knows this is a legitimate request
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TechPortAPIClient/1.0)"}


def remove_html_tags(text):
    """
    Project descriptions sometimes contain HTML tags like <p> and <br>.
    This function strips those out so the text prints cleanly in the terminal.
    """
    if not text:
        return ""
    return re.sub(r"<[^>]+>", " ", text).strip()


# ENDPOINT: GET /api/projects
def get_recent_project_ids(updated_since="2024-01-01"):
    """
    Asks TechPort for a list of project IDs that have been updated
    since the given date. Returns just the IDs — not the full project data.
    Full details are fetched separately in get_project().
    """
    url = f"{BASE_URL}/api/projects"
    response = requests.get(url, params={"updatedSince": updated_since}, headers=HEADERS, verify=VERIFY_SSL)

    # raise_for_status() will throw an error if the request failed (e.g. 404, 500)
    response.raise_for_status()

    # The API returns a JSON object. We pull out the "projects" list from it.
    return response.json().get("projects", [])


# ENDPOINT: GET /api/projects/{projectId}
def get_project(project_id):
    """
    Fetches the full details for a single project by its ID.
    Returns a dictionary with all the project's fields.
    """
    url = f"{BASE_URL}/api/projects/{project_id}"
    response = requests.get(url, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()

    # The response wraps the project in a "project" key, so we unwrap it here
    return response.json().get("project", {})


def print_project_summary(project):
    """
    Prints a formatted summary of one project to the terminal.
    The project argument is a dictionary returned by get_project().
    """
    # Pull out the nested objects we need, defaulting to empty dicts
    # so we don't crash if a field is missing
    program  = project.get("program") or {}
    md       = project.get("responsibleMd") or {}
    lead_org = project.get("leadOrganization") or {}
    contacts = project.get("projectContacts") or []

    # Get the state abbreviation — it's nested inside stateTerritory
    state_info = lead_org.get("stateTerritory") or {}
    state      = state_info.get("abbreviation", "")

    # Find the project manager in the contacts list, or just use the first contact
    project_manager = {}
    for contact in contacts:
        role = contact.get("projectContactRolePretty") or ""
        if "manager" in role.lower():
            project_manager = contact
            break
    if not project_manager and contacts:
        project_manager = contacts[0]

    # Clean the description text and trim it to a short snippet
    raw_description = project.get("description", "")
    clean_description = remove_html_tags(raw_description)
    if len(clean_description) > 250:
        clean_description = clean_description[:250] + "..."

    # Print everything out
    print(f"  {'─' * 58}")
    print(f"  ID       : {project.get('projectId')}")
    print(f"  Title    : {project.get('title')}")
    print(f"  Status   : {project.get('status')}  |  Last updated: {project.get('lastUpdated')}")
    print(f"  TRL      : {project.get('trlBegin')} -> {project.get('trlCurrent')} -> {project.get('trlEnd')}  (begin / current / end)")
    print(f"  Duration : {project.get('startMonth')}/{project.get('startYear')} - {project.get('endMonth')}/{project.get('endYear')}")
    print(f"  Program  : {program.get('title', 'N/A')} ({program.get('acronym', '')})")
    print(f"  Dir.     : {md.get('organizationName', 'N/A')} ({md.get('acronym', '')})")
    print(f"  Lead Org : {lead_org.get('organizationName', 'N/A')} - {lead_org.get('city', 'N/A')}, {state}")

    if project_manager:
        name  = project_manager.get("fullName", "N/A")
        role  = project_manager.get("projectContactRolePretty", "")
        email = project_manager.get("email", "N/A")
        print(f"  Contact  : {name} ({role}) - {email}")

    if clean_description:
        print(f"  Summary  : {clean_description}")


def main():
    updated_since = "2024-01-01"
    how_many      = 5

    print(f"Fetching projects updated since {updated_since}...\n")
    project_list = get_recent_project_ids(updated_since=updated_since)

    if not project_list:
        print("No projects found for the given date range.")
        return

    print(f"Found {len(project_list):,} projects. Showing full detail for the first {how_many}:\n")

    for entry in project_list[:how_many]:
        project_id = entry.get("projectId")
        try:
            project = get_project(project_id)
            print_project_summary(project)
            print()
        except requests.HTTPError as e:
            print(f"  Could not fetch project {project_id}: {e}")


if __name__ == "__main__":
    main()
