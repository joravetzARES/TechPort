"""
TechPort API - Search
=====================
NOTE: For simplicity, requests below show only required fields and responses are summarized, not shown in full. See the README's "A Note on These Examples" section for details.

Examples for browsing through all TechPort records using the search endpoint.

The search endpoint is different from the individual project/organization
endpoints — it returns many records at once in a paginated format.

Important: on the public API, you can only page through records in
alphabetical order. Filtering and keyword search require an API key.
See internal/python/search_internal.py for authenticated examples.

Endpoints used:
  GET /api/projects/search       - Page through all projects
  GET /api/organizations/search  - Page through all organizations
  GET /api/project/schema        - See what fields a project has

No login or API key needed.
"""

import requests

BASE_URL = "https://techport.nasa.gov"
HEADERS    = {"User-Agent": "Mozilla/5.0 (compatible; TechPortAPIClient/1.0)"}

# Set to False for dev VPC environments with self-signed SSL certificates.
# Set to True for production (techport.nasa.gov uses a valid certificate).
VERIFY_SSL = True   # Change to False if testing against the internal dev VPC


# ENDPOINT: GET /api/{objectType}/search  (objectType="projects")
def search_projects(limit=10, offset=0):
    """
    Returns a page of projects from TechPort.

    Think of this like a paginated table — limit is how many rows per page,
    offset is which row to start from.

    Examples:
        # First 10 projects
        data = search_projects(limit=10)

        # Next 10 (rows 11-20)
        data = search_projects(limit=10, offset=10)

        # A big batch starting from record 500
        data = search_projects(limit=100, offset=500)

    The returned dict contains:
        results  - list of project dicts
        total    - total number of projects in TechPort
        offset   - the offset you requested
    """
    url      = f"{BASE_URL}/api/projects/search"
    params   = {"limit": limit, "offset": offset}
    response = requests.get(url, params=params, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json()


# ENDPOINT: GET /api/{objectType}/search  (objectType="organizations")
def search_organizations(limit=10, offset=0):
    """
    Returns a page of organizations from TechPort.
    Works the same way as search_projects() — use limit and offset to paginate.
    """
    url      = f"{BASE_URL}/api/organizations/search"
    params   = {"limit": limit, "offset": offset}
    response = requests.get(url, params=params, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json()


# ENDPOINT: GET /api/{objectType}/search/allData  (objectType="projects")
def get_all_projects():
    """
    Downloads every project in TechPort with all fields in a single request.

    WARNING: This is a large download — over 20,000 records with all their
    fields. Only use this if you need the complete dataset. For most uses,
    search_projects() with pagination is better.
    """
    url      = f"{BASE_URL}/api/projects/search/allData"
    response = requests.get(url, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json()


# ENDPOINT: GET /api/{objectType}/schema  (objectType="project")
def get_project_schema():
    """
    Returns the schema (field definitions) for the project object type.
    Useful for discovering what fields exist and what types they are.
    """
    url      = f"{BASE_URL}/api/project/schema"
    response = requests.get(url, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json()


def print_project(p):
    """Print a short summary of one project from search results."""
    lead = (p.get("leadOrganization") or {}).get("organization_name", "N/A")
    prog = (p.get("program") or {}).get("title", "N/A")

    # Destination types is a list — join them into a readable string
    dest_list = [d for d in (p.get("destinationTypes") or []) if d]
    dest      = ", ".join(dest_list) if dest_list else "N/A"

    print(f"  [{p.get('projectId')}] {p.get('title')}")
    print(f"    Status  : {p.get('status')} | TRL: {p.get('trlBegin')} -> {p.get('trlCurrent')} -> {p.get('trlEnd')}")
    print(f"    Program : {prog} | Lead: {lead}")
    print(f"    Dest    : {dest}")


# ── Examples ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # Example 1: First page of projects
    print("=== First 5 projects ===")
    data     = search_projects(limit=5)
    total    = data.get("total", 0)
    results  = data.get("results", [])
    print(f"Total projects in TechPort: {total:,}")
    print(f"(Results are alphabetical — filtering not available on public endpoints)")
    print()
    for p in results:
        print_project(p)
        print()

    # Example 2: Second page (records 6-10)
    print("=== Records 6-10 (offset=5) ===")
    data = search_projects(limit=5, offset=5)
    for p in data.get("results", []):
        print(f"  [{p.get('projectId')}] {p.get('title')} | {p.get('status')}")
    print()

    # Example 3: Fetch a large batch (100 records starting from #500)
    print("=== Records 501-600 ===")
    data    = search_projects(limit=100, offset=500)
    results = data.get("results", [])
    print(f"Fetched: {len(results)} records")
    if results:
        print(f"  First: [{results[0].get('projectId')}] {results[0].get('title')}")
        print(f"  Last : [{results[-1].get('projectId')}] {results[-1].get('title')}")
    print()

    # Example 4: Organizations
    print("=== First 5 organizations ===")
    data  = search_organizations(limit=5)
    total = data.get("total", 0)
    print(f"Total organizations in TechPort: {total:,}")
    for o in data.get("results", []):
        name  = o.get("organization_name") or o.get("organizationName", "N/A")
        otype = o.get("organization_type") or o.get("organizationType", "N/A")
        city  = o.get("city", "N/A")
        state = o.get("state_abbreviation") or o.get("stateAbbreviation", "")
        print(f"  {name} ({otype}) - {city}, {state}")
    print()

    # Example 5: Look at available schema types
    print("=== Available schema types for 'project' ===")
    schema = get_project_schema()
    print(f"  {list(schema.keys())}")
