# Tag-Based CUR Queries Guide

## Overview

All AWS resource tags in the Cost and Usage Report (CUR) are stored in the `raw_tags` column as a JSON object. This guide explains how to query and filter by tags correctly.

## Tag Storage Format

Tags are stored in the `raw_tags` column with keys prefixed by `resourceTags/`:

```json
{
  "resourceTags/Environment": "production",
  "resourceTags/Team": "platform",
  "resourceTags/aws:eks:cluster-name": "dataplatform",
  "resourceTags/aws:eks:namespace": "spark"
}
```

## JSON Extraction Syntax

Use `json_extract_scalar()` function to access tag values:

```sql
json_extract_scalar(raw_tags, '$.resourceTags/TagKey')
```

**Important**: Tag keys must include the `resourceTags/` prefix!

## Query Examples

### 1. Filter by Environment Tag

```sql
SELECT
    "product/productname" as service,
    SUM("lineitem/unblendedcost") as cost
FROM "raw-data-v1"."raw_aws_amnic"
WHERE json_extract_scalar(raw_tags, '$.resourceTags/Environment') = 'production'
AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
AND YEAR("bill/billingperiodstartdate") = YEAR(current_date)
GROUP BY "product/productname"
ORDER BY cost DESC
```

### 2. Group Costs by Environment

```sql
SELECT
    json_extract_scalar(raw_tags, '$.resourceTags/Environment') as environment,
    COUNT(DISTINCT "lineitem/resourceid") as resource_count,
    ROUND(SUM("lineitem/unblendedcost"), 2) as total_cost
FROM "raw-data-v1"."raw_aws_amnic"
WHERE json_extract_scalar(raw_tags, '$.resourceTags/Environment') IS NOT NULL
AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
GROUP BY json_extract_scalar(raw_tags, '$.resourceTags/Environment')
ORDER BY total_cost DESC
```

### 3. Find Untagged Resources

```sql
SELECT
    "product/productname" as service,
    ROUND(SUM("lineitem/unblendedcost"), 2) as untagged_cost,
    COUNT(DISTINCT "lineitem/resourceid") as resource_count
FROM "raw-data-v1"."raw_aws_amnic"
WHERE (json_extract_scalar(raw_tags, '$.resourceTags/Environment') IS NULL
       OR json_extract_scalar(raw_tags, '$.resourceTags/Environment') = '')
AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
GROUP BY "product/productname"
ORDER BY untagged_cost DESC
```

### 4. EKS Cluster Costs (AWS System Tags)

```sql
SELECT
    json_extract_scalar(raw_tags, '$.resourceTags/aws:eks:cluster-name') as cluster_name,
    ROUND(SUM("lineitem/unblendedcost"), 2) as cluster_cost
FROM "raw-data-v1"."raw_aws_amnic"
WHERE json_extract_scalar(raw_tags, '$.resourceTags/aws:eks:cluster-name') IS NOT NULL
AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
GROUP BY json_extract_scalar(raw_tags, '$.resourceTags/aws:eks:cluster-name')
ORDER BY cluster_cost DESC
```

### 5. Multi-Tag Filter

```sql
SELECT
    "lineitem/resourceid" as resource,
    ROUND(SUM("lineitem/unblendedcost"), 2) as cost
FROM "raw-data-v1"."raw_aws_amnic"
WHERE json_extract_scalar(raw_tags, '$.resourceTags/Environment') = 'production'
  AND json_extract_scalar(raw_tags, '$.resourceTags/Team') = 'platform'
AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
GROUP BY "lineitem/resourceid"
ORDER BY cost DESC
LIMIT 10
```

### 6. Costs by Team (Multiple Tags)

```sql
SELECT
    json_extract_scalar(raw_tags, '$.resourceTags/Team') as team,
    json_extract_scalar(raw_tags, '$.resourceTags/Environment') as environment,
    ROUND(SUM("lineitem/unblendedcost"), 2) as cost
FROM "raw-data-v1"."raw_aws_amnic"
WHERE json_extract_scalar(raw_tags, '$.resourceTags/Team') IS NOT NULL
AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
GROUP BY
    json_extract_scalar(raw_tags, '$.resourceTags/Team'),
    json_extract_scalar(raw_tags, '$.resourceTags/Environment')
ORDER BY cost DESC
```

## Common Tag Keys

### User-Defined Tags
- `resourceTags/Environment` - production, staging, dev, qa
- `resourceTags/Team` - platform, data, frontend, backend
- `resourceTags/Project` - project name
- `resourceTags/Owner` - team or person responsible
- `resourceTags/CostCenter` - billing department
- `resourceTags/Application` - application name

### AWS System Tags
- `resourceTags/aws:eks:cluster-name` - EKS cluster identifier
- `resourceTags/aws:eks:namespace` - Kubernetes namespace
- `resourceTags/aws:eks:node` - EKS node identifier
- `resourceTags/aws:eks:workload-name` - Kubernetes workload
- `resourceTags/aws:createdBy` - Creator identity
- `resourceTags/aws:cloudformation:stack-name` - CloudFormation stack

