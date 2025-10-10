# KPI Management from Chat Interface

## Overview

The FinOps Agent now supports **full KPI dashboard management directly from the chat interface**. Users can create, update, delete, list, and refresh KPIs using natural language, making the dashboard highly flexible and customizable.

## Features

### 1. Create KPIs from Chat
Create custom KPIs with natural language requests. The agent will:
- Generate appropriate SQL queries for your metrics
- Apply specified styling (icons, colors, sizes)
- Add the KPI to the dashboard automatically

**Example:**
```
You: "Create a KPI to track S3 costs this month. Use a bucket emoji 🪣,
      purple color (#a826b3), and medium size card."

Agent: ✓ Created KPI: S3 Monthly Cost (ID: s3_monthly_cost)
       View it at: http://localhost:8000/api/dashboard
```

### 2. List All KPIs
View all dashboard metrics with their current values.

**Example:**
```
You: "Show me all KPIs on the dashboard"

Agent: ✓ Found 7 KPIs
       💰 Total Monthly Cost (total_monthly_cost): $10929.60
       📊 Daily Cost (daily_cost): $341.55
       🥇 Top Service (top_service): AmazonEC2
       🖥️ EC2 Instances (ec2_instances): 1355
       🎯 RI Coverage (ri_coverage): 0.0%
       ⚠️ Cost Anomalies (cost_anomalies): 0
       🪣 S3 Monthly Cost (s3_monthly_cost): $946.29
```

### 3. Update KPIs
Modify existing KPI configurations.

**Example:**
```
You: "Update the S3 Monthly Cost KPI to use a large card size"

Agent: ✓ Updated KPI: s3_monthly_cost
       Changed: size = large
```

### 4. Delete KPIs
Remove KPIs you no longer need.

**Example:**
```
You: "Delete the Lambda cost KPI"

Agent: ✓ Deleted KPI: lambda_monthly_cost
```

### 5. Refresh KPIs
Manually update KPI values with latest data.

**Example:**
```
You: "Refresh the S3 Monthly Cost KPI"

Agent: ✓ Refreshed KPI: s3_monthly_cost
       Value: $946.29
       Updated: 2025-10-10T10:31:08
```

## Available Tools

The following tools have been added to the agent:

### `create_kpi`
Creates a new KPI and adds it to the dashboard.

