# EC2 Utilization Fix - October 9, 2025

## Problem
EC2 utilization metrics were always showing zero, even for running instances with actual CPU usage.

## Root Cause
The bug was in the `get_ec2_utilization` handler in [agent-simple.js:369](src/agent-simple.js#L369):

```javascript
// OLD BUGGY CODE
average: data.Datapoints.reduce((sum, dp) => sum + dp.Average, 0) / data.Datapoints.length || 0
```

When `data.Datapoints.length` was 0 (no metrics for stopped instances):
- `0 / 0` evaluates to `NaN`
- `NaN || 0` evaluates to `0`
- But this also incorrectly returned `0` for instances with actual data

## Fixes Applied

### 1. Proper Null Handling
```javascript
// NEW FIXED CODE
if (data.Datapoints.length === 0) {
  results[instanceId][metricName] = {
    datapoints: 0,
    average: null,  // null instead of 0
    maximum: null,
    minimum: null,
    note: 'No data available - instance may be stopped or metrics not yet available'
  };
} else {
  const average = data.Datapoints.reduce((sum, dp) => sum + dp.Average, 0) / data.Datapoints.length;
  // ... proper calculation
}
```

### 2. Dynamic Period Adjustment
Added intelligent period selection based on time range to avoid CloudWatch limits (max 1440 datapoints):

```javascript
let period = 300; // 5 minutes (default)
if (durationDays > 1) period = 3600; // 1 hour for >1 day
if (durationDays > 7) period = 3600 * 6; // 6 hours for >7 days
if (durationDays > 30) period = 3600 * 24; // 1 day for >30 days
```

### 3. Enhanced Logging
Added detailed logging to help debug issues:
- Duration and period selection
- Datapoint counts per metric
- Clear warnings for stopped instances
- Per-instance utilization summary

### 4. Better Error Messages
Updated `correlate_cost_utilization` to handle all edge cases:
- No utilization data (instance stopped)
- Errors fetching metrics
- Zero datapoints with clear explanations

## Test Results

Running instance (i-0efa97294459ae827):
```
✓ 288 datapoints retrieved
Average: 10.73%
Maximum: 18.47%
Minimum: 9.43%
```

Stopped instance (i-01c30559d5ab54e15):
```
⚠️  No data (expected for stopped instance)
✓ New code will report: "No data available - instance may be stopped"
```

## Key Improvements

1. ✅ **Accurate Metrics**: Shows actual CPU utilization instead of zero
2. ✅ **Null Safety**: Properly distinguishes between "0%" and "no data"
3. ✅ **Smart Period**: Automatically adjusts sampling period based on time range
4. ✅ **Better UX**: Clear messages for stopped instances and errors
5. ✅ **Datapoint Tracking**: Includes datapoint count in results for verification

## Files Modified

- [src/agent-simple.js](src/agent-simple.js) - Lines 337-415 (get_ec2_utilization)
- [src/agent-simple.js](src/agent-simple.js) - Lines 457-542 (correlate_cost_utilization)

## Testing

Run the test script to verify:
```bash
node test-utilization-fix.cjs
```

Or test with the full agent:
```bash
npm start
# Ask: "Show me EC2 utilization for the last 24 hours"
```