## KPI Examples with Tags

### Production Environment Costs
```json
{
  "name": "Production Cost",
  "query_type": "cur",
  "query": "SELECT SUM(\"lineitem/unblendedcost\") as cost FROM {table} WHERE json_extract_scalar(raw_tags, '$.resourceTags/Environment') = 'production' AND MONTH(\"bill/billingperiodstartdate\") = MONTH(current_date)",
  "format": "currency"
}
```

### Untagged Resources Cost
```json
{
  "name": "Untagged Cost",
  "query_type": "cur",
  "query": "SELECT SUM(\"lineitem/unblendedcost\") as cost FROM {table} WHERE (json_extract_scalar(raw_tags, '$.resourceTags/Environment') IS NULL OR json_extract_scalar(raw_tags, '$.resourceTags/Environment') = '') AND MONTH(\"bill/billingperiodstartdate\") = MONTH(current_date)",
  "format": "currency"
}
```

### Top EKS Cluster
```json
{
  "name": "Top EKS Cluster",
  "query_type": "cur",
  "query": "SELECT json_extract_scalar(raw_tags, '$.resourceTags/aws:eks:cluster-name') as cluster FROM {table} WHERE json_extract_scalar(raw_tags, '$.resourceTags/aws:eks:cluster-name') IS NOT NULL AND MONTH(\"bill/billingperiodstartdate\") = MONTH(current_date) GROUP BY json_extract_scalar(raw_tags, '$.resourceTags/aws:eks:cluster-name') ORDER BY SUM(\"lineitem/unblendedcost\") DESC LIMIT 1",
  "format": "text"
}
```

## Creating Tag-Based KPIs from Chat

You can create tag-based KPIs directly from the chat interface:

**Example 1: Production Environment Costs**
```
You: Create a KPI to track production environment costs.
     Filter by Environment tag = production.
     Use 🏭 emoji, red color (#ff5c69), medium card.

Agent: [Creates KPI with proper tag query]
       ✓ Created KPI: Production Environment Cost
```

**Example 2: Untagged Resources**
```
You: Create a KPI showing costs from resources without Environment tag.
     Use ⚠️ emoji, yellow color (#ffcc00), large card.

Agent: [Creates KPI to find untagged resources]
       ✓ Created KPI: Untagged Resources Cost
```

**Example 3: EKS Cluster Costs**
```
You: Show costs for my largest EKS cluster using the aws:eks:cluster-name tag.
     Use ☸️ emoji, blue color (#326CE5), medium card.

Agent: [Creates KPI querying EKS cluster tags]
       ✓ Created KPI: Top EKS Cluster Cost
```

## Best Practices

### 1. Always Check for NULL
```sql
WHERE json_extract_scalar(raw_tags, '$.resourceTags/TagKey') IS NOT NULL
```

### 2. Use Consistent Tag Keys
- Standardize tag naming across your organization
- Document required tags
- Use the same case (e.g., "Environment" not "environment" or "ENVIRONMENT")

### 3. Monitor Untagged Resources
Create KPIs to track costs from untagged resources to improve cost allocation.

### 4. Group by Multiple Dimensions
Combine tags with other dimensions for richer insights:
```sql
GROUP BY
    "product/productname",
    json_extract_scalar(raw_tags, '$.resourceTags/Environment')
```

### 5. Use Date Filters
Always filter by date to improve query performance:
```sql
AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
AND YEAR("bill/billingperiodstartdate") = YEAR(current_date)
```

## Troubleshooting

### Query Returns No Results
- Check tag key spelling (case-sensitive)
- Verify `resourceTags/` prefix is included
- Confirm resources are actually tagged
- Check date range filters

### Syntax Errors
- Always use single quotes inside `json_extract_scalar()`: `'$.resourceTags/Key'`
- Use double quotes for CUR column names: `"lineitem/unblendedcost"`
- Don't forget the `$` prefix in JSON path: `$.resourceTags/Key`

### Performance Issues
- Add date filters to reduce data scanned
- Use `LIMIT` for exploratory queries
- Consider partitioning by date first, then filtering by tags

## Testing Tag Queries

Test your tag queries in the CLI before creating KPIs:

```bash
python3 main.py
```

Then ask:
```
Query CUR data to show costs grouped by Environment tag
```

The agent will generate and execute the proper tag query.

## Summary

- ✅ Tags are in `raw_tags` column as JSON
- ✅ Use `json_extract_scalar(raw_tags, '$.resourceTags/TagKey')`
- ✅ Tag keys include `resourceTags/` prefix
- ✅ Works for user tags and AWS system tags
- ✅ Create tag-based KPIs from chat
- ✅ Always check for NULL values
- ✅ Use date filters for performance

---

**Updated**: October 10, 2025
**Status**: ✅ Tested and Verified
