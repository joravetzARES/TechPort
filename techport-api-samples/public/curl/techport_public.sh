#!/usr/bin/env bash
# =============================================================================
# TechPort API - curl Examples (Public Endpoints)
# =============================================================================
# No API key required for any command in this script.
#
# NOTE: For simplicity, requests below show only required fields and
# responses are parsed down to a few key fields, not shown in full. See the
# README's "A Note on These Examples" section for details.
#
# RUNNING THE WHOLE FILE:
#   bash techport_public.sh
#
# RUNNING JUST ONE ENDPOINT:
#   This file is a single top-to-bottom script — there's no built-in way to
#   run one block by itself just by calling this file. Instead:
#     1. Open this file in a text editor.
#     2. Copy the variables/helpers section near the top of the file.
#     3. Copy the one example block you want to run (the echo line plus the
#        curl call below it).
#     4. Paste both into your terminal, or save them together as a small
#        scratch .sh file and run that instead.
#
# NOTE ON PUBLIC SEARCH LIMITATIONS:
#   The public search endpoint (GET and POST) returns ALL records regardless
#   of any query or filter values. Filtering only works for authenticated users.
#   Public search is useful for: pagination, sorting, and full dataset dumps.
#
# NOTE ON NONCE / SESSION:
#   POST requests require a "nonce" field in the request body for CSRF
#   protection. The nonce is session-tied — the nonce fetch and the POST
#   must share the same HTTP session cookie (JWT token cookie).
#   This script uses a cookie jar file to persist the session.
#
#   If running individual POST commands manually (two-step):
#     1. curl -s -c C:\Scripts\cookies.txt "https://techport.nasa.gov/api/nonce"
#     2. curl -s -b C:\Scripts\cookies.txt -X POST <url> -H "Content-Type: application/json" -d "{\"nonce\":\"<value>\", ...}"
#
#
# Requirements: curl, python3
# Usage: bash techport_public.sh
# =============================================================================

BASE_URL="https://techport.nasa.gov"

# Cookie jar — stores the session token between nonce fetch and POST calls.
# On Windows (Git Bash), use a path under your Scripts folder.
# On Linux/Mac, /tmp works fine.
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
  COOKIE_JAR="$(pwd)/techport_cookies_$$.txt"
else
  COOKIE_JAR="/tmp/techport_cookies_$$.txt"
fi

