---
name: arkime-tag-manager
description: Manage Arkime session tags (add/remove) using API
---

# Arkime Tag Manager

This skill provides commands and code for adding and removing tags from Arkime sessions using the API.

## Important: When to Use Tags

**Tags are designed for marking small subsets of sessions, not for bulk labeling.**

| Use Case | Recommended | Notes |
|----------|-------------|-------|
| Mark suspicious sessions for review | ✅ Yes | Dozens to hundreds of sessions |
| Flag specific incidents | ✅ Yes | Small, targeted sets |
| Annotate interesting traffic | ✅ Yes | Manual or semi-automated |
| Label all sessions by experiment | ❌ No | Use query expressions instead |
| Categorize billions of sessions | ❌ No | Tags don't scale to production volumes |

**Why not bulk tag?**
- Production environments can have **billions of sessions**
- Adding tags modifies every document in OpenSearch/Elasticsearch
- Bulk tagging is slow and resource-intensive
- Query expressions (`ip.dst == prefix`) achieve the same filtering without modification

**Alternative: Use Query Expressions**

Instead of tagging all sessions belonging to an experiment:
```bash
# Don't do this (slow, modifies data):
# curl ... -d '{"expression": "ip.dst == 2406:da1a::/64", "tags": "exp:mumbai"}'

# Do this instead (fast, no modification):
curl 'http://localhost:8041/api/sessions?expression=ip.dst%20%3D%3D%202406%3Ada1a%3A%3A%2F64'
```

## Prerequisites

- **Authentication**: HTTP Digest Authentication with username/password
- **Add Tags**: Standard authenticated user access
- **Remove Tags**: Requires `remove` permission (admin privilege)

## API Endpoints

- **Add Tags**: `POST /api/sessions/addtags`
- **Remove Tags**: `POST /api/sessions/removetags` (requires remove permission)

## Common Parameters

Both endpoints accept:
- `tags` (required): Comma-separated list of tags
- `date`: Time range parameter (`-1` = all data, `N` = last N hours)
- **Either**:
  - `expression`: Arkime query expression to filter sessions
  - `ids`: Comma-separated session IDs

## Add Tags

### Using curl with Expression

```bash
# Add single tag to sessions matching expression
curl --anyauth -u 'admin:admin' \
  -H 'Content-Type: application/json' \
  -d '{"expression": "protocols == ntp", "tags": "ntp-traffic"}' \
  'http://localhost:8041/api/sessions/addtags?date=-1'

# Add multiple tags (comma-separated)
curl --anyauth -u 'admin:admin' \
  -H 'Content-Type: application/json' \
  -d '{"expression": "ip.dst == 2406:da14:11a0:20c4:/64", "tags": "exp:exp-ntp-tokyo,region:tokyo,dataset:aws"}' \
  'http://localhost:8041/api/sessions/addtags?date=-1'
```

### Using curl with Session IDs

```bash
curl --anyauth -u 'admin:admin' \
  -H 'Content-Type: application/json' \
  -d '{"ids": "session_id_1,session_id_2,session_id_3", "tags": "malware,suspicious"}' \
  'http://localhost:8041/api/sessions/addtags?date=-1'
```

### Using Python

```python
import requests
from requests.auth import HTTPDigestAuth

ARKIME_URL = "http://localhost:8041"
AUTH = HTTPDigestAuth("admin", "admin")

def add_tags_by_expression(expression, tags, date="-1"):
    """Add tags to sessions matching expression

    Args:
        expression: Arkime query expression
        tags: Single tag or comma-separated tags
        date: Time range ("-1" = all data)

    Returns:
        API response dict with 'success' and 'text' fields
    """
    url = f"{ARKIME_URL}/api/sessions/addtags"

    params = {"date": date}
    payload = {
        "tags": tags,
        "expression": expression
    }

    response = requests.post(
        url,
        params=params,
        json=payload,
        auth=AUTH,
        timeout=60
    )
    response.raise_for_status()
    return response.json()

# Example usage
result = add_tags_by_expression(
    expression="ip.dst == 2406:da14:11a0:20c4:/64",
    tags="exp:exp-ntp-tokyo"
)
print(result)  # {"success": true, "text": "Tags added successfully"}
```

