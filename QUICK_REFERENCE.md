# FinOps Agent - Quick Reference Card

## 🚀 Start Commands

```bash
# Web UI (Recommended)
./run_web.sh          # → http://localhost:8000

# Command Line
./run.sh              # Terminal interface
```

## 🎨 Web UI Overview

```
┌─────────────────────────────────────────────────────────┐
│  [A] FinOps Agent                    Powered by Claude  │
├──────────┬──────────────────────────────────────────────┤
│ Status   │                                              │
│ ● AWS    │         Welcome to FinOps Agent              │
│ ● Athena │                                              │
│ ● Claude │    Ask me anything about your AWS costs     │
│          │                                              │
│ Quick    │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │
│ Actions  │  │ Top  │ │ Last │ │  RI  │ │ Find │      │
│ ┌──────┐ │  │  5   │ │  30  │ │Cover │ │Saves │      │
│ │📊Top5│ │  └──────┘ └──────┘ └──────┘ └──────┘      │
│ │📈Days│ │                                              │
│ │🎯 RI │ │  ┌────────────────────────────────────┐    │
│ │🔮Cast│ │  │ [User] What were my top costs?     │    │
│ │💡Save│ │  └────────────────────────────────────┘    │
│ └──────┘ │                                              │
│          │  ┌────────────────────────────────────┐    │
│ History  │  │ [AI] Here are your top 5 services: │    │
│ ┌──────┐ │  │ 1. EC2: $1,500                     │    │
│ │Clear │ │  │ 2. S3: $800                        │    │
│ └──────┘ │  │ 3. RDS: $600...                    │    │
│          │  └────────────────────────────────────┘    │
│          │                                              │
│          │  ┌─────────────────────────────────────┐   │
│          │  │ Type your question here...          │   │
│          │  │                              [Send] │   │
│          │  └─────────────────────────────────────┘   │
└──────────┴──────────────────────────────────────────────┘
```

## 💬 Example Questions

### Cost Analysis
```
What were my top 5 services by cost last month?
Show me costs for the last 30 days
Which services had the highest cost increase?
Break down costs by region
```

### EC2 Optimization
```
Show me underutilized EC2 instances
Find EC2 instances with low CPU utilization
Calculate savings from rightsizing opportunities
Which instances are running 24/7 with low usage?
```

### RI/SP Coverage
```
Analyze my RI coverage
Show me Savings Plans utilization
Find EC2 instances not covered by RIs
Calculate potential RI savings
```

### Cost Forecasting
```
Forecast costs for next quarter
Predict next month's spend
Show cost trends over the last 6 months
What's my daily cost burn rate?
```

### CloudWatch Integration
```
Show me EC2 costs with CPU utilization
Correlate RDS costs with connection metrics
Find instances with high cost but low utilization
```

### Custom Code
```
Execute Python code to calculate average daily S3 cost
Write JavaScript to export costs to CSV
Create a custom anomaly detection script
```

### Workflows
```
Save this analysis as "Weekly Cost Report"
List my saved workflows
Run the monthly optimization check
```

## 🛠️ Available Tools (14)

| Tool | Purpose |
|------|---------|
| **query_cur_data** | Execute SQL against CUR |
| **get_cost_forecast** | Predict future costs |
| **get_cost_anomalies** | Detect unusual spending |
| **get_cloudwatch_metrics** | Get CloudWatch data |
| **correlate_ec2_utilization** | EC2 cost + metrics |
| **execute_code** | Run Python/JS code |
| **save_workflow** | Save analysis workflow |
| **list_workflows** | Show saved workflows |
| **run_workflow** | Execute workflow |
| **search_cur_columns** | Find CUR columns |
| **get_sample_queries** | Example SQL queries |
| **analyze_ri_coverage** | RI/SP analysis |
| **export_data** | Export to CSV/JSON |
| **get_tag_analysis** | Costs by tags |

## 🎨 Amnic Theme Colors

```
Primary:   #33ccff (Blue)   ████
           #a826b3 (Purple) ████

Accents:   #ff5c69 (Coral)  ████
           #3cf    (Mint)   ████

UI:        #1a1a1a (Text)   ████
           #f9fafb (BG)     ████
```

## ⌨️ CLI Commands

```bash
/clear      # Clear conversation history
/history    # Show conversation history
exit        # Quit the agent
```

## 📊 Quick Stats

- **Model**: Claude 3.7 Sonnet
- **Max Iterations**: 50 per conversation
- **History**: Last 10 exchanges
- **CUR Columns**: 214 available
- **Response Time**: 2-5 seconds (AWS dependent)

## 🔧 Configuration Files

```
.env                  # AWS & API credentials
cur-schema.json       # CUR schema (214 columns)
workspace/
  ├── scripts/        # Generated code
  ├── workflows/      # Saved workflows
  └── data/          # Exported data
```

## 🐛 Quick Fixes

```bash
# Web UI port conflict
# Edit web_server.py line 225: port=8000

# Recreate venv
rm -rf venv && python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test AWS connection
python3 -c "import boto3; boto3.client('ce')"

# Check .env
cat .env | grep AWS
```

## 📱 Browser Access

```
http://localhost:8000        # Local
http://192.168.x.x:8000     # Network (if firewall allows)
```

## 🎯 Workflow

```
1. Start web UI    → ./run_web.sh
2. Open browser    → http://localhost:8000
3. Ask question    → Type or click Quick Action
4. Watch tools     → See real-time execution
5. Get answer      → Agent responds with analysis
6. Follow up       → Ask related questions
7. Save workflow   → "Save this as [name]"
```

## 📚 Documentation Map

```
START_HERE.md           ← You are here
├── README.md           → Full documentation
├── WEB_UI_README.md    → Web UI details
├── WEB_UI_COMPLETE.md  → Build summary
├── HOW_TO_RUN.md       → Detailed instructions
├── CODE_EXECUTION_GUIDE.md → Custom code
└── ATHENA_SETUP.md     → AWS setup
```

---

**Ready to start? Run:** `./run_web.sh`
