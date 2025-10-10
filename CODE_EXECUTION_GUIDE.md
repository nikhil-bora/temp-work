# Code Execution & Custom Workflows Guide

## Overview
The FinOps agent now supports executing custom Python and JavaScript/Node.js code, enabling you to create sophisticated analytical workflows, custom reports, and integrations beyond the built-in tools.

## Features

### 1. Code Execution
- **Languages**: Python 3, JavaScript (Node.js)
- **AWS SDK**: Pre-configured with your credentials
- **File System**: Access to workspace directory
- **Timeout**: 30 seconds max execution time
- **Output**: Captured stdout/stderr

### 2. Workflow Management
- **Save**: Store reusable workflows for future use
- **List**: View all saved workflows
- **Load**: Load and execute saved workflows
- **Tags**: Organize workflows with tags

### 3. Workspace Structure
```
workspace/
├── scripts/        # Temporary execution scripts
├── workflows/      # Saved workflows (.json)
└── data/          # Output data (CSV, JSON, etc.)
```

## Usage Examples

### Example 1: Simple Cost Calculation
```
You: Calculate the cost per resource for EC2 in the last 7 days using custom code

Agent: I'll execute a Node.js script to calculate this...

[Executes JavaScript code with AWS SDK to query and process data]
```

### Example 2: Custom Report Generation
```
You: Create a workflow that generates a monthly cost summary and save it

Agent: I'll create and save a workflow for you...

[Creates reusable workflow, saves to workspace/workflows/]
```

### Example 3: Data Export
```
You: Export EC2 costs to CSV format with custom columns

Agent: I'll write code to export the data...

[Executes code that queries Athena and generates CSV file]
```

## Available Tools

### `execute_code`
Execute custom code immediately.

**Parameters:**
- `language`: "python", "javascript", or "nodejs"
- `code`: Code to execute
- `description`: (optional) What this code does

**Example Ask:**
```
You: Write Python code to calculate the average daily cost for EC2
```

**What the Agent Does:**
```javascript
{
  language: 'python',
  code: `
import boto3
from datetime import datetime, timedelta

athena = boto3.client('athena', region_name='ap-south-1')

# Calculate average EC2 cost
query = '''
SELECT
  AVG(daily_cost) as avg_daily_cost
FROM (
  SELECT
    DATE("lineitem/usagestartdate") as day,
    SUM("lineitem/unblendedcost") as daily_cost
  FROM "raw-data-v1"."raw_aws_amnic"
  WHERE "lineitem/productcode" = 'AmazonEC2'
    AND "lineitem/usagestartdate" >= CURRENT_DATE - INTERVAL '30' DAY
  GROUP BY DATE("lineitem/usagestartdate")
)
'''

print(f"Average daily EC2 cost: {avg_daily_cost}")
`
}
```

### `save_workflow`
Save a workflow for future reuse.

**Parameters:**
- `name`: Workflow name
- `description`: What it does
- `code`: The code
- `language`: Programming language
- `tags`: (optional) Tags for categorization

**Example Ask:**
```
You: Save this as a reusable workflow called "Weekly EC2 Report"
```

### `list_workflows`
List all saved workflows.

**Example Ask:**
```
You: Show me all my saved workflows
```

**Response:**
```
📋 Saved Workflows:

1. Monthly Cost Report
   Language: javascript
   Tags: reporting, monthly, costs
   Created: 2025-10-09

2. Cost Anomaly Detector
   Language: javascript
   Tags: anomaly, alerting, monitoring
   Created: 2025-10-09

3. Export Costs to CSV
   Language: javascript
   Tags: export, csv, reporting
   Created: 2025-10-09
```

### `load_workflow`
Load a saved workflow.

**Example Ask:**
```
You: Load and run the "Monthly Cost Report" workflow
```

## Code Capabilities

### JavaScript/Node.js

**Pre-imported Modules:**
```javascript
const AWS = require('aws-sdk');
const fs = require('fs');
const path = require('path');
```

**Pre-configured AWS SDK:**
```javascript
AWS.config.update({
  region: 'ap-south-1',
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
});
```

