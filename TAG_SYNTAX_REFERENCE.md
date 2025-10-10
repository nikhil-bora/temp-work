# CUR Tag Query Syntax - Quick Reference

## Tag Storage Format

Tags in `raw_tags` column are stored as plain JSON without any prefix:

```json
{
  "Environment": "production",
  "Team": "platform",
  "goog-k8s-cluster-name": "gke123",
  "aws:eks:cluster-name": "dataplatform"
}
```

## Query Syntax Rules

### Simple Tags (Alphanumeric Only)

Use `json_extract_scalar()` for tag keys without special characters:

```sql
json_extract_scalar(raw_tags, '$.TagKey')
```

**Example:**
```sql
WHERE json_extract_scalar(raw_tags, '$.Environment') = 'production'
GROUP BY json_extract_scalar(raw_tags, '$.Team')
```

### Tags with Special Characters (Hyphens, Colons, Dots)

Use `json_extract()` with bracket notation for tag keys containing `-`, `:`, or `.`:

```sql
json_extract(raw_tags, '$["tag-key-with-hyphens"]')
```

⚠️ **Important**: `json_extract()` returns **quoted** JSON strings, so you must compare with quoted values:

```sql
WHERE json_extract(raw_tags, '$["goog-k8s-cluster-name"]') = '"gke123"'
-- Note the double and single quotes: = '"value"'
```

## Common Tag Examples

### Simple Tags

| Tag Key | Query |
|---------|-------|
| Environment | `json_extract_scalar(raw_tags, '$.Environment')` |
| Team | `json_extract_scalar(raw_tags, '$.Team')` |
| Project | `json_extract_scalar(raw_tags, '$.Project')` |
| Owner | `json_extract_scalar(raw_tags, '$.Owner')` |

### Tags with Hyphens

| Tag Key | Query |
|---------|-------|
| goog-k8s-cluster-name | `json_extract(raw_tags, '$["goog-k8s-cluster-name"]')` |
| goog-k8s-node-pool-name | `json_extract(raw_tags, '$["goog-k8s-node-pool-name"]')` |
| goog-k8s-cluster-location | `json_extract(raw_tags, '$["goog-k8s-cluster-location"]')` |
| app-name | `json_extract(raw_tags, '$["app-name"]')` |

### Tags with Colons

| Tag Key | Query |
|---------|-------|
| aws:eks:cluster-name | `json_extract(raw_tags, '$["aws:eks:cluster-name"]')` |
| aws:eks:namespace | `json_extract(raw_tags, '$["aws:eks:namespace"]')` |
| aws:autoscaling:groupName | `json_extract(raw_tags, '$["aws:autoscaling:groupName"]')` |
| aws:createdBy | `json_extract(raw_tags, '$["aws:createdBy"]')` |

## Complete Query Examples

### 1. Filter by Simple Tag

```sql
SELECT
    "product/productname" as service,
    SUM("lineitem/unblendedcost") as cost
FROM "raw-data-v1"."raw_aws_amnic"
WHERE json_extract_scalar(raw_tags, '$.Environment') = 'production'
AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
GROUP BY "product/productname"
ORDER BY cost DESC
```

### 2. Group by Tag with Hyphens

```sql
SELECT
    json_extract(raw_tags, '$["goog-k8s-cluster-name"]') as cluster,
    COUNT(*) as line_items,
    ROUND(SUM("lineitem/unblendedcost"), 2) as cost
FROM "raw-data-v1"."raw_aws_amnic"
WHERE json_extract(raw_tags, '$["goog-k8s-cluster-name"]') IS NOT NULL
AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
GROUP BY json_extract(raw_tags, '$["goog-k8s-cluster-name"]')
ORDER BY cost DESC
```

### 3. Filter by Specific Cluster (Note the Quoted Value!)

```sql
SELECT
    SUM("lineitem/unblendedcost") as cost
FROM "raw-data-v1"."raw_aws_amnic"
WHERE json_extract(raw_tags, '$["goog-k8s-cluster-name"]') = '"gke123"'
--    Note: Compare with '"gke123"' (with quotes) not 'gke123' ────────┘
AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
```

### 4. Mixed Simple and Special Character Tags

