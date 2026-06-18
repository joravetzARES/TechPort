# TechPort API Sample Scripts

Sample scripts for interacting with the [TechPort RESTful API](https://techport.nasa.gov/help/api).

## Structure

```
public/
  python/
    quickstart.py                    # Start here — fetches and summarizes recent projects
    projects.py                      # GET /api/projects, /api/projects/{id}
    search.py                        # GET + POST /api/{objectType}/search, schema, allData
    organizations.py                 # GET /api/organizations, /{id}, POST searchOrgs
    misc_endpoints.py                # Opportunities, programs, enumerations
    use-cases/
      explore_program_projects.py    # Multi-step: pick a program → fetch projects → CSV
  curl/
    techport_public.sh               # All confirmed public endpoints as curl commands
```

## Authentication

**Public endpoints** — No authentication required for all GET requests and
the following POST requests: project search, organization search, opportunity search.

## Base URL

```
https://techport.nasa.gov
```

## Requirements (Python scripts)

- Python 3.7+
- `requests` library: `pip install requests`

## Quick Start

```bash
pip install requests
python public/python/quickstart.py
```

## A Note on These Examples

These scripts are written for clarity, not completeness. To keep them readable:

- **Requests show only the required fields**, not every optional field the API
  accepts. Real request bodies can often include more — check the API spec or
  the in-app network tab if you need a field that isn't shown here.
- **Responses are summarized**, not dumped in full. Most TechPort API responses
  include far more data than what gets printed (nested objects, additional
  metadata fields, pagination info, etc.). The scripts pull out a few fields to
  prove the call worked and keep the output readable — they are not showing you
  everything that comes back.
- **Function signatures simplify some endpoints.** A few endpoints accept
  several alternate body shapes or optional parameters not exposed here. Where
  that's the case, the docstring or a nearby comment calls it out, but treat
  these as starting points rather than exhaustive wrappers.

If you're building something that depends on a field or response shape not
shown in these examples, don't assume it doesn't exist — check the full API
spec or inspect a live response.

## Public Endpoint Coverage

| Endpoint | Methods |
|---|---|
| /api/projects | GET |
| /api/projects/{projectId} | GET |
| /api/{objectType}/search | GET, POST |
| /api/{objectType}/search/allData | GET |
| /api/{objectType}/schema | GET |
| /api/organizations | GET |
| /api/organizations/{organizationId} | GET |
| /api/organizations/searchOrgs | POST |
| /api/programs | GET |
| /api/programs/{programId} | GET |
| /api/opportunities | GET, POST |
| /api/opportunities/{opportunityId} | GET |
| /api/opportunities/export | POST |
| /api/opportunities/maxFundingAmount | GET |
| /api/enums | GET |
| /api/enums/{enumName} | GET |

*Note: /drex/predict and /trex/predict are excluded currently.*

*Not yet covered by these samples, though present in the public spec:
/api/contacts, /api/flex, /api/nonce, /api/feedback, /api/searches/{searchId},
and the /api/taxonomies family of endpoints.*

## Questions / Support

Contact the TechPort Team: hq-techport@mail.nasa.gov
