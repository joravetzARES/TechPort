"""
TechPort API - Opportunities, Programs, and Enumerations
=========================================================
NOTE: For simplicity, requests below show only required fields and responses are summarized, not shown in full. See the README's "A Note on These Examples" section for details.

Examples for three more sets of public endpoints:

  Opportunities - NASA funding mechanisms (SBIR, NIAC, grants, etc.)
  Programs      - NASA programs that projects belong to
  Enumerations  - The valid values for fields like "status" and "destinationType"

No login or API key needed for reading. The export function (POST) uses
a session/nonce for security but still requires no API key.
"""

import re
import requests

BASE_URL = "https://techport.nasa.gov"
HEADERS    = {"User-Agent": "Mozilla/5.0 (compatible; TechPortAPIClient/1.0)"}

# Set to False for dev VPC environments with self-signed SSL certificates.
# Set to True for production (techport.nasa.gov uses a valid certificate).
VERIFY_SSL = True   # Change to False if testing against the internal dev VPC


def remove_html_tags(text):
    """Strip HTML tags from text so it prints cleanly."""
    if not text:
        return ""
    return re.sub(r"<[^>]+>", " ", text).strip()


def _get_nonce_and_session():
    """
    Some POST requests on TechPort require a 'nonce' — a short-lived token
    that proves the request is legitimate (not forged). The nonce is tied
    to your session, so we create a persistent session, fetch the nonce
    within that session, and return both so they can be used together.

    This is handled automatically by functions that need it (like export_opportunities).
    You don't need to call this directly.
    """
    session = requests.Session()
    session.headers.update(HEADERS)  # Include our User-Agent in the session

    response = session.get(f"{BASE_URL}/api/nonce")
    response.raise_for_status()

    nonce = response.json().get("nonce")
    return session, nonce


# =============================================================================
# OPPORTUNITIES
# =============================================================================

