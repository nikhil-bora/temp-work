#!/usr/bin/env python3
"""
Demo: KPI Management from Chat Interface

This script demonstrates how to manage KPIs from the chat interface.
You can:
- Create new KPIs with custom queries
- List all KPIs
- Update existing KPIs
- Delete KPIs
- Refresh KPIs to get latest values
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     KPI Management from Chat - Feature Demonstration            ║
║                                                                  ║
╔══════════════════════════════════════════════════════════════════╗

The FinOps Agent now supports full KPI management directly from the chat!

AVAILABLE COMMANDS:
------------------

1. CREATE A KPI
   Example: "Create a KPI to track Lambda costs this month. Use a
            lightning emoji ⚡, yellow color, and medium size card."

   The agent will:
   - Generate appropriate SQL query for CUR data
   - Create the KPI with specified styling
   - Add it to the dashboard automatically

2. LIST ALL KPIS
   Example: "Show me all KPIs on the dashboard"

   Returns all KPIs with their current values and metadata

3. UPDATE A KPI
   Example: "Update the S3 Monthly Cost KPI to use a large card size"

   Modifies existing KPI configuration

4. DELETE A KPI
   Example: "Delete the Lambda cost KPI"

   Removes KPI from dashboard

5. REFRESH A KPI
   Example: "Refresh the S3 Monthly Cost KPI"

   Manually updates KPI value with latest data


EXAMPLE KPIS YOU CAN CREATE:
----------------------------

✓ Service-specific costs (EC2, S3, RDS, Lambda, etc.)
✓ Cost by environment/tag
✓ Resource counts (instances, buckets, databases)
✓ Cost trends and forecasts
✓ Anomaly detection
✓ RI/Savings Plans coverage
✓ Custom business metrics


QUERY TYPES:
-----------

1. CUR Queries (Athena SQL)
   - Most flexible and detailed
   - Direct access to billing data
   - Use {table} placeholder
   - Double-quote column names with slashes

2. Cost Explorer Queries
   - Pre-built API methods
   - get_ri_coverage
   - get_anomalies_count


EXAMPLE CONVERSATION:
--------------------

You: "Create a KPI for Lambda costs this month with ⚡ emoji"

Agent: ✓ Created KPI: Lambda Monthly Cost (ID: lambda_monthly_cost)
       View it at: http://localhost:8000/api/dashboard

       KPI Details:
       - Query: Sums Lambda costs from CUR data for current month
       - Format: Currency ($)
       - Refresh: Every hour

You: "Show all KPIs"

Agent: ✓ Found 8 KPIs
       💰 Total Monthly Cost (total_monthly_cost): $10929.60
       📊 Daily Cost (daily_cost): $341.55
       🥇 Top Service (top_service): AmazonEC2
       ... (and more)

You: "Refresh the Lambda cost KPI"

Agent: ✓ Refreshed KPI: lambda_monthly_cost
       Value: $1,245.67
       Updated: 2025-10-10T10:35:22


TRY IT NOW:
----------
Run the main CLI: python3 main.py
Or use the web interface: python3 web_server.py

Then type natural language requests like:
- "Create a KPI for RDS costs"
- "Show me all dashboard metrics"
- "Update S3 KPI to use large card"
- "Delete the Lambda KPI"

═══════════════════════════════════════════════════════════════════
""")

# Example usage
if __name__ == "__main__":
    print("\nFor a live demo, run: python3 main.py")
    print("Then type: 'Create a KPI for Lambda costs this month'\n")
