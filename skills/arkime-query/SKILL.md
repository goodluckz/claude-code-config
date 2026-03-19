---
name: arkime-query
description: Query Arkime/OpenSearch for session counts, unique ASes, and traffic statistics. Use when user wants to check NTP/TCP/UDP/ICMP sessions or analyze source AS data.
---

# Arkime Query Skill

Query Arkime API directly for session counts, unique source ASes, and traffic analysis.

## Prerequisites

- SSH tunnel must be active to the appropriate cluster:
  - **ENV-28 (HoneyNet)**: `ssh -N -L 8010:localhost:8007 dns-analy4 &`
  - **ENV-30 (AWS NTP)**: `ssh -N -L 8011:localhost:8005 dns-analy4 &`
- Redis must be running locally (required by analyutils cache)

## Common Queries

### 1. Session Count by Expression

Query total sessions matching an expression:

```python
import analyutils as utils

url = 'http://localhost:8010/api/sessions'  # 8010=HoneyNet, 8011=AWS
params = {
    'expression': 'source.as.number==4134&&protocols==ntp',
    'startTime': '0',
    'stopTime': '1769871600',  # 2026/2/1
    'length': '1'
}
sessions = utils.get_sessions(url, params)
print(f"Total sessions: {sessions}")
```

### 2. Protocol-Specific Queries

Common protocol expressions:
- **NTP**: `protocols==ntp`
- **TCP**: `protocols==tcp`
- **UDP (non-NTP)**: `protocols==udp&&port.dst!=123`
- **ICMP Echo**: `protocols==icmp&&icmp.type==128`
- **All scans**: `protocols==tcp||(protocols==udp&&port.dst!=123)||(protocols==icmp&&icmp.type==128)`

### 3. Query by Source AS

```python
# NTP sessions from AS4134
expression = 'source.as.number==4134&&protocols==ntp'

# TCP sessions from AS16509 (Amazon)
expression = 'source.as.number==16509&&protocols==tcp'
```

### 4. Query by Destination Prefix

```python
# Traffic to Tokyo honeynet NTP experiments
expression = 'protocols==ntp&&(ip.dst==2001:200:0:c0c2::/64||ip.dst==2001:200:0:c0c4::/64)'

# Traffic to specific /56 prefix
expression = 'ip.dst==2001:200:0:c000::/56'
```

### 5. Get Unique Source ASes

```python
import analyutils as utils

url = 'http://localhost:8010/api/sessions'
params = {
    'expression': 'protocols==ntp',
    'startTime': '0',
    'stopTime': '1769871600',
    'counts': 0,
    'exp': 'source.as.full'  # or 'source.as.number' for just AS numbers
}
result = utils.request_api_with_cache(url, headers={}, params=params)
# result contains unique AS list with session counts
```

### 6. Get Source IPs with ASN

```python
params = {
    'expression': 'protocols==ntp&&ip.dst==2001:200:0:c0c4::/64',
    'startTime': '0',
    'stopTime': '1769871600',
    'counts': 1,
    'exp': 'ip.src'
}
```

## Experiment Prefixes Reference

### HoneyNet (ENV-28, port 8010)
| ID | Experiment | Prefix |
|----|------------|--------|
| 12 | exp-ntp-dark | 2001:200:0:c0c2:/64 |
| 13 | exp-ntp-honey | 2001:200:0:c0c4:/64 |
| 14 | exp-whole | 2001:200:0:c000:/56 |

### AWS NTP (ENV-30, port 8011)
| ID | Region | Prefix |
|----|--------|--------|
| 15 | tokyo | 2406:da14:11a0:20c4:/64 |
| 17 | california | 2600:1f1c:601:6100:/64 |
| 18 | frankfurt | 2a05:d014:199d:f300:/64 |
| 19 | virginia | 2600:1f18:7ac5:b70:/64 |
| 20 | mumbai | 2406:da1a:6f3:3daa:/64 |
| 21 | saopaulo | 2600:1f1e:d51:f1de:/64 |
| 22 | sydney | 2406:da1c:6ac:b6b5:/64 |

## Quick One-Liner Examples

```bash
# Check NTP sessions for AS4134 on HoneyNet
source .venv/bin/activate && python3 -c "
import analyutils as utils
sessions = utils.get_sessions('http://localhost:8010/api/sessions', {
    'expression': 'source.as.number==4134&&protocols==ntp',
    'startTime': '0', 'stopTime': '1769871600', 'length': '1'
})
print(f'AS4134 NTP sessions: {sessions:,}')
"

# Check total NTP sessions on AWS Tokyo
source .venv/bin/activate && python3 -c "
import analyutils as utils
sessions = utils.get_sessions('http://localhost:8011/api/sessions', {
    'expression': 'protocols==ntp&&ip.dst==2406:da14:11a0:20c4::/64',
    'startTime': '0', 'stopTime': '1769871600', 'length': '1'
})
print(f'AWS Tokyo NTP sessions: {sessions:,}')
"
```

## stopTime Reference

- `1759276800` = 2025/10/1 (old default)
- `1769871600` = 2026/2/1 (current default)

To calculate a new stopTime:
```python
from datetime import datetime
print(int(datetime(2026, 3, 1).timestamp()))  # For March 1, 2026
```

## Troubleshooting

1. **Connection refused**: Check SSH tunnel is active
2. **Unauthorized**: analyutils handles auth automatically, but ensure you're using `utils.get_sessions()` not raw requests
3. **Redis error**: Start Redis with `redis-server` or `brew services start redis`
4. **Empty results**: Verify the expression syntax and check stopTime covers your data range
