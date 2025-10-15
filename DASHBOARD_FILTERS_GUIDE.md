# Dashboard Filters & Analytics Guide

## Overview
The FinOps Agent now includes a professional analytics dashboard with comprehensive filtering capabilities, similar to tools like Looker, Tableau, or AWS QuickSight.

## Accessing the Analytics Dashboard

### From the Dashboards List
1. Navigate to **📋 Dashboards** from the main menu
2. Find the dashboard you want to analyze
3. Click the **📊 Analytics** button on the dashboard card
4. You'll be taken to the full-featured analytics view

### Direct URL
```
http://localhost:8000/api/dashboard/{dashboard_id}/analytics
```

## Using Filters

### Method 1: Quick Filter Presets (Easiest)
The analytics page displays 5 quick-filter buttons for common date ranges:

- **📅 Today** - Filter to today's data
- **📅 Last 7 Days** - Past week of data
- **📅 Last 30 Days** - Past month of data
- **📅 This Month** - Current month-to-date
- **📅 Last Month** - Previous complete month

**How to use:**
1. Simply click any preset button
2. The filter is instantly applied
3. A filter chip appears showing the active filter
4. All dashboard charts update automatically

### Method 2: Custom Filters (Advanced)
For more specific filtering needs:

1. Click the **"➕ Add Filter"** button in the filter bar
2. Select a filter type from the dropdown:
   - **Date Range** - Custom start/end dates
   - **Service** - Filter by AWS service (EC2, S3, RDS, etc.)
   - **Region** - Filter by AWS region
   - **Tag** - Filter by resource tags
   - **Account** - Filter by AWS account

3. Fill in the filter details based on type:

   **Date Range Example:**
   ```
   Start Date: 2025-09-01
   End Date: 2025-09-30
   ```

   **Service Example:**
   ```
   Value: AmazonEC2
   ```

   **Tag Example:**
   ```
   Tag Key: Environment
   Tag Value: Production
   ```

4. Click **"Add Filter"** to apply
5. The filter chip appears and charts update

## Managing Active Filters

### View Active Filters
All active filters are displayed as chips in the filter bar below the presets:
```
[Date Range: 2025-09-01 to 2025-09-30] ×
[Service: AmazonEC2] ×
```

### Remove Individual Filter
Click the **×** button on any filter chip to remove that specific filter.

### Clear All Filters
Click the **"🗑️ Clear All"** button to remove all active filters at once.

## Filter Behavior

### Automatic Chart Updates
- When you add/remove filters, all widgets on the dashboard update automatically
- No need to refresh the page
- Charts are re-rendered with filtered data

### Multiple Filters (AND Logic)
You can apply multiple filters simultaneously:
- All filters are combined with AND logic
- Example: "Last 30 Days" + "AmazonEC2" = EC2 costs for the last 30 days only

### Filter Persistence
- Filters are saved with the dashboard
- When you reload the page, your filters are restored
- Filters persist across browser sessions

## Linking Filters to Specific Widgets

### API Method (For Advanced Users)
You can link specific filters to specific widgets so only those widgets respond to the filter:

```bash
POST /api/dashboards/{dashboard_id}/widgets/{widget_id}/filters
{
  "filter_ids": ["filter_123", "filter_456"]
}
```

This creates selective filtering where:
- Widget A responds only to Filter 1
- Widget B responds only to Filter 2
- Widget C responds to both filters

## API Reference

### Get Dashboard Filters
```bash
GET /api/dashboards/{dashboard_id}/filters
```

### Add Filter
```bash
POST /api/dashboards/{dashboard_id}/filters
{
  "type": "date_range",
  "name": "Last 30 Days",
  "start": "2025-09-14",
  "end": "2025-10-14"
}
```

### Update Filter
```bash
PUT /api/dashboards/{dashboard_id}/filters/{filter_id}
{
  "start": "2025-09-01",
  "end": "2025-09-30"
}
```

### Delete Filter
```bash
DELETE /api/dashboards/{dashboard_id}/filters/{filter_id}
```

### Get Filter Presets
```bash
GET /api/filter-presets
```

Returns:
```json
{
  "date_ranges": [
    {
      "name": "Last 30 Days",
      "type": "date_range",
      "start": "2025-09-14",
      "end": "2025-10-14"
    }
  ],
  "services": [
    {"name": "EC2", "value": "AmazonEC2"},
    {"name": "S3", "value": "AmazonS3"}
  ],
  "regions": [
    {"name": "US East (N. Virginia)", "value": "us-east-1"}
  ]
}
```

## Tips & Best Practices

### 1. Start with Presets
- Use quick presets first for common scenarios
- They're faster and less error-prone than custom filters

### 2. Combine Filters
- Layer multiple filters for precise analysis
- Example: Date Range + Service + Region for targeted insights

### 3. Clear Filters Regularly
- Use "Clear All" between different analyses
- Prevents confusion from stale filters

### 4. Filter Naming
- Filters automatically get descriptive names
- "Last 30 Days" is clearer than just "date_range"

### 5. Check Active Filters
- Always look at the filter chips to see what's active
- Easy to forget a filter is applied

## Example Workflow

### Analyzing EC2 Costs Last Month
1. Go to your cost dashboard
2. Click **📊 Analytics**
3. Click **📅 Last Month** preset
4. Click **➕ Add Filter**
5. Select "Service" type
6. Enter "AmazonEC2"
7. Click Add Filter
8. View filtered results showing only EC2 costs for last month

### Comparing Production vs Development
1. Apply date range filter
2. Add tag filter: `Environment = Production`
3. Note the total cost
4. Remove the Production filter
5. Add tag filter: `Environment = Development`
6. Compare the totals

## Troubleshooting

### Filters Not Working?
- Ensure the dashboard has widgets (charts) to filter
- Check that filter chips appear after adding
- Refresh the page if charts don't update

### Wrong Data Showing?
- Check active filter chips
- Click "Clear All" to start fresh
- Verify date ranges are correct

### Can't Find Add Filter Button?
- Look for **"➕ Add Filter"** in the filter bar at the top
- It's next to the "🗑️ Clear All" button
- The filter bar has a dark background

## Future Enhancements

Planned features:
- [ ] Save filter combinations as views
- [ ] Share filtered dashboards via URL
- [ ] Schedule reports with specific filters
- [ ] Export filtered data to CSV
- [ ] Filter by cost thresholds
- [ ] Comparison mode (side-by-side filtered views)

## Support

For issues or questions:
- Check the console for errors (F12)
- Verify API endpoints are responding
- Review filter syntax in the API docs above
