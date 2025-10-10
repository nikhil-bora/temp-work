# KPI Dashboard - FinOps Agent

A powerful, customizable KPI dashboard for monitoring AWS costs and usage metrics in real-time.

## Features

- ✅ **6 Pre-configured KPIs** - Ready to use out of the box
- ✅ **Custom KPI Creation** - Build your own metrics
- ✅ **Multiple Query Types** - CUR (Athena), Cost Explorer, Custom
- ✅ **Auto-refresh** - Configurable refresh intervals
- ✅ **KPI Templates** - Quick-start templates for common metrics
- ✅ **Drag-and-Drop Layout** - Responsive grid (small, medium, large cards)
- ✅ **Amnic Theme** - Beautiful gradient UI
- ✅ **Add/Edit/Delete** - Full CRUD operations

## Quick Start

### Access Dashboard

```bash
./run_web.sh
```

Then navigate to: **http://localhost:8000/api/dashboard**

Or click **"📊 Dashboard"** in the header navigation.

## Default KPIs

The dashboard comes with 6 pre-configured KPIs:

### 1. 💰 Total Monthly Cost (Large)
- **Description**: Total AWS spend for current month
- **Query Type**: CUR (Athena SQL)
- **Format**: Currency
- **Refresh**: Every 60 minutes

### 2. 📊 Daily Cost (Medium)
- **Description**: Average daily spend this month
- **Query Type**: CUR (Athena SQL)
- **Format**: Currency
- **Refresh**: Every 30 minutes

### 3. 🥇 Top Service (Medium)
- **Description**: Highest cost service this month
- **Query Type**: CUR (Athena SQL)
- **Format**: Text
- **Refresh**: Every 60 minutes

### 4. 🖥️ EC2 Instances (Small)
- **Description**: Total running EC2 instances
- **Query Type**: CUR (Athena SQL)
- **Format**: Number
- **Refresh**: Every 30 minutes

### 5. 🎯 RI Coverage (Medium)
- **Description**: Reserved Instance coverage percentage
- **Query Type**: Cost Explorer API
- **Format**: Percentage
- **Refresh**: Every 60 minutes

### 6. ⚠️ Cost Anomalies (Small)
- **Description**: Number of cost anomalies detected
- **Query Type**: Cost Explorer API
- **Format**: Number
- **Refresh**: Every 30 minutes

## Creating Custom KPIs

### Step 1: Click "+ Add KPI"

Click the **"+ Add KPI"** button in the dashboard header.

### Step 2: Fill in KPI Details

**Basic Information:**
- **Name**: Short, descriptive name (e.g., "S3 Storage Cost")
- **Description**: Brief explanation of what this KPI measures
- **Icon**: Emoji icon (e.g., 🗄️)
- **Color**: Hex color for the card accent
- **Size**: Small, Medium, or Large card

**Query Configuration:**
- **Query Type**: Choose from CUR, Cost Explorer, or Custom
- **Query**: SQL query or function name
- **Format**: Currency, Number, Percentage, or Text
- **Refresh Interval**: Seconds between auto-refreshes

### Step 3: Write Query

#### CUR (Athena SQL) Example:

```sql
SELECT
    SUM(line_item_unblended_cost) as s3_cost
FROM {table}
WHERE
    line_item_product_code = 'AmazonS3'
    AND year = CAST(year(current_date) AS varchar)
    AND month = CAST(month(current_date) AS varchar)
```

**Note**: Use `{table}` placeholder - it will be replaced with your actual CUR table name.

#### Cost Explorer API Example:

```
get_ri_coverage
```

Enter the function name that will be called.

### Step 4: Save

Click **"Save KPI"** and it will appear on your dashboard.

## Using KPI Templates

The dashboard includes 5 quick-start templates:

### 📦 S3 Total Cost
Total S3 storage and data transfer costs for current month.

### ⚡ Lambda Invocations
Total Lambda function invocations this month.

### 💾 RDS Cost
Total RDS database costs for current month.

### 🌐 Data Transfer Cost
Total data transfer out costs this month.

### 🎯 Cost vs Budget
Current month cost as percentage of budget.

**To use a template:**
1. Click "+ Add KPI"
2. Scroll to "Quick Templates"
3. Click a template
4. Customize if needed
5. Save

## Managing KPIs

### Refresh Single KPI

Hover over a KPI card and click the **🔄** button.

### Refresh All KPIs

Click **"🔄 Refresh All"** in the dashboard header.

### Edit KPI

Hover over a KPI card and click the **✏️** button.

### Delete KPI