## Remove Tags

**⚠️ IMPORTANT**: Removing tags requires `remove` permission. If you get:
```json
{"success":false,"text":"You do not have permission to access this resource"}
```
This means your user lacks the `remove` permission in Arkime configuration.

### Using curl with Expression

```bash
# Remove single tag from sessions matching expression
curl --anyauth -u 'admin:admin' \
  -H 'Content-Type: application/json' \
  -d '{"expression": "tags == test-tag", "tags": "test-tag"}' \
  'http://localhost:8041/api/sessions/removetags?date=-1'

# Remove multiple tags
curl --anyauth -u 'admin:admin' \
  -H 'Content-Type: application/json' \
  -d '{"expression": "tags == [exp:*]", "tags": "exp:exp-ntp-tokyo,exp:exp-ntp-california"}' \
  'http://localhost:8041/api/sessions/removetags?date=-1'
```

### Using curl with Session IDs

```bash
curl --anyauth -u 'admin:admin' \
  -H 'Content-Type: application/json' \
  -d '{"ids": "session_id_1,session_id_2", "tags": "malware"}' \
  'http://localhost:8041/api/sessions/removetags?date=-1'
```

### Using Python

```python
def remove_tags_by_expression(expression, tags, date="-1"):
    """Remove tags from sessions matching expression

    Requires: 'remove' permission in Arkime

    Args:
        expression: Arkime query expression
        tags: Single tag or comma-separated tags
        date: Time range ("-1" = all data)

    Returns:
        API response dict with 'success' and 'text' fields
    """
    url = f"{ARKIME_URL}/api/sessions/removetags"

    params = {"date": date}
    payload = {
        "tags": tags,
        "expression": expression
    }

    response = requests.post(
        url,
        params=params,
        json=payload,
        auth=AUTH,
        timeout=60
    )
    response.raise_for_status()
    return response.json()

# Example usage
result = remove_tags_by_expression(
    expression="tags == test-tag",
    tags="test-tag"
)
print(result)  # {"success": true, "text": "Tags removed successfully"}
```

## Bulk Tag Management Examples

### Bulk Add Tags to All Experiments

```bash
# Generate comma-separated tag list from exps.json
TAGS=$(cat data/exps.json | jq -r '.[] | select((.id | IN(14, 16)) | not) | "exp:\(.exp)"' | paste -sd ',' -)

# Add tags to each experiment by destination prefix
for exp in $(cat data/exps.json | jq -c '.[] | select((.id | IN(14, 16)) | not)'); do
    exp_name=$(echo $exp | jq -r '.exp')
    prefix=$(echo $exp | jq -r '.prefix')
    tag="exp:$exp_name"

    echo "Adding tag $tag to sessions with ip.dst == $prefix"

    curl --anyauth -u 'admin:admin' \
      -H 'Content-Type: application/json' \
      -d "{\"expression\": \"ip.dst == $prefix\", \"tags\": \"$tag\"}" \
      'http://localhost:8041/api/sessions/addtags?date=-1'
done
```

### Bulk Remove Experiment Tags

```bash
# Remove all experiment tags (requires remove permission)
TAGS=$(cat data/exps.json | jq -r '.[] | select((.id | IN(14, 16)) | not) | "exp:\(.exp)"' | paste -sd ',' -)

curl --anyauth -u 'admin:admin' \
  -H 'Content-Type: application/json' \
  -d "{\"expression\": \"tags == [exp:*]\", \"tags\": \"$TAGS\"}" \
  'http://localhost:8041/api/sessions/removetags?date=-1'
```

### Verify Tags Added

