"""
AWS MCP Client Wrapper
Provides a Python interface to AWS MCP servers for FinOps operations
"""

import os
import json
import logging
import subprocess
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class AWSMCPClient:
    """
    Wrapper for AWS MCP servers (Cost Explorer, Billing & Cost Management, Pricing)
    Provides synchronous interface for FinOps operations
    """

    def __init__(self, aws_profile: Optional[str] = None):
        """
        Initialize AWS MCP client

        Args:
            aws_profile: AWS profile name (defaults to environment or 'default')
        """
        self.aws_profile = aws_profile or os.getenv('AWS_PROFILE', 'default')
        self._initialized = False

    def _run_mcp_command(self, server: str, tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute MCP server command using subprocess

        Args:
            server: MCP server name (cost-explorer, billing-cost-management, pricing)
            tool: Tool name to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        try:
            # Prepare environment
            env = os.environ.copy()
            env['AWS_PROFILE'] = self.aws_profile

            # Build command based on server type
            if server == 'cost-explorer':
                cmd = ['python', '-m', 'awslabs.cost_explorer_mcp_server']
            elif server == 'billing-cost-management':
                cmd = ['python', '-m', 'awslabs.billing_cost_management_mcp_server']
            elif server == 'pricing':
                cmd = ['python', '-m', 'awslabs.aws_pricing_mcp_server']
            else:
                raise ValueError(f"Unknown server: {server}")

            # For now, we'll use the MCP servers as Python libraries directly
            # This is a placeholder for the actual MCP implementation
            logger.warning(f"MCP command execution is a placeholder: {server}/{tool}")

            return {'error': 'MCP direct execution not yet implemented', 'status': 'placeholder'}

        except Exception as e:
            logger.error(f"Error executing MCP command: {e}")
            return {'error': str(e)}

    # ===== Cost Explorer MCP Tools =====

    def get_cost_and_usage(
        self,
        start_date: str,
        end_date: str,
        granularity: str = 'DAILY',
        metrics: List[str] = None,
        group_by: List[Dict[str, str]] = None,
        filter_dict: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get cost and usage data from AWS Cost Explorer

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            granularity: DAILY, MONTHLY, or HOURLY
            metrics: List of metrics (e.g., ['UnblendedCost', 'UsageQuantity'])
            group_by: Group by dimensions (e.g., [{'Type': 'DIMENSION', 'Key': 'SERVICE'}])
            filter_dict: Cost Explorer filter expression

        Returns:
            Cost and usage data
        """
        try:
            # Use boto3 Cost Explorer directly for now
            import boto3

            ce = boto3.client('ce', region_name='us-east-1')

            params = {
                'TimePeriod': {
                    'Start': start_date,
                    'End': end_date
                },
                'Granularity': granularity,
                'Metrics': metrics or ['UnblendedCost']
            }

            if group_by:
                params['GroupBy'] = group_by

            if filter_dict:
                params['Filter'] = filter_dict

            response = ce.get_cost_and_usage(**params)

            return {
                'success': True,
                'data': response.get('ResultsByTime', []),
                'total': response.get('Total', {})
            }

        except Exception as e:
            logger.error(f"Error getting cost and usage: {e}")
            return {'success': False, 'error': str(e)}

    def get_cost_forecast(
        self,
        start_date: str,
        end_date: str,
        metric: str = 'UNBLENDED_COST',
        granularity: str = 'MONTHLY'
    ) -> Dict[str, Any]:
        """
        Get cost forecast from AWS Cost Explorer

        Args:
            start_date: Forecast start date (YYYY-MM-DD)
            end_date: Forecast end date (YYYY-MM-DD)
            metric: UNBLENDED_COST, BLENDED_COST, etc.
            granularity: DAILY or MONTHLY

        Returns:
            Cost forecast data
        """
        try:
            import boto3

            ce = boto3.client('ce', region_name='us-east-1')

            response = ce.get_cost_forecast(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Metric=metric,
                Granularity=granularity
            )

            return {
                'success': True,
                'total': response.get('Total', {}),
                'forecast': response.get('ForecastResultsByTime', [])
            }

        except Exception as e:
            logger.error(f"Error getting cost forecast: {e}")
            return {'success': False, 'error': str(e)}

    def get_dimension_values(
        self,
        dimension: str,
        start_date: str,
        end_date: str,
        search_string: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get available values for a Cost Explorer dimension

        Args:
            dimension: Dimension name (SERVICE, REGION, LINKED_ACCOUNT, etc.)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            search_string: Optional search filter

        Returns:
            List of dimension values
        """
        try:
            import boto3

            ce = boto3.client('ce', region_name='us-east-1')

            params = {
                'TimePeriod': {
                    'Start': start_date,
                    'End': end_date
                },
                'Dimension': dimension
            }

            if search_string:
                params['SearchString'] = search_string

            response = ce.get_dimension_values(**params)

            return {
                'success': True,
                'dimension': dimension,
                'values': response.get('DimensionValues', [])
            }

        except Exception as e:
            logger.error(f"Error getting dimension values: {e}")
            return {'success': False, 'error': str(e)}

    def get_anomalies(
        self,
        start_date: str,
        end_date: str,
        monitor_arn: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get cost anomalies detected by AWS Cost Anomaly Detection

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            monitor_arn: Optional specific monitor ARN

        Returns:
            List of detected anomalies
        """
        try:
            import boto3

            ce = boto3.client('ce', region_name='us-east-1')

            params = {
                'DateInterval': {
                    'StartDate': start_date,
                    'EndDate': end_date
                }
            }

            if monitor_arn:
                params['MonitorArn'] = monitor_arn

            response = ce.get_anomalies(**params)

            return {
                'success': True,
                'anomalies': response.get('Anomalies', []),
                'count': len(response.get('Anomalies', []))
            }

        except Exception as e:
            logger.error(f"Error getting anomalies: {e}")
            return {'success': False, 'error': str(e)}

    # ===== Compute Optimizer Tools =====

    def get_ec2_recommendations(self) -> Dict[str, Any]:
        """
        Get EC2 instance recommendations from AWS Compute Optimizer

        Returns:
            EC2 rightsizing recommendations
        """
        try:
            import boto3

            co = boto3.client('compute-optimizer', region_name='us-east-1')

            response = co.get_ec2_instance_recommendations()

            recommendations = response.get('instanceRecommendations', [])

            # Calculate potential savings
            total_savings = 0
            for rec in recommendations:
                current_cost = rec.get('currentInstanceType', {})
                for option in rec.get('recommendationOptions', []):
                    savings = option.get('estimatedMonthlySavings', {}).get('value', 0)
                    if savings > 0:
                        total_savings += savings
                        break

            return {
                'success': True,
                'recommendations': recommendations,
                'count': len(recommendations),
                'potential_savings': round(total_savings, 2)
            }

        except Exception as e:
            logger.error(f"Error getting EC2 recommendations: {e}")
            return {'success': False, 'error': str(e)}

    def get_lambda_recommendations(self) -> Dict[str, Any]:
        """
        Get Lambda function recommendations from AWS Compute Optimizer

        Returns:
            Lambda rightsizing recommendations
        """
        try:
            import boto3

            co = boto3.client('compute-optimizer', region_name='us-east-1')

            response = co.get_lambda_function_recommendations()

            recommendations = response.get('lambdaFunctionRecommendations', [])

            return {
                'success': True,
                'recommendations': recommendations,
                'count': len(recommendations)
            }

        except Exception as e:
            logger.error(f"Error getting Lambda recommendations: {e}")
            return {'success': False, 'error': str(e)}

    # ===== Budgets Tools =====

    def get_budgets(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get AWS Budgets for the account

        Args:
            account_id: AWS account ID (defaults to current account)

        Returns:
            List of budgets
        """
        try:
            import boto3

            if not account_id:
                sts = boto3.client('sts')
                account_id = sts.get_caller_identity()['Account']

            budgets = boto3.client('budgets', region_name='us-east-1')

            response = budgets.describe_budgets(AccountId=account_id)

            return {
                'success': True,
                'budgets': response.get('Budgets', []),
                'count': len(response.get('Budgets', []))
            }

        except Exception as e:
            logger.error(f"Error getting budgets: {e}")
            return {'success': False, 'error': str(e)}

    # ===== Pricing Tools =====

    def get_service_pricing(
        self,
        service_code: str,
        filters: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get AWS service pricing information

        Args:
            service_code: AWS service code (e.g., 'AmazonEC2')
            filters: Pricing filters

        Returns:
            Pricing information
        """
        try:
            import boto3

            pricing = boto3.client('pricing', region_name='us-east-1')

            params = {
                'ServiceCode': service_code,
                'MaxResults': 100
            }

            if filters:
                params['Filters'] = filters

            response = pricing.get_products(**params)

            return {
                'success': True,
                'service_code': service_code,
                'products': response.get('PriceList', [])
            }

        except Exception as e:
            logger.error(f"Error getting service pricing: {e}")
            return {'success': False, 'error': str(e)}


# Singleton instance
mcp_client = AWSMCPClient()
