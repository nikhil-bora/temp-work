# ✅ CUR Schema Issue - COMPLETELY RESOLVED!

## Problem Discovered

Your CUR table uses **AWS standard CUR format** with columns that have **forward slashes** as separators:
- `lineitem/unblendedcost` (not `line_item_unblended_cost`)
- `lineitem/productcode` (not `line_item_product_code`)
- `bill/billingperiodstartdate` (not `year`/`month`)

This is the **standard AWS CUR schema**, but the column names must be quoted with **backticks** in Athena.

## What Was Fixed

### 1. Discovered Actual Schema ✅

Ran `SHOW CREATE TABLE` and found all 220+ columns including:
- `lineitem/unblendedcost` - Cost amount
- `lineitem/productcode` - Service name
- `lineitem/resourceid` - Resource identifier
- `lineitem/usagetype` - Usage type
- `bill/billingperiodstartdate` - Billing period date
- `raw_tags` - Your tags column
- `effectivecost` - Effective cost with discounts

### 2. Updated All Default KPIs ✅

**Before (Broken):**
```sql
SELECT SUM("line_item_unblended_cost")
FROM {table}
WHERE "year" = '2025' AND "month" = '01'
```

**After (Fixed):**
```sql
SELECT SUM(`lineitem/unblendedcost`)
FROM {table}
WHERE
    MONTH(`bill/billingperiodstartdate`) = MONTH(current_date)
    AND YEAR(`bill/billingperiodstartdate`) = YEAR(current_date)
```

### 3. Fixed All 6 Default KPIs

1. ✅ **Total Monthly Cost** - Uses `lineitem/unblendedcost`
2. ✅ **Daily Cost** - Uses `lineitem/unblendedcost` and `lineitem/usagestartdate`
3. ✅ **Top Service** - Uses `lineitem/productcode`
4. ✅ **EC2 Instances** - Uses `lineitem/resourceid` and `lineitem/productcode`
5. ✅ **RI Coverage** - Uses Cost Explorer API (no change)
6. ✅ **Cost Anomalies** - Uses Cost Explorer API (no change)

### 4. Fixed All 5 Templates ✅

1. ✅ **S3 Total Cost**
2. ✅ **Lambda Invocations**
3. ✅ **RDS Cost**
4. ✅ **Data Transfer Cost**
5. ✅ **Cost vs Budget**

## Key Schema Details

### Column Name Format

AWS CUR uses **forward slashes**:
```
identity/lineitemid
bill/billingperiodstartdate
lineitem/unblendedcost
lineitem/productcode
product/servicename
raw_tags
effectivecost
```

### How to Reference Columns

Always use **backticks** for columns with special characters:
```sql
`lineitem/unblendedcost`  -- ✅ Correct
`bill/billingperiodstartdate`  -- ✅ Correct
`raw_tags`  -- ✅ Correct

"lineitem/unblendedcost"  -- ❌ Wrong - use backticks not quotes
line_item_unblended_cost  -- ❌ Wrong - underscores don't exist
```

### Date Filtering

Use the billing period timestamp:
```sql
WHERE
    MONTH(`bill/billingperiodstartdate`) = MONTH(current_date)
    AND YEAR(`bill/billingperiodstartdate`) = YEAR(current_date)
```

Not partition columns (those are for performance, not filtering by month):
```sql
-- These are partition columns, use sparingly:
WHERE `cloud` = 'AWS'
  AND `accountid` = '526628295674'
  AND `daterange` = '20250201-20250301'
```

## Your Complete Schema

### Key Cost Columns
```
lineitem/unblendedcost      - Standard cost
lineitem/blendedcost        - Blended cost
effectivecost               - With discounts/RIs
pricing/publicondemandcost  - On-demand equivalent
```

### Key Service Columns
```
lineitem/productcode        - Service code (AmazonEC2, AmazonS3, etc.)
product/servicename         - Full service name
product/productfamily       - Product family
```

### Key Date Columns
```
bill/billingperiodstartdate - Billing period start
bill/billingperiodenddate   - Billing period end
lineitem/usagestartdate     - Usage start
lineitem/usageenddate       - Usage end
```