```bash
# Check session count for a specific tag
curl -s --anyauth -u 'admin:admin' \
  "http://localhost:8041/api/sessions?expression=tags%20%3D%3D%20exp:exp-ntp-tokyo&date=-1&length=0" \
  | jq '.recordsTotal'

# Verify multiple tags
for tag in "exp:exp-ntp-tokyo" "exp:exp-ntp-california" "exp:exp-ntp-mumbai"; do
  count=$(curl -s --anyauth -u 'admin:admin' \
    "http://localhost:8041/api/sessions?expression=tags%20%3D%3D%20$tag&date=-1&length=0" \
    | jq '.recordsTotal')
  echo "$tag: $count sessions"
done
```

## Python Bulk Tag Management

```python
import json
import requests
from requests.auth import HTTPDigestAuth

ARKIME_URL = "http://localhost:8041"
AUTH = HTTPDigestAuth("admin", "admin")

def bulk_tag_experiments(exps_file="data/exps.json", skip_ids=[14, 16], dry_run=False):
    """Add experiment tags to all sessions by destination prefix

    Args:
        exps_file: Path to experiments JSON file
        skip_ids: List of experiment IDs to skip
        dry_run: If True, only preview without adding tags

    Returns:
        List of results for each experiment
    """
    # Load experiments
    with open(exps_file) as f:
        all_exps = json.load(f)

    exps_to_tag = [e for e in all_exps if e["id"] not in skip_ids]
    results = []

    for exp in exps_to_tag:
        exp_name = exp["exp"]
        prefix = exp["prefix"]
        tag = f"exp:{exp_name}"
        expression = f"ip.dst == {prefix}"

        print(f"Processing {exp_name}...")

        if dry_run:
            # Count sessions
            response = requests.get(
                f"{ARKIME_URL}/api/sessions",
                params={"expression": expression, "date": "-1", "length": 0},
                auth=AUTH
            )
            count = response.json().get("recordsTotal", 0)
            print(f"  Would tag {count:,} sessions")
            results.append({"exp": exp_name, "sessions": count, "dry_run": True})
        else:
            # Add tag
            result = add_tags_by_expression(expression, tag)
            results.append({"exp": exp_name, "success": result.get("success")})
            print(f"  {result.get('text')}")

    return results

# Run bulk tagging
results = bulk_tag_experiments(dry_run=True)
print(f"\nProcessed {len(results)} experiments")
```

## Tag Expression Syntax

Common tag query expressions:

- `tags == mytag` - Sessions with exact tag
- `tags == [prefix:*]` - Sessions with tags starting with "prefix:"
- `tags == [exp:exp-ntp-*]` - Sessions with experiment tags matching pattern
- `tags != mytag` - Sessions without the tag
- `tags == tag1 && tags == tag2` - Sessions with both tags
- `tags == tag1 || tags == tag2` - Sessions with either tag

## Troubleshooting

### Permission Denied for Remove Tags

**Error**: `{"success":false,"text":"You do not have permission to access this resource"}`

**Solution**: The user needs `remove` permission in Arkime. There are 3 ways to enable it:

#### Method 1: Web UI (Easiest)

1. Login to Arkime Web UI as admin
2. Go to **Settings** → **Users**
3. Find the user that needs remove permission
4. **Uncheck** the "Disable arkime data removal" checkbox
5. Save changes

#### Method 2: Command Line (addUser.js)

```bash
# Inside Arkime container
cd /opt/arkime/viewer
node addUser.js -u <username> --remove

# For Docker (ENV-41 example)
docker exec env-41_arkime /opt/arkime/node-v20.19.6-linux-arm64/bin/node \
  /opt/arkime/viewer/addUser.js -u admin --remove
```

#### Method 3: Config File

```ini
# In Arkime config.ini
[default]
...
# Grant remove permission to admin users
removeEnabled=true
```

**Note**: After using Method 2 or 3, you may need to restart the Arkime viewer for changes to take effect.

