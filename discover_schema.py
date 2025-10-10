#!/usr/bin/env python3
"""
Discover actual CUR table schema
This will help us understand what columns are actually available
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agent import athena, config
import time

def discover_schema():
    """Discover the actual schema of your CUR table"""

    print("=" * 80)
    print("CUR Table Schema Discovery Tool")
    print("=" * 80)
    print(f"\nDatabase: {config['curDatabase']}")
    print(f"Table: {config['curTable']}")
    print()

    # Try to get table metadata using SHOW COLUMNS
    query = f"SHOW COLUMNS IN \"{config['curTable']}\" IN \"{config['curDatabase']}\""

    print("Attempting to get column list...")
    print(f"Query: {query}\n")

    try:
        response = athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': config['curDatabase']},
            ResultConfiguration={'OutputLocation': config['athenaOutputLocation']}
        )

        query_id = response['QueryExecutionId']

        # Wait for completion
        for _ in range(60):
            status = athena.get_query_execution(QueryExecutionId=query_id)
            state = status['QueryExecution']['Status']['State']

            if state == 'SUCCEEDED':
                result = athena.get_query_results(QueryExecutionId=query_id, MaxResults=1000)

                # Extract column names
                columns = []
                for row in result['ResultSet']['Rows'][1:]:  # Skip header
                    if row['Data']:
                        col_name = row['Data'][0].get('VarCharValue', '')
                        if col_name:
                            columns.append(col_name)

                print(f"✓ Found {len(columns)} columns!\n")
                print("=" * 80)
                print("ALL COLUMNS IN YOUR TABLE:")
                print("=" * 80)

                for i, col in enumerate(columns, 1):
                    print(f"{i:3}. {col}")

                # Analyze columns
                print("\n" + "=" * 80)
                print("COLUMN ANALYSIS:")
                print("=" * 80)

                cost_cols = [c for c in columns if any(x in c.lower() for x in ['cost', 'charge', 'price', 'amount', 'fee'])]
                print(f"\n💰 Cost-related columns ({len(cost_cols)}):")
                for col in cost_cols:
                    print(f"   - {col}")

                service_cols = [c for c in columns if any(x in c.lower() for x in ['service', 'product', 'resource_type'])]
                print(f"\n🔧 Service/Product columns ({len(service_cols)}):")
                for col in service_cols:
                    print(f"   - {col}")

                time_cols = [c for c in columns if any(x in c.lower() for x in ['date', 'time', 'period', 'year', 'month', 'day'])]
                print(f"\n📅 Time-related columns ({len(time_cols)}):")
                for col in time_cols:
                    print(f"   - {col}")

                resource_cols = [c for c in columns if any(x in c.lower() for x in ['resource', 'instance', 'arn', 'id'])]
                print(f"\n🖥️  Resource columns ({len(resource_cols)}):")
                for col in resource_cols[:10]:  # Limit to 10
                    print(f"   - {col}")
                if len(resource_cols) > 10:
                    print(f"   ... and {len(resource_cols) - 10} more")

                tag_cols = [c for c in columns if 'tag' in c.lower()]
                print(f"\n🏷️  Tag columns ({len(tag_cols)}):")
                for col in tag_cols:
                    print(f"   - {col}")

                # Save to file
                output_file = Path(__file__).parent / "discovered_columns.txt"
                with open(output_file, 'w') as f:
                    f.write("All columns in CUR table:\n")
                    f.write("=" * 80 + "\n")
                    for col in columns:
                        f.write(f"{col}\n")

                print(f"\n✓ Column list saved to: {output_file}")

                return columns

            elif state in ['FAILED', 'CANCELLED']:
                print(f"✗ Query {state}")
                if 'StateChangeReason' in status['QueryExecution']['Status']:
                    print(f"Reason: {status['QueryExecution']['Status']['StateChangeReason']}")
                return None

            time.sleep(1)

        print("✗ Query timeout")
        return None

    except Exception as e:
        print(f"✗ Error: {e}")
        return None

if __name__ == "__main__":
    columns = discover_schema()

    if columns:
        print("\n" + "=" * 80)
        print("NEXT STEPS:")
        print("=" * 80)
        print("\n1. Review the columns above")
        print("2. Identify which columns to use for KPIs:")
        print("   - Main cost column (e.g., 'unblended_cost', 'total_cost')")
        print("   - Service/product column")
        print("   - Date columns (year, month, or billing_period)")
        print("   - Resource identifier")
        print("\n3. I'll update all KPI queries to use YOUR actual columns!")
        print("\n✓ Ready to create working KPIs for your schema")
    else:
        print("\n✗ Could not discover schema automatically")
        print("\nPlease manually run in Athena:")
        print(f'   SHOW COLUMNS IN "{config["curTable"]}" IN "{config["curDatabase"]}"')
        print("\nOr:")
        print(f'   SELECT * FROM "{config["curDatabase"]}"."{config["curTable"]}" LIMIT 1')
