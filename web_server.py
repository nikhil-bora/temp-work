#!/usr/bin/env python3
"""
FinOps Agent Web Server
Flask + WebSocket server for the web UI
"""

import asyncio
import json
import sys
import logging
from pathlib import Path
from threading import Thread
from flask import Flask, render_template, request, jsonify, send_from_directory
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

    logger.info(f"User message: {user_message[:100]}...")
    logger.info(f"Conversation ID: {conversation_id}")
    logger.info(f"Session ID: {session_id}")

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
    thread = Thread(target=process_message_background, args=(user_message, conversation_id, session_id))
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


def process_message_background(user_message: str, conversation_id: str, session_id: str = 'default'):
    """Process message in background and send updates via WebSocket"""
    logger.info("=" * 80)
    logger.info(f"BACKGROUND PROCESSING: {user_message[:100]}")
    logger.info(f"Conversation ID: {conversation_id}, Session ID: {session_id}")

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

        current_messages = messages
        max_attempts = 50
        attempts = 0

        logger.info("Starting Claude API interaction loop")
        while attempts < max_attempts:
            attempts += 1
            logger.info(f"API call attempt {attempts}/{max_attempts}")

            # Call Claude API
            logger.debug("Calling Claude API...")
            logger.debug(f"Message count: {len(current_messages)}")
            response = anthropic.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=4096,
                system=get_finops_system_prompt(),
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
                        'content': text.text
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
                            'status': 'started'
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
                            'result': ui_result
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
                            'result': error_msg
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


if __name__ == "__main__":
    main()
