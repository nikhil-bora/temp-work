# 🚀 FinOps Agent - Start Here

## What is This?

An AI-powered FinOps agent that helps you analyze AWS costs using natural language. Powered by Amnic AI Sonnet.

## 🎯 Quick Start (Choose One)

### Option 1: Web UI (Recommended) 🌐

Beautiful browser interface with Amnic theme:

```bash
./run_web.sh
```

Then open: **http://localhost:8000**

### Option 2: Command Line 💻

Terminal-based interface:

```bash
./run.sh
```

## ✨ What You Can Do

Ask questions like:
- "What were my top 5 services by cost last month?"
- "Show me EC2 costs grouped by instance type"
- "Find underutilized instances and calculate savings"
- "Forecast costs for next quarter"
- "Analyze my RI coverage"

## 📦 What's Included

### Two Interfaces
1. **Web UI**: Modern browser interface with Amnic branding
2. **CLI**: Terminal-based for quick queries

### Core Features
- ✅ Query AWS Cost & Usage Reports (Athena)
- ✅ Cost Explorer forecasting
- ✅ CloudWatch metrics correlation
- ✅ Custom Python/JavaScript code execution
- ✅ Workflow management
- ✅ Conversation context/memory
- ✅ Real-time updates via WebSocket (Web UI)

### Tools Available (14 total)
1. Query CUR data (SQL)
2. Get cost forecasts
3. Detect anomalies
4. Get CloudWatch metrics
5. Correlate EC2 utilization
6. Execute custom code
7. Save workflows
8. List workflows
9. Run workflows
10. Search CUR columns
11. Get sample queries
12. Analyze RI coverage
13. Export data
14. Get tag analysis

## 🎨 Web UI Features

- **Amnic Brand Theme**: Professional purple/blue gradients
- **Real-time Updates**: See tools execute live via WebSocket
- **Quick Actions**: One-click common queries
- **Responsive**: Works on desktop and mobile
- **Clean Interface**: Minimalist, modern design

## 📁 Project Structure

```
finops-agent/
├── run_web.sh          # Start web UI (port 8000)
├── run.sh              # Start CLI
├── web_server.py       # Flask + WebSocket server
├── main.py             # CLI entry point
├── agent.py            # Core agent logic
├── tools.py            # Tool definitions
├── templates/          # HTML templates
│   └── index.html
└── static/             # CSS and JavaScript
    ├── css/style.css   # Amnic theme
    └── js/app.js       # Frontend logic
```

## ⚙️ Configuration

All settings in `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
CUR_DATABASE_NAME=raw-data-v1
CUR_TABLE_NAME=raw_aws_amnic
ATHENA_OUTPUT_LOCATION=s3://your-bucket/
```

## 📚 Documentation

- **[README.md](README.md)** - Complete documentation
- **[WEB_UI_README.md](WEB_UI_README.md)** - Web UI details
- **[WEB_UI_COMPLETE.md](WEB_UI_COMPLETE.md)** - Build summary
- **[HOW_TO_RUN.md](HOW_TO_RUN.md)** - Detailed instructions
- **[CODE_EXECUTION_GUIDE.md](CODE_EXECUTION_GUIDE.md)** - Custom code
- **[ATHENA_SETUP.md](ATHENA_SETUP.md)** - AWS setup

## 🔧 Requirements

- Python 3.8+
- AWS credentials
- Anthropic API key
- Node.js (optional, for JavaScript code execution)

## 💡 Pro Tips

1. **Web UI** is better for visual exploration
2. **CLI** is better for quick queries and automation
3. Use **Quick Actions** in sidebar for common queries
4. Agent can handle up to **50 tool iterations** per conversation
5. Clear history if conversation gets confused

## 🆘 Troubleshooting

### Web UI won't start
```bash
# Check port 8000 is free
lsof -i :8000

# Try different port (edit web_server.py line 225)
```

### CLI won't start
```bash
# Recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### AWS errors
```bash
# Verify .env file
cat .env

# Test AWS connection
python3 -c "import boto3; print(boto3.client('ce').describe_cost_category_definition)"
```

## 🎯 Next Steps

1. **Start the Web UI**: `./run_web.sh`
2. **Ask a question**: Try one of the examples
3. **Explore Quick Actions**: Click buttons in sidebar
4. **Try custom code**: Ask to "execute Python code to..."
5. **Save workflows**: Ask to "save this as [name]"

## 📊 Stats

- **Total Code**: ~3,000 lines
- **Languages**: Python, HTML, CSS, JavaScript
- **AI Model**: Claude 3.7 Sonnet
- **Tools**: 14 specialized tools
- **Max Iterations**: 50 per conversation

## 🎨 Design Credits

Web UI theme inspired by [Amnic.com](http://amnic.com/) - FinOps OS powered by AI Agents

## 📝 Version History

### Latest (Oct 2024)
- ✅ Added beautiful web UI with Amnic theme
- ✅ WebSocket real-time updates
- ✅ Increased iteration limit to 50
- ✅ Updated to Claude 3.7 Sonnet
- ✅ Removed Node.js version (Python only)
- ✅ Simplified project structure

---

**Status**: ✅ PRODUCTION READY

**Choose your interface and start analyzing AWS costs!**

🌐 Web UI: `./run_web.sh` → http://localhost:8000

💻 CLI: `./run.sh`
