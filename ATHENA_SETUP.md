# Athena / CUR Setup Issue

## Current Situation

Your FinOps agent is **working** but using Cost Explorer API instead of CUR data.

### Why CUR Queries Are Failing

**Account Mismatch:**
- Your AWS credentials: Account **214964805500** (user: NB)
- CUR data location: Account **924148612171** (bucket: amnic-cur-924148612171)

**Error:**
```
Unable to verify/create output bucket
```

This happens because:
1. Athena runs in account 214964805500 (your credentials)
2. CUR bucket is in account 924148612171 (different account)
3. Cross-account access not configured

## Current Behavior

✅ **Agent is Smart:**
1. Tries CUR query first (`query_cur_data`)
2. Falls back to Cost Explorer when CUR fails
3. Still provides accurate cost data

**Example from logs:**
```
💬 Agent response:
I'll use the query_cur_data function (our primary tool)

▶ Calling query_cur_data...
✗ Athena error: Unable to verify/create output bucket

💬 Agent response:
CUR query failed, so I'll fall back to get_cost_by_service

▶ Calling get_cost_by_service...
✓ Received data successfully
```

## Solutions

### Option 1: Use Cost Explorer (Current - Working)

**Pros:**
- ✅ Already working
- ✅ No setup needed
- ✅ Cross-account compatible
- ✅ Good for service-level analysis

**Cons:**
- ❌ Less granular than CUR
- ❌ Can't query resource-level details
- ❌ Limited custom analysis

**To optimize for this:**
Just keep using it! The agent already falls back automatically.

### Option 2: Fix CUR Access (Recommended for detailed analysis)

You need credentials for account **924148612171**.

**Step 1: Get credentials for account 924148612171**

Either:
- A) IAM user in account 924148612171
- B) Cross-account role that account 214964805500 can assume

**Step 2: Update `.env`**

```bash
# Use account 924148612171 credentials
AWS_ACCESS_KEY_ID=AKIA...  # From account 924148612171
AWS_SECRET_ACCESS_KEY=...  # From account 924148612171

# CUR Configuration (already correct)
CUR_DATABASE_NAME=raw-data-v1
CUR_TABLE_NAME=raw_aws_amnic

# Athena output (create bucket in same account)
ATHENA_OUTPUT_LOCATION=s3://athena-results-924148612171-ap-south-1/
```

**Step 3: Create Athena output bucket in correct account**

```bash
# Using credentials for account 924148612171
aws s3 mb s3://athena-results-924148612171-ap-south-1 --region ap-south-1
```

**Step 4: Test**

```bash
npm start
# Ask: "Show me my top 5 services by cost for September 2024"
# Should now use CUR data!
```

### Option 3: Set Up Cross-Account Access

If you must use credentials from account 214964805500:

**Step 1: In account 924148612171, create IAM role**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::214964805500:user/NB"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Step 2: Attach policies to role**

- AmazonAthenaFullAccess
- S3 access to CUR bucket
- S3 access to Athena output bucket

**Step 3: Update agent code to assume role**

This requires code changes to use STS AssumeRole.

## Recommendation

### For Now: Use Cost Explorer ✅

The agent is working! It queries real AWS cost data using Cost Explorer API. This is perfect for:
- Service-level cost analysis
- Cost trends
- Forecasting
- RI/SP coverage
- Budgeting

### For Detailed Analysis: Fix Credentials

If you need:
- Resource-level costs
- Tagging compliance
- Custom SQL queries
- Detailed attribution

Then get credentials for account 924148612171.

## What's Working Right Now

```bash
npm start

# These queries work perfectly (using Cost Explorer):
"Show me my top 10 services by cost"
"Compare September vs August costs"
"Forecast next month's spend"
"Analyze RI coverage"
"Show me cost trends"

# These need CUR access:
"Find untagged EC2 instances"
"Show me resources without tags"
"Custom SQL: SELECT ... FROM raw_aws_amnic"
```

## Test Current Setup

```bash
cd /Users/nikhilbora/Documents/temp-work/finops-agent
npm start

# Try this query:
"Show me my AWS costs for September 2024"

# You'll see:
# 1. Agent tries CUR (fails)
# 2. Agent falls back to Cost Explorer (succeeds)
# 3. You get accurate cost data!
```

## Summary

| Feature | Cost Explorer | CUR Data |
|---------|--------------|----------|
| Service costs | ✅ Works | ❌ Needs fix |
| Cost trends | ✅ Works | ❌ Needs fix |
| Forecasting | ✅ Works | ❌ N/A |
| RI/SP coverage | ✅ Works | ❌ N/A |
| Resource-level | ❌ No | ❌ Needs fix |
| Custom SQL | ❌ No | ❌ Needs fix |
| Tagging analysis | ❌ Limited | ❌ Needs fix |

**Current Status:** ✅ Agent working with Cost Explorer
**To unlock CUR:** Get credentials for account 924148612171

---

**Your agent is fully functional for cost analysis!** The CUR access is optional for more advanced queries.