# Helper: fetch a fresh nonce (saving session cookie), then POST with that session
# Usage: post_with_nonce <url> <json_body_without_nonce>
post_with_nonce() {
  local URL="$1"
  local BODY="$2"
  local NONCE
  NONCE=$(curl -s -c "$COOKIE_JAR" "$BASE_URL/api/nonce" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('nonce') or list(d.values())[0])
")
  local BODY_WITH_NONCE
  BODY_WITH_NONCE=$(python3 -c "
import json
body = json.loads('''$BODY''')
body['nonce'] = '$NONCE'
print(json.dumps(body))
")
  curl -s -b "$COOKIE_JAR" -X POST "$URL" \
    -H "Content-Type: application/json" \
    -d "$BODY_WITH_NONCE"
}

# Cleanup cookie jar on exit
trap "rm -f $COOKIE_JAR" EXIT

echo ""


# =============================================================================
# PROJECTS
# =============================================================================

echo "=== GET /api/projects — all project IDs ==="
curl -s "$BASE_URL/api/projects" | python3 -c "
import sys, json
data     = json.load(sys.stdin)
projects = data.get('projects', [])
print(f'Total projects: {len(projects):,}')
print(f'First 5 IDs  : {[p.get(\"projectId\") for p in projects[:5]]}')
"
echo ""

echo "=== GET /api/projects?updatedSince=2024-01-01 ==="
curl -s "$BASE_URL/api/projects?updatedSince=2024-01-01" | python3 -c "
import sys, json
projects = json.load(sys.stdin).get('projects', [])
print(f'Updated since 2024-01-01: {len(projects):,}')
print(f'First 5 IDs             : {[p.get(\"projectId\") for p in projects[:5]]}')
"
echo ""

echo "=== GET /api/projects/{projectId} ==="
PROJECT_ID=184674
curl -s "$BASE_URL/api/projects/$PROJECT_ID" | python3 -c "
import sys, json, re
p        = json.load(sys.stdin).get('project', {})
prog     = p.get('program') or {}
md       = p.get('responsibleMd') or {}
lead     = p.get('leadOrganization') or {}
contacts = p.get('projectContacts') or []
outcomes = p.get('technologyOutcomes') or []
library  = p.get('libraryItems') or []
desc     = re.sub(r'<[^>]+>', ' ', p.get('description', '') or '').strip()[:200]
lead_state = (lead.get('stateTerritory') or {}).get('abbreviation', 'N/A')
print(f'ID           : {p.get(\"projectId\")}')
print(f'Title        : {p.get(\"title\")}')
print(f'Status       : {p.get(\"status\")}  |  Updated: {p.get(\"lastUpdated\")}')
print(f'TRL          : {p.get(\"trlBegin\")} -> {p.get(\"trlCurrent\")} -> {p.get(\"trlEnd\")}  (begin / current / end)')
print(f'Duration     : {p.get(\"startMonth\")}/{p.get(\"startYear\")} - {p.get(\"endMonth\")}/{p.get(\"endYear\")}')
print(f'Program      : {prog.get(\"title\")} ({prog.get(\"acronym\")})')
print(f'Directorate  : {md.get(\"organizationName\", \"N/A\")} ({md.get(\"acronym\", \"N/A\")})')
print(f'Lead Org     : {lead.get(\"organizationName\", \"N/A\")} - {lead.get(\"city\", \"N/A\")}, {lead_state}')
print(f'Contacts     : {len(contacts)}  |  Outcomes: {len(outcomes)}  |  Library: {len(library)}')
print(f'Views        : {p.get(\"viewCount\", 0):,}')
if desc: print(f'Description  : {desc}...')
"
echo ""


# =============================================================================
# SEARCH
# NOTE: Public search returns ALL records in default alphabetical order.
#       query, filters, and sortString are all ignored on public endpoints.
#       Only limit and offset work — use them to paginate through the dataset.
#       For filtered/sorted/keyword search, see internal/curl/techport_internal.sh
# =============================================================================

echo "=== GET /api/projects/search — first 5 projects ==="
curl -s "$BASE_URL/api/projects/search?limit=5" | python3 -c "
import sys, json
data    = json.load(sys.stdin)
results = data.get('results', [])
print(f'Total in TechPort: {data.get(\"total\", 0):,}  |  Returned: {len(results)}')
print('(Default alphabetical order — sort/filter not available publicly)')
for p in results:
    lead = (p.get('leadOrganization') or {}).get('organization_name', 'N/A')
    print(f'  [{p.get(\"projectId\")}] {p.get(\"title\")}')
    print(f'    TRL: {p.get(\"trlBegin\")} -> {p.get(\"trlCurrent\")} -> {p.get(\"trlEnd\")} | {p.get(\"status\")} | {lead}')
"
echo ""

echo "=== GET /api/projects/search — page 2 (offset=5) ==="
curl -s "$BASE_URL/api/projects/search?limit=5&offset=5" | python3 -c "
import sys, json
results = json.load(sys.stdin).get('results', [])
print(f'Records 6-10 (offset=5), returned: {len(results)}')
for p in results:
    print(f'  [{p.get(\"projectId\")}] {p.get(\"title\")} | {p.get(\"status\")}')
"
echo ""

echo "=== GET /api/projects/search — large page (limit=100, offset=500) ==="
curl -s "$BASE_URL/api/projects/search?limit=100&offset=500" | python3 -c "
import sys, json
data    = json.load(sys.stdin)
results = data.get('results', [])
print(f'Records 501-600, returned: {len(results)}')
print(f'First: [{results[0].get(\"projectId\")}] {results[0].get(\"title\")}' if results else '')
print(f'Last : [{results[-1].get(\"projectId\")}] {results[-1].get(\"title\")}' if results else '')
"
echo ""

echo "=== GET /api/project/schema — available schema types ==="
curl -s "$BASE_URL/api/project/schema" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Schema types ({len(data)}): {list(data.keys())}')
"
echo ""


# =============================================================================
# ORGANIZATIONS
# =============================================================================

echo "=== GET /api/organizations?organizationName=Jet+Propulsion ==="
curl -s "$BASE_URL/api/organizations?organizationName=Jet+Propulsion" | python3 -c "
import sys, json
orgs = json.load(sys.stdin).get('organizations', [])
for o in orgs:
    state = (o.get('stateTerritory') or {}).get('abbreviation', 'N/A')
    print(f'  [{o.get(\"organizationId\")}] {o.get(\"organizationName\")} ({o.get(\"organizationType\")}) - {o.get(\"city\",\"N/A\")}, {state}')
"
echo ""

echo "=== GET /api/organizations?organizationAcronym=GRC ==="
curl -s "$BASE_URL/api/organizations?organizationAcronym=GRC" | python3 -c "
import sys, json
orgs = json.load(sys.stdin).get('organizations', [])
for o in orgs:
    state = (o.get('stateTerritory') or {}).get('abbreviation', 'N/A')
    print(f'  [{o.get(\"organizationId\")}] {o.get(\"organizationName\")} ({o.get(\"acronym\",\"N/A\")}) - {o.get(\"city\",\"N/A\")}, {state}')
"
echo ""

echo "=== GET /api/organizations/{organizationId} — full org detail ==="
ORG_ID=4946
curl -s "$BASE_URL/api/organizations/$ORG_ID" | python3 -c "
import sys, json
o       = json.load(sys.stdin).get('organization', {})
state   = (o.get('stateTerritory') or {}).get('abbreviation', 'N/A')
country = (o.get('country') or {}).get('name', 'N/A')
print(f'ID       : {o.get(\"organizationId\")}')
print(f'Name     : {o.get(\"organizationName\")}')
print(f'Type     : {o.get(\"organizationTypePretty\", o.get(\"organizationType\"))}')
print(f'Acronym  : {o.get(\"acronym\", \"N/A\")}')
print(f'Location : {o.get(\"city\",\"N/A\")}, {state}, {country}')
print(f'ZIP      : {o.get(\"zipCode\",\"N/A\")}')
print(f'DUNS     : {o.get(\"dunsNumber\",\"N/A\")}')
"
echo ""


# =============================================================================
# PROGRAMS
# =============================================================================

echo "=== GET /api/programs?activeOnly=true — grouped by directorate (first 3 per group) ==="
curl -s "$BASE_URL/api/programs?activeOnly=true" | python3 -c "
import sys, json
programs = json.load(sys.stdin).get('programs', [])
print(f'Total active programs: {len(programs)} (showing first 3 per directorate)')
by_md = {}
for p in programs:
    md = (p.get('responsibleMd') or {}).get('acronym', 'Unknown')
    by_md.setdefault(md, []).append(p)
for md in sorted(by_md):
    total = len(by_md[md])
    shown = by_md[md][:3]
    print(f'  {md} ({total} total):')
    for p in shown:
        print(f'    [{p.get(\"programId\")}] {p.get(\"title\")}')
    if total > 3:
        print(f'    ... and {total - 3} more')
"
echo ""

echo "=== GET /api/programs/{programId} — full detail ==="
PROGRAM_ID=18792
curl -s "$BASE_URL/api/programs/$PROGRAM_ID" | python3 -c "
import sys, json, re
p        = json.load(sys.stdin).get('program', {})
md       = p.get('responsibleMd') or {}
contacts = p.get('programContacts') or []
desc     = re.sub(r'<[^>]+>', ' ', p.get('description', '') or '').strip()[:300]
print(f'ID          : {p.get(\"programId\")}')
print(f'Title       : {p.get(\"title\")}')
print(f'Acronym     : {p.get(\"acronym\", p.get(\"acronymOrTitle\",\"N/A\"))}')
print(f'Active      : {p.get(\"isActive\")}')
print(f'Directorate : {md.get(\"organizationName\")} ({md.get(\"acronym\")})')
for c in contacts:
    print(f'  Contact   : {c.get(\"fullName\")} ({c.get(\"programContactRolePretty\")}) - {c.get(\"email\")}')
if desc: print(f'Description : {desc}...')
"
echo ""


# =============================================================================
# OPPORTUNITIES
# =============================================================================

echo "=== GET /api/opportunities ==="
curl -s "$BASE_URL/api/opportunities" | python3 -c "
import sys, json
opps = json.load(sys.stdin).get('opportunities', [])
print(f'Total: {len(opps)}')
for o in opps:
    trl_vals = o.get('trlValues') or []
    trl_str  = f'TRL {trl_vals[0]}-{trl_vals[-1]}' if trl_vals else 'Any TRL'
    amt      = o.get('amount', 0)
    print(f'  [{o.get(\"opportunityId\"):>3}] \${amt:>12,}  {trl_str:<12}  {o.get(\"name\")}')
"
echo ""

echo "=== GET /api/opportunities/maxFundingAmount ==="
curl -s "$BASE_URL/api/opportunities/maxFundingAmount" | python3 -c "
import sys, json
print(f'Max funding: \${json.load(sys.stdin).get(\"maxFunding\", 0):,}')
"
echo ""

echo "=== GET /api/opportunities/{opportunityId} ==="
OPP_ID=38
curl -s "$BASE_URL/api/opportunities/$OPP_ID" | python3 -c "
import sys, json, re
o        = json.load(sys.stdin).get('opportunity', {})
dir_obj  = o.get('directorate') or {}
trl_vals = o.get('trlValues') or []
desc     = re.sub(r'<[^>]+>', ' ', o.get('description', '') or '').strip()[:300]
print(f'ID               : {o.get(\"opportunityId\")}')
print(f'Name             : {o.get(\"name\")}')
print(f'Amount           : \${o.get(\"amount\", 0):,}')
print(f'Duration         : {o.get(\"duration\", \"N/A\")} months')
print(f'Frequency        : {o.get(\"frequency\", \"N/A\")}')
print(f'Next Solicitation: {o.get(\"nextSolicitation\", \"N/A\")}')
print(f'Topic Based      : {o.get(\"topicBased\", \"N/A\")}')
print(f'Eligible TRLs    : {trl_vals if trl_vals else \"N/A\"}')
print(f'Roles            : {\", \".join(o.get(\"opportunityRole\") or [])}')
print(f'Directorate      : {dir_obj.get(\"organizationName\", \"N/A\")} ({dir_obj.get(\"acronym\", \"N/A\")})')
if desc: print(f'Description      : {desc}...')
"
echo ""

echo "=== POST /api/opportunities — filtered search ==="
post_with_nonce "$BASE_URL/api/opportunities" \
  '{"limit":5}' \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
opps = data.get('opportunities') or data.get('results') or []
print(f'Returned: {len(opps)}')
for o in opps:
    print(f'  [{o.get(\"opportunityId\")}] {o.get(\"name\")} - \${o.get(\"amount\",0):,}')
"
echo ""


# =============================================================================
# ENUMERATIONS
# =============================================================================

echo "=== GET /api/enums — all enum names ==="
curl -s "$BASE_URL/api/enums" | python3 -c "
import sys, json
enums = json.load(sys.stdin).get('enums', {})
print(f'Available enums ({len(enums)}):')
for name in sorted(enums.keys()):
    vals  = enums[name]
    count = len(vals) if isinstance(vals, list) else '?'
    print(f'  {name:<45} ({count} values)')
"
echo ""

echo "=== GET /api/enums/projectStatusType ==="
curl -s "$BASE_URL/api/enums/projectStatusType" | python3 -c "
import sys, json
for v in json.load(sys.stdin).get('values', []):
    print(f'  {v.get(\"value\",\"\"):<40} {v.get(\"label\",\"\")}')
"
echo ""

echo "=== GET /api/enums/destinationTypes ==="
curl -s "$BASE_URL/api/enums/destinationTypes" | python3 -c "
import sys, json
for v in json.load(sys.stdin).get('values', []):
    print(f'  {v.get(\"value\",\"\"):<45} {v.get(\"label\",\"\")}')
"
echo ""

echo "=== GET /api/enums/organizationTypes ==="
curl -s "$BASE_URL/api/enums/organizationTypes" | python3 -c "
import sys, json
for v in json.load(sys.stdin).get('values', []):
    print(f'  {v.get(\"value\",\"\"):<45} {v.get(\"label\",\"\")}')
"
echo ""

echo "Done."