Hover over a KPI card and click the **🗑️** button. Confirm deletion.

## KPI Sizes

### Small (1 column)
- Compact display
- Perfect for counters or simple metrics
- Examples: Instance count, anomaly count

### Medium (1 column)
- Standard size
- Good for most KPIs
- Examples: Daily cost, service name

### Large (2 columns)
- Wide display
- Emphasizes important metrics
- Examples: Total monthly cost, major trends

## Query Types

### 1. CUR (Athena SQL)

Execute SQL queries against your Cost and Usage Report.

**Advantages:**
- Full SQL power
- Access to all 214 CUR columns
- Complex aggregations and joins

**Template Variables:**
- `{table}` - Replaced with `CUR_DATABASE_NAME.CUR_TABLE_NAME`

**Example:**
```sql
SELECT
    line_item_product_code,
    SUM(line_item_unblended_cost) as cost
FROM {table}
WHERE
    year = CAST(year(current_date) AS varchar)
    AND month = CAST(month(current_date) AS varchar)
GROUP BY line_item_product_code
ORDER BY cost DESC
LIMIT 1
```

### 2. Cost Explorer API

Call AWS Cost Explorer APIs directly.

**Supported Functions:**
- `get_ri_coverage` - RI coverage percentage
- `get_anomalies_count` - Number of detected anomalies
- More can be added in `web_server.py`

**Example:**
```
get_ri_coverage
```

### 3. Custom Functions

Define custom Python functions for complex calculations.

**Example:**
```
calculate_budget_percentage
```

**Implementation**: Add function to `web_server.py` in the `refresh_kpi()` endpoint.

## KPI Storage

KPIs are stored in JSON format:

```
workspace/kpis/kpi_config.json
```

**Structure:**
```json
{
  "kpi_id": {
    "id": "total_monthly_cost",
    "name": "Total Monthly Cost",
    "description": "...",
    "query_type": "cur",
    "query": "SELECT...",
    "format": "currency",
    "icon": "💰",
    "color": "#a826b3",
    "size": "large",
    "refresh_interval": 3600,
    "last_updated": "2024-10-09T...",
    "last_value": 1234.56,
    "trend": "up"
  }
}
```

## API Endpoints

```
GET    /api/kpis                  # List all KPIs
GET    /api/kpis/<id>             # Get single KPI
POST   /api/kpis                  # Create KPI
PUT    /api/kpis/<id>             # Update KPI
DELETE /api/kpis/<id>             # Delete KPI
POST   /api/kpis/<id>/refresh     # Refresh KPI value
GET    /api/kpis/templates        # Get templates
```

## Auto-Refresh

KPIs automatically refresh based on their `refresh_interval`:

- **On page load**: KPIs with no value or stale data refresh immediately
- **Background**: Each KPI tracks its own refresh schedule
- **Manual**: Click refresh button anytime

**Refresh intervals:**
- 1800s (30 min) - Default
- 3600s (60 min) - For expensive queries
- Custom - Set any interval

## Format Types

### Currency
- **Display**: $1,234.56
- **Use for**: Cost metrics

### Number
- **Display**: 1,234
- **Use for**: Counts, quantities

### Percentage
- **Display**: 85.5%
- **Use for**: Coverage, utilization

### Text
- **Display**: AmazonEC2
- **Use for**: Service names, regions

## Best Practices

### Query Performance

1. **Use date filters**: Always filter by year/month
2. **Limit results**: Use `LIMIT` for top-N queries
3. **Aggregate early**: Use `GROUP BY` wisely
4. **Test in Athena first**: Verify query works

### Refresh Intervals

1. **Expensive queries**: 1 hour (3600s)
2. **Medium queries**: 30 minutes (1800s)
3. **Light queries**: 15 minutes (900s)
4. **Real-time**: 5 minutes (300s) minimum

### Card Layout

1. **Large cards**: Use for primary metrics (1-2 max)
2. **Medium cards**: Standard for most KPIs (4-6)
3. **Small cards**: Use for counts and indicators (2-4)

### Naming

1. **Be concise**: "EC2 Cost" not "Total Amazon EC2 Service Cost"
2. **Use context**: "Daily Cost" not just "Cost"
3. **Be specific**: "Last 30 Days" not "Recent"

## Troubleshooting

### KPI shows "—" (no value)

**Causes:**
- Query hasn't run yet
- Query returned no results
- Query failed

**Solutions:**
1. Click refresh button
2. Check browser console for errors
3. Verify query in Athena manually
4. Check AWS credentials

### KPI not refreshing

**Causes:**
- Browser tab inactive
- Network error
- AWS API throttling

