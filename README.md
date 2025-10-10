# FinOps Analyst Agent

A powerful AI-powered FinOps agent that helps you analyze AWS costs using natural language.

## Features

- ✅ **Cost Analysis** - Query AWS CUR data with natural language
- ✅ **Cost Explorer Integration** - Forecasting and anomaly detection
- ✅ **CloudWatch Metrics** - EC2 utilization correlation with costs
- ✅ **Custom Code Execution** - Run Python and JavaScript code
- ✅ **Workflow Management** - Save and run reusable workflows
- ✅ **Conversation Context** - Remembers previous exchanges
- ✅ **CUR Schema Integration** - Knows all 214 column names
- ✅ **Web UI** - Beautiful browser interface with Amnic theme
- ✅ **Real-time Updates** - WebSocket for live agent responses
- ✅ **KPI Dashboard** - Customizable metrics dashboard with auto-refresh
- ✅ **KPI Management** - Add, edit, delete custom KPIs with templates

## Quick Start

### Prerequisites

- Python 3.8 or higher
- AWS credentials configured
- Node.js (optional, for JavaScript code execution feature)

### Installation

```bash
# Option 1: Automated setup (recommended)
./run.sh

# Option 2: Manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

### Configuration

Create a `.env` file with your credentials:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
CUR_DATABASE_NAME=raw-data-v1
CUR_TABLE_NAME=raw_aws_amnic
ATHENA_OUTPUT_LOCATION=s3://your-bucket/finops-agent/
```

## Usage

### Two Ways to Run

#### 1. Web UI (Recommended) 🌐

Beautiful browser interface with Amnic theme:

```bash
./run_web.sh
```

Then open **http://localhost:8000** in your browser.

See [WEB_UI_README.md](WEB_UI_README.md) for details.

#### 2. Command Line Interface 💻

Terminal-based interface:

```bash
./run.sh
```

Or manually:

```bash
source venv/bin/activate
python3 main.py
```

### CLI Commands

- `/clear` - Clear conversation history
- `/history` - View conversation history
- `exit` - Quit the agent

### Example Questions

```
What were my top 5 services by cost last month?
Show me EC2 costs grouped by instance type
Find underutilized instances and calculate savings
Forecast my costs for next quarter
Show me costs with CloudWatch utilization metrics
```

## Architecture

### File Structure

```
finops-agent/
├── main.py              # Main entry point and CLI
├── agent.py             # Core agent logic and AWS integrations
├── tools.py             # Tool definitions for Claude
├── requirements.txt     # Python dependencies
├── run.sh              # Automated startup script
├── cur-schema.json     # CUR schema (214 columns)
├── .env                # Environment variables
└── workspace/          # Scripts, workflows, data
    ├── scripts/        # Generated code files
    ├── workflows/      # Saved workflows (JSON)
    └── data/          # Exported data files
```

### Key Components

**main.py**
- CLI interface with colored output
- Conversation loop (up to 50 tool iterations)
- Command handling
- History management

**agent.py**
- AWS SDK initialization (boto3)
- Athena query execution
- Cost Explorer API calls
- CloudWatch metrics retrieval
- Code execution handler (Python/JavaScript)
- Workflow management

**tools.py**
- 14 tool definitions for Claude
- Input schemas for all tools

## Available Tools

1. **query_cur_data** - Execute SQL against AWS CUR
2. **get_cost_forecast** - Cost Explorer forecasting
3. **get_cost_anomalies** - Anomaly detection
4. **get_cloudwatch_metrics** - CloudWatch metrics
5. **correlate_ec2_utilization** - EC2 cost + metrics
6. **execute_code** - Run Python/JavaScript code
7. **save_workflow** - Save reusable workflows
8. **list_workflows** - List saved workflows
9. **run_workflow** - Execute workflows
10. **search_cur_columns** - Search schema
11. **get_sample_queries** - Example SQL queries
12. **analyze_ri_coverage** - RI/SP analysis
13. **export_data** - Export to CSV/JSON
14. **get_tag_analysis** - Cost by tags

## Advanced Features

### Custom Code Execution

Run Python code with AWS access:

```
You: Execute Python code to calculate average daily costs
```

The agent will write and execute:

```python
import boto3
athena = boto3.client('athena')
# Your analysis code...
```

### Workflow Management

Save complex analyses:

```
You: Save this as "Weekly EC2 Report"
You: List my workflows
You: Run the weekly EC2 report
```

### Conversation Context

Natural follow-up questions:

```
You: Show me top 5 services
Agent: [Shows S3, EC2, RDS, Lambda, CloudFront]
You: Tell me more about the second one
Agent: [Knows you mean EC2, provides details]
```

## Performance

- **Startup**: ~1-2 seconds
- **Query Execution**: Depends on Athena (typically 2-5 seconds)
- **Tool Iterations**: Up to 50 per conversation
- **Memory**: ~50-100MB

## Troubleshooting

### Installation Issues

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install anthropic boto3 python-dotenv colorama

# Test installation
python3 -c "import anthropic, boto3; print('✓ All packages installed')"
```

### AWS Credentials

```bash
# Verify .env file is loaded
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('AWS Region:', os.getenv('AWS_REGION'))
"
```

### Agent Stops After 5-6 Steps

This was fixed by increasing `max_attempts` from 5 to 50 in [main.py:35](main.py#L35).

## Documentation

- [READY_TO_USE.md](READY_TO_USE.md) - Current status and quick start
- [HOW_TO_RUN.md](HOW_TO_RUN.md) - Detailed run instructions
- [QUICKSTART.md](QUICKSTART.md) - Step-by-step setup guide
- [CODE_EXECUTION_GUIDE.md](CODE_EXECUTION_GUIDE.md) - Custom code feature
- [ATHENA_SETUP.md](ATHENA_SETUP.md) - AWS setup instructions
- [CUR_SCHEMA.md](CUR_SCHEMA.md) - Complete CUR schema reference

## Recent Updates

### Latest Changes (Oct 9, 2024)

- ✅ Removed Node.js version completely
- ✅ Moved Python version to root directory
- ✅ Increased max iterations from 5 to 50
- ✅ Updated Claude model to `claude-3-7-sonnet-20250219`
- ✅ Fixed deprecation warnings
- ✅ Simplified project structure

## Technical Details

**Python Version**: 3.8+
**AWS SDK**: boto3
**AI Model**: Claude 3.7 Sonnet
**Dependencies**: anthropic, boto3, python-dotenv, colorama

## Contributing

This is a Python-only implementation. All features are maintained in this single version.

## License

MIT License