**Parameters:**
- `name` (required): Display name (e.g., "S3 Monthly Cost")
- `description` (required): What this KPI measures
- `query_type` (required): "cur" or "cost_explorer"
- `query` (required): SQL query (for CUR) or API method name (for Cost Explorer)
- `format` (required): "currency", "number", "percentage", or "text"
- `icon` (optional): Emoji icon (default: 📊)
- `color` (optional): Hex color (default: #a826b3)
- `size` (optional): "small", "medium", or "large" (default: medium)
- `refresh_interval` (optional): Auto-refresh seconds (default: 3600)

### `list_kpis`
Lists all KPIs with their current values and metadata.

### `update_kpi`
Updates an existing KPI's configuration.

**Parameters:**
- `kpi_id` (required): KPI identifier
- `updates` (required): Object with fields to update

### `delete_kpi`
Removes a KPI from the dashboard.

**Parameters:**
- `kpi_id` (required): KPI identifier to delete

### `refresh_kpi`
Manually refreshes a KPI to get the latest value.

**Parameters:**
- `kpi_id` (required): KPI identifier to refresh

## Query Types

### CUR Queries (Athena SQL)
Most flexible option - direct access to detailed billing data.

**Key Rules:**
- Use `{table}` as placeholder for the CUR table
- Always double-quote column names with slashes: `"lineitem/unblendedcost"`
- Filter by date: `"bill/billingperiodstartdate"`
- Filter by service: `"product/productname"`

**Example Query:**
```sql
SELECT
    ROUND(SUM("lineitem/unblendedcost"), 2) as value
FROM {table}
WHERE
    "product/productname" = 'Amazon Simple Storage Service'
    AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
    AND YEAR("bill/billingperiodstartdate") = YEAR(current_date)
```

### Cost Explorer Queries
Pre-built API methods for common metrics.

**Available Methods:**
- `get_ri_coverage` - Reserved Instance coverage percentage
- `get_anomalies_count` - Number of cost anomalies detected

## Example KPIs You Can Create

### Service-Specific Costs
- **Lambda Monthly Cost**: Track serverless compute costs
- **RDS Monthly Cost**: Monitor database costs
- **ECS/EKS Costs**: Container service spending
- **CloudFront Costs**: CDN costs

### Resource Counts
- **Lambda Functions**: Number of active functions
- **RDS Instances**: Count of database instances
- **S3 Buckets**: Number of storage buckets

### Cost by Tag/Environment
- **Production Costs**: Filter by environment=production tag
- **Team Costs**: Group by team/department tags
- **Project Costs**: Track costs per project

### Optimization Metrics
- **Idle Resources**: Resources with low utilization
- **Untagged Resources**: Resources missing required tags
- **Savings Opportunities**: RI/SP purchase recommendations

## Integration with Web UI

All KPIs created from chat automatically appear on the web dashboard at:
**http://localhost:8000/api/dashboard**

Features:
- ✅ Real-time updates via WebSocket
- ✅ Auto-refresh based on configured intervals
- ✅ Manual refresh button per KPI
- ✅ Visual styling (icons, colors, card sizes)
- ✅ Multiple format types (currency, number, percentage, text)

## Technical Implementation

### Files Modified

1. **tools.py** - Added 5 new tool definitions
   - `create_kpi`
   - `list_kpis`
   - `update_kpi`
   - `delete_kpi`
   - `refresh_kpi`

2. **agent.py** - Added tool handlers (lines 628-729)
   - Import KPIManager
   - Generate KPI IDs from names
   - Call KPI manager methods
   - Handle refresh via web API

3. **kpi_manager.py** - Existing KPI storage and management
   - Stores KPIs in `workspace/kpis/kpi_config.json`
   - Provides CRUD operations
   - Handles default KPIs

4. **web_server.py** - Existing KPI API endpoints
   - GET /api/kpis - List all KPIs
   - POST /api/kpis/{id}/refresh - Refresh specific KPI
   - GET /api/dashboard - Dashboard UI

### Dependencies

- `requests` - Added for HTTP calls to web server API
- All other dependencies already present

## Usage Examples

### Start the System

```bash
# Terminal 1: Start web server
source venv/bin/activate
python3 web_server.py

# Terminal 2: Start chat CLI
source venv/bin/activate
python3 main.py
```

### Example Conversations

**Creating a Lambda Cost KPI:**
```
You: Create a KPI to track Lambda costs this month. Use a lightning bolt emoji ⚡,
     yellow color #ffcc00, and make it a medium card.

Agent: [Analyzes request]
       [Generates SQL query for Lambda costs]
       [Creates KPI with specified styling]

       ✓ Created KPI: Lambda Monthly Cost (ID: lambda_monthly_cost)
       View it at: http://localhost:8000/api/dashboard
```

**Creating an RDS Instance Count KPI:**
```
You: I need a KPI showing how many RDS instances we have running. Use 🗄️ emoji,
     blue color, small card.

Agent: ✓ Created KPI: RDS Instances (ID: rds_instances)

       Query details:
       - Counts distinct RDS resources from CUR data
       - Filters for Amazon RDS service
       - Updates hourly
```

**Updating a KPI:**
```
You: Change the S3 cost KPI to use a large card and refresh every 30 minutes

Agent: ✓ Updated KPI: s3_monthly_cost
       Changes applied:
       - size: large
       - refresh_interval: 1800 (30 minutes)
```

**Listing KPIs:**
```
You: What KPIs do I have on the dashboard?

Agent: ✓ Found 8 KPIs

       1. 💰 Total Monthly Cost ($10,929.60)
       2. 📊 Daily Cost ($341.55)
       3. 🥇 Top Service (AmazonEC2)
       4. 🖥️ EC2 Instances (1,355)
       5. 🎯 RI Coverage (0%)
       6. ⚠️ Cost Anomalies (0)
       7. 🪣 S3 Monthly Cost ($946.29)
       8. ⚡ Lambda Monthly Cost ($1,245.67)
```

## Benefits

### Flexibility
- Create KPIs on-the-fly without editing code
- Customize metrics for your specific needs
- Adapt dashboard as requirements change

### Natural Language
- No need to write SQL manually
- Agent generates queries from descriptions
- Handles column name quoting automatically

### Real-Time Updates
- KPIs automatically refresh based on intervals
- Manual refresh option available
- WebSocket updates push changes to dashboard

### Team Collaboration
- Share dashboard URL with team
- Create team-specific KPIs via chat
- Track metrics relevant to different stakeholders

## Demo

Run the demo script to see all features:

```bash
python3 demo_kpi_chat.py
```

Or try it live:

```bash
python3 main.py
```

Then type:
```
Create a KPI for Lambda costs this month
```

## Troubleshooting

### KPI Not Appearing on Dashboard
- Refresh the browser page
- Check that web server is running
- Verify KPI was created: `cat workspace/kpis/kpi_config.json`

### Refresh Errors
- Ensure web server is running on port 8000
- Check SQL syntax in query
- Verify CUR table has data for the query period

### Query Syntax Errors
- Always double-quote CUR columns: `"lineitem/unblendedcost"`
- Use `{table}` placeholder for table name
- Test queries with `query_cur_data` tool first

## Next Steps

Potential enhancements:
- [ ] Add KPI templates (pre-built queries)
- [ ] Support for alerts/thresholds
- [ ] Historical trend graphs
- [ ] Export KPI data to CSV
- [ ] Schedule KPI reports via email
- [ ] KPI groups/categories
- [ ] Comparative metrics (week-over-week, month-over-month)

---

**Status**: ✅ Feature Complete and Tested
**Version**: 1.0
**Date**: October 10, 2025