### Authentication Failed

Use `--anyauth` flag with curl to automatically detect the authentication method:

```bash
curl --anyauth -u 'username:password' ...
```

### Tags Not Applied

1. **Check expression syntax**: Verify your Arkime expression is valid
2. **Check session count**: Query first to ensure sessions match your expression
3. **Index refresh delay**: Tags may take a few seconds to appear in queries

### addtags API Only Processes 100 Sessions (Default Limit)

**Symptom**: API returns `{"success":true,"text":"Tags added successfully"}` but only 100 sessions are tagged, even when the expression matches thousands of sessions.

**Root Cause**: The Arkime `addtags` API has a **default limit of 100 sessions** when no `length` parameter is specified. This is the same as the default page size for session queries.

**Solution 1: Add `length` parameter**

Specify a larger `length` parameter to process more sessions:

```bash
# Add length parameter to process up to 1,000,000 sessions
curl --anyauth -u 'admin:admin' \
  -H 'Content-Type: application/json' \
  -d '{"expression": "ip.dst == 2406:da1a:6f3:3daa::/64", "tags": "exp:exp-ntp-mumbai"}' \
  'http://localhost:8041/api/sessions/addtags?date=-1&length=1000000'
```

```python
# Python: specify length parameter
response = requests.post(
    f"{ARKIME_URL}/api/sessions/addtags",
    params={"date": "-1", "length": 1000000},  # Process up to 1M sessions
    json={"expression": expression, "tags": tag},
    auth=AUTH,
    timeout=600  # Increase timeout for large operations
)
```

**⚠️ Warning**: With `length` parameter, the API processes sessions one-by-one, which is **very slow** for large datasets (e.g., 700K sessions can take 10+ minutes).

**Solution 2: Use OpenSearch update_by_query (Recommended for Bulk)**

For tagging large numbers of sessions (10K+), use OpenSearch's `update_by_query` directly:

```python
import requests

def add_tag_via_opensearch(cidr, tag, opensearch_url="http://localhost:9200"):
    """Add tag to sessions matching CIDR using OpenSearch update_by_query

    Much faster than Arkime API for large datasets.

    Args:
        cidr: IPv6 CIDR (e.g., "2406:da1a:6f3:3daa::/64")
        tag: Tag string to add
        opensearch_url: OpenSearch endpoint URL
    """
    auth = ("admin", "admin")

    # Count matching sessions
    count_resp = requests.post(
        f"{opensearch_url}/arkime_sessions3-*/_count",
        json={"query": {"term": {"destination.ip": cidr}}},
        auth=auth
    )
    count = count_resp.json().get('count', 0)
    print(f"Matching sessions: {count:,}")

    if count == 0:
        return 0

    # Add tag using update_by_query
    response = requests.post(
        f"{opensearch_url}/arkime_sessions3-*/_update_by_query?conflicts=proceed&wait_for_completion=false",
        json={
            "query": {"term": {"destination.ip": cidr}},
            "script": {
                "source": """
                    if (ctx._source.tags == null) {
                        ctx._source.tags = [params.tag];
                    } else if (!ctx._source.tags.contains(params.tag)) {
                        ctx._source.tags.add(params.tag);
                    }
                """,
                "params": {"tag": tag}
            }
        },
        auth=auth,
        timeout=60
    )

    if response.ok:
        task_id = response.json().get('task')
        print(f"Task submitted: {task_id}")
        return task_id
    else:
        print(f"Error: {response.text}")
        return None

# Example: Tag 700K+ sessions in seconds
task_id = add_tag_via_opensearch("2406:da1a:6f3:3daa::/64", "exp:exp-ntp-mumbai")

# Check task status
resp = requests.get(f"http://localhost:9200/_tasks/{task_id}", auth=("admin", "admin"))
print(resp.json())
```

