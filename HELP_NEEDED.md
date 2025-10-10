# Help Needed: Discover Your CUR Column Names

## What I Know

✅ Your table has a column called: **`raw_tags`**

## What I Need

To fix all the KPI queries, please tell me the **actual column names** in your table for:

### 1. Cost Column
What column contains the cost/charge amount?
- [ ] `unblended_cost`
- [ ] `cost`
- [ ] `total_cost`
- [ ] `blended_cost`
- [ ] `amount`
- [ ] Other: ___________

### 2. Service/Product Column
What column contains the AWS service name?
- [ ] `product_code`
- [ ] `service`
- [ ] `service_name`
- [ ] `line_item_product_code`
- [ ] `cloud_service`
- [ ] Other: ___________

### 3. Date Columns
How is time/date represented?
- [ ] Separate `year` and `month` columns
- [ ] Single `billing_period` column (format: _______)
- [ ] `usage_date` or `usage_start_date`
- [ ] `date` column
- [ ] Other: ___________

### 4. Resource Column
What column identifies resources (instances, buckets, etc.)?
- [ ] `resource_id`
- [ ] `line_item_resource_id`
- [ ] `instance_id`
- [ ] `arn`
- [ ] Other: ___________

### 5. Usage Type Column
What column shows usage types (BoxUsage, DataTransfer, etc.)?
- [ ] `usage_type`
- [ ] `line_item_usage_type`
- [ ] `operation`
- [ ] Other: ___________

## Quick Way to Help

### Option 1: Share a Working Query

Copy any query from Athena that successfully returns data:

```sql
-- Your working query here
SELECT _____, _____, SUM(_____) as total
FROM "raw-data-v1"."raw_aws_amnic"
WHERE _____
GROUP BY _____
```

### Option 2: Run SHOW COLUMNS

In AWS Athena Console, run:

```sql
SHOW COLUMNS FROM `raw-data-v1`.`raw_aws_amnic`
```

And share the output.

### Option 3: Sample Data

Share the first row output from:

```sql
SELECT * FROM "raw-data-v1"."raw_aws_amnic" LIMIT 1
```

(Remove any sensitive data first)

## What I'll Do Next

Once you share the column names, I will:

1. ✅ Update all 6 default KPI queries
2. ✅ Update all 5 KPI templates
3. ✅ Add tag-based KPIs using `raw_tags`
4. ✅ Test all queries work with your schema
5. ✅ Provide working dashboard immediately

## Example: If Your Columns Are

Let's say your columns are:
- `totalcost` - Cost amount
- `servicename` - AWS service
- `billingmonth` - Date (format: 2025-01)
- `resourcearn` - Resource identifier
- `raw_tags` - Tags (already confirmed)

Then I'll update all queries like:

**Before:**
```sql
SELECT SUM("line_item_unblended_cost")
FROM {table}
WHERE "year" = '2025' AND "month" = '01'
```

**After (for your schema):**
```sql
SELECT SUM("totalcost")
FROM {table}
WHERE "billingmonth" = '2025-01'
```

## Waiting For

Please reply with:
1. ✅ Cost column name
2. ✅ Service column name
3. ✅ Date column name(s)
4. ✅ Resource column name (optional)

Or just share a working query, and I'll figure it out!

**I'm ready to fix everything as soon as you provide the column names.** 🚀
