# Filter Troubleshooting Guide

## Testing the Filter Feature

### Step 1: Access the Analytics Dashboard
1. Start the server: `python web_server.py`
2. Open browser: `http://localhost:8000`
3. Click **📋 Dashboards**
4. Click **📊 Analytics** on any dashboard

### Step 2: Open Browser Console
- Press **F12** (or Cmd+Option+I on Mac)
- Go to the **Console** tab
- You should see logs like:
  ```
  Loading dashboard: dash_xxxxx
  Dashboard loaded: {id: "dash_xxxxx", name: "...", ...}
  ```

### Step 3: Test Quick Filter (Easiest)
1. Click one of the preset buttons (e.g., **📅 Last 30 Days**)
2. Check console for:
   ```
   Applying preset filter: {name: "Last 30 Days", type: "date_range", ...}
   Filter response status: 200
   Filter response data: {success: true, filters: [...]}
   Filter applied successfully
   ```
3. You should see a filter chip appear below the buttons:
   ```
   [Last 30 Days: 2025-09-14 to 2025-10-14] ×
   ```

### Step 4: Test Custom Filter
1. Click **➕ Add Filter** button
2. Check console for: `Opening filter modal`
3. Modal should appear with a form
4. Select "Date Range" from dropdown
5. Fill in dates
6. Click "Add Filter"
7. Check console for logs

## Common Issues & Solutions

### Issue 1: Modal Doesn't Open
**Symptoms:** Clicking "Add Filter" does nothing

**Check Console For:**
```
Opening filter modal
Modal element not found  ← Error!
```

**Solution:**
- Refresh the page
- Check if modal HTML exists in page source (View Page Source, search for "filterModal")

### Issue 2: API Returns 404
**Symptoms:** Console shows:
```
Filter response status: 404
```

**Solution:**
- Ensure server is running on correct port
- Check dashboard ID is valid
- Try accessing: `http://localhost:8000/api/dashboards/{dashboard_id}/filters` directly

### Issue 3: Filters Don't Persist
**Symptoms:** Filter chips don't appear after adding

**Check Console For:**
```
Filter applied successfully
```

**If you see this but no chips:**
- Check `renderActiveFilters()` function
- Verify `activeFilters` object has data

**Solution:**
```javascript
// In browser console, run:
console.log(activeFilters);
// Should show: {filter_123: {id: "filter_123", ...}}
```

### Issue 4: No Preset Buttons Appear
**Symptoms:** Filter bar is empty below the "Add Filter" button

**Check Console For:**
```
Error loading presets: ...
```

**Solution:**
- Check `/api/filter-presets` endpoint: `http://localhost:8000/api/filter-presets`
- Should return JSON with date_ranges, services, regions

### Issue 5: Backend Error on Add Filter
**Symptoms:** Alert says "Error adding filter"

**Check Server Logs For:**
```
Error adding filter: ...
Traceback ...
```

**Common Causes:**
- Dashboard doesn't exist
- Dashboard file is corrupted
- Filters field missing (should be auto-added now)

**Manual Fix:**
Edit the dashboard JSON file directly:
```bash
# Find dashboard file
ls data/dashboards/dash_*.json

# Edit and add filters field if missing
{
  "id": "dash_...",
  "name": "...",
  "filters": [],  ← Add this line
  "widgets": []
}
```

## Manual Testing via API

### Test 1: Get Dashboard
```bash
curl http://localhost:8000/api/dashboards/{dashboard_id}
```

Should return JSON with `filters: []` field.

### Test 2: Get Filter Presets
```bash
curl http://localhost:8000/api/filter-presets
```

Should return date ranges, services, regions.

### Test 3: Add a Filter
```bash
curl -X POST http://localhost:8000/api/dashboards/{dashboard_id}/filters \
  -H "Content-Type: application/json" \
  -d '{
    "type": "date_range",
    "name": "Test Filter",
    "start": "2025-09-01",
    "end": "2025-09-30"
  }'
```

Should return: `{"success": true, "filters": [...]}`

### Test 4: List Filters
```bash
curl http://localhost:8000/api/dashboards/{dashboard_id}/filters
```

Should return: `{"filters": [...]}`

### Test 5: Delete a Filter
```bash
curl -X DELETE http://localhost:8000/api/dashboards/{dashboard_id}/filters/{filter_id}
```

Should return: `{"success": true}`

## Debug Checklist

- [ ] Server is running (`python web_server.py`)
- [ ] Browser console is open (F12)
- [ ] Dashboard loads without errors
- [ ] Filter presets appear as buttons
- [ ] Clicking preset shows console logs
- [ ] API returns 200 status
- [ ] Filter chips appear after adding
- [ ] Remove (×) button works on chips
- [ ] "Clear All" button works
- [ ] Custom filter modal opens
- [ ] Modal form shows correct fields

## Getting More Help

If issues persist:

1. **Share Console Output:**
   - Copy all console logs (right-click in console → Save As)
   - Look for red errors

2. **Share Server Logs:**
   - Check terminal where server is running
   - Look for Python tracebacks

3. **Share Network Tab:**
   - Open DevTools → Network tab
   - Filter by "Fetch/XHR"
   - Click failed request
   - Share Response tab

4. **Check Dashboard JSON:**
   ```bash
   cat data/dashboards/dash_*.json | python -m json.tool
   ```
   - Verify it's valid JSON
   - Check filters field exists

## Expected Console Output (Success)

```
Loading dashboard: dash_1728934567_AWS_Cost
Dashboard loaded: {id: "dash_...", name: "AWS Cost", filters: [], ...}
Loading dashboard filters...
Filter presets loaded: {date_ranges: Array(5), services: Array(6), ...}

[User clicks "Last 30 Days"]
Applying preset filter: {name: "Last 30 Days", type: "date_range", ...}
Filter response status: 200
Filter response data: {success: true, filters: Array(1)}
Filter applied successfully

[Filter chip appears]
[Charts update]
```

## Status: Enhanced with Debug Logging

✅ Backward compatibility added (auto-adds filters field)
✅ Console logging throughout
✅ Alert messages for user-facing errors
✅ Validation on form inputs
✅ Modal reset on close
✅ Comprehensive error handling

All filter operations now log to console. Open browser DevTools (F12) to see what's happening!