**Example: Query Athena**
```javascript
const athena = new AWS.Athena({ region: 'ap-south-1' });

const params = {
  QueryString: `
    SELECT "product/productname", SUM("lineitem/unblendedcost") as cost
    FROM "raw-data-v1"."raw_aws_amnic"
    WHERE "lineitem/usagestartdate" >= CURRENT_DATE - INTERVAL '7' DAY
    GROUP BY "product/productname"
  `,
  QueryExecutionContext: { Database: 'raw-data-v1' },
  ResultConfiguration: {
    OutputLocation: 's3://amnic-athena-result-in/finops-agent/'
  }
};

athena.startQueryExecution(params, (err, data) => {
  if (err) {
    console.error('Error:', err);
  } else {
    console.log('Query ID:', data.QueryExecutionId);
  }
});
```

**Example: Save to File**
```javascript
const results = {
  date: new Date().toISOString(),
  totalCost: 1234.56,
  services: ['EC2', 'S3', 'RDS']
};

fs.writeFileSync(
  'workspace/data/results.json',
  JSON.stringify(results, null, 2)
);

console.log('Results saved to workspace/data/results.json');
```

### Python

**Example: AWS SDK (boto3)**
```python
import boto3
import json
from datetime import datetime, timedelta

# AWS clients (credentials from environment)
athena = boto3.client('athena', region_name='ap-south-1')
s3 = boto3.client('s3', region_name='ap-south-1')

# Query Athena
response = athena.start_query_execution(
    QueryString='''
        SELECT "product/productname", SUM("lineitem/unblendedcost") as cost
        FROM "raw-data-v1"."raw_aws_amnic"
        WHERE "lineitem/usagestartdate" >= CURRENT_DATE - INTERVAL '7' DAY
        GROUP BY "product/productname"
    ''',
    QueryExecutionContext={'Database': 'raw-data-v1'},
    ResultConfiguration={
        'OutputLocation': 's3://amnic-athena-result-in/finops-agent/'
    }
)

print(f"Query started: {response['QueryExecutionId']}")
```

**Example: Data Processing**
```python
import pandas as pd

# Process cost data
data = {
    'service': ['EC2', 'S3', 'RDS'],
    'cost': [1500, 800, 600]
}

df = pd.DataFrame(data)
df['percentage'] = (df['cost'] / df['cost'].sum() * 100).round(2)

# Save to CSV
df.to_csv('workspace/data/costs.csv', index=False)

print(df.to_string(index=False))
```

## Use Cases

### 1. Custom Report Generation
**Task:** Generate monthly cost report with charts

**Ask:**
```
Create a workflow that generates a monthly cost report with:
- Total costs by service
- Day-by-day breakdown
- Top 10 resources
- Cost trends
Save the results as a JSON file
```

### 2. Cost Anomaly Detection
**Task:** Alert on unusual cost spikes

**Ask:**
```
Write code to detect cost anomalies by:
- Comparing yesterday's costs to 7-day average
- Flag services with >50% increase
- Save anomalies to workspace/data/anomalies.json
```

### 3. Data Export & Integration
**Task:** Export data for external tools

**Ask:**
```
Export the last 30 days of EC2 costs to CSV with columns:
- date, instance_id, instance_type, region, cost, hours
Save to workspace/data/ec2_costs.csv
```

### 4. Custom Calculations
**Task:** Complex cost calculations

**Ask:**
```
Calculate the effective hourly rate for each EC2 instance type
considering:
- Reserved Instance discounts
- Spot instance usage
- On-demand pricing
```

### 5. API Integrations
**Task:** Send data to external systems

**Ask:**
```
Write code to:
1. Get top 10 cost resources
2. Format as Slack message
3. Print the JSON payload (ready to send via webhook)
```

## Example Workflows

### Monthly Cost Report
```javascript
// workspace/workflows/monthly_cost_report.json
const athena = new AWS.Athena({ region: 'ap-south-1' });

const currentMonth = new Date().toISOString().split('T')[0].substring(0, 7);

const query = `
SELECT
  "product/productname" as service,
  ROUND(SUM("lineitem/unblendedcost"), 2) as cost,
  COUNT(DISTINCT "lineitem/resourceid") as resources
FROM "raw-data-v1"."raw_aws_amnic"
WHERE "lineitem/usagestartdate" >= DATE('${currentMonth}-01')
GROUP BY "product/productname"
ORDER BY cost DESC
`;

console.log('Generating monthly report for', currentMonth);
// Execute query and process results...
```