```sql
SELECT
    json_extract_scalar(raw_tags, '$.Environment') as env,
    json_extract(raw_tags, '$["goog-k8s-cluster-name"]') as cluster,
    SUM("lineitem/unblendedcost") as cost
FROM "raw-data-v1"."raw_aws_amnic"
WHERE json_extract_scalar(raw_tags, '$.Environment') IS NOT NULL
AND json_extract(raw_tags, '$["goog-k8s-cluster-name"]') IS NOT NULL
AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
GROUP BY
    json_extract_scalar(raw_tags, '$.Environment'),
    json_extract(raw_tags, '$["goog-k8s-cluster-name"]')
ORDER BY cost DESC
```

### 5. Find Untagged Resources

```sql
SELECT
    "product/productname" as service,
    ROUND(SUM("lineitem/unblendedcost"), 2) as untagged_cost
FROM "raw-data-v1"."raw_aws_amnic"
WHERE (json_extract_scalar(raw_tags, '$.Environment') IS NULL
       OR json_extract_scalar(raw_tags, '$.Environment') = '')
AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
GROUP BY "product/productname"
ORDER BY untagged_cost DESC
```

## Common Mistakes

### ❌ Wrong: Using json_extract_scalar for tags with hyphens
```sql
-- This will FAIL with syntax error
WHERE json_extract_scalar(raw_tags, '$.goog-k8s-cluster-name') = 'gke123'
```

### ✅ Correct: Use json_extract with bracket notation
```sql
WHERE json_extract(raw_tags, '$["goog-k8s-cluster-name"]') = '"gke123"'
```

---

### ❌ Wrong: Comparing json_extract result without quotes
```sql
-- This will return 0 rows even if data exists
WHERE json_extract(raw_tags, '$["cluster-name"]') = 'gke123'
```

### ✅ Correct: Include quotes in comparison value
```sql
WHERE json_extract(raw_tags, '$["cluster-name"]') = '"gke123"'
```

---

### ❌ Wrong: Using resourceTags/ prefix
```sql
-- This will FAIL - tags don't have resourceTags/ prefix
WHERE json_extract_scalar(raw_tags, '$.resourceTags/Environment') = 'production'
```

### ✅ Correct: Tags have no prefix
```sql
WHERE json_extract_scalar(raw_tags, '$.Environment') = 'production'
```

## Quick Decision Tree

```
Does your tag key contain hyphens, colons, or dots?
│
├─ NO → Use json_extract_scalar(raw_tags, '$.TagKey')
│        Compare with: = 'value'
│
└─ YES → Use json_extract(raw_tags, '$["tag-key"]')
          Compare with: = '"value"' (note the quotes!)
```

## Creating KPIs with Tags

### Simple Tag KPI

```python
{
  "name": "Production Cost",
  "query": """
    SELECT SUM("lineitem/unblendedcost") as cost
    FROM {table}
    WHERE json_extract_scalar(raw_tags, '$.Environment') = 'production'
    AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
  """,
  "format": "currency"
}
```

### Special Character Tag KPI

```python
{
  "name": "Top GKE Cluster",
  "query": """
    SELECT json_extract(raw_tags, '$["goog-k8s-cluster-name"]') as cluster
    FROM {table}
    WHERE json_extract(raw_tags, '$["goog-k8s-cluster-name"]') IS NOT NULL
    AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
    GROUP BY json_extract(raw_tags, '$["goog-k8s-cluster-name"]')
    ORDER BY SUM("lineitem/unblendedcost") DESC
    LIMIT 1
  """,
  "format": "text"
}
```

## Testing Your Queries

Use this pattern to test tag queries:

```sql
-- 1. First check if tag exists
SELECT COUNT(*) as count
FROM {table}
WHERE json_extract(raw_tags, '$["your-tag-key"]') IS NOT NULL
LIMIT 1;

-- 2. Sample tag values
SELECT DISTINCT json_extract(raw_tags, '$["your-tag-key"]') as tag_value
FROM {table}
WHERE json_extract(raw_tags, '$["your-tag-key"]') IS NOT NULL
LIMIT 10;

-- 3. Then build your full query
SELECT
    json_extract(raw_tags, '$["your-tag-key"]') as tag_value,
    SUM("lineitem/unblendedcost") as cost
FROM {table}
WHERE json_extract(raw_tags, '$["your-tag-key"]') IS NOT NULL
GROUP BY json_extract(raw_tags, '$["your-tag-key"]')
ORDER BY cost DESC;
```

---

**Remember**:
- Simple keys → `json_extract_scalar()` → compare with `'value'`
- Special char keys → `json_extract()` → compare with `'"value"'` (quoted!)
- No `resourceTags/` prefix needed

---

**Last Updated**: October 10, 2025
**Status**: ✅ Tested and Verified