# ENDPOINT: GET /api/opportunities
def get_all_opportunities():
    """
    Returns the list of all NASA funding opportunities.

    Each opportunity represents a funding mechanism — like SBIR, NIAC, or
    a grant program. Key fields in each opportunity:
        opportunityId    - Unique ID
        name             - Name of the opportunity
        amount           - Funding amount in dollars
        duration         - How long funded projects typically run (in months)
        frequency        - How often the opportunity is offered (e.g. "Annual")
        nextSolicitation - When the next round opens (e.g. "Every September")
        topicBased       - Whether proposals must address a specific topic
        trlValues        - List of TRL levels this opportunity targets
        opportunityRole  - Who can apply (e.g. ["NASA"], ["Industry"])
        directorate      - Which NASA directorate administers it
    """
    url      = f"{BASE_URL}/api/opportunities"
    response = requests.get(url, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json().get("opportunities", [])


# ENDPOINT: GET /api/opportunities/{opportunityId}
def get_opportunity(opportunity_id):
    """
    Returns full details for one specific funding opportunity.

    Example:
        opp = get_opportunity(38)   # A-IRAD
    """
    url      = f"{BASE_URL}/api/opportunities/{opportunity_id}"
    response = requests.get(url, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json().get("opportunity", {})


# ENDPOINT: GET /api/opportunities/maxFundingAmount
def get_max_funding_amount():
    """
    Returns the highest funding amount across all opportunities (in dollars).
    Useful for building range sliders or setting filter bounds in a UI.
    """
    url      = f"{BASE_URL}/api/opportunities/maxFundingAmount"
    response = requests.get(url, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json().get("maxFunding", 0)


# ENDPOINT: POST /api/opportunities/export
def export_opportunities(criteria=None, output_path="opportunities.xlsx"):
    """
    Downloads a filtered set of opportunities as an Excel file.

    The criteria argument is a dict of filters (optional — pass an empty
    dict or omit it to export all opportunities).

    This endpoint uses a nonce for security. The function handles that
    automatically — you just provide the filter criteria and output path.

    Example:
        # Export all opportunities
        export_opportunities(output_path="all_opportunities.xlsx")

        # Export with a filter (filters may require an API key to take effect)
        export_opportunities({"limit": 10}, output_path="sample.xlsx")
    """
    if criteria is None:
        criteria = {}

    session, nonce = _get_nonce_and_session()

    # Add the nonce to the request body
    body = {**criteria, "nonce": nonce}

    response = session.post(
        f"{BASE_URL}/api/opportunities/export",
        json=body,
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()

    # Write the raw bytes to the output file
    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"Saved to: {output_path}")


# =============================================================================
# PROGRAMS
# =============================================================================

# ENDPOINT: GET /api/programs
def get_all_programs(active_only=False):
    """
    Returns the list of NASA programs tracked in TechPort.

    Programs are the organizational units that projects belong to —
    things like "SBIR/STTR", "NIAC", or "Human Research Program".

    Pass active_only=True to get only currently running programs.

    Key fields in each program:
        programId            - Unique ID
        title                - Program name
        acronym              - Short abbreviation
        isActive             - True if the program is currently active
        responsibleMd        - Which Mission Directorate runs this program
        programContacts      - List of contacts with names, emails, and roles
        description          - What the program does (may contain HTML)
    """
    url    = f"{BASE_URL}/api/programs"
    params = {}
    if active_only:
        params["activeOnly"] = "true"

    response = requests.get(url, params=params, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json().get("programs", [])


# ENDPOINT: GET /api/programs/{programId}
def get_program(program_id):
    """
    Returns full details for one specific NASA program.

    Example:
        program = get_program(18792)   # Advanced Air Vehicles Program
    """
    url      = f"{BASE_URL}/api/programs/{program_id}"
    response = requests.get(url, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json().get("program", {})


def print_program(prog):
    """Prints a detailed summary of one program dict."""
    md       = prog.get("responsibleMd") or {}
    contacts = prog.get("programContacts") or []

    # Clean the description text
    description = remove_html_tags(prog.get("description", ""))
    if len(description) > 300:
        description = description[:300] + "..."

    print(f"  ID          : {prog.get('programId')}")
    print(f"  Title       : {prog.get('title')}")
    print(f"  Acronym     : {prog.get('acronym') or prog.get('acronymOrTitle', 'N/A')}")
    print(f"  Active      : {prog.get('isActive')}")
    print(f"  Directorate : {md.get('organizationName')} ({md.get('acronym')})")

    for c in contacts:
        name  = c.get("fullName", "N/A")
        role  = c.get("programContactRolePretty", "")
        email = c.get("email", "N/A")
        print(f"  Contact     : {name} ({role}) - {email}")

    if description:
        print(f"  Description : {description}")


# =============================================================================
# ENUMERATIONS
# =============================================================================

# ENDPOINT: GET /api/enums
def get_all_enums():
    """
    Returns all the enumeration (allowed values) sets available in TechPort.

    Enumerations tell you what values are valid for specific fields.
    For example, the "projectStatusType" enum tells you that valid
    statuses are: Active, Planned, Completed, Canceled.

    Returns a dict where each key is an enum name and the value is
    a list of {label, value} objects.

    Use get_enum() to look up a specific one by name.
    """
    url      = f"{BASE_URL}/api/enums"
    response = requests.get(url, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json().get("enums", {})


# ENDPOINT: GET /api/enums/{enumName}
def get_enum(enum_name):
    """
    Returns the valid values for a specific enumeration.

    Each item in the returned list has:
        value - the actual string used in API calls and filters
        label - the human-readable display version

    Confirmed enum names (from GET /api/enums):
        projectStatusType, destinationTypes, organizationTypes,
        technologyOutcomePathType, opportunityRoles, fundingCategories,
        libraryItemTypes, projectContactRoles, workflowType, and more.

    Example:
        values = get_enum("destinationTypes")
        for v in values:
            print(v["value"], "->", v["label"])
    """
    url      = f"{BASE_URL}/api/enums/{enum_name}"
    response = requests.get(url, headers=HEADERS, verify=VERIFY_SSL)
    response.raise_for_status()
    return response.json().get("values", [])


# ── Examples ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # Example 1: List all funding opportunities
    print("=== All Funding Opportunities ===")
    opportunities  = get_all_opportunities()
    max_funding    = get_max_funding_amount()
    print(f"Total: {len(opportunities)}  |  Largest award: ${max_funding:,}")
    print()
    for opp in opportunities:
        trl_values = opp.get("trlValues") or []
        if trl_values:
            trl_range = f"TRL {trl_values[0]}-{trl_values[-1]}"
        else:
            trl_range = "Any TRL"
        amount = opp.get("amount", 0)
        print(f"  [{opp.get('opportunityId'):>3}] ${amount:>12,}  {trl_range:<12}  {opp.get('name')}")
    print()

    # Example 2: Full detail for one opportunity
    print("=== Full detail: opportunity 38 (A-IRAD) ===")
    opp        = get_opportunity(38)
    directorate = opp.get("directorate") or {}
    trl_values  = opp.get("trlValues") or []
    description = remove_html_tags(opp.get("description", ""))
    if len(description) > 300:
        description = description[:300] + "..."

    print(f"  Name             : {opp.get('name')}")
    print(f"  Amount           : ${opp.get('amount', 0):,}")
    print(f"  Duration         : {opp.get('duration', 'N/A')} months")
    print(f"  Frequency        : {opp.get('frequency', 'N/A')}")
    print(f"  Next Solicitation: {opp.get('nextSolicitation', 'N/A')}")
    print(f"  Topic Based      : {opp.get('topicBased', 'N/A')}")
    print(f"  Eligible TRLs    : {trl_values if trl_values else 'N/A'}")
    print(f"  Roles            : {', '.join(opp.get('opportunityRole') or [])}")
    print(f"  Directorate      : {directorate.get('organizationName', 'N/A')} ({directorate.get('acronym', 'N/A')})")
    if description:
        print(f"  Description      : {description}")
    print()

    # Example 3: Export all opportunities to Excel
    # Uncomment the two lines below to run this example:
    # print("=== Exporting opportunities to Excel ===")
    # export_opportunities(output_path="opportunities.xlsx")

    # Example 4: Active programs grouped by Mission Directorate
    print("=== Active programs by Mission Directorate ===")
    programs = get_all_programs(active_only=True)
    print(f"Total active programs: {len(programs)}")
    print()

    # Group programs by their mission directorate acronym
    by_directorate = {}
    for prog in programs:
        md_info = prog.get("responsibleMd") or {}
        md      = md_info.get("acronym", "Unknown")
        by_directorate.setdefault(md, []).append(prog)

    for md in sorted(by_directorate):
        prog_list = by_directorate[md]
        print(f"  {md} ({len(prog_list)} programs):")
        for p in prog_list:
            print(f"    [{p.get('programId'):>6}] {p.get('title')}")
    print()

    # Example 5: Full detail for one program
    print("=== Full detail: program 18792 (AAVP) ===")
    prog = get_program(18792)
    print_program(prog)
    print()

    # Example 6: All available enumeration names
    print("=== All enumeration names ===")
    all_enums = get_all_enums()
    for name in sorted(all_enums.keys()):
        values = all_enums[name]
        count  = len(values) if isinstance(values, list) else "?"
        print(f"  {name:<45} ({count} values)")
    print()

    # Example 7: Look up specific enum values
    # These are useful when building search filters — use the "value" field
    for enum_name in ["projectStatusType", "destinationTypes", "organizationTypes"]:
        print(f"=== Valid values for '{enum_name}' ===")
        values = get_enum(enum_name)
        for v in values:
            print(f"  {v.get('value', ''):<45} ({v.get('label', '')})")
        print()
