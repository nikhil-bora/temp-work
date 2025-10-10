# CUR Schema Issue - Resolution Guide

## Problem Detected

Your CUR table has a **schema mismatch** between:
1. The Athena table definition
2. The actual Parquet files in S3

Error message:
```
HIVE_BAD_DATA: Malformed Parquet file. Field bill/invoiceid's type BINARY in parquet file
is incompatible with type integer defined in table schema
```

## This Explains Why KPIs Fail

The default KPI queries assume standard CUR column names like:
- `line_item_unblended_cost`
- `line_item_product_code`
- `year`, `month`

But these columns may:
1. Not exist in your table
2. Have different names
3. Have incompatible types

## Solution Options

### Option 1: Fix Your CUR Table Schema (Recommended)

Your table `raw-data-v1.raw_aws_amnic` needs to be recreated with the correct schema.

**Steps:**
1. Check the actual Parquet file schema
2. Recreate the Athena table with matching schema
3. Or fix the data files to match the table schema

### Option 2: Use Custom Queries (Quick Fix)

Since we don't know your actual column names, you'll need to:

1. **Find a working query** in Athena that returns data
2. **Create custom KPIs** based on YOUR actual columns

### Option 3: Disable Default KPIs

If you can't fix the schema right now:

1. Delete all default KPIs
2. Create only custom KPIs with queries you know work

## How to Find Your Actual Column Names

### Method 1: AWS Glue Catalog

```bash
# In AWS Console:
1. Go to AWS Glue
2. Navigate to Tables
3. Find: raw-data-v1 > raw_aws_amnic
4. Click "View Table"
5. See the Schema tab
```

### Method 2: Query a Working Table

If you have ANY query that works in Athena against your data:

```sql
-- Use that table/query to understand your schema
SELECT * FROM your_working_table LIMIT 1
```

Then share those column names with me.

### Method 3: Check S3 Parquet Files

The error shows your data is at:
```
s3://prod-ccm-raw-data/parquet/orgname=amnic/cloud=AWS/...
```

This suggests you're using a **custom data export**, not AWS CUR!

Your table might be from:
- Cloud Cost Management (CCM) tool
- Custom FinOps pipeline
- Third-party cost tool

## What I Need From You

To fix the KPI queries, please provide:

### 1. A Working Query

Share ANY query that successfully returns data:
```sql
-- Example: your working query
SELECT column1, column2, SUM(cost_column) as total
FROM "raw-data-v1"."raw_aws_amnic"
WHERE <your filters>
GROUP BY column1, column2
```

### 2. Column Names for These Metrics

What columns exist for:
- **Cost amount**: `line_item_unblended_cost`? `cost`? `amount`?
- **Service name**: `line_item_product_code`? `service`? `product`?
- **Date/Time**: `year`/`month`? `date`? `billing_period`?
- **Resource ID**: `line_item_resource_id`? `resource`? `instance_id`?

### 3. Table Schema

Run this in Athena and share the output:
```sql
SHOW COLUMNS FROM "raw-data-v1"."raw_aws_amnic"
```

Or use AWS Glue Console to export the schema.

## Temporary Workaround

Until we fix the schema, you can:

### 1. Delete Default KPIs

```bash
rm workspace/kpis/kpi_config.json
```

### 2. Start Fresh

When you open the dashboard, it will show "No KPIs Yet"

### 3. Add Manual KPIs

Click "+ Add KPI" and use queries YOU KNOW WORK.

For example, if you know this works:
```sql
SELECT SUM(totalcost) FROM "raw-data-v1"."raw_aws_amnic"
WHERE billingperiod = '2025-01'
```

Then create a KPI with that exact query.

## Next Steps

Please provide:
1. ✅ A working Athena query against your table
2. ✅ List of actual column names in your table
3. ✅ What the columns represent (cost, service, date, etc.)

Then I can:
1. Update all default KPI queries to match YOUR schema
2. Update all templates to match YOUR schema
3. Provide working KPIs out of the box

## Alternative: Different Data Source?

The error suggests your data might not be standard AWS CUR.

Is your data from:
- [ ] AWS Cost and Usage Report (CUR)
- [ ] Cloud Cost Management tool
- [ ] Custom export
- [ ] Third-party FinOps platform
- [ ] Other: ___________

This will help me understand what schema to expect.

## Summary

🔴 **Current Issue**: Your table schema doesn't match standard CUR format
🟡 **Impact**: Default KPI queries fail
🟢 **Solution**: Provide working query + column names, and I'll fix all KPIs

**I'm ready to help as soon as you share:**
1. A working Athena query
2. Your actual column names
3. What each column represents
