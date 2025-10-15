#!/usr/bin/env python3
"""
FinOps Agent Web Server
Flask + WebSocket server for the web UI
"""

import asyncio
import json
import sys
import logging
from datetime import datetime
from pathlib import Path
from threading import Thread
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from flask_sock import Sock
from simple_websocket import ConnectionClosed

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('finops-web-server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agent import (
    anthropic, conversation_history, get_finops_system_prompt,
    handle_tool_call, execute_athena_query
)
from tools import AVAILABLE_TOOLS
from kpi_manager import kpi_manager
from conversation_manager import conversation_manager
from context_manager import ContextManager
from dashboard_manager import dashboard_manager

# Initialize managers
context_manager = ContextManager()

# Initialize Flask app
app = Flask(__name__)
sock = Sock(app)

# Store WebSocket connections and sessions
active_connections = set()
session_conversations = {}  # Maps session_id to conversation_id


@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages from the UI"""
    logger.info("=" * 80)
    logger.info("API: /api/chat - New chat message received")

    data = request.json
    logger.debug(f"Request data: {json.dumps(data, indent=2)}")

    user_message = data.get('message', '').strip()
    conversation_id = data.get('conversation_id', None)
    session_id = data.get('session_id', 'default')
    context_ids = data.get('context_ids', [])

    logger.info(f"User message: {user_message[:100]}...")
    logger.info(f"Conversation ID: {conversation_id}")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Context IDs: {context_ids}")

    if not user_message:
        logger.warning("Empty message received")
        return jsonify({'error': 'Empty message'}), 400

    # Create new conversation if no ID provided
    if not conversation_id:
        logger.info("Creating new conversation")
        conversation_id = conversation_manager.create_conversation(
            session_id=session_id,
            title=user_message[:50]
        )
        logger.info(f"Created conversation: {conversation_id}")

    # Process message in background thread
    logger.debug("Starting background thread for message processing")
    thread = Thread(target=process_message_background, args=(user_message, conversation_id, session_id, context_ids))
    thread.daemon = True
    thread.start()

    response = {
        'status': 'processing',
        'conversation_id': conversation_id
    }
    logger.debug(f"Response: {response}")
    return jsonify(response)


@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear conversation history or start new conversation"""
    data = request.json or {}
    session_id = data.get('session_id', 'default')

    # Create a new conversation for this session
    conversation_id = conversation_manager.create_conversation(
        session_id=session_id,
        title='New Conversation'
    )

    # Clear in-memory history for backward compatibility
    conversation_history.clear()

    return jsonify({
        'status': 'cleared',
        'conversation_id': conversation_id
    })


# ============================================================================
# KPI Dashboard API Endpoints
# ============================================================================

@app.route('/api/kpis', methods=['GET'])
def get_kpis():
    """Get all KPIs"""
    # Reload KPIs from file to get latest changes (in case they were created via agent)
    logger.debug("Reloading KPIs from file before returning list")
    kpi_manager.load_kpis()
    kpis = kpi_manager.list_kpis()
    logger.debug(f"Returning {len(kpis)} KPIs")
    return jsonify(kpis)


@app.route('/api/kpis/<kpi_id>', methods=['GET'])
def get_kpi(kpi_id):
    """Get a specific KPI"""
    kpi = kpi_manager.get_kpi(kpi_id)
    if kpi:
        return jsonify(kpi)
    return jsonify({'error': 'KPI not found'}), 404


@app.route('/api/kpis', methods=['POST'])
def create_kpi():
    """Create a new KPI"""
    try:
        kpi_data = request.json
        kpi = kpi_manager.create_kpi(kpi_data)
        return jsonify(kpi), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/kpis/<kpi_id>', methods=['PUT'])
