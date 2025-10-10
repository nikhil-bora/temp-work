# Custom Code Execution Feature - Summary

## Overview
The FinOps agent now supports executing custom Python and JavaScript code, enabling analysts to create sophisticated workflows, custom reports, and integrations beyond built-in capabilities.

## What Was Added

### 1. Code Execution Engine
- **Execute Python** and **JavaScript/Node.js** code on-demand
- **Pre-configured AWS SDK** with credentials from .env
- **30-second timeout** for safety
- **Workspace isolation** - scripts run in dedicated workspace directory
- **Stdout/stderr capture** - all output is captured and returned

### 2. Workflow Management System
- **Save** custom workflows for reuse
- **List** all saved workflows with metadata
- **Load** workflows to view or execute
- **Tags** for organization (e.g., "reporting", "optimization", "ec2")

### 3. Workspace Structure
```
workspace/
├── scripts/        # Temporary execution scripts (auto-generated)
│   ├── script_1728560123.cjs
│   └── script_1728560456.py
├── workflows/      # Saved workflows (persistent)
│   ├── monthly_cost_report.json
│   ├── cost_anomaly_detector.json
│   └── export_to_csv.json
└── data/          # Output data from scripts
    ├── costs_export.csv
    └── results.json
```

### 4. Pre-built Example Workflows
- **Monthly Cost Report** - Generate comprehensive monthly cost summary
- **Cost Anomaly Detector** - Detect unusual cost spikes
- **Export to CSV** - Export detailed cost data for external analysis

## New Tools Available

### `execute_code`
Execute custom code immediately.

**Use for:**
- Complex calculations
- Data transformations
- Custom reports
- API integrations
- Advanced analysis

**Example:**
```
You: Calculate the cost per hour for each EC2 instance type using custom code
```

### `save_workflow`
Save a reusable workflow.

**Use for:**
- Monthly/weekly reports
- Recurring analysis
- Standardized checks
- Team playbooks

**Example:**
```
You: Save this as a workflow called "Weekly EC2 Report"
```

### `list_workflows`
View all saved workflows.

**Example:**
```
You: Show me my workflows
Agent: Found 3 workflows:
  1. Monthly Cost Report (javascript)
  2. Cost Anomaly Detector (javascript)
  3. Export to CSV (javascript)
```

### `load_workflow`
Load and optionally execute a workflow.

**Example:**
```
You: Load and run the monthly cost report
```

## Technical Implementation

### Files Modified

**[src/agent-simple.js](src/agent-simple.js)**
- Added imports: `writeFileSync`, `readFileSync`, `readdirSync`, `existsSync`, `mkdirSync`, `exec`
- Added `execute_code` handler (lines 584-657)
- Added `save_workflow` handler (lines 659-686)
- Added `list_workflows` handler (lines 688-711)
- Added `load_workflow` handler (lines 713-726)
- Added tool definitions (lines 993-1069)
- Updated system prompt with code execution guidance (lines 771-784)

### Key Implementation Details

**JavaScript Execution:**
- Uses `.cjs` extension to avoid ES module conflicts
- Pre-imports AWS SDK, fs, path
- Pre-configures AWS credentials
- Executes with `node` command

**Python Execution:**
- Uses `.py` extension
- Executes with `python3` command
- User must import required modules

**Security:**
- 30-second execution timeout
- Runs in isolated workspace directory
- Uses existing AWS credentials from .env
- No network access except AWS APIs

## Use Cases

### 1. Advanced Cost Analysis
**Scenario:** Calculate effective hourly rates with complex discount logic

```javascript
// Query CUR for raw costs
// Apply RI discount calculations
// Factor in Savings Plans
// Account for spot instance variations
// Output detailed breakdown
```

### 2. Custom Report Generation
**Scenario:** Generate monthly executive report

```javascript
// Query costs by service
// Calculate month-over-month trends
// Identify top cost drivers
// Generate optimization recommendations
// Format as JSON/CSV for presentation
```

### 3. Anomaly Detection & Alerting
**Scenario:** Detect unusual cost spikes

```javascript
// Calculate 7-day rolling average per service
// Compare today's costs to average
// Flag anomalies (>50% deviation)
// Generate alert payload for Slack/PagerDuty
```

### 4. Data Export & Integration
**Scenario:** Export data to external BI tools

```javascript
// Query detailed cost data from Athena
// Transform to required format
// Add calculated fields
// Export to CSV/JSON
// Save to workspace/data/ for pickup
```

### 5. Resource Optimization
**Scenario:** Identify underutilized resources

```javascript
// Get all EC2 instances from CUR
// Fetch CloudWatch utilization metrics
// Calculate utilization rates
// Identify optimization candidates
// Estimate potential savings
```

