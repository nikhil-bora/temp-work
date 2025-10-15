#!/usr/bin/env python3
"""
KPI Dashboard Manager
Handles KPI creation, storage, calculation, and management
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# KPI storage directory
KPI_DIR = Path(__file__).parent / "workspace" / "kpis"
KPI_DIR.mkdir(parents=True, exist_ok=True)

KPI_CONFIG_FILE = KPI_DIR / "kpi_config.json"


class KPIManager:
    """Manages KPI definitions and calculations"""

    def __init__(self):
        self.kpis: Dict[str, Dict] = {}
        self.load_kpis()

    def load_kpis(self):
        """Load KPIs from storage"""
        if KPI_CONFIG_FILE.exists():
            with open(KPI_CONFIG_FILE, 'r') as f:
                self.kpis = json.load(f)
        else:
            # Initialize with default KPIs
            self.kpis = self._get_default_kpis()
            self.save_kpis()

    def save_kpis(self):
        """Save KPIs to storage"""
        with open(KPI_CONFIG_FILE, 'w') as f:
            json.dump(self.kpis, f, indent=2)

    def _get_default_kpis(self) -> Dict[str, Dict]:
        """Get default KPI definitions - Updated for actual CUR schema with forward slashes"""
        return {
            "total_monthly_cost": {
                "id": "total_monthly_cost",
                "name": "Total Monthly Cost",
                "description": "Total AWS spend for current month",
                "query_type": "cur",
                "query": """
                    SELECT
                        SUM("lineitem/unblendedcost") as total_cost
                    FROM {table}
                    WHERE
                        MONTH("bill/billingperiodstartdate") = MONTH(current_date)
                        AND YEAR("bill/billingperiodstartdate") = YEAR(current_date)
                """,
                "format": "currency",
                "icon": "💰",
                "color": "#a826b3",
                "size": "large",
                "refresh_interval": 3600,
                "last_updated": None,
                "last_value": None,
                "trend": None
            },
            "daily_cost": {
                "id": "daily_cost",
                "name": "Daily Cost",
                "description": "Average daily spend this month",
                "query_type": "cur",
                "query": """
                    SELECT
                        SUM("lineitem/unblendedcost") / COUNT(DISTINCT DATE("lineitem/usagestartdate")) as daily_avg
                    FROM {table}
                    WHERE
                        MONTH("bill/billingperiodstartdate") = MONTH(current_date)
                        AND YEAR("bill/billingperiodstartdate") = YEAR(current_date)
                """,
                "format": "currency",
                "icon": "📊",
                "color": "#33ccff",
                "size": "medium",
                "refresh_interval": 1800,
                "last_updated": None,
                "last_value": None,
                "trend": None
            },
            "top_service": {
                "id": "top_service",
                "name": "Top Service",
                "description": "Highest cost service this month",
                "query_type": "cur",
                "query": """
                    SELECT
                        "lineitem/productcode" as service
                    FROM {table}
                    WHERE
                        MONTH("bill/billingperiodstartdate") = MONTH(current_date)
                        AND YEAR("bill/billingperiodstartdate") = YEAR(current_date)
                    GROUP BY "lineitem/productcode"
                    ORDER BY SUM("lineitem/unblendedcost") DESC
                    LIMIT 1
                """,
                "format": "text",
                "icon": "🥇",
                "color": "#ff5c69",
                "size": "medium",
                "refresh_interval": 3600,
                "last_updated": None,
                "last_value": None,
                "trend": None
            },
            "ec2_instances": {
                "id": "ec2_instances",
                "name": "EC2 Instances",
                "description": "Total running EC2 instances",
                "query_type": "cur",
                "query": """
                    SELECT
                        COUNT(DISTINCT "lineitem/resourceid") as instance_count
                    FROM {table}
                    WHERE
                        "lineitem/productcode" = 'AmazonEC2'
                        AND "lineitem/usagetype" LIKE '%BoxUsage%'
                        AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
                    AND YEAR("bill/billingperiodstartdate") = YEAR(current_date)
                """,
                "format": "number",
                "icon": "🖥️",
                "color": "#3cf",
                "size": "small",
                "refresh_interval": 1800,
                "last_updated": None,
                "last_value": None,
                "trend": None
            },
            "ri_coverage": {
                "id": "ri_coverage",
                "name": "RI Coverage",
                "description": "Reserved Instance coverage percentage",
                "query_type": "cost_explorer",
                "query": "get_ri_coverage",
                "format": "percentage",
                "icon": "🎯",
                "color": "#a826b3",
                "size": "medium",
                "refresh_interval": 3600,
                "last_updated": None,
                "last_value": None,
                "trend": None
            },
            "cost_anomalies": {
                "id": "cost_anomalies",
                "name": "Cost Anomalies",
                "description": "Number of cost anomalies detected",
                "query_type": "cost_explorer",
                "query": "get_anomalies_count",
                "format": "number",
                "icon": "⚠️",
                "color": "#ff5c69",
                "size": "small",
                "refresh_interval": 1800,
                "last_updated": None,
                "last_value": None,
                "trend": None
            }
        }

    def list_kpis(self) -> List[Dict]:
        """List all KPIs"""
        return list(self.kpis.values())

    def get_kpi(self, kpi_id: str) -> Optional[Dict]:
        """Get a specific KPI"""
        return self.kpis.get(kpi_id)

    def create_kpi(self, kpi_data: Dict) -> Dict:
        """Create a new KPI"""
        kpi_id = kpi_data.get('id') or f"kpi_{int(time.time())}"

        kpi = {
            "id": kpi_id,
            "name": kpi_data.get('name', 'Untitled KPI'),
            "description": kpi_data.get('description', ''),
            "query_type": kpi_data.get('query_type', 'cur'),
            "query": kpi_data.get('query', ''),
            "format": kpi_data.get('format', 'number'),
            "icon": kpi_data.get('icon', '📊'),
            "color": kpi_data.get('color', '#33ccff'),
            "size": kpi_data.get('size', 'medium'),
            "refresh_interval": kpi_data.get('refresh_interval', 1800),
            "last_updated": None,
            "last_value": None,
            "trend": None
        }

        self.kpis[kpi_id] = kpi
        self.save_kpis()
        return kpi

    def update_kpi(self, kpi_id: str, kpi_data: Dict) -> Optional[Dict]:
        """Update an existing KPI"""
        if kpi_id not in self.kpis:
            return None

        kpi = self.kpis[kpi_id]

        # Update fields
        for key in ['name', 'description', 'query_type', 'query', 'format',
                    'icon', 'color', 'size', 'refresh_interval']:
            if key in kpi_data:
                kpi[key] = kpi_data[key]

        self.save_kpis()
        return kpi

    def delete_kpi(self, kpi_id: str) -> bool:
        """Delete a KPI"""
        if kpi_id in self.kpis:
            del self.kpis[kpi_id]
            self.save_kpis()
            return True
        return False

    def update_kpi_value(self, kpi_id: str, value: Any, trend: Optional[str] = None):
        """Update KPI value and timestamp"""
        if kpi_id in self.kpis:
            self.kpis[kpi_id]['last_value'] = value
            self.kpis[kpi_id]['last_updated'] = datetime.now().isoformat()
            if trend:
                self.kpis[kpi_id]['trend'] = trend
            self.save_kpis()

    def needs_refresh(self, kpi_id: str) -> bool:
        """Check if KPI needs to be refreshed"""
        kpi = self.kpis.get(kpi_id)
        if not kpi:
            return False

        if not kpi['last_updated']:
            return True

        last_updated = datetime.fromisoformat(kpi['last_updated'])
        refresh_interval = timedelta(seconds=kpi['refresh_interval'])

        return datetime.now() - last_updated > refresh_interval

    def get_kpi_templates(self) -> List[Dict]:
        """Get KPI templates for quick creation"""
        return [
            # MCP-based KPI templates
            {
                "name": "Next Month Cost Forecast",
                "description": "AI-predicted costs for next month based on historical usage",
                "query_type": "mcp_forecast",
                "query": "get_cost_forecast_next_month",
                "format": "currency",
                "icon": "🔮",
                "color": "#a826b3"
            },
            {
                "name": "Cost Anomalies (30d)",
                "description": "Number of cost anomalies detected in last 30 days",
                "query_type": "mcp_anomaly",
                "query": "get_anomalies_30d",
                "format": "number",
                "icon": "⚠️",
                "color": "#ff5c69"
            },
            {
                "name": "EC2 Rightsizing Savings",
                "description": "Potential monthly savings from EC2 rightsizing",
                "query_type": "mcp_optimizer",
                "query": "get_ec2_savings",
                "format": "currency",
                "icon": "✂️",
                "color": "#33ccff"
            },
            {
                "name": "Budget Status",
                "description": "Number of budgets over their limit",
                "query_type": "mcp_budget",
                "query": "get_budget_overages",
                "format": "number",
                "icon": "💰",
                "color": "#ff5c69"
            },
            # CUR-based KPI templates
            {
                "name": "S3 Total Cost",
                "description": "Total S3 storage and data transfer costs",
                "query_type": "cur",
                "query": """
                    SELECT SUM("lineitem/unblendedcost") as s3_cost
                    FROM {table}
                    WHERE "lineitem/productcode" = 'AmazonS3'
                    AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
                    AND YEAR("bill/billingperiodstartdate") = YEAR(current_date)
                """,
                "format": "currency",
                "icon": "🗄️",
                "color": "#ff5c69"
            },
            {
                "name": "Lambda Invocations",
                "description": "Total Lambda function invocations",
                "query_type": "cur",
                "query": """
                    SELECT SUM("lineitem/usageamount") as invocations
                    FROM {table}
                    WHERE "lineitem/productcode" = 'AWSLambda'
                    AND "lineitem/usagetype" LIKE '%Request%'
                    AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
                    AND YEAR("bill/billingperiodstartdate") = YEAR(current_date)
                """,
                "format": "number",
                "icon": "⚡",
                "color": "#3cf"
            },
            {
                "name": "RDS Cost",
                "description": "Total RDS database costs",
                "query_type": "cur",
                "query": """
                    SELECT SUM("lineitem/unblendedcost") as rds_cost
                    FROM {table}
                    WHERE "lineitem/productcode" = 'AmazonRDS'
                    AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
                    AND YEAR("bill/billingperiodstartdate") = YEAR(current_date)
                """,
                "format": "currency",
                "icon": "💾",
                "color": "#a826b3"
            },
            {
                "name": "Data Transfer Cost",
                "description": "Total data transfer out costs",
                "query_type": "cur",
                "query": """
                    SELECT SUM("lineitem/unblendedcost") as transfer_cost
                    FROM {table}
                    WHERE "lineitem/usagetype" LIKE '%DataTransfer-Out%'
                    AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
                    AND YEAR("bill/billingperiodstartdate") = YEAR(current_date)
                """,
                "format": "currency",
                "icon": "🌐",
                "color": "#ff5c69"
            },
            {
                "name": "Cost vs Budget",
                "description": "Current month cost as % of budget",
                "query_type": "custom",
                "query": "calculate_budget_percentage",
                "format": "percentage",
                "icon": "🎯",
                "color": "#33ccff"
            },
            {
                "name": "Production Env Cost",
                "description": "Costs for production environment (by tag)",
                "query_type": "cur",
                "query": """
                    SELECT SUM("lineitem/unblendedcost") as prod_cost
                    FROM {table}
                    WHERE json_extract_scalar(raw_tags, '$.Environment') = 'production'
                    AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
                    AND YEAR("bill/billingperiodstartdate") = YEAR(current_date)
                """,
                "format": "currency",
                "icon": "🏭",
                "color": "#ff5c69"
            },
            {
                "name": "Untagged Resources Cost",
                "description": "Costs from resources without Environment tag",
                "query_type": "cur",
                "query": """
                    SELECT SUM("lineitem/unblendedcost") as untagged_cost
                    FROM {table}
                    WHERE (json_extract_scalar(raw_tags, '$.Environment') IS NULL
                           OR json_extract_scalar(raw_tags, '$.Environment') = '')
                    AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
                    AND YEAR("bill/billingperiodstartdate") = YEAR(current_date)
                """,
                "format": "currency",
                "icon": "⚠️",
                "color": "#ffcc00"
            },
            {
                "name": "GKE Cluster Costs",
                "description": "Costs for top GKE cluster (by tag)",
                "query_type": "cur",
                "query": """
                    SELECT json_extract(raw_tags, '$["goog-k8s-cluster-name"]') as cluster_name
                    FROM {table}
                    WHERE json_extract(raw_tags, '$["goog-k8s-cluster-name"]') IS NOT NULL
                    AND MONTH("bill/billingperiodstartdate") = MONTH(current_date)
                    AND YEAR("bill/billingperiodstartdate") = YEAR(current_date)
                    GROUP BY json_extract(raw_tags, '$["goog-k8s-cluster-name"]')
                    ORDER BY SUM("lineitem/unblendedcost") DESC
                    LIMIT 1
                """,
                "format": "text",
                "icon": "☸️",
                "color": "#4285F4"
            }
        ]


# Global KPI manager instance
kpi_manager = KPIManager()