def update_kpi(kpi_id):
    """Update an existing KPI"""
    try:
        kpi_data = request.json
        kpi = kpi_manager.update_kpi(kpi_id, kpi_data)
        if kpi:
            return jsonify(kpi)
        return jsonify({'error': 'KPI not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/kpis/<kpi_id>', methods=['DELETE'])
def delete_kpi(kpi_id):
    """Delete a KPI"""
    if kpi_manager.delete_kpi(kpi_id):
        return jsonify({'status': 'deleted'})
    return jsonify({'error': 'KPI not found'}), 404


@app.route('/api/kpis/<kpi_id>/refresh', methods=['POST'])
def refresh_kpi(kpi_id):
    """Refresh a KPI value"""
    kpi = kpi_manager.get_kpi(kpi_id)
    if not kpi:
        return jsonify({'error': 'KPI not found'}), 404

    try:
        # Execute KPI query based on type
        if kpi['query_type'] == 'cur':
            # Replace {table} placeholder with properly quoted table name
            import os
            from dotenv import load_dotenv
            load_dotenv()

            db_name = os.getenv('CUR_DATABASE_NAME')
            table_name = os.getenv('CUR_TABLE_NAME')

            # Quote database and table names (they may contain hyphens/underscores)
            quoted_table = f'"{db_name}"."{table_name}"'
            query = kpi['query'].replace('{table}', quoted_table)

            result = execute_athena_query(query)

            if result.get('data') and len(result['data']) > 0:
                # Get first value from first row
                row = result['data'][0]
                if row and len(row) > 0:
                    value = list(row.values())[0]

                    # Handle NULL values
                    if value is None:
                        return jsonify({'error': 'Query returned NULL value - check date filters'}), 400

                    kpi_manager.update_kpi_value(kpi_id, value)

                    # Get updated KPI with new timestamp
                    updated_kpi = kpi_manager.get_kpi(kpi_id)

                    return jsonify({
                        'kpi_id': kpi_id,
                        'value': value,
                        'updated': updated_kpi['last_updated']
                    })

            return jsonify({'error': 'Query returned no data'}), 400

        elif kpi['query_type'] == 'cost_explorer':
            # Handle Cost Explorer queries
            if kpi['query'] == 'get_ri_coverage':
                # Call Cost Explorer for RI coverage
                from agent import cost_explorer
                from datetime import datetime, timedelta

                end = datetime.now()
                start = end - timedelta(days=30)

                response = cost_explorer.get_reservation_coverage(
                    TimePeriod={
                        'Start': start.strftime('%Y-%m-%d'),
                        'End': end.strftime('%Y-%m-%d')
                    }
                )

                coverage = response['Total']['CoverageHours']['CoverageHoursPercentage']
                kpi_manager.update_kpi_value(kpi_id, float(coverage))

                # Get updated KPI with new timestamp
                updated_kpi = kpi_manager.get_kpi(kpi_id)

                return jsonify({
                    'kpi_id': kpi_id,
                    'value': float(coverage),
                    'updated': updated_kpi['last_updated']
                })

            elif kpi['query'] == 'get_anomalies_count':
                # Call Cost Explorer for anomaly detection
                from agent import cost_explorer
                from datetime import datetime, timedelta

                end = datetime.now()
                start = end - timedelta(days=30)

                response = cost_explorer.get_anomalies(
                    DateInterval={
                        'StartDate': start.strftime('%Y-%m-%d'),
                        'EndDate': end.strftime('%Y-%m-%d')
                    },
                    TotalImpact={
                        'NumericOperator': 'GREATER_THAN_OR_EQUAL',
                        'StartValue': 100  # Only significant anomalies over $100
                    }
                )

                anomaly_count = len(response.get('Anomalies', []))
                kpi_manager.update_kpi_value(kpi_id, anomaly_count)

                # Get updated KPI with new timestamp
                updated_kpi = kpi_manager.get_kpi(kpi_id)

                return jsonify({
                    'kpi_id': kpi_id,
                    'value': anomaly_count,
                    'updated': updated_kpi['last_updated']
                })

        elif kpi['query_type'] == 'mcp_forecast':
            # Handle MCP cost forecast queries
            from mcp_aws_client import mcp_client
            from datetime import datetime, timedelta

            if kpi['query'] == 'get_cost_forecast_next_month':
                today = datetime.now()
                # Start from tomorrow
                start = (today + timedelta(days=1)).strftime('%Y-%m-%d')
                # End at end of next month
                end_of_next_month = (today.replace(day=1) + timedelta(days=62)).replace(day=1) - timedelta(days=1)
                end = end_of_next_month.strftime('%Y-%m-%d')

                result = mcp_client.get_cost_forecast(start, end, 'UNBLENDED_COST', 'MONTHLY')

                if result.get('success'):
                    total_forecast = float(result.get('total', {}).get('Amount', 0))
                    kpi_manager.update_kpi_value(kpi_id, total_forecast)

                    updated_kpi = kpi_manager.get_kpi(kpi_id)
                    return jsonify({
                        'kpi_id': kpi_id,
                        'value': total_forecast,
                        'updated': updated_kpi['last_updated']
                    })
                else:
                    return jsonify({'error': result.get('error', 'Failed to get forecast')}), 400

            elif kpi['query'] == 'get_mtd_vs_forecast':
                # Get MTD cost from CUR and forecast from Cost Explorer
                today = datetime.now()

                # Get MTD (month-to-date) cost
                start_of_month = today.replace(day=1).strftime('%Y-%m-%d')
                end_of_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

                # Query MTD cost
                import os
                from dotenv import load_dotenv
                load_dotenv()

                db_name = os.getenv('CUR_DATABASE_NAME')
                table_name = os.getenv('CUR_TABLE_NAME')
                quoted_table = f'"{db_name}"."{table_name}"'

                mtd_query = f'''
                SELECT ROUND(SUM("lineitem/unblendedcost"), 2) as cost
                FROM {quoted_table}
                WHERE "lineitem/usagestartdate" >= DATE_TRUNC('month', CURRENT_DATE)
                AND "lineitem/usagestartdate" < CURRENT_DATE
                '''

                mtd_result = execute_athena_query(mtd_query)
                mtd_cost = 0
                if mtd_result.get('data') and len(mtd_result['data']) > 0:
                    mtd_cost = float(list(mtd_result['data'][0].values())[0] or 0)

                # Get forecast for rest of month
                tomorrow = (today + timedelta(days=1)).strftime('%Y-%m-%d')
                forecast_end = (end_of_month + timedelta(days=1)).strftime('%Y-%m-%d')

                forecast_result = mcp_client.get_cost_forecast(tomorrow, forecast_end, 'UNBLENDED_COST', 'MONTHLY')

                if forecast_result.get('success'):
                    remaining_forecast = float(forecast_result.get('total', {}).get('Amount', 0))
                    total_forecast = mtd_cost + remaining_forecast

                    # Format as "MTD / Forecast"
                    value_text = f"${mtd_cost:,.2f} / ${total_forecast:,.2f}"
                    kpi_manager.update_kpi_value(kpi_id, value_text)

                    updated_kpi = kpi_manager.get_kpi(kpi_id)
                    return jsonify({
                        'kpi_id': kpi_id,
                        'value': value_text,
                        'updated': updated_kpi['last_updated']
                    })
                else:
                    # Fallback to just MTD if forecast fails
                    value_text = f"${mtd_cost:,.2f} (forecast unavailable)"
                    kpi_manager.update_kpi_value(kpi_id, value_text)

                    updated_kpi = kpi_manager.get_kpi(kpi_id)
                    return jsonify({
                        'kpi_id': kpi_id,
                        'value': value_text,
                        'updated': updated_kpi['last_updated']
                    })

        elif kpi['query_type'] == 'mcp_anomaly':
            # Handle MCP anomaly detection queries
            from mcp_aws_client import mcp_client
            from datetime import datetime, timedelta

            if kpi['query'] == 'get_anomalies_30d':
                end = datetime.now()
                start = end - timedelta(days=30)

                result = mcp_client.get_anomalies(
                    start.strftime('%Y-%m-%d'),
                    end.strftime('%Y-%m-%d')
                )

                if result.get('success'):
                    anomaly_count = result.get('count', 0)
                    kpi_manager.update_kpi_value(kpi_id, anomaly_count)

                    updated_kpi = kpi_manager.get_kpi(kpi_id)
                    return jsonify({
                        'kpi_id': kpi_id,
                        'value': anomaly_count,
                        'updated': updated_kpi['last_updated']
                    })
                else:
                    return jsonify({'error': result.get('error', 'Failed to get anomalies')}), 400

        elif kpi['query_type'] == 'mcp_optimizer':
            # Handle MCP Compute Optimizer queries
            from mcp_aws_client import mcp_client

            if kpi['query'] == 'get_ec2_savings':
                result = mcp_client.get_ec2_recommendations()

                if result.get('success'):
                    savings = result.get('potential_savings', 0)
                    kpi_manager.update_kpi_value(kpi_id, savings)

                    updated_kpi = kpi_manager.get_kpi(kpi_id)
                    return jsonify({
                        'kpi_id': kpi_id,
                        'value': savings,
                        'updated': updated_kpi['last_updated']
                    })
                else:
                    return jsonify({'error': result.get('error', 'Failed to get recommendations')}), 400

        elif kpi['query_type'] == 'mcp_budget':
            # Handle MCP Budget queries
            from mcp_aws_client import mcp_client

            if kpi['query'] == 'get_budget_overages':
                result = mcp_client.get_budgets()

                if result.get('success'):
                    over_budget_count = 0
                    for budget in result.get('budgets', []):
                        actual = float(budget.get('CalculatedSpend', {}).get('ActualSpend', {}).get('Amount', 0))
                        limit = float(budget.get('BudgetLimit', {}).get('Amount', 0))
                        if actual > limit:
                            over_budget_count += 1

                    kpi_manager.update_kpi_value(kpi_id, over_budget_count)

                    updated_kpi = kpi_manager.get_kpi(kpi_id)
                    return jsonify({
                        'kpi_id': kpi_id,
                        'value': over_budget_count,
                        'updated': updated_kpi['last_updated']
                    })
                else:
                    return jsonify({'error': result.get('error', 'Failed to get budgets')}), 400

        return jsonify({'error': 'Query type not supported yet'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kpis/templates', methods=['GET'])
def get_kpi_templates():
    """Get KPI templates"""
    return jsonify(kpi_manager.get_kpi_templates())


@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Get dashboard page"""
    return render_template('dashboard.html')


@app.route('/charts/<filename>')
def serve_chart(filename):
    """Serve chart HTML files"""
    # Check both finops-agent/workspace and parent workspace directories
    charts_dir = Path(__file__).parent / 'workspace' / 'charts'
    if not charts_dir.exists() or not (charts_dir / filename).exists():
        charts_dir = Path(__file__).parent.parent / 'workspace' / 'charts'
    return send_from_directory(charts_dir, filename)


@app.route('/api/charts', methods=['GET'])
def list_charts():
    """List all available charts"""
    # Check both directories for charts
    charts_dir1 = Path(__file__).parent / 'workspace' / 'charts'
    charts_dir2 = Path(__file__).parent.parent / 'workspace' / 'charts'

    charts_dir1.mkdir(parents=True, exist_ok=True)
    charts_dir2.mkdir(parents=True, exist_ok=True)

    # Collect charts from both directories
    charts = []
    for charts_dir in [charts_dir1, charts_dir2]:
        if not charts_dir.exists():
            continue
        for chart_file in sorted(charts_dir.glob('chart_*.html'), reverse=True):
            charts.append({
                'filename': chart_file.name,
                'url': f'/charts/{chart_file.name}',
                'created': chart_file.stat().st_mtime
            })

    # Remove duplicates and sort by creation time
    seen = set()
    unique_charts = []
    for chart in charts:
        if chart['filename'] not in seen:
            seen.add(chart['filename'])
            unique_charts.append(chart)

    return jsonify(sorted(unique_charts, key=lambda x: x['created'], reverse=True))


@app.route('/api/charts-page', methods=['GET'])
def charts_page():
    """Charts gallery page"""
    return render_template('charts.html')


# Conversation Management Endpoints

@app.route('/api/conversations', methods=['GET'])
def list_conversations():
    """List all conversations"""
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    conversations = conversation_manager.list_conversations(limit=limit, offset=offset)
    return jsonify({
        'conversations': conversations,
        'limit': limit,
        'offset': offset
    })


@app.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get a specific conversation with all messages"""
    conversation = conversation_manager.get_conversation(conversation_id)
    if conversation:
        return jsonify(conversation)
    else:
        return jsonify({'error': 'Conversation not found'}), 404


@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation"""
    success = conversation_manager.delete_conversation(conversation_id)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to delete conversation'}), 500


@app.route('/api/conversations/new', methods=['POST'])
def new_conversation():
    """Start a new conversation"""
    data = request.json or {}
    session_id = data.get('session_id', 'default')
    title = data.get('title', 'New Conversation')

    conversation_id = conversation_manager.create_conversation(
        session_id=session_id,
        title=title
    )

    # Update session mapping
    session_conversations[session_id] = conversation_id
    conversation_manager.set_session_conversation(session_id, conversation_id)

    return jsonify({
        'conversation_id': conversation_id,
        'session_id': session_id
    })


@app.route('/api/conversations/history', methods=['GET'])
def conversations_history_page():
    """Conversations history page"""
    return render_template('conversations.html')


# ===== Custom Context Management Endpoints =====

@app.route('/api/contexts', methods=['GET'])
def get_contexts():
    """Get all custom contexts"""
    contexts = context_manager.list_contexts()
    return jsonify(contexts)


@app.route('/api/contexts', methods=['POST'])
def create_context():
    """Create a new custom context"""
    data = request.json
    name = data.get('name', '').strip()
    content = data.get('content', '').strip()
    description = data.get('description', '').strip()

    if not name or not content:
        return jsonify({'error': 'Name and content are required'}), 400

    try:
        context = context_manager.add_context(name, content, description)
        return jsonify(context), 201
    except Exception as e:
        logger.error(f"Error creating context: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/contexts/upload', methods=['POST'])
def upload_context_file():
    """Upload a file as custom context (text or image)"""
    import base64

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        # Use filename as name if not provided
        name = file.filename

    # Detect file type
    filename_lower = file.filename.lower()
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')
    pdf_extensions = ('.pdf',)
    is_image = filename_lower.endswith(image_extensions)
    is_pdf = filename_lower.endswith(pdf_extensions)

    try:
        if is_image:
            # Handle image file
            file_data = file.read()

            # Get media type from extension
            ext = filename_lower.split('.')[-1]
            media_type_map = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'gif': 'image/gif',
                'webp': 'image/webp',
                'bmp': 'image/bmp'
            }
            media_type = media_type_map.get(ext, 'image/jpeg')

            # Encode as base64
            base64_image = base64.b64encode(file_data).decode('utf-8')

            # Store with media type prefix
            content = f"{media_type}:{base64_image}"

            context = context_manager.add_context(name, content, description, context_type="image")
            return jsonify(context), 201

        elif is_pdf:
            # Handle PDF file - store as base64 with text extraction
            import io
            try:
                import PyPDF2

                file_data = file.read()

                # Extract text from PDF
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
                text_content = ""
                total_pages = len(pdf_reader.pages)

                for page_num, page in enumerate(pdf_reader.pages):
                    text_content += f"\n--- Page {page_num + 1} of {total_pages} ---\n"
                    text_content += page.extract_text()

                # Check if content is too large (rough estimate: 1 token ≈ 4 chars)
                # Claude has 200k token context limit, leave room for conversation
                # Max ~150k tokens for PDF = ~600k characters
                MAX_CHARS = 600000

                if len(text_content) > MAX_CHARS:
                    # Content is too large - create a summary instead of storing full text
                    logger.warning(f"PDF too large ({len(text_content)} chars), creating summary")

                    summary = f"""PDF Document: {name}
Total Pages: {total_pages}
Size: {len(text_content):,} characters

⚠️ This PDF is too large to load entirely into context ({len(text_content):,} characters).

Available options:
1. Ask specific questions about the document (the agent can search through it)
2. Request specific page ranges (e.g., "show me pages 1-10")
3. Search for specific keywords or topics

First 10 pages preview:
"""
                    # Add preview of first 10 pages
                    preview_pages = []
                    for page_num in range(min(10, total_pages)):
                        preview_pages.append(f"\n--- Page {page_num + 1} ---\n")
                        preview_pages.append(pdf_reader.pages[page_num].extract_text()[:2000])  # First 2000 chars per page

                    summary += ''.join(preview_pages)
                    summary += f"\n\n... ({total_pages - 10} more pages available) ..."

                    # Store PDF base64 separately for potential retrieval
                    base64_pdf = base64.b64encode(file_data).decode('utf-8')
                    content = f"PDF:{base64_pdf}\n\nSUMMARY:\n{summary}\n\nFULL_TEXT_AVAILABLE:true"
                else:
                    # Store both the extracted text and base64 PDF
                    base64_pdf = base64.b64encode(file_data).decode('utf-8')
                    content = f"PDF:{base64_pdf}\n\nEXTRACTED_TEXT:\n{text_content}"

                context = context_manager.add_context(name, content, description, context_type="pdf")
                return jsonify(context), 201

            except ImportError:
                # If PyPDF2 not installed, store as binary base64
                logger.warning("PyPDF2 not installed, storing PDF without text extraction")
                file_data = file.read()
                base64_pdf = base64.b64encode(file_data).decode('utf-8')
                content = f"application/pdf:{base64_pdf}"
                context = context_manager.add_context(name, content, description, context_type="pdf")
                return jsonify(context), 201

        else:
            # Handle text file
            content = file.read().decode('utf-8')

            if not content.strip():
                return jsonify({'error': 'File is empty'}), 400

            context = context_manager.add_context(name, content, description, context_type="text")
            return jsonify(context), 201

    except UnicodeDecodeError:
        return jsonify({'error': 'File must be a text file (UTF-8 encoded) or an image'}), 400
    except Exception as e:
        logger.error(f"Error uploading context file: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/contexts/<context_id>', methods=['GET'])
def get_context(context_id):
    """Get a specific context with content"""
    context = context_manager.get_context(context_id)
    if not context:
        return jsonify({'error': 'Context not found'}), 404

    content = context_manager.get_context_content(context_id)
    return jsonify({**context, 'content': content})


@app.route('/api/contexts/<context_id>', methods=['PUT'])
def update_context(context_id):
    """Update a context"""
    data = request.json
    name = data.get('name')
    description = data.get('description')
    content = data.get('content')

    try:
        context = context_manager.update_context(context_id, name, description, content)
        if not context:
            return jsonify({'error': 'Context not found'}), 404
        return jsonify(context)
    except Exception as e:
        logger.error(f"Error updating context: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/contexts/<context_id>', methods=['DELETE'])
def delete_context(context_id):
    """Delete a context"""
    success = context_manager.delete_context(context_id)
    if not success:
        return jsonify({'error': 'Context not found'}), 404
    return jsonify({'success': True})


@sock.route('/ws')
def websocket(ws):
    """WebSocket connection for real-time updates"""
    logger.info("=" * 80)
    logger.info("WebSocket: New connection established")
    active_connections.add(ws)
    logger.info(f"Active WebSocket connections: {len(active_connections)}")

    try:
        while True:
            # Keep connection alive
            data = ws.receive(timeout=1)
            if data:
                logger.debug(f"WebSocket received data: {data}")
                # Echo back for testing
                ws.send(json.dumps({'type': 'ping', 'data': data}))
    except ConnectionClosed:
        logger.info("WebSocket connection closed by client")
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        print(f"WebSocket error: {e}")
    finally:
        active_connections.discard(ws)
        logger.info(f"WebSocket connection removed. Active connections: {len(active_connections)}")


def broadcast_to_clients(message):
    """Send message to all connected WebSocket clients"""
    logger.debug(f"Broadcasting message to {len(active_connections)} clients")
    logger.debug(f"Message type: {message.get('type', 'unknown')}")

    disconnected = set()
    for ws in active_connections:
        try:
            ws.send(json.dumps(message))
            logger.debug("Message sent to client successfully")
        except Exception as e:
            logger.error(f"Error broadcasting to client: {e}", exc_info=True)
            print(f"Error broadcasting to client: {e}")
            disconnected.add(ws)

    # Remove disconnected clients
    if disconnected:
        logger.warning(f"Removing {len(disconnected)} disconnected clients")
        active_connections.difference_update(disconnected)


def process_message_background(user_message: str, conversation_id: str, session_id: str = 'default', context_ids: list = None):
    """Process message in background and send updates via WebSocket"""
    logger.info("=" * 80)
    logger.info(f"BACKGROUND PROCESSING: {user_message[:100]}")
    logger.info(f"Conversation ID: {conversation_id}, Session ID: {session_id}")
    logger.info(f"Context IDs: {context_ids}")

    if context_ids is None:
        context_ids = []

    try:
        # Validate conversation exists
        logger.debug(f"Validating conversation exists: {conversation_id}")
        conversation = conversation_manager.get_conversation(conversation_id)
        if not conversation:
            logger.error(f"Conversation {conversation_id} not found")
            print(f"Error: Conversation {conversation_id} not found")
            broadcast_to_clients({
                'type': 'error',
                'message': f'Conversation {conversation_id} not found'
            })
            return

        logger.debug("Conversation validated successfully")

        # Add user message to THIS specific conversation only
        logger.debug("Adding user message to conversation")
        conversation_manager.add_message(conversation_id, 'user', user_message)

        # Build messages array ONLY from THIS conversation (strict isolation)
        logger.debug("Building message history from conversation")
        conv_messages = conversation_manager.get_conversation_messages(conversation_id)
        logger.debug(f"Retrieved {len(conv_messages)} messages from conversation")

        messages = []
        for msg in conv_messages:
            if msg['role'] in ['user', 'assistant']:
                messages.append({"role": msg['role'], "content": msg['content']})

        logger.debug(f"Built message array with {len(messages)} messages")

        # Ensure current message is in the list
        if not messages or messages[-1]['content'] != user_message:
            messages.append({"role": "user", "content": user_message})
            logger.debug("Added current message to array")

        # If there are image contexts, prepend them to the first user message
        if context_ids:
            image_contexts = context_manager.get_image_contexts(context_ids)
            if image_contexts and messages:
                # Find first user message and make it multimodal
                for i, msg in enumerate(messages):
                    if msg['role'] == 'user':
                        # Convert first user message to multimodal format
                        original_content = msg['content']
                        msg['content'] = image_contexts + [{"type": "text", "text": original_content}]
                        logger.info(f"Added {len(image_contexts)} image contexts to first user message")
                        break

        current_messages = messages
        max_attempts = 50
        attempts = 0

        logger.info("Starting Claude API interaction loop")
        while attempts < max_attempts:
            attempts += 1
            logger.info(f"API call attempt {attempts}/{max_attempts}")

            # Build system prompt with custom contexts if provided
            system_prompt = get_finops_system_prompt()
            if context_ids:
                logger.info(f"Adding {len(context_ids)} custom contexts to system prompt")
                custom_context = context_manager.get_contexts_for_prompt(context_ids)
                system_prompt += custom_context

            # Call Claude API
            logger.debug("Calling Claude API...")
            logger.debug(f"Message count: {len(current_messages)}")
            response = anthropic.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=4096,
                system=system_prompt,
                messages=current_messages,
                tools=AVAILABLE_TOOLS
            )
            logger.info(f"Claude API response received - Stop reason: {response.stop_reason}")

            # Check for tool calls
            tool_calls = [c for c in response.content if c.type == "tool_use"]
            text_content = [c for c in response.content if c.type == "text"]
            logger.info(f"Response contains {len(tool_calls)} tool calls and {len(text_content)} text blocks")

            # Send any text responses
            if text_content:
                logger.debug(f"Broadcasting {len(text_content)} text responses")
                for text in text_content:
                    broadcast_to_clients({
                        'type': 'text_response',
                        'content': text.text,
                        'conversation_id': conversation_id
                    })

            if tool_calls:
                logger.info(f"Executing {len(tool_calls)} tool calls")
                # Execute tools and send updates
                tool_results = []
                for i, tool_call in enumerate(tool_calls, 1):
                    logger.info(f"Tool {i}/{len(tool_calls)}: {tool_call.name}")
                    try:
                        # Notify clients that tool is starting
                        logger.debug(f"Notifying clients: {tool_call.name} started")
                        broadcast_to_clients({
                            'type': 'tool_call',
                            'tool_name': tool_call.name,
                            'status': 'started',
                            'conversation_id': conversation_id
                        })

                        # Execute tool
                        logger.debug(f"Executing tool: {tool_call.name}")
                        result = handle_tool_call(tool_call.name, tool_call.input)
                        logger.info(f"Tool {tool_call.name} completed successfully")
                        result_str = str(result) if not isinstance(result, str) else result

                        # Save tool execution to conversation
                        conversation_manager.add_tool_execution(
                            conversation_id, tool_call.name, tool_call.input, result
                        )

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": result_str
                        })

                        # Notify clients that tool completed
                        # For create_visualization, send full result dict for chart display
                        if tool_call.name == 'create_visualization' and isinstance(result, dict):
                            ui_result = result
                        else:
                            ui_result = result_str[:500]  # Truncate for UI

                        broadcast_to_clients({
                            'type': 'tool_call',
                            'tool_name': tool_call.name,
                            'status': 'completed',
                            'result': ui_result,
                            'conversation_id': conversation_id
                        })

                        # If KPI was created, notify dashboard to refresh
                        if tool_call.name == 'create_kpi' and isinstance(result, dict):
                            logger.info("KPI created - broadcasting dashboard refresh notification")
                            broadcast_to_clients({
                                'type': 'kpi_created',
                                'kpi_id': result.get('kpi_id'),
                                'message': 'Dashboard should refresh to show new KPI'
                            })

                    except Exception as error:
                        error_msg = str(error)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": str({"error": error_msg}),
                            "is_error": True
                        })

                        # Notify clients of error
                        broadcast_to_clients({
                            'type': 'tool_call',
                            'tool_name': tool_call.name,
                            'status': 'error',
                            'result': error_msg,
                            'conversation_id': conversation_id
                        })

                # Add assistant response and tool results to messages
                current_messages = current_messages + [
                    {"role": "assistant", "content": response.content},
                    {"role": "user", "content": tool_results}
                ]

            else:
                # No more tool calls, conversation complete
                final_text_response = '\n'.join(t.text for t in text_content)

                if final_text_response:
                    # Save assistant response to THIS conversation only (strict isolation)
                    conversation_manager.add_message(conversation_id, 'assistant', final_text_response)

                # Notify completion with conversation ID
                broadcast_to_clients({
                    'type': 'complete',
                    'conversation_id': conversation_id
                })
                break

    except Exception as error:
        print(f"Error processing message: {error}")
        broadcast_to_clients({
            'type': 'error',
            'message': str(error)
        })


# ===== Dashboard Filter Endpoints =====

@app.route('/api/dashboards/<dashboard_id>/filters', methods=['GET'])
def get_dashboard_filters(dashboard_id):
    """Get all filters for a dashboard"""
    dashboard = dashboard_manager.get_dashboard(dashboard_id)
    if not dashboard:
        return jsonify({'error': 'Dashboard not found'}), 404

    filters = dashboard.get('filters', [])
    return jsonify({'filters': filters})


@app.route('/api/dashboards/<dashboard_id>/filters', methods=['POST'])
def add_dashboard_filter(dashboard_id):
    """Add a filter to dashboard"""
    try:
        logger.info(f"Adding filter to dashboard {dashboard_id}")
        data = request.json
        logger.info(f"Filter data: {data}")

        if not data or 'type' not in data:
            logger.error("Filter type is missing")
            return jsonify({'error': 'Filter type is required'}), 400

        # Check if dashboard exists
        dashboard = dashboard_manager.get_dashboard(dashboard_id)
        if not dashboard:
            logger.error(f"Dashboard {dashboard_id} not found")
            return jsonify({'error': f'Dashboard {dashboard_id} not found'}), 404

        success = dashboard_manager.add_filter(dashboard_id, data)

        if success:
            dashboard = dashboard_manager.get_dashboard(dashboard_id)
            logger.info(f"Filter added successfully. Total filters: {len(dashboard.get('filters', []))}")
            return jsonify({'success': True, 'filters': dashboard.get('filters', [])})
        else:
            logger.error("Failed to add filter")
            return jsonify({'error': 'Failed to add filter'}), 500

    except Exception as e:
        logger.error(f"Error adding filter: {e}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/dashboards/<dashboard_id>/filters/<filter_id>', methods=['PUT'])
def update_dashboard_filter(dashboard_id, filter_id):
    """Update a dashboard filter"""
    data = request.json

    success = dashboard_manager.update_filter(dashboard_id, filter_id, data)

    if success:
        dashboard = dashboard_manager.get_dashboard(dashboard_id)
        return jsonify({'success': True, 'filters': dashboard.get('filters', [])})
    else:
        return jsonify({'error': 'Failed to update filter'}), 500


@app.route('/api/dashboards/<dashboard_id>/filters/<filter_id>', methods=['DELETE'])
def delete_dashboard_filter(dashboard_id, filter_id):
    """Delete a dashboard filter"""
    success = dashboard_manager.remove_filter(dashboard_id, filter_id)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to delete filter'}), 500


@app.route('/api/dashboards/<dashboard_id>/widgets/<widget_id>/filters', methods=['POST'])
def link_widget_filters(dashboard_id, widget_id):
    """Link filters to a widget"""
    data = request.json

    if not data or 'filter_ids' not in data:
        return jsonify({'error': 'filter_ids array is required'}), 400

    success = dashboard_manager.apply_filters_to_widget(dashboard_id, widget_id, data['filter_ids'])

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to link filters'}), 500


@app.route('/api/filter-presets', methods=['GET'])
def get_filter_presets():
    """Get filter presets for quick selection"""
    presets = dashboard_manager.get_filter_presets()
    return jsonify(presets)


@app.route('/api/filter-values/<dimension>', methods=['GET'])
def get_filter_dimension_values(dimension):
    """Get available values for a filter dimension"""
    try:
        from mcp_aws_client import mcp_client
        from datetime import datetime, timedelta

        # Default to last 30 days
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        # Map filter types to AWS dimensions
        dimension_map = {
            'service': 'SERVICE',
            'region': 'REGION',
            'account': 'LINKED_ACCOUNT',
            'instance_type': 'INSTANCE_TYPE',
            'usage_type': 'USAGE_TYPE'
        }

        aws_dimension = dimension_map.get(dimension, dimension.upper())

        result = mcp_client.get_dimension_values(
            dimension=aws_dimension,
            start_date=start_date,
            end_date=end_date
        )

        if result.get('success'):
            # Extract just the values from the response
            values = [dv.get('Value') for dv in result.get('values', [])]
            return jsonify({
                'success': True,
                'dimension': dimension,
                'values': sorted(values)[:50]  # Limit to 50 values
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 500

    except Exception as e:
        logger.error(f"Error fetching dimension values: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/dashboards/<dashboard_id>/analytics', methods=['GET'])
def dashboard_analytics_view(dashboard_id):
    """Analytics dashboard view with filters"""
    logger.info(f"Loading analytics view for dashboard: {dashboard_id}")

    # Verify dashboard exists
    dashboard = dashboard_manager.get_dashboard(dashboard_id)
    if not dashboard:
        logger.error(f"Dashboard {dashboard_id} not found")
        return "Dashboard not found", 404

    logger.info(f"Rendering analytics for dashboard: {dashboard.get('name', dashboard_id)}")
    return render_template('dashboard_analytics.html', dashboard_id=dashboard_id, dashboard_name=dashboard.get('name', 'Dashboard'))


@app.route('/api/charts/<chart_id>/render', methods=['POST'])
def render_chart_with_filters():
    """Generate chart dynamically with filters"""
    try:
        from chart_generator import chart_generator

        chart_id = request.view_args.get('chart_id')
        filters = request.json or {}

        logger.info(f"Rendering chart {chart_id} with filters: {filters}")

        # Generate chart with filters
        chart_url = chart_generator.generate_chart(chart_id, filters)

        return jsonify({
            'success': True,
            'chart_url': chart_url
        })

    except Exception as e:
        logger.error(f"Error rendering chart: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/dashboards/<dashboard_id>/widgets', methods=['GET'])
def get_dashboard_widgets_with_filters(dashboard_id):
    """Get dashboard widgets with applied filters"""
    try:
        from chart_generator import chart_generator

        # Get dashboard
        dashboard = dashboard_manager.get_dashboard(dashboard_id)
        if not dashboard:
            return jsonify({'error': 'Dashboard not found'}), 404

        # Get active filters
        filters_dict = {}
        for filter_obj in dashboard.get('filters', []):
            if filter_obj.get('type') == 'date_range':
                filters_dict['start_date'] = filter_obj.get('start')
                filters_dict['end_date'] = filter_obj.get('end')
            elif filter_obj.get('type') in ['service', 'region', 'account']:
                filters_dict[filter_obj['type']] = filter_obj.get('value')

        # Process each widget
        widgets = []
        for widget in dashboard.get('widgets', []):
            widget_copy = widget.copy()

            # If chart widget has a template, generate filtered chart
            if widget.get('type') == 'chart' and widget.get('chart_url'):
                # Extract chart ID from URL
                chart_url = widget['chart_url']
                chart_filename = chart_url.split('/')[-1]
                chart_id = chart_filename.replace('.html', '')

                # Check if template exists
                template = chart_generator.get_chart_template(chart_id)
                if template and filters_dict:
                    try:
                        # Generate filtered chart
                        new_chart_url = chart_generator.generate_chart(chart_id, filters_dict)
                        widget_copy['chart_url'] = f"http://localhost:8000{new_chart_url}"
                        widget_copy['filtered'] = True
                    except Exception as e:
                        logger.warning(f"Could not generate filtered chart for {chart_id}: {e}")
                        widget_copy['filtered'] = False
                else:
                    widget_copy['filtered'] = False

            widgets.append(widget_copy)

        return jsonify({
            'widgets': widgets,
            'filters': dashboard.get('filters', [])
        })

    except Exception as e:
        logger.error(f"Error getting filtered widgets: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def main():
    """Run the web server"""
    print("\n" + "="*60)
    print("🚀 FinOps Agent Web UI Starting...")
    print("="*60)
    print("\n📍 Open your browser to: http://localhost:8000")
    print("\n✓ AWS Cost Explorer connected")
    print("✓ Athena ready for CUR queries")
    print("✓ Claude AI ready")
    print("\nPress Ctrl+C to stop the server\n")

    try:
        app.run(
            host='0.0.0.0',
            port=8000,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...\n")


# ===== Dashboard Management Endpoints =====

@app.route('/api/dashboards', methods=['GET'])
def list_custom_dashboards():
    """Get all custom dashboards"""
    try:
        dashboards = dashboard_manager.list_dashboards()
        return jsonify({'dashboards': dashboards})
    except Exception as e:
        logger.error(f"Error listing dashboards: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboards', methods=['POST'])
def create_custom_dashboard():
    """Create a new custom dashboard"""
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        conversation_id = data.get('conversation_id')

        if not name:
            return jsonify({'error': 'Name is required'}), 400

        # If creating from conversation, extract widgets
        if conversation_id:
            messages = conversation_manager.get_conversation_messages(conversation_id)
            dashboard = dashboard_manager.create_from_conversation(
                conversation_id, name, messages
            )
        else:
            dashboard = dashboard_manager.create_dashboard(name, description, conversation_id)

        return jsonify(dashboard)
    except Exception as e:
        logger.error(f"Error creating dashboard: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboards/<dashboard_id>', methods=['GET'])
def get_custom_dashboard(dashboard_id):
    """Get a specific custom dashboard"""
    try:
        dashboard = dashboard_manager.get_dashboard(dashboard_id)
        if not dashboard:
            return jsonify({'error': 'Dashboard not found'}), 404
        return jsonify(dashboard)
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboards/<dashboard_id>', methods=['PUT'])
def update_custom_dashboard(dashboard_id):
    """Update custom dashboard"""
    try:
        data = request.json
        success = dashboard_manager.update_dashboard(
            dashboard_id,
            name=data.get('name'),
            description=data.get('description'),
            widgets=data.get('widgets')
        )
        if not success:
            return jsonify({'error': 'Dashboard not found'}), 404
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating dashboard: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboards/<dashboard_id>', methods=['DELETE'])
def delete_custom_dashboard(dashboard_id):
    """Delete custom dashboard"""
    try:
        success = dashboard_manager.delete_dashboard(dashboard_id)
        if not success:
            return jsonify({'error': 'Dashboard not found'}), 404
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting dashboard: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboards/<dashboard_id>/widgets', methods=['POST'])
def add_dashboard_widget(dashboard_id):
    """Add a widget to custom dashboard"""
    try:
        widget = request.json
        success = dashboard_manager.add_widget(dashboard_id, widget)
        if not success:
            return jsonify({'error': 'Dashboard not found'}), 404
        return jsonify({'success': True, 'widget': widget})
    except Exception as e:
        logger.error(f"Error adding widget: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboards/<dashboard_id>/widgets/<widget_id>', methods=['PUT'])
def update_dashboard_widget(dashboard_id, widget_id):
    """Update a dashboard widget"""
    try:
        updates = request.json
        success = dashboard_manager.update_widget(dashboard_id, widget_id, updates)
        if not success:
            return jsonify({'error': 'Dashboard or widget not found'}), 404
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating widget: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboards/<dashboard_id>/widgets/<widget_id>', methods=['DELETE'])
def remove_dashboard_widget(dashboard_id, widget_id):
    """Remove a widget from custom dashboard"""
    try:
        success = dashboard_manager.remove_widget(dashboard_id, widget_id)
        if not success:
            return jsonify({'error': 'Dashboard not found'}), 404
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error removing widget: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboards-page', methods=['GET'])
def dashboards_list_page():
    """Dashboards list page"""
    return render_template('dashboards.html')


@app.route('/api/dashboard/<dashboard_id>/view', methods=['GET'])
def dashboard_view_page(dashboard_id):
    """Dashboard viewer page"""
    return render_template('dashboard_view.html', dashboard_id=dashboard_id)


if __name__ == "__main__":
    main()