## Example Interactions

### Example 1: Quick Analysis
```
You: Write code to calculate my average daily EC2 cost for the last 30 days

Agent: I'll execute JavaScript code to calculate this...
[Executes code querying Athena]

Agent: Based on the analysis:
- Average daily EC2 cost: $125.45
- Highest day: $189.23 (Oct 5)
- Lowest day: $98.76 (Oct 2)
- Total 30-day cost: $3,763.50
```

### Example 2: Create Workflow
```
You: Create a workflow that checks for EC2 instances running more than 24 hours and saves it

Agent: I'll create a reusable workflow...
[Saves workflow to workspace/workflows/]

Agent: ✓ Workflow saved: long_running_instances_check.json
You can run it anytime by asking: "Run the long running instances check"
```

### Example 3: Run Saved Workflow
```
You: List my workflows

Agent: You have 4 workflows:
1. Monthly Cost Report (last updated: Oct 9)
2. Cost Anomaly Detector
3. Export to CSV
4. Long Running Instances Check (created today)

You: Run the monthly cost report

Agent: Executing monthly cost report workflow...
[Runs saved JavaScript code]

Agent: ✓ Report generated
Top 5 services this month:
1. EC2: $3,450
2. RDS: $1,200
...
```

### Example 4: Data Export
```
You: Export the last 7 days of costs by service to CSV and save it

Agent: I'll create a script to export this data...
[Executes code that queries and formats data]

Agent: ✓ Export complete
File: workspace/data/costs_by_service_7days.csv
Rows: 234
Columns: date, service, cost, resource_count
```

## Best Practices for Users

### 1. Start Simple
Begin with small scripts, then build complexity:
```javascript
// Start with simple query
console.log('Testing Athena query...');

// Then add processing
// Then add error handling
// Then save as workflow
```

### 2. Use Descriptive Names
When saving workflows:
- Good: "Monthly EC2 Cost Report"
- Bad: "report1"

### 3. Add Tags
Organize workflows with tags:
```
Tags: ["reporting", "ec2", "monthly"]
```

### 4. Test Before Saving
Execute code first, verify it works, then save as workflow

### 5. Include Console Output
Add console.log statements for visibility:
```javascript
console.log('Processing 1,234 resources...');
console.log('Completed analysis');
console.log('Results:', results);
```

## Limitations

1. **Execution Time**: 30-second max (prevents runaway processes)
2. **No User Input**: Cannot prompt for interactive input
3. **Limited Network**: Only AWS API access (no external HTTP)
4. **Single Run**: Code executes once, doesn't stay running
5. **Dependencies**: Only built-in modules + AWS SDK (Python requires manual `pip install`)

## Troubleshooting

### Python Not Found
```bash
# Install Python 3
brew install python3

# Verify
python3 --version
```

### Missing Python Packages
```bash
# Install required packages
pip3 install boto3 pandas
```

### Timeout Errors
- Optimize queries (add WHERE clauses, LIMIT)
- Break into smaller operations
- Use async operations for Athena queries

### Permission Errors
```bash
# Check workspace permissions
ls -la workspace/
chmod -R 755 workspace/
```

## Testing

### Test Code Execution
```bash
node test-code-execution.js
```

**Expected Output:**
```
✓ JavaScript execution successful
✓ AWS SDK code execution successful
✓ Python execution successful
✓ Found 3 example workflows
```

### Test with Agent
```bash
npm start

You: Execute JavaScript code that prints "Hello World" and the current date
You: List my workflows
You: Calculate 2+2 using Python code
```

## Documentation

- **Full Guide**: [CODE_EXECUTION_GUIDE.md](CODE_EXECUTION_GUIDE.md)
- **Example Workflows**: [workspace/workflows/](workspace/workflows/)
- **Test Script**: [test-code-execution.js](test-code-execution.js)

## Future Enhancements

Potential improvements:
- [ ] Support for more languages (Ruby, Go)
- [ ] Scheduled workflow execution (cron-style)
- [ ] Workflow parameters/variables
- [ ] Email/Slack notifications from code
- [ ] Access to more AWS services (Lambda, DynamoDB)
- [ ] Workflow versioning and history
- [ ] Code template library
- [ ] Debugging support (breakpoints, step-through)

## Summary

The custom code execution feature transforms the FinOps agent from a query tool into a full analytical platform. Analysts can now:

✅ **Write custom code** for complex analysis
✅ **Save workflows** for recurring tasks
✅ **Generate reports** in any format
✅ **Integrate** with external systems
✅ **Automate** routine FinOps operations

This enables true analyst self-service, allowing you to create exactly the analysis and workflows you need without waiting for development cycles.
