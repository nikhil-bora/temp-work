# SQL Query Fix for Athena

## Issue Fixed

Athena queries were failing with:
```
mismatched input '-'. Expecting: ','...
```

This error occurs when column names contain special characters (like hyphens or underscores) and aren't properly quoted.

## Solution

All CUR column names must be wrapped in **double quotes** in Athena queries.

### Before (Broken):
```sql
SELECT
    SUM(line_item_unblended_cost) as total_cost
FROM {table}
WHERE
    year = CAST(year(current_date) AS varchar)
    AND month = CAST(month(current_date) AS varchar)
```

### After (Fixed):
```sql
SELECT
    SUM("line_item_unblended_cost") as total_cost
FROM {table}
WHERE
    "year" = CAST(year(current_date) AS varchar)
    AND "month" = CAST(month(current_date) AS varchar)
```

## What Was Updated

### 1. Default KPIs (kpi_manager.py)

All 6 default KPI queries were updated:
- ✅ Total Monthly Cost
- ✅ Daily Cost
- ✅ Top Service
- ✅ EC2 Instances
- ✅ RI Coverage (no change - uses Cost Explorer API)
- ✅ Cost Anomalies (no change - uses Cost Explorer API)

### 2. KPI Templates (kpi_manager.py)

All 5 template queries were updated:
- ✅ S3 Total Cost
- ✅ Lambda Invocations
- ✅ RDS Cost
- ✅ Data Transfer Cost
- ✅ Cost vs Budget (no change - uses custom function)

## Rules for Writing Athena Queries

### 1. Quote Column Names

Always quote CUR column names:
```sql
✓ "line_item_unblended_cost"
✗ line_item_unblended_cost

✓ "line_item_product_code"
✗ line_item_product_code

✓ "year"
✗ year
```

### 2. Partition Columns

CUR partition columns also need quotes:
```sql
WHERE
    "year" = '2024'
    AND "month" = '10'
```

### 3. Aliases Don't Need Quotes

Column aliases (after AS) don't need quotes:
```sql
SELECT
    SUM("line_item_unblended_cost") as total_cost  -- 'total_cost' doesn't need quotes
```

### 4. String Literals

Use single quotes for string values:
```sql
WHERE "line_item_product_code" = 'AmazonEC2'  -- single quotes for string
```

### 5. LIKE Patterns

LIKE patterns use single quotes:
```sql
WHERE "line_item_usage_type" LIKE '%BoxUsage%'  -- single quotes
```

## Example Queries

### Count Resources
```sql
SELECT
    COUNT(DISTINCT "line_item_resource_id") as resource_count
FROM {table}
WHERE
    "line_item_product_code" = 'AmazonEC2'
    AND "year" = CAST(year(current_date) AS varchar)
    AND "month" = CAST(month(current_date) AS varchar)
```

### Sum Costs by Service
```sql
SELECT
    "line_item_product_code" as service,
    SUM("line_item_unblended_cost") as cost
FROM {table}
WHERE
    "year" = CAST(year(current_date) AS varchar)
    AND "month" = CAST(month(current_date) AS varchar)
GROUP BY "line_item_product_code"
ORDER BY cost DESC
```

### Filter by Usage Type
```sql
SELECT
    SUM("line_item_unblended_cost") as cost
FROM {table}
WHERE
    "line_item_usage_type" LIKE '%DataTransfer-Out%'
    AND "year" = CAST(year(current_date) AS varchar)
    AND "month" = CAST(month(current_date) AS varchar)
```

## Testing Queries

### Method 1: Athena Console

1. Go to AWS Athena Console
2. Select your CUR database
3. Test query with proper quoting
4. Copy working query to KPI

### Method 2: KPI Dashboard

1. Create test KPI
2. Use query with quotes
3. Click refresh button
4. Check browser console for errors

## Common Mistakes

### ❌ Mistake 1: No Quotes
```sql
SELECT line_item_unblended_cost FROM table
-- ERROR: mismatched input '-'
```

### ✅ Fix: Add Quotes
```sql
SELECT "line_item_unblended_cost" FROM table
```

### ❌ Mistake 2: Single Quotes on Column Names
```sql
SELECT 'line_item_unblended_cost' FROM table
-- ERROR: Returns literal string, not column
```

### ✅ Fix: Use Double Quotes
```sql
SELECT "line_item_unblended_cost" FROM table
```

### ❌ Mistake 3: Double Quotes on String Values
```sql
WHERE "line_item_product_code" = "AmazonEC2"
-- ERROR: Tries to find column named AmazonEC2
```

### ✅ Fix: Use Single Quotes
```sql
WHERE "line_item_product_code" = 'AmazonEC2'
```

## Summary

✅ **Always quote CUR column names** with double quotes
✅ **Use single quotes** for string values
✅ **Test in Athena** before adding to KPI
✅ **All default KPIs** are now fixed
✅ **All templates** are now fixed

Your KPI dashboard queries will now work correctly!
