# FinOps Agent - Web UI

Beautiful web interface for the FinOps Agent with Amnic theme styling.

## Features

- ✅ **Amnic Brand Theme** - Professional color palette and design
- ✅ **Real-time Updates** - WebSocket for live agent responses
- ✅ **Tool Execution Tracking** - See each tool as it runs
- ✅ **Conversation History** - Remembers previous exchanges
- ✅ **Quick Actions** - One-click common queries
- ✅ **Responsive Design** - Works on desktop and mobile
- ✅ **Clean UI** - Modern, minimalist interface

## Quick Start

### Start the Web UI

```bash
./run_web.sh
```

Then open your browser to: **http://localhost:8000**

### Manual Start

```bash
source venv/bin/activate
python3 web_server.py
```

## Architecture

### Frontend (Static Files)

- **templates/index.html** - Main HTML structure
- **static/css/style.css** - Amnic theme styling
- **static/js/app.js** - WebSocket client and UI logic

### Backend (Flask + WebSocket)

- **web_server.py** - Flask server with WebSocket support
- Uses existing **agent.py** for all FinOps logic
- Real-time tool execution updates via WebSocket

### Technology Stack

- **Frontend**: Vanilla JavaScript, CSS3, HTML5
- **Backend**: Flask 3.0, Flask-Sock (WebSocket)
- **AI**: Claude 3.7 Sonnet via Anthropic API
- **AWS**: boto3 for Cost Explorer, Athena, CloudWatch

## Theme Details

### Amnic Color Palette

```css
Primary Blue:   #33ccff
Primary Purple: #a826b3
Accent Coral:   #ff5c69
Accent Mint:    #3cf
Text Primary:   #1a1a1a
Text Secondary: #6b7280
Background:     #f9fafb → #ffffff gradient
```

### Typography

- **Primary Font**: Inter
- **Secondary Font**: DM Sans
- **Font Weights**: 300-900

### Design Elements

- **Gradient Buttons**: Purple → Blue
- **Rounded Corners**: 8px-16px border radius
- **Soft Shadows**: Subtle elevation
- **Smooth Animations**: 0.2s transitions

## Features

### 1. Welcome Screen

When you first open the app, you see:
- Large icon with gradient background
- Welcome message
- Example queries you can click
- Amnic-branded color scheme

### 2. Chat Interface

- **User Messages**: Blue gradient avatar, right-aligned
- **Agent Messages**: Purple gradient avatar, left-aligned
- **Timestamps**: Subtle gray text
- **Markdown Support**: Code blocks, bold text, line breaks

### 3. Tool Execution Display

When the agent runs tools:
- **Spinner Animation**: While tool is running
- **Tool Name**: Formatted and highlighted
- **Results**: Truncated preview in UI
- **Status Indicators**: ✓ success, ✗ error

### 4. Sidebar

Quick access to:
- **Connection Status**: AWS, Athena, Claude
- **Quick Actions**: Pre-built queries
- **Clear History**: Reset conversation

### 5. Real-time Updates

WebSocket connection provides:
- Live tool execution updates
- Streaming agent responses
- Error notifications
- Connection status

## API Endpoints

### HTTP Endpoints

```
GET  /                 # Serve main UI
POST /api/chat         # Send message (returns immediately)
POST /api/clear        # Clear conversation history
```

### WebSocket Endpoint

```
WS /ws                 # Real-time bidirectional communication
```

### WebSocket Message Types

**From Server:**

```json
// Text response from agent
{
  "type": "text_response",
  "content": "Here is your cost analysis..."
}

// Tool execution started
{
  "type": "tool_call",
  "tool_name": "query_cur_data",
  "status": "started"
}

// Tool execution completed
{
  "type": "tool_call",
  "tool_name": "query_cur_data",
  "status": "completed",
  "result": "Query returned 5 rows..."
}

// Tool execution error
{
  "type": "tool_call",
  "tool_name": "query_cur_data",
  "status": "error",
  "result": "Error message..."
}

// Conversation complete
{
  "type": "complete"
}

// Error
{
  "type": "error",
  "message": "Error message..."
}
```

## File Structure

```
finops-agent/
├── web_server.py           # Flask + WebSocket server
├── run_web.sh             # Startup script
├── templates/
│   └── index.html         # Main UI template
└── static/
    ├── css/
    │   └── style.css      # Amnic theme styles
    └── js/
        └── app.js         # Frontend JavaScript
```

## Configuration

The web UI uses the same `.env` file as the CLI:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
CUR_DATABASE_NAME=raw-data-v1
CUR_TABLE_NAME=raw_aws_amnic
ATHENA_OUTPUT_LOCATION=s3://your-bucket/
```

## Development

### Run in Development Mode

```bash
source venv/bin/activate
python3 web_server.py
```

### Hot Reload CSS Changes

Since Flask doesn't cache static files in development, just refresh your browser to see CSS changes.

### Debug WebSocket Issues

Open browser console (F12) to see WebSocket connection logs and messages.

## Production Deployment

For production, use a WSGI server:

### Using Gunicorn

```bash
pip install gunicorn gevent-websocket
gunicorn -w 4 -k flask_sockets.worker web_server:app
```

### Using uWSGI

```bash
pip install uwsgi
uwsgi --http :8000 --gevent 1000 --http-websockets --master --wsgi-file web_server.py --callable app
```

## Troubleshooting

### Port Already in Use

If port 8000 is taken, edit `web_server.py` line 225:

```python
port=8000,  # Change to different port
```

### WebSocket Connection Failed

1. Check browser console for errors
2. Ensure server is running
3. Try refreshing the page
4. Check firewall settings

### Agent Not Responding

1. Check server console for errors
2. Verify AWS credentials in `.env`
3. Test with CLI version first: `python3 main.py`

### Styling Issues

1. Clear browser cache (Ctrl+Shift+R)
2. Check `static/css/style.css` exists
3. Verify fonts loaded from Google Fonts

## Browser Compatibility

Tested and working on:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Mobile Support

The UI is responsive and works on:
- ✅ iOS Safari
- ✅ Android Chrome
- ✅ Tablet devices

On mobile, the sidebar is hidden and the chat takes full width.

## Screenshots

### Desktop View
- Two-column layout: Sidebar + Chat
- Gradient header with Amnic branding
- Tool execution cards with status

### Mobile View
- Single column: Chat only
- Full-width messages
- Touch-friendly buttons

## Comparison: CLI vs Web UI

| Feature | CLI | Web UI |
|---------|-----|--------|
| Interface | Terminal | Browser |
| Colors | Colorama | CSS |
| Real-time | Yes | Yes (WebSocket) |
| History | In-memory | In-memory |
| Markdown | Basic | Full support |
| Tools Display | Text | Visual cards |
| Quick Actions | Manual | Buttons |
| Mobile | No | Yes |

## Next Steps

The web UI is production-ready! You can:

1. **Start using it**: `./run_web.sh`
2. **Customize theme**: Edit `static/css/style.css`
3. **Add features**: Extend `web_server.py` and `app.js`
4. **Deploy**: Use Gunicorn or uWSGI

## Credits

- **Design**: Inspired by [Amnic.com](http://amnic.com/)
- **AI Model**: Claude 3.7 Sonnet by Anthropic
- **Framework**: Flask by Pallets
- **Icons**: Unicode emojis

---

Built with ❤️ using Amnic's beautiful design system