### Optimization Analyzer
```javascript
// Analyzes resources and suggests optimizations
const ec2 = new AWS.EC2({ region: 'ap-south-1' });
const cloudwatch = new AWS.CloudWatch({ region: 'ap-south-1' });

// Get all running instances
ec2.describeInstances({
  Filters: [{ Name: 'instance-state-name', Values: ['running'] }]
}, (err, data) => {
  if (err) {
    console.error(err);
    return;
  }

  const instances = [];
  data.Reservations.forEach(res => {
    res.Instances.forEach(inst => {
      instances.push({
        id: inst.InstanceId,
        type: inst.InstanceType,
        state: inst.State.Name
      });
    });
  });

  console.log(`Found ${instances.length} running instances`);
  console.log('Analyzing utilization...');

  // Fetch CloudWatch metrics for each instance
  // Identify underutilized resources
  // Generate optimization recommendations
});
```

## Best Practices

### 1. Error Handling
Always include error handling:
```javascript
try {
  // Your code
  const result = await someOperation();
  console.log('Success:', result);
} catch (error) {
  console.error('Error:', error.message);
}
```

### 2. Output
Use console.log for output (captured by agent):
```javascript
console.log('Processing...');
console.log('Results:', JSON.stringify(results, null, 2));
```

### 3. File Paths
Use relative paths in workspace:
```javascript
// Good
fs.writeFileSync('workspace/data/output.json', data);

// Also good
const outputPath = path.join('workspace', 'data', 'output.json');
fs.writeFileSync(outputPath, data);
```

### 4. Timeouts
Keep execution under 30 seconds:
- For long-running queries, start them and return the query ID
- User can check status separately

### 5. Security
- Code runs with your AWS credentials
- Be cautious with data export
- Don't hardcode sensitive data

## Limitations

1. **Execution Time**: 30 second timeout
2. **No Interactive Input**: Code cannot prompt for user input
3. **No Network Access**: Cannot make external HTTP requests (except AWS APIs)
4. **Single Execution**: Code runs once, no persistent processes
5. **Limited Dependencies**: Only built-in modules and AWS SDK

## Troubleshooting

### Code Won't Execute
**Problem**: "Command not found: python3"
**Solution**: Install Python 3: `brew install python3`

**Problem**: "Module not found: pandas"
**Solution**: Install required module: `pip3 install pandas boto3`

### Timeout Errors
**Problem**: Code execution times out
**Solution**:
- Optimize query (add WHERE clauses, LIMIT)
- Break into smaller operations
- Use asynchronous operations

### Permission Errors
**Problem**: Cannot write to workspace
**Solution**: Check workspace directory exists and has write permissions

### AWS Errors
**Problem**: "Unable to locate credentials"
**Solution**: Ensure .env file has AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY

## Examples in Action

### Example Session 1: Custom Analysis
```bash
You: Calculate the cost per GB for S3 storage across all buckets

Agent: I'll write JavaScript code to analyze S3 costs...
[Executes code querying CUR data]
Agent: Here are the results:
- Bucket A: $0.023 per GB
- Bucket B: $0.025 per GB
- Bucket C: $0.021 per GB
```

### Example Session 2: Create Workflow
```bash
You: Create a weekly EC2 optimization report that I can run every Monday

Agent: I'll create a reusable workflow for you...
[Saves workflow to workspace/workflows/]
Agent: ✓ Workflow saved: weekly_ec2_optimization.json

You can run it anytime by asking: "Run the weekly EC2 optimization workflow"
```

### Example Session 3: Data Export
```bash
You: Export all costs grouped by tag to CSV

Agent: I'll generate a CSV export...
[Executes code to query and format data]
Agent: ✓ Export complete: workspace/data/costs_by_tag.csv
File contains 1,234 rows with columns: tag_key, tag_value, service, cost
```

## Future Enhancements

Planned features:
- [ ] Support for more languages (Ruby, Go)
- [ ] Scheduled workflow execution
- [ ] Workflow parameters/variables
- [ ] Email/Slack notifications from code
- [ ] Access to more AWS services
- [ ] Workflow versioning
- [ ] Code templates library
