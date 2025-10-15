#!/usr/bin/env python3
"""
Test script for dashboard filters
Run this to verify the filter system works correctly
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_filters():
    print("=" * 60)
    print("DASHBOARD FILTER TEST")
    print("=" * 60)

    # Step 1: List dashboards
    print("\n1. Listing dashboards...")
    response = requests.get(f"{BASE_URL}/api/dashboards")
    if response.status_code != 200:
        print(f"❌ Failed to list dashboards: {response.status_code}")
        return

    dashboards = response.json()
    if not dashboards:
        print("❌ No dashboards found. Create a dashboard first!")
        print("\nTo create a dashboard:")
        print("  1. Go to http://localhost:8000")
        print("  2. Chat with the agent")
        print("  3. Ask: 'create a dashboard for AWS cost analysis'")
        return

    dashboard = dashboards[0]
    dashboard_id = dashboard['id']
    print(f"✅ Found dashboard: {dashboard['name']} (ID: {dashboard_id})")

    # Step 2: Get dashboard details
    print(f"\n2. Getting dashboard details...")
    response = requests.get(f"{BASE_URL}/api/dashboards/{dashboard_id}")
    if response.status_code != 200:
        print(f"❌ Failed to get dashboard: {response.status_code}")
        return

    dashboard_data = response.json()
    print(f"✅ Dashboard loaded")
    print(f"   - Widgets: {len(dashboard_data.get('widgets', []))}")
    print(f"   - Filters: {len(dashboard_data.get('filters', []))}")

    # Step 3: Get filter presets
    print(f"\n3. Getting filter presets...")
    response = requests.get(f"{BASE_URL}/api/filter-presets")
    if response.status_code != 200:
        print(f"❌ Failed to get presets: {response.status_code}")
        return

    presets = response.json()
    print(f"✅ Filter presets loaded")
    print(f"   - Date ranges: {len(presets.get('date_ranges', []))}")
    print(f"   - Services: {len(presets.get('services', []))}")
    print(f"   - Regions: {len(presets.get('regions', []))}")

    # Step 4: Add a date range filter
    print(f"\n4. Adding 'Last 30 Days' filter...")
    preset = presets['date_ranges'][2]  # Last 30 Days
    filter_data = {
        'type': preset['type'],
        'name': preset['name'],
        'start': preset['start'],
        'end': preset['end']
    }

    print(f"   Filter data: {json.dumps(filter_data, indent=2)}")

    response = requests.post(
        f"{BASE_URL}/api/dashboards/{dashboard_id}/filters",
        json=filter_data,
        headers={'Content-Type': 'application/json'}
    )

    print(f"   Response status: {response.status_code}")
    print(f"   Response body: {response.text}")

    if response.status_code != 200:
        print(f"❌ Failed to add filter")
        try:
            error_data = response.json()
            print(f"   Error: {error_data.get('error', 'Unknown error')}")
        except:
            pass
        return

    result = response.json()
    if result.get('success'):
        print(f"✅ Filter added successfully!")
        print(f"   Total filters: {len(result.get('filters', []))}")
    else:
        print(f"❌ Failed to add filter: {result.get('error')}")
        return

    # Step 5: List filters
    print(f"\n5. Listing dashboard filters...")
    response = requests.get(f"{BASE_URL}/api/dashboards/{dashboard_id}/filters")
    if response.status_code != 200:
        print(f"❌ Failed to list filters: {response.status_code}")
        return

    filters_data = response.json()
    filters = filters_data.get('filters', [])
    print(f"✅ Found {len(filters)} filter(s)")
    for i, f in enumerate(filters, 1):
        print(f"   {i}. {f.get('name')} (ID: {f.get('id')})")

    # Step 6: Add a service filter
    print(f"\n6. Adding 'EC2' service filter...")
    service_filter = {
        'type': 'service',
        'name': 'Service: EC2',
        'value': 'AmazonEC2'
    }

    response = requests.post(
        f"{BASE_URL}/api/dashboards/{dashboard_id}/filters",
        json=service_filter,
        headers={'Content-Type': 'application/json'}
    )

    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"✅ Service filter added!")
            print(f"   Total filters: {len(result.get('filters', []))}")
        else:
            print(f"❌ Failed: {result.get('error')}")
    else:
        print(f"❌ Failed to add service filter: {response.status_code}")

    # Step 7: Remove first filter
    if filters:
        filter_id = filters[0]['id']
        print(f"\n7. Removing filter '{filters[0]['name']}'...")
        response = requests.delete(f"{BASE_URL}/api/dashboards/{dashboard_id}/filters/{filter_id}")

        if response.status_code == 200:
            print(f"✅ Filter removed!")
        else:
            print(f"❌ Failed to remove filter: {response.status_code}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)
    print(f"\nView the dashboard:")
    print(f"  {BASE_URL}/api/dashboard/{dashboard_id}/analytics")
    print("\n")

if __name__ == "__main__":
    try:
        test_filters()
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server!")
        print("   Make sure the server is running:")
        print("   python web_server.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