**Performance Comparison**:
| Method | 100 sessions | 100K sessions | 700K sessions |
|--------|-------------|---------------|---------------|
| Arkime API (default) | ~1s | N/A (limited) | N/A (limited) |
| Arkime API + length | ~1s | ~60s | ~10+ min |
| OpenSearch update_by_query | ~1s | ~10s | ~60s |

### removetags API Returns Success But Tags Not Removed

**Symptom**: API returns `{"success":true,"text":"Tags removed successfully"}` but tags are still present.

**Known Issue**: For complex tags containing commas (e.g., `dataset:aws,ip-version:v6,protocol:scan,region:tokyo`), the Arkime removetags API may not work correctly.

**Workaround**: Use OpenSearch's `update_by_query` directly to remove tags:

```python
import requests

def remove_tag_via_opensearch(tag, opensearch_url="http://localhost:9200"):
    """Remove tag directly via OpenSearch update_by_query

    Use this when Arkime's removetags API doesn't work.

    Args:
        tag: Exact tag string to remove
        opensearch_url: OpenSearch endpoint URL
    """
    # Count before
    count_response = requests.post(
        f'{opensearch_url}/arkime_sessions3-*/_count',
        json={"query": {"term": {"tags": tag}}},
        auth=("admin", "admin")
    )
    before = count_response.json().get('count', 0)
    print(f"Before: {before} sessions with tag")

    # Remove tag using update_by_query
    response = requests.post(
        f'{opensearch_url}/arkime_sessions3-*/_update_by_query?conflicts=proceed',
        headers={'Content-Type': 'application/json'},
        json={
            "query": {"term": {"tags": tag}},
            "script": {
                "source": "ctx._source.tags.removeIf(t -> t == params.tag)",
                "params": {"tag": tag}
            }
        },
        auth=("admin", "admin"),
        timeout=300
    )

    result = response.json()
    print(f"Updated: {result.get('updated', 0)} sessions")

    # Refresh index
    requests.post(f'{opensearch_url}/arkime_sessions3-*/_refresh', auth=("admin", "admin"))

    # Count after
    count_response = requests.post(
        f'{opensearch_url}/arkime_sessions3-*/_count',
        json={"query": {"term": {"tags": tag}}},
        auth=("admin", "admin")
    )
    after = count_response.json().get('count', 0)
    print(f"After: {after} sessions with tag")

    return before - after

# Example usage
tag = "dataset:aws,ip-version:v6,protocol:scan,region:frankfurt"
removed = remove_tag_via_opensearch(tag)
print(f"Successfully removed tag from {removed} sessions")
```

### Using curl for OpenSearch Direct Tag Removal

```bash
# Remove specific tag using update_by_query
curl -X POST "http://localhost:9200/arkime_sessions3-*/_update_by_query?conflicts=proceed" \
  -u admin:admin \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "term": {
        "tags": "dataset:aws,ip-version:v6,protocol:scan,region:frankfurt"
      }
    },
    "script": {
      "source": "ctx._source.tags.removeIf(t -> t == params.tag)",
      "params": {
        "tag": "dataset:aws,ip-version:v6,protocol:scan,region:frankfurt"
      }
    }
  }'

# Refresh index after update
curl -X POST "http://localhost:9200/arkime_sessions3-*/_refresh" -u admin:admin

# Verify removal
curl -X POST "http://localhost:9200/arkime_sessions3-*/_count" \
  -u admin:admin \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "term": {
        "tags": "dataset:aws,ip-version:v6,protocol:scan,region:frankfurt"
      }
    }
  }'
```

## References

- Arkime API Documentation: `/api/sessions/addtags` and `/api/sessions/removetags`
- Project file: `ARKIME_API_SUMMARY.md` - Complete Arkime API reference
- Project file: `docs/SOLUTION_SUMMARY.md` - API usage examples
- Implementation: `scripts/bulk_tag_experiments.py` - Bulk tagging script
- Implementation: `src/awsntpdagster/defs/arkime_resource.py` - ArkimeResource class with tag methods
