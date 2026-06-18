"""
TechPort API - Organizations
============================
NOTE: For simplicity, requests below show only required fields and responses are summarized, not shown in full. See the README's "A Note on These Examples" section for details.

Examples for looking up organizations in TechPort — NASA centers,
universities, companies, and other entities involved in NASA projects.

Endpoints used:
  GET /api/organizations              - Search organizations by name or acronym
  GET /api/organizations/{id}         - Get full details for one organization

No login or API key needed.

Note: Filtering by organization type (e.g. "show only NASA Centers") requires
an API key and is covered in internal/python/search_internal.py.
"""

import requests

BASE_URL = "https://techport.nasa.gov"
HEADERS    = {"User-Agent": "Mozilla/5.0 (compatible; TechPortAPIClient/1.0)"}

# Set to False for dev VPC environments with self-signed SSL certificates.
# Set to True for production (techport.nasa.gov uses a valid certificate).
VERIFY_SSL = True   # Change to False if testing against the internal dev VPC


# ENDPOINT: GET /api/organizations
def find_organizations(name=None, acronym=None, uei=None, cage_code=None, limit=25):
    """
    Search for organizations by name, acronym, or identifier.

    You can pass any combination of the filters below. At least one
    should be provided or you'll get a generic list back.

    Arguments:
        name      - Partial name match. "Jet Propulsion" finds JPL.
        acronym   - Exact acronym. "JPL", "GRC", "GSFC", etc.
        uei       - Unique Entity Identifier (federal contracting ID)
        cage_code - CAGE code (another federal contractor identifier)
        limit     - Max results to return (default 25)

    Returns a list of organization dicts. Key fields:
        organizationId       - Unique numeric ID
        organizationName     - Full name
        organizationType     - e.g. "NASA_Center", "Industry", "Academia"
        organizationTypePretty - Human-readable version of the type
        acronym              - Short abbreviation
        city, stateTerritory, country - Location info
        zipCode, dunsNumber  - Identifier fields

    Examples:
        # Find by partial name
        orgs = find_organizations(name="Jet Propulsion")

        # Look up a specific center by acronym
        orgs = find_organizations(acronym="GRC")
    """
    url    = f"{BASE_URL}/api/organizations"
    params = {"limit": limit}

    # Only add params that were actually provided
    if name:      params["organizationName"]     = name
    if acronym:   params["organizationAcronym"]  = acronym
    if uei:       params["organizationUei"]      = uei
    if cage_code: params["organizationCageCode"] = cage_code

    response = requests.get(url, params=params, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json().get("organizations", [])


# ENDPOINT: GET /api/organizations/{organizationId}
def get_organization(org_id):
    """
    Returns the full details for one specific organization by its numeric ID.

    Example:
        org = get_organization(4946)   # Jet Propulsion Laboratory
        org = get_organization(4860)   # Glenn Research Center
    """
    url      = f"{BASE_URL}/api/organizations/{org_id}"
    response = requests.get(url, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json().get("organization", {})


def format_location(org):
    """
    Returns a readable location string like "Pasadena, CA, US".
    Handles cases where city, state, or country may be missing.
    """
    city    = org.get("city", "")
    # State is nested inside a stateTerritory object
    state_info = org.get("stateTerritory") or {}
    state      = state_info.get("abbreviation", "")
    # Country is also nested
    country_info = org.get("country") or {}
    country      = country_info.get("abbreviation", "")

    # Build the string from whatever parts we have, skipping blanks
    parts = [p for p in [city, state, country] if p]
    return ", ".join(parts) if parts else "N/A"


def print_organization(org):
    """Prints a detailed summary of one organization dict."""
    # Use the pretty version of the type if it exists, otherwise the raw value
    org_type = org.get("organizationTypePretty") or org.get("organizationType", "N/A")

    print(f"  ID       : {org.get('organizationId')}")
    print(f"  Name     : {org.get('organizationName')}")
    print(f"  Type     : {org_type}")
    print(f"  Acronym  : {org.get('acronym', 'N/A')}")
    print(f"  Location : {format_location(org)}")
    print(f"  ZIP      : {org.get('zipCode', 'N/A')}")
    print(f"  DUNS     : {org.get('dunsNumber', 'N/A')}")


# ── Examples ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # Example 1: Search by partial name
    print("=== Organizations matching 'Jet Propulsion' ===")
    orgs = find_organizations(name="Jet Propulsion")
    for org in orgs:
        print(f"  [{org.get('organizationId')}] {org.get('organizationName')} "
              f"({org.get('organizationType')}) - {format_location(org)}")
    print()

    # Example 2: Look up NASA Centers by acronym
    # Note: some acronyms match multiple entries (e.g. the center itself
    # plus associated IRAD programs), so we show all matches
    print("=== Lookup NASA Centers by acronym ===")
    nasa_center_acronyms = ["GRC", "GSFC", "JPL", "ARC", "JSC", "KSC", "LaRC", "MSFC", "SSC"]
    for acronym in nasa_center_acronyms:
        results = find_organizations(acronym=acronym)
        if not results:
            print(f"  {acronym}: (no results)")
        elif len(results) == 1:
            o   = results[0]
            loc = format_location(o)
            loc_str = f" - {loc}" if loc != "N/A" else ""
            print(f"  [{o.get('organizationId')}] {o.get('organizationName')} "
                  f"({o.get('organizationType')}){loc_str}")
        else:
            # Multiple matches — show all of them
            print(f"  {acronym} ({len(results)} matches):")
            for o in results:
                loc     = format_location(o)
                loc_str = f" - {loc}" if loc != "N/A" else ""
                print(f"    [{o.get('organizationId')}] {o.get('organizationName')} "
                      f"({o.get('organizationType')}){loc_str}")
    print()

    # Example 3: Get full details for JPL
    print("=== Full detail: JPL (ID 4946) ===")
    jpl = get_organization(4946)
    print_organization(jpl)
    print()

    # Example 4: Find industry partners by name
    print("=== Organizations matching 'Lockheed' ===")
    orgs = find_organizations(name="Lockheed", limit=5)
    for org in orgs:
        print(f"  [{org.get('organizationId')}] {org.get('organizationName')} "
              f"({org.get('organizationType')}) - {format_location(org)}")
    print()

    # Example 5: Find universities
    print("=== Organizations matching 'Massachusetts Institute' ===")
    orgs = find_organizations(name="Massachusetts Institute", limit=5)
    for org in orgs:
        print(f"  [{org.get('organizationId')}] {org.get('organizationName')} "
              f"- {format_location(org)}")