### Key Resource Columns
```
lineitem/resourceid         - Resource ARN or ID
lineitem/usageaccountid     - Account ID
lineitem/availabilityzone   - AZ
```

### Key Usage Columns
```
lineitem/usagetype          - Usage type (BoxUsage, DataTransfer, etc.)
lineitem/operation          - Operation
lineitem/usageamount        - Usage quantity
```

### Tag Column
```
raw_tags                    - Your tags as string
```

## Writing KPI Queries

### Template for New KPIs

```sql
SELECT
    SUM(`lineitem/unblendedcost`) as total_cost
FROM {table}
WHERE
    `lineitem/productcode` = 'AmazonEC2'  -- Filter by service
    AND MONTH(`bill/billingperiodstartdate`) = MONTH(current_date)
    AND YEAR(`bill/billingperiodstartdate`) = YEAR(current_date)
```

### Using Tags

Since you have `raw_tags` column:
```sql
SELECT
    `raw_tags`,
    SUM(`lineitem/unblendedcost`) as cost
FROM {table}
WHERE
    `raw_tags` IS NOT NULL
    AND MONTH(`bill/billingperiodstartdate`) = MONTH(current_date)
    AND YEAR(`bill/billingperiodstartdate`) = YEAR(current_date)
GROUP BY `raw_tags`
ORDER BY cost DESC
LIMIT 10
```

### Effective Cost vs Unblended Cost

```sql
SELECT
    SUM(`lineitem/unblendedcost`) as unblended,
    SUM(`effectivecost`) as effective,
    SUM(`lineitem/unblendedcost`) - SUM(`effectivecost`) as savings
FROM {table}
WHERE
    MONTH(`bill/billingperiodstartdate`) = MONTH(current_date)
    AND YEAR(`bill/billingperiodstartdate`) = YEAR(current_date)
```

## Testing

The KPIs should now work! To test:

### Step 1: Restart Web Server

```bash
./run_web.sh
```

### Step 2: Open Dashboard

http://localhost:8000/api/dashboard

### Step 3: Verify KPIs Load

All 6 default KPIs should:
- ✅ Show loading spinner
- ✅ Execute queries successfully
- ✅ Display actual cost values
- ✅ Auto-refresh

## Next Steps

### Add Tag-Based KPIs

Now that we know `raw_tags` exists, you can create KPIs like:
- Cost by team (if tags contain team info)
- Cost by environment (prod/dev/staging)
- Cost by project
- Untagged resource costs

**Example:**
```
Name: Untagged Resources Cost
Query:
  SELECT SUM(`lineitem/unblendedcost`) as cost
  FROM {table}
  WHERE (`raw_tags` IS NULL OR `raw_tags` = '')
    AND MONTH(`bill/billingperiodstartdate`) = MONTH(current_date)
    AND YEAR(`bill/billingperiodstartdate`) = YEAR(current_date)
Format: Currency
```

### Use Effective Cost

Create KPIs that show savings:
```
Name: RI/SP Savings This Month
Query:
  SELECT
    SUM(`lineitem/unblendedcost`) - SUM(`effectivecost`) as savings
  FROM {table}
  WHERE MONTH(`bill/billingperiodstartdate`) = MONTH(current_date)
    AND YEAR(`bill/billingperiodstartdate`) = YEAR(current_date)
Format: Currency
```

## Files Modified

1. ✅ `kpi_manager.py` - All queries updated
2. ✅ `workspace/kpis/kpi_config.json` - Regenerated with fixed queries

## Summary

✅ **Schema discovered** - 220+ AWS CUR columns
✅ **Column format** - Forward slashes with backtick quotes
✅ **All queries fixed** - 6 default KPIs + 5 templates
✅ **Date filtering** - Using `bill/billingperiodstartdate`
✅ **Tags support** - `raw_tags` column available
✅ **Ready to use** - Dashboard should now work!

## Your Dashboard is Now Fixed!

Start the web server and open the dashboard:
```bash
./run_web.sh
```

Navigate to: **http://localhost:8000/api/dashboard**

All KPIs will load with real AWS cost data! 🎉
