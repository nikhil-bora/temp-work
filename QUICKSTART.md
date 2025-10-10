# Quick Start Guide - Python Version

## 3 Ways to Run

### Option 1: Quick Start Script (Easiest)
```bash
cd python-version
./run.sh
```

This script will:
- Check if dependencies are installed
- Install them if needed (user install)
- Launch the agent

---

### Option 2: Manual Steps (Recommended)
```bash
# 1. Go to python-version directory
cd /Users/nikhilbora/Documents/temp-work/finops-agent/python-version

# 2. Install dependencies (user install)
pip3 install --user anthropic boto3 python-dotenv colorama

# 3. Run the agent
python3 main.py
```

---

### Option 3: Virtual Environment (Cleanest)
```bash
# 1. Go to python-version directory
cd /Users/nikhilbora/Documents/temp-work/finops-agent/python-version

# 2. Create virtual environment (first time only)
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies (first time only)
pip install -r requirements.txt

# 5. Run the agent
python3 main.py

# When done, deactivate:
deactivate
```

---

## What You'll See

```
$ python3 main.py

Loaded CUR schema: 214 columns
Initializing AWS SDK with region: ap-south-1

╔════════════════════════════════════════╗
║   FinOps Analyst Agent v1.0           ║
╚════════════════════════════════════════╝

✓ AWS Cost Explorer connected
✓ Athena ready for CUR queries
✓ Claude AI ready

Ask me anything about your AWS costs!

Examples:
  - What were my top 5 services by cost last month?
  - Show me costs for the last 30 days
  - Analyze my RI coverage
  - Forecast costs for next quarter

Commands:
  - /clear    - Clear conversation history
  - /history  - Show conversation history
  - exit      - Quit the agent

You: _
```

---

## Common Issues

### Issue: "No module named 'anthropic'"

**Solution:**
```bash
pip3 install --user anthropic boto3 python-dotenv colorama
```

### Issue: "externally-managed-environment"

**Solution 1 - Use virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Solution 2 - User install:**
```bash
pip3 install --user anthropic boto3 python-dotenv colorama
```

**Solution 3 - Break system packages (not recommended):**
```bash
pip3 install --break-system-packages -r requirements.txt
```

### Issue: "command not found: python3"

**Solution:**
```bash
# Install Python 3
brew install python3

# Or use python instead of python3
python main.py
```

### Issue: ".env file not found"

**Solution:**
The Python version shares the `.env` file with the Node.js version. Make sure it exists:
```bash
# Should be at:
/Users/nikhilbora/Documents/temp-work/finops-agent/.env

# Check if it exists:
ls -la ../.env
```

---

## Test It Works

Quick test commands:
```bash
You: Calculate 2+2 using Python code
You: List my workflows
You: /history
You: /clear
You: exit
```

---

## Comparison with Node.js Version

| Command | Node.js | Python |
|---------|---------|--------|
| Install | `npm install` | `pip3 install -r requirements.txt` |
| Run | `npm start` | `python3 main.py` |
| Features | All features | All features (identical) |

Both versions:
- ✅ Use same `.env` file
- ✅ Share same `workspace/` directory
- ✅ Work with same workflows
- ✅ Have identical features

---

## Next Steps

Once running, try these:

1. **Simple query:**
   ```
   You: What were my costs last month?
   ```

2. **Code execution:**
   ```
   You: Write Python code to calculate average EC2 cost
   ```

3. **Workflow:**
   ```
   You: List my workflows
   You: Run the monthly cost report
   ```

4. **Conversation context:**
   ```
   You: Show me top 5 services
   You: Tell me more about the second one
   ```

---

## Getting Help

If you have issues:

1. Check Python version: `python3 --version` (needs 3.8+)
2. Check dependencies: `pip3 list | grep -E "anthropic|boto3"`
3. Check .env exists: `ls -la ../.env`
4. Run test: `python3 test_basic.py`

Still stuck? The Node.js version works identically:
```bash
cd ..
npm start
```
