#!/usr/bin/env python3
"""
Fix all KPI queries to use the correct CUR schema
Column names use forward slashes: lineitem/unblendedcost
"""

import re

# Read the current file
with open('kpi_manager.py', 'r') as f:
    content = f.read()

# Column mappings: old -> new
column_mapping = {
    '"line_item_unblended_cost"': '`lineitem/unblendedcost`',
    '"line_item_usage_start_date"': '`lineitem/usagestartdate`',
    '"line_item_product_code"': '`lineitem/productcode`',
    '"line_item_resource_id"': '`lineitem/resourceid`',
    '"line_item_usage_type"': '`lineitem/usagetype`',
    '"line_item_usage_amount"': '`lineitem/usageamount`',
    '"year"': '',  # Will be replaced differently
    '"month"': '',  # Will be replaced differently
}

# Apply replacements
for old, new in column_mapping.items():
    if new:  # Skip empty replacements
        content = content.replace(old, new)

# Fix date filters - replace year/month with bill/billingperiodstartdate
# Pattern: WHERE "year" = ... AND "month" = ...
date_pattern = r'WHERE\s+""?\s*=\s*CAST\(year\(current_date\)\s*AS\s*varchar\)\s+AND\s+""?\s*=\s*CAST\(month\(current_date\)\s*AS\s*varchar\)'
date_replacement = '''WHERE
                        MONTH(`bill/billingperiodstartdate`) = MONTH(current_date)
                        AND YEAR(`bill/billingperiodstartdate`) = YEAR(current_date)'''

content = re.sub(date_pattern, date_replacement, content, flags=re.MULTILINE)

# Also handle simpler WHERE clause patterns
content = re.sub(
    r'AND "year" = CAST\(year\(current_date\) AS varchar\)\s+AND "month" = CAST\(month\(current_date\) AS varchar\)',
    'AND MONTH(`bill/billingperiodstartdate`) = MONTH(current_date)\n                    AND YEAR(`bill/billingperiodstartdate`) = YEAR(current_date)',
    content
)

# Write back
with open('kpi_manager.py', 'w') as f:
    f.write(content)

print("✓ Fixed all KPI queries to use correct schema")
print("\nColumn mappings applied:")
for old, new in column_mapping.items():
    if new:
        print(f"  {old} → {new}")
print("\n✓ Date filters updated to use bill/billingperiodstartdate")
