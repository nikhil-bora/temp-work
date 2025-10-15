"""
Dashboard Manager - Persistent editable dashboards from conversations
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class DashboardManager:
    """Manages persistent dashboards with charts and analysis"""

    def __init__(self, storage_dir: str = "data/dashboards"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "dashboards_index.json"
        self.dashboards = self._load_index()

    def _load_index(self) -> Dict:
        """Load dashboards index"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading dashboards index: {e}")
                return {}
        return {}

    def _save_index(self):
        """Save dashboards index"""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.dashboards, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving dashboards index: {e}")

    def create_dashboard(self, name: str, description: str = "",
                        conversation_id: Optional[str] = None) -> Dict:
        """Create a new dashboard"""
        dashboard_id = f"dash_{int(time.time())}_{name.replace(' ', '_')[:20]}"

        dashboard = {
            'id': dashboard_id,
            'name': name,
            'description': description,
            'created': time.time(),
            'updated': time.time(),
            'conversation_id': conversation_id,
            'widgets': [],  # List of widgets (charts, text blocks, etc.)
            'filters': [],  # Dashboard-level filters
            'layout': 'grid'  # Layout type: grid, freeform
        }

        # Save dashboard data
        dashboard_file = self.storage_dir / f"{dashboard_id}.json"
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard, f, indent=2)

        # Update index
        self.dashboards[dashboard_id] = {
            'id': dashboard_id,
            'name': name,
            'description': description,
            'created': dashboard['created'],
            'updated': dashboard['updated']
        }
        self._save_index()

        logger.info(f"Created dashboard: {dashboard_id}")
        return dashboard

    def get_dashboard(self, dashboard_id: str) -> Optional[Dict]:
        """Get dashboard by ID"""
        dashboard_file = self.storage_dir / f"{dashboard_id}.json"
        if not dashboard_file.exists():
            return None

        try:
            with open(dashboard_file, 'r') as f:
                dashboard = json.load(f)

            # Ensure backward compatibility - add filters if missing
            if 'filters' not in dashboard:
                dashboard['filters'] = []

            if 'layout' not in dashboard:
                dashboard['layout'] = 'grid'

            return dashboard
        except Exception as e:
            logger.error(f"Error loading dashboard {dashboard_id}: {e}")
            return None

    def update_dashboard(self, dashboard_id: str, name: Optional[str] = None,
                        description: Optional[str] = None,
                        widgets: Optional[List] = None) -> bool:
        """Update dashboard"""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return False

        # Update fields
        if name is not None:
            dashboard['name'] = name
        if description is not None:
            dashboard['description'] = description
        if widgets is not None:
            dashboard['widgets'] = widgets

        dashboard['updated'] = time.time()

        # Save dashboard
        dashboard_file = self.storage_dir / f"{dashboard_id}.json"
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard, f, indent=2)

        # Update index
        if dashboard_id in self.dashboards:
            self.dashboards[dashboard_id]['name'] = dashboard['name']
            self.dashboards[dashboard_id]['description'] = dashboard['description']
            self.dashboards[dashboard_id]['updated'] = dashboard['updated']
            self._save_index()

        logger.info(f"Updated dashboard: {dashboard_id}")
        return True

    def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete dashboard"""
        dashboard_file = self.storage_dir / f"{dashboard_id}.json"
        if dashboard_file.exists():
            dashboard_file.unlink()

        if dashboard_id in self.dashboards:
            del self.dashboards[dashboard_id]
            self._save_index()
            logger.info(f"Deleted dashboard: {dashboard_id}")
            return True

        return False

    def list_dashboards(self) -> List[Dict]:
        """List all dashboards"""
        return sorted(
            self.dashboards.values(),
            key=lambda x: x['updated'],
            reverse=True
        )

    def add_widget(self, dashboard_id: str, widget: Dict) -> bool:
        """Add a widget to dashboard"""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return False

        # Generate widget ID
        widget_id = f"widget_{int(time.time())}_{len(dashboard['widgets'])}"
        widget['id'] = widget_id
        widget['created'] = time.time()

        dashboard['widgets'].append(widget)
        dashboard['updated'] = time.time()

        # Save dashboard
        dashboard_file = self.storage_dir / f"{dashboard_id}.json"
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard, f, indent=2)

        # Update index
        if dashboard_id in self.dashboards:
            self.dashboards[dashboard_id]['updated'] = dashboard['updated']
            self._save_index()

        return True

    def remove_widget(self, dashboard_id: str, widget_id: str) -> bool:
        """Remove a widget from dashboard"""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return False

        # Remove widget
        dashboard['widgets'] = [w for w in dashboard['widgets'] if w['id'] != widget_id]
        dashboard['updated'] = time.time()

        # Save dashboard
        dashboard_file = self.storage_dir / f"{dashboard_id}.json"
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard, f, indent=2)

        # Update index
        if dashboard_id in self.dashboards:
            self.dashboards[dashboard_id]['updated'] = dashboard['updated']
            self._save_index()

        return True

    def update_widget(self, dashboard_id: str, widget_id: str, updates: Dict) -> bool:
        """Update a specific widget"""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return False

        # Find and update widget
        for widget in dashboard['widgets']:
            if widget['id'] == widget_id:
                widget.update(updates)
                widget['updated'] = time.time()
                break
        else:
            return False

        dashboard['updated'] = time.time()

        # Save dashboard
        dashboard_file = self.storage_dir / f"{dashboard_id}.json"
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard, f, indent=2)

        # Update index
        if dashboard_id in self.dashboards:
            self.dashboards[dashboard_id]['updated'] = dashboard['updated']
            self._save_index()

        return True

    def create_from_conversation(self, conversation_id: str, name: str,
                                 messages: List[Dict]) -> Optional[Dict]:
        """Create dashboard from conversation messages"""
        # Extract charts and analysis from messages
        widgets = []
        position = 0

        for msg in messages:
            # Extract chart widgets
            if msg.get('role') == 'tool' and msg.get('tool_name') == 'create_visualization':
                try:
                    tool_output = msg.get('tool_output', {})
                    if isinstance(tool_output, str):
                        tool_output = json.loads(tool_output)

                    if tool_output.get('url') or tool_output.get('filename'):
                        widgets.append({
                            'type': 'chart',
                            'title': tool_output.get('title', 'Chart'),
                            'description': tool_output.get('description', ''),
                            'chart_url': tool_output.get('url') or f"/charts/{tool_output.get('filename')}",
                            'position': position,
                            'width': 'full'  # full, half, third
                        })
                        position += 1
                except Exception as e:
                    logger.error(f"Error extracting chart widget: {e}")

            # Extract text analysis widgets
            elif msg.get('role') == 'assistant':
                content = msg.get('content', '')
                if len(content) > 50:  # Only add substantial content
                    widgets.append({
                        'type': 'text',
                        'title': 'Analysis',
                        'content': content,
                        'position': position,
                        'width': 'full'
                    })
                    position += 1

        # Create dashboard
        dashboard = self.create_dashboard(name, f"Generated from conversation {conversation_id}", conversation_id)
        dashboard['widgets'] = widgets

        # Save with widgets
        dashboard_file = self.storage_dir / f"{dashboard['id']}.json"
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard, f, indent=2)

        return dashboard

    def add_filter(self, dashboard_id: str, filter_config: Dict) -> bool:
        """Add a filter to dashboard"""
        try:
            logger.info(f"Adding filter to dashboard {dashboard_id}")
            dashboard = self.get_dashboard(dashboard_id)
            if not dashboard:
                logger.error(f"Dashboard {dashboard_id} not found in add_filter")
                return False

            # Ensure filters key exists
            if 'filters' not in dashboard:
                dashboard['filters'] = []
                logger.info("Added filters array to dashboard")

            # Generate filter ID
            filter_id = f"filter_{int(time.time())}_{len(dashboard['filters'])}"
            filter_config['id'] = filter_id
            filter_config['created'] = time.time()

            logger.info(f"Generated filter ID: {filter_id}")
            dashboard['filters'].append(filter_config)
            dashboard['updated'] = time.time()

            # Save dashboard
            dashboard_file = self.storage_dir / f"{dashboard_id}.json"
            logger.info(f"Saving dashboard to {dashboard_file}")
            with open(dashboard_file, 'w') as f:
                json.dump(dashboard, f, indent=2)

            # Update index
            if dashboard_id in self.dashboards:
                self.dashboards[dashboard_id]['updated'] = dashboard['updated']
                self._save_index()

            logger.info(f"Filter added successfully. Total filters: {len(dashboard['filters'])}")
            return True

        except Exception as e:
            logger.error(f"Error in add_filter: {e}", exc_info=True)
            return False

    def update_filter(self, dashboard_id: str, filter_id: str, updates: Dict) -> bool:
        """Update a specific filter"""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard or 'filters' not in dashboard:
            return False

        # Find and update filter
        for filter_item in dashboard['filters']:
            if filter_item['id'] == filter_id:
                filter_item.update(updates)
                filter_item['updated'] = time.time()
                break
        else:
            return False

        dashboard['updated'] = time.time()

        # Save dashboard
        dashboard_file = self.storage_dir / f"{dashboard_id}.json"
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard, f, indent=2)

        # Update index
        if dashboard_id in self.dashboards:
            self.dashboards[dashboard_id]['updated'] = dashboard['updated']
            self._save_index()

        return True

    def remove_filter(self, dashboard_id: str, filter_id: str) -> bool:
        """Remove a filter from dashboard"""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard or 'filters' not in dashboard:
            return False

        # Remove filter
        dashboard['filters'] = [f for f in dashboard['filters'] if f['id'] != filter_id]
        dashboard['updated'] = time.time()

        # Save dashboard
        dashboard_file = self.storage_dir / f"{dashboard_id}.json"
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard, f, indent=2)

        # Update index
        if dashboard_id in self.dashboards:
            self.dashboards[dashboard_id]['updated'] = dashboard['updated']
            self._save_index()

        return True

    def apply_filters_to_widget(self, dashboard_id: str, widget_id: str, filter_ids: List[str]) -> bool:
        """Link specific filters to a widget"""
        dashboard = self.get_dashboard(dashboard_id)
        if not dashboard:
            return False

        # Find and update widget
        for widget in dashboard['widgets']:
            if widget['id'] == widget_id:
                widget['linked_filters'] = filter_ids
                widget['updated'] = time.time()
                break
        else:
            return False

        dashboard['updated'] = time.time()

        # Save dashboard
        dashboard_file = self.storage_dir / f"{dashboard_id}.json"
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard, f, indent=2)

        return True

    def get_filter_presets(self) -> Dict:
        """Get common filter presets"""
        from datetime import datetime, timedelta

        today = datetime.now()
        return {
            'date_ranges': [
                {
                    'name': 'Today',
                    'type': 'date_range',
                    'start': today.strftime('%Y-%m-%d'),
                    'end': today.strftime('%Y-%m-%d')
                },
                {
                    'name': 'Last 7 Days',
                    'type': 'date_range',
                    'start': (today - timedelta(days=7)).strftime('%Y-%m-%d'),
                    'end': today.strftime('%Y-%m-%d')
                },
                {
                    'name': 'Last 30 Days',
                    'type': 'date_range',
                    'start': (today - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'end': today.strftime('%Y-%m-%d')
                },
                {
                    'name': 'This Month',
                    'type': 'date_range',
                    'start': today.replace(day=1).strftime('%Y-%m-%d'),
                    'end': today.strftime('%Y-%m-%d')
                },
                {
                    'name': 'Last Month',
                    'type': 'date_range',
                    'start': (today.replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d'),
                    'end': (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
                }
            ],
            'services': [
                {'name': 'EC2', 'value': 'AmazonEC2'},
                {'name': 'S3', 'value': 'AmazonS3'},
                {'name': 'RDS', 'value': 'AmazonRDS'},
                {'name': 'Lambda', 'value': 'AWSLambda'},
                {'name': 'EKS', 'value': 'AmazonEKS'},
                {'name': 'DynamoDB', 'value': 'AmazonDynamoDB'}
            ],
            'regions': [
                {'name': 'US East (N. Virginia)', 'value': 'us-east-1'},
                {'name': 'US West (Oregon)', 'value': 'us-west-2'},
                {'name': 'EU (Ireland)', 'value': 'eu-west-1'},
                {'name': 'Asia Pacific (Singapore)', 'value': 'ap-southeast-1'}
            ]
        }


# Global instance
dashboard_manager = DashboardManager()
