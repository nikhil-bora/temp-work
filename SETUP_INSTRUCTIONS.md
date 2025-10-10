# Setup Instructions for Your FinOps Agent

## ✅ What's Already Done

1. ✅ Project created and dependencies installed
2. ✅ All code files ready
3. ✅ Documentation complete

## 🔐 What You Need to Configure

The agent needs two sets of credentials to work:

### 1. Anthropic API Key (Required)

Get your Claude API key:
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to **API Keys** section
4. Click **Create Key**
5. Copy the key (starts with `sk-ant-`)

### 2. AWS Credentials (Required)

You need AWS access to your Cost and Usage Reports:

**Option A: Use existing AWS CLI credentials**
```bash
# Check if you already have AWS configured
aws configure list

# If configured, just copy your credentials:
# Access Key ID and Secret Access Key
cat ~/.aws/credentials
```

**Option B: Create new IAM user**
1. AWS Console → IAM → Users → Create User
2. Attach these policies:
   - `CostExplorerReadOnlyAccess`
   - `AmazonAthenaFullAccess`
   - `AWSBudgetsReadOnlyAccess`
3. Create access key → Download credentials

### 3. AWS CUR Setup (Required for full functionality)

**Check if CUR is already enabled:**
1. AWS Console → Billing → Cost & Usage Reports
2. If you see reports listed, note the:
   - Report name
   - S3 bucket
   - Database name (in Athena)
   - Table name (in Athena)

**If CUR is not enabled:**
1. AWS Console → Billing → Cost & Usage Reports
2. Click **Create report**
3. Settings:
   - Report name: `finops-cur`
   - Include resource IDs: ✅
   - Time granularity: **Hourly**
   - Report versioning: **Create new report version**
   - Enable report data integration: **Amazon Athena** ✅
   - S3 bucket: Create new or select existing
4. Save and wait 24 hours for first data

**Find your CUR database/table:**
```bash
# In AWS Console → Athena → Query Editor
# You'll see databases in the left sidebar
# Database name format: athenacurcfn_<report-name>
# Table name format: <report-name>
```

### 4. Create S3 Bucket for Athena Results

```bash
aws s3 mb s3://finops-athena-results-YOUR-ACCOUNT-ID --region us-east-1
```

## 📝 Update Your .env File

Edit `/Users/nikhilbora/Documents/temp-work/finops-agent/.env`:

```bash
# 1. Add your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# 2. Add your AWS credentials
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA...your-actual-key
AWS_SECRET_ACCESS_KEY=your-actual-secret

# 3. Add your CUR configuration (from step 3 above)
CUR_S3_BUCKET=your-actual-cur-bucket
CUR_DATABASE_NAME=athenacurcfn_finops_cur
CUR_TABLE_NAME=finops_cur

# 4. Add Athena output location (from step 4)
ATHENA_OUTPUT_LOCATION=s3://finops-athena-results-YOUR-ACCOUNT-ID/
ATHENA_WORKGROUP=primary
```

## 🧪 Test Your Setup

Once you've updated `.env`, run:

```bash
cd /Users/nikhilbora/Documents/temp-work/finops-agent

# Test configuration
npm run verify
```

This will check:
- ✅ Environment variables set
- ✅ AWS connectivity
- ✅ Athena access
- ✅ Cost Explorer API
- ✅ Anthropic API

## 🚀 Start Using the Agent

```bash
# Start interactive agent
npm start
```

## 🎯 Try These First Queries

Once running, try:

```
"Show me my AWS costs for the last 7 days"

"What are my top 5 services by cost?"

"Help me understand my current spend"
```

## ⚠️ If You Don't Have CUR Setup Yet

The agent can still work with AWS Cost Explorer API (doesn't require CUR):
- Service-level cost analysis
- Forecasts
- RI/SP coverage
- Budgets

But for detailed resource-level analysis, tagging compliance, and custom queries, you'll need CUR enabled.

## 📞 Need Help?

**Common Issues:**

1. **"ANTHROPIC_API_KEY not set"**
   - Make sure you copied the key correctly
   - Key should start with `sk-ant-`

2. **"AWS credentials not set"**
   - Check access key format: starts with `AKIA`
   - Make sure secret key has no spaces/quotes

3. **"CUR database not found"**
   - Check database name in Athena Query Editor
   - Wait 24 hours after enabling CUR
   - Verify S3 bucket has data

4. **"Permission denied"**
   - Verify IAM policies are attached
   - Enable Cost Explorer in billing preferences
   - Check Athena workgroup permissions

## 🎓 Next Steps After Setup

1. **Explore the agent** - Try the example queries
2. **Set up tagging strategy** - Define required tags
3. **Create budgets** - Set up alerts
4. **Schedule regular reviews** - Weekly cost analysis
5. **Customize for your org** - Add company-specific rules

---

**Estimated setup time:** 15-30 minutes (plus 24 hours for CUR data if enabling for first time)

Let me know when you have the credentials ready and I can help you test it!
