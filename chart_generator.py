"""
Dynamic Chart Generator with Filter Support
Stores chart query templates and regenerates charts on-the-fly with filters
"""

import json
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import boto3
import logging

logger = logging.getLogger(__name__)

WORKSPACE_DIR = Path(__file__).parent / "data"

class ChartGenerator:
    def __init__(self):
        self.charts_dir = WORKSPACE_DIR / "charts"
        self.templates_dir = WORKSPACE_DIR / "chart_templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    def save_chart_template(self, chart_id: str, template: Dict[str, Any]) -> bool:
        """Save a chart template for later regeneration"""
        try:
            template_file = self.templates_dir / f"{chart_id}.json"
            with open(template_file, 'w') as f:
                json.dump(template, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving chart template: {e}")
            return False

    def get_chart_template(self, chart_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a chart template"""
        try:
            template_file = self.templates_dir / f"{chart_id}.json"
            if not template_file.exists():
                return None
            with open(template_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading chart template: {e}")
            return None

    def apply_filters_to_query(self, query_params: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply dashboard filters to query parameters"""
        filtered_params = query_params.copy()

        # Apply date range filters
        if 'start_date' in filters:
            filtered_params['start_date'] = filters['start_date']
        if 'end_date' in filters:
            filtered_params['end_date'] = filters['end_date']

        # Apply dimension filters (service, region, account, etc.)
        if 'service' in filters:
            if 'filter_expressions' not in filtered_params:
                filtered_params['filter_expressions'] = []
            filtered_params['filter_expressions'].append({
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': [filters['service']]
                }
            })

        if 'region' in filters:
            if 'filter_expressions' not in filtered_params:
                filtered_params['filter_expressions'] = []
            filtered_params['filter_expressions'].append({
                'Dimensions': {
                    'Key': 'REGION',
                    'Values': [filters['region']]
                }
            })

        if 'account' in filters:
            if 'filter_expressions' not in filtered_params:
                filtered_params['filter_expressions'] = []
            filtered_params['filter_expressions'].append({
                'Dimensions': {
                    'Key': 'LINKED_ACCOUNT',
                    'Values': [filters['account']]
                }
            })

        return filtered_params

    def execute_query(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the query with given parameters"""
        query_type = query_params.get('query_type', 'cost_explorer')

        if query_type == 'cost_explorer':
            return self._query_cost_explorer(query_params)
        elif query_type == 'athena':
            return self._query_athena(query_params)
        elif query_type == 'static':
            # For static data, just return the data directly
            return query_params.get('data', {})
        else:
            logger.error(f"Unknown query type: {query_type}")
            return {}

    def _query_cost_explorer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query AWS Cost Explorer with filters"""
        try:
            ce = boto3.client('ce', region_name='us-east-1')

            # Build time period
            time_period = {
                'Start': params.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')),
                'End': params.get('end_date', datetime.now().strftime('%Y-%m-%d'))
            }

            # Build filter expression
            filter_expr = None
            if 'filter_expressions' in params and params['filter_expressions']:
                if len(params['filter_expressions']) == 1:
                    filter_expr = params['filter_expressions'][0]
                else:
                    # Combine multiple filters with AND
                    filter_expr = {
                        'And': params['filter_expressions']
                    }

            # Build request
            request = {
                'TimePeriod': time_period,
                'Granularity': params.get('granularity', 'DAILY'),
                'Metrics': params.get('metrics', ['UnblendedCost']),
            }

            if filter_expr:
                request['Filter'] = filter_expr

            if params.get('group_by'):
                request['GroupBy'] = params['group_by']

            # Execute query
            response = ce.get_cost_and_usage(**request)

            # Transform response to chart data format
            return self._transform_ce_response(response, params)

        except Exception as e:
            logger.error(f"Error querying Cost Explorer: {e}")
            return {}

    def _transform_ce_response(self, response: Dict, params: Dict) -> Dict[str, Any]:
        """Transform Cost Explorer response to chart data format"""
        chart_type = params.get('chart_type', 'bar')

        if chart_type in ['bar', 'line', 'area']:
            # Time series data
            x = []
            y = []

            for result in response.get('ResultsByTime', []):
                x.append(result['TimePeriod']['Start'])
                if 'Groups' in result and result['Groups']:
                    # Grouped data
                    total = sum(float(group['Metrics']['UnblendedCost']['Amount']) for group in result['Groups'])
                    y.append(total)
                else:
                    # Single metric
                    y.append(float(result['Total']['UnblendedCost']['Amount']))

            return {'x': x, 'y': y}

        elif chart_type in ['pie', 'donut']:
            # Aggregated data by dimension
            labels = []
            values = []

            # Aggregate across all time periods
            aggregated = {}
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    key = group['Keys'][0] if group['Keys'] else 'Unknown'
                    amount = float(group['Metrics']['UnblendedCost']['Amount'])
                    aggregated[key] = aggregated.get(key, 0) + amount

            labels = list(aggregated.keys())
            values = list(aggregated.values())

            return {'labels': labels, 'values': values}

        return {}

    def _query_athena(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query Athena with filters (placeholder for now)"""
        # TODO: Implement Athena querying
        logger.warning("Athena querying not yet implemented")
        return {}

    def generate_chart(self, chart_id: str, filters: Optional[Dict[str, Any]] = None) -> str:
        """Generate a chart with optional filters"""
        # Load template
        template = self.get_chart_template(chart_id)
        if not template:
            raise ValueError(f"Chart template not found: {chart_id}")

        # Apply filters to query
        query_params = template.get('query_params', {})
        if filters:
            query_params = self.apply_filters_to_query(query_params, filters)

        # Execute query to get data
        data = self.execute_query(query_params)

        if not data:
            raise ValueError("Query returned no data")

        # Generate chart with Plotly
        fig = self._create_plotly_chart(
            chart_type=template.get('chart_type', 'bar'),
            data=data,
            title=template.get('title', 'Chart'),
            x_label=template.get('x_label', ''),
            y_label=template.get('y_label', ''),
            color_scheme=template.get('color_scheme', 'default')
        )

        # Save chart
        chart_filename = f"{chart_id}_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        chart_path = self.charts_dir / chart_filename
        fig.write_html(str(chart_path))

        return f"/charts/{chart_filename}"

    def _create_plotly_chart(self, chart_type: str, data: Dict, title: str,
                            x_label: str, y_label: str, color_scheme: str) -> go.Figure:
        """Create a Plotly chart"""
        color_maps = {
            'default': ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52'],
            'blues': ['#4472C4', '#5B9BD5', '#70AD47', '#FFC000', '#ED7D31'],
            'financial': ['#2E7D32', '#C62828', '#1565C0', '#F57C00', '#6A1B9A']
        }
        colors = color_maps.get(color_scheme, color_maps['default'])

        fig = None

        if chart_type == 'bar':
            fig = go.Figure(data=[go.Bar(x=data.get('x', []), y=data.get('y', []), marker_color=colors[0])])

        elif chart_type == 'line':
            fig = go.Figure(data=[go.Scatter(x=data.get('x', []), y=data.get('y', []),
                                            mode='lines+markers', line=dict(color=colors[0], width=3))])

        elif chart_type == 'area':
            fig = go.Figure(data=[go.Scatter(x=data.get('x', []), y=data.get('y', []),
                                            fill='tozeroy', line=dict(color=colors[0]))])

        elif chart_type in ['pie', 'donut']:
            hole = 0.4 if chart_type == 'donut' else 0
            fig = go.Figure(data=[go.Pie(labels=data.get('labels', []), values=data.get('values', []),
                                         hole=hole, marker=dict(colors=colors))])

        elif chart_type == 'grouped_bar':
            fig = go.Figure()
            y_data = data.get('y', {})
            if isinstance(y_data, dict):
                for i, (name, values) in enumerate(y_data.items()):
                    fig.add_trace(go.Bar(name=name, x=data.get('x', []), y=values,
                                        marker_color=colors[i % len(colors)]))
                fig.update_layout(barmode='group')

        if fig:
            fig.update_layout(
                title=dict(text=title, x=0.5, xanchor='center', font=dict(size=20, color='#333')),
                xaxis_title=x_label,
                yaxis_title=y_label,
                template='plotly_white',
                hovermode='x unified',
                font=dict(family='Inter, sans-serif', size=12),
                margin=dict(l=60, r=40, t=80, b=60),
                height=500
            )

        return fig

# Global instance
chart_generator = ChartGenerator()