**Solutions:**
1. Click manual refresh
2. Check network tab in dev tools
3. Restart web server
4. Check AWS CloudWatch logs

### Query timeout

**Causes:**
- Complex query
- Large date range
- No partition filter

**Solutions:**
1. Add year/month filters
2. Reduce date range
3. Optimize query
4. Increase Athena timeout

### Wrong value displayed

**Causes:**
- Wrong format selected
- Query returns multiple columns
- Data type mismatch

**Solutions:**
1. Query should return ONE value
2. Use correct format type
3. Cast values to correct type

## Advanced: Custom Functions

Add custom KPI calculation functions:

### Step 1: Edit web_server.py

Add function in `refresh_kpi()` endpoint:

```python
elif kpi['query_type'] == 'custom':
    if kpi['query'] == 'calculate_budget_percentage':
        # Your custom logic
        budget = 10000  # Get from config
        actual = get_mtd_cost()  # Get actual cost
        percentage = (actual / budget) * 100

        kpi_manager.update_kpi_value(kpi_id, percentage)

        return jsonify({
            'kpi_id': kpi_id,
            'value': percentage,
            'updated': kpi['last_updated']
        })
```

### Step 2: Create KPI

Use `query_type: custom` and `query: calculate_budget_percentage`.

## Examples

### Example 1: Top 3 Services by Cost

```sql
SELECT
    line_item_product_code as service,
    CAST(SUM(line_item_unblended_cost) AS varchar) as cost
FROM {table}
WHERE
    year = CAST(year(current_date) AS varchar)
    AND month = CAST(month(current_date) AS varchar)
GROUP BY line_item_product_code
ORDER BY SUM(line_item_unblended_cost) DESC
LIMIT 3
```

**Format**: Text
**Display**: Will show as "service1, service2, service3"

### Example 2: Month-over-Month Growth

```sql
SELECT
    CAST(
        (current_month.cost - last_month.cost) / last_month.cost * 100
        AS decimal(10,2)
    ) as growth_percent
FROM
    (SELECT SUM(line_item_unblended_cost) as cost
     FROM {table}
     WHERE year = CAST(year(current_date) AS varchar)
     AND month = CAST(month(current_date) AS varchar)) current_month,
    (SELECT SUM(line_item_unblended_cost) as cost
     FROM {table}
     WHERE year = CAST(year(current_date - interval '1' month) AS varchar)
     AND month = CAST(month(current_date - interval '1' month) AS varchar)) last_month
```

**Format**: Percentage
**Display**: 12.5% (or -5.3% if negative)

### Example 3: Spot Instance Savings

```sql
SELECT
    CAST(SUM(
        CASE
            WHEN pricing_term = 'OnDemand'
            THEN line_item_unblended_cost
            ELSE 0
        END
    ) - SUM(
        CASE
            WHEN pricing_term = 'Spot'
            THEN line_item_unblended_cost
            ELSE 0
        END
    ) AS decimal(10,2)) as savings
FROM {table}
WHERE
    line_item_product_code = 'AmazonEC2'
    AND year = CAST(year(current_date) AS varchar)
    AND month = CAST(month(current_date) AS varchar)
```

**Format**: Currency
**Display**: $1,234.56

## Architecture

```
User Browser
    ↓
GET /api/dashboard
    ↓
dashboard.html + dashboard.js
    ↓
GET /api/kpis
    ↓
kpi_manager.py (load from JSON)
    ↓
Return KPI configs
    ↓
POST /api/kpis/<id>/refresh
    ↓
Execute query (Athena or Cost Explorer)
    ↓
Update KPI value
    ↓
Return to browser
    ↓
Render updated card
```

## Files

```
finops-agent/
├── kpi_manager.py              # KPI logic & storage
├── web_server.py               # API endpoints (updated)
├── templates/
│   └── dashboard.html         # Dashboard UI
├── static/
│   ├── css/
│   │   └── dashboard.css      # Dashboard styles
│   └── js/
│       └── dashboard.js       # Dashboard logic
└── workspace/
    └── kpis/
        └── kpi_config.json    # KPI data
```

## Summary

✅ **6 default KPIs ready to use**
✅ **Create custom KPIs with SQL or APIs**
✅ **5 quick-start templates**
✅ **Auto-refresh with configurable intervals**
✅ **Add/edit/delete KPIs easily**
✅ **Beautiful Amnic-themed UI**
✅ **Responsive grid layout**
✅ **Full CRUD via REST API**

**Start monitoring your AWS costs now!**

Navigate to: **http://localhost:8000/api/dashboard**
