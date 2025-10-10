#!/usr/bin/env python3
"""
FinOps Analyst Agent - Python Version
AI-powered FinOps analyst for AWS cloud cost optimization
"""

import os
import sys
import json
import time
import subprocess
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

import boto3
from anthropic import Anthropic
from dotenv import load_dotenv
from colorama import Fore, Style, init as colorama_init

# Initialize colorama for colored output
colorama_init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('finops-agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize paths
SCRIPT_DIR = Path(__file__).parent
WORKSPACE_DIR = SCRIPT_DIR.parent / "workspace"
SCRIPTS_DIR = WORKSPACE_DIR / "scripts"
WORKFLOWS_DIR = WORKSPACE_DIR / "workflows"
DATA_DIR = WORKSPACE_DIR / "data"

# Ensure directories exist
for directory in [WORKSPACE_DIR, SCRIPTS_DIR, WORKFLOWS_DIR, DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'ap-south-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# Initialize AWS clients
boto3.setup_default_session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

athena = boto3.client('athena', region_name=AWS_REGION)
cost_explorer = boto3.client('ce', region_name='us-east-1')  # Cost Explorer only in us-east-1
budgets = boto3.client('budgets', region_name='us-east-1')
cloudwatch = boto3.client('cloudwatch', region_name=AWS_REGION)
ec2 = boto3.client('ec2', region_name=AWS_REGION)

# Initialize Anthropic client
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Configuration
config = {
    'curDatabase': os.getenv('CUR_DATABASE_NAME'),
    'curTable': os.getenv('CUR_TABLE_NAME'),
    'athenaOutputLocation': os.getenv('ATHENA_OUTPUT_LOCATION'),
}

# Load CUR schema
CUR_SCHEMA = None
try:
    schema_path = SCRIPT_DIR.parent / 'cur-schema.json'
    with open(schema_path, 'r') as f:
        CUR_SCHEMA = json.load(f)
    print(f"{Fore.LIGHTBLACK_EX}Loaded CUR schema: {CUR_SCHEMA['totalColumns']} columns")
except FileNotFoundError:
    print(f"{Fore.YELLOW}Warning: Could not load cur-schema.json. Run 'node get-cur-schema.cjs' first.")

print(f"{Fore.LIGHTBLACK_EX}Initializing AWS SDK with region: {AWS_REGION}")

# Conversation history storage
conversation_history: List[Dict[str, str]] = []


def execute_athena_query(query: str) -> Dict[str, Any]:
    """Execute Athena query and return results"""
    logger.info("=" * 80)
    logger.info("EXECUTING ATHENA QUERY")
    logger.debug(f"Query: {query}")
    logger.debug(f"Database: {config['curDatabase']}")
    logger.debug(f"Output Location: {config['athenaOutputLocation']}")
    logger.debug(f"Region: {AWS_REGION}")

    print(f"{Fore.LIGHTBLACK_EX}\n📝 Executing Athena Query:")
    print(f"{Fore.LIGHTBLACK_EX}{query[:200]}{'...' if len(query) > 200 else ''}")
    print(f"{Fore.LIGHTBLACK_EX}Database: {config['curDatabase']}")
    print(f"{Fore.LIGHTBLACK_EX}Output: {config['athenaOutputLocation']}")
    print(f"{Fore.LIGHTBLACK_EX}Region: {AWS_REGION}")

    try:
        logger.debug("Starting Athena query execution...")
        # Start query execution
        response = athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': config['curDatabase']},
            ResultConfiguration={'OutputLocation': config['athenaOutputLocation']}
        )

        query_execution_id = response['QueryExecutionId']
        logger.info(f"Query started with ID: {query_execution_id}")
        print(f"{Fore.LIGHTBLACK_EX}Query ID: {query_execution_id}")

        # Wait for query to complete
        max_attempts = 60
        attempts = 0
        logger.debug(f"Polling for query completion (max {max_attempts} attempts)...")
        while attempts < max_attempts:
            attempts += 1
            status_response = athena.get_query_execution(QueryExecutionId=query_execution_id)
            status = status_response['QueryExecution']['Status']['State']
            logger.debug(f"Attempt {attempts}/{max_attempts}: Query status = {status}")

            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break

            time.sleep(1)

        if status != 'SUCCEEDED':
            reason = status_response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown')
            logger.error(f"Query {status}: {reason}")
            logger.error(f"Full status response: {json.dumps(status_response, indent=2, default=str)}")
            raise Exception(f"Query {status}: {reason}")

        # Get results
        logger.debug("Fetching query results...")
        results_response = athena.get_query_results(QueryExecutionId=query_execution_id)

        # Parse results
        columns = [col['Name'] for col in results_response['ResultSet']['ResultSetMetadata']['ColumnInfo']]
        logger.debug(f"Result columns: {columns}")
        rows = []

        for row in results_response['ResultSet']['Rows'][1:]:  # Skip header row
            row_data = {}
            for i, col in enumerate(columns):
                value = row['Data'][i].get('VarCharValue', '')
                row_data[col] = value
            rows.append(row_data)

        logger.info(f"Query completed successfully - {len(rows)} rows returned")
        logger.debug(f"First 3 rows: {json.dumps(rows[:3], indent=2)}")
        print(f"{Fore.GREEN}✓ Query returned {len(rows)} rows")

        return {
            'columns': columns,
            'data': rows,
            'rowCount': len(rows)
        }

    except Exception as error:
        logger.error(f"Athena query failed: {str(error)}", exc_info=True)
        print(f"{Fore.RED}✗ Athena query failed: {str(error)}")
        raise


def handle_tool_call(tool_name: str, tool_input: Dict[str, Any]) -> Any:
    """Handle tool calls from Claude"""
    logger.info("=" * 80)
    logger.info(f"TOOL CALL: {tool_name}")
    logger.debug(f"Tool input: {json.dumps(tool_input, indent=2, default=str)}")

    if tool_name == 'query_cur_data':
        logger.info("Executing CUR data query via Athena")
        return execute_athena_query(tool_input['query'])

    elif tool_name == 'get_cost_by_service':
        print(f"{Fore.LIGHTBLACK_EX}📊 Fetching costs by service from Cost Explorer...")

        response = cost_explorer.get_cost_and_usage(
            TimePeriod={
                'Start': tool_input['start_date'],
                'End': tool_input['end_date']
            },
            Granularity=tool_input.get('granularity', 'MONTHLY'),
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )

        print(f"{Fore.GREEN}✓ Retrieved cost data")
        return response

    elif tool_name == 'get_cost_by_tag':
        print(f"{Fore.LIGHTBLACK_EX}🏷️  Fetching costs by tag...")

        response = cost_explorer.get_cost_and_usage(
            TimePeriod={
                'Start': tool_input['start_date'],
                'End': tool_input['end_date']
            },
            Granularity=tool_input.get('granularity', 'MONTHLY'),
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'TAG', 'Key': tool_input['tag_key']}]
        )

        return response

    elif tool_name == 'get_cost_forecast':
        logger.info("Generating cost forecast")
        print(f"{Fore.LIGHTBLACK_EX}🔮 Generating cost forecast...")

        # Get today's date
        today = datetime.now().date()
        logger.debug(f"Today's date: {today}")

        # Parse input dates
        try:
            start_date = datetime.strptime(tool_input['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(tool_input['end_date'], '%Y-%m-%d').date()
            logger.debug(f"Parsed dates - Start: {start_date}, End: {end_date}")
        except:
            from datetime import date
            start_date = date.fromisoformat(tool_input['start_date'])
            end_date = date.fromisoformat(tool_input['end_date'])
            logger.debug(f"ISO parsed dates - Start: {start_date}, End: {end_date}")

        # AWS Cost Explorer forecast requirements:
        # - Start date must be today or in the future
        # - Maximum forecast period is 12 months

        # Adjust start date if it's in the past
        if start_date < today:
            logger.warning(f"Adjusting forecast start from {start_date} to {today}")
            print(f"{Fore.YELLOW}⚠️  Adjusting forecast start from {start_date} to {today}")
            start_date = today

        # Ensure reasonable forecast period (max 12 months)
        max_end_date = start_date + timedelta(days=365)
        if end_date > max_end_date:
            logger.warning(f"Adjusting forecast end from {end_date} to {max_end_date} (12 month limit)")
            print(f"{Fore.YELLOW}⚠️  Adjusting forecast end from {end_date} to {max_end_date}")
            end_date = max_end_date

        # Ensure minimum forecast period (at least 1 day ahead)
        if end_date <= start_date:
            end_date = start_date + timedelta(days=30)
            logger.warning(f"Adjusted end date to {end_date} (30 days ahead)")
            print(f"{Fore.YELLOW}⚠️  Adjusted end date to {end_date} (30 days ahead)")

        logger.info(f"Final forecast period: {start_date} to {end_date}")
        print(f"{Fore.LIGHTBLACK_EX}  Forecast: {start_date} to {end_date}")

        try:
            logger.debug("Calling Cost Explorer get_cost_forecast API...")
            response = cost_explorer.get_cost_forecast(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Metric='UNBLENDED_COST',
                Granularity=tool_input.get('granularity', 'MONTHLY')
            )
            logger.info("Forecast generated successfully")
            logger.debug(f"Forecast response: {json.dumps(response, indent=2, default=str)}")
            print(f"{Fore.GREEN}✓ Forecast generated")
            return response
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Forecast API error: {error_msg}", exc_info=True)
            print(f"{Fore.RED}✗ Forecast error: {error_msg}")
            return {
                'error': 'Cost Explorer forecast unavailable',
                'message': f'Could not generate forecast for {start_date} to {end_date}. AWS Cost Explorer may not have sufficient data or the period is outside supported range. Consider using historical CUR data to estimate future costs based on trends.',
                'details': error_msg
            }

    elif tool_name == 'analyze_cost_anomalies':
        logger.info("Analyzing cost anomalies")
        print(f"{Fore.LIGHTBLACK_EX}🔍 Analyzing cost anomalies...")

        # Get today's date
        today = datetime.now().date()
        logger.debug(f"Today's date: {today}")

        # Parse input dates
        try:
            start_date = datetime.strptime(tool_input['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(tool_input['end_date'], '%Y-%m-%d').date()
            logger.debug(f"Parsed dates - Start: {start_date}, End: {end_date}")
        except:
            from datetime import date
            start_date = date.fromisoformat(tool_input['start_date'])
            end_date = date.fromisoformat(tool_input['end_date'])
            logger.debug(f"ISO parsed dates - Start: {start_date}, End: {end_date}")

        # AWS Cost Anomaly Detection requirements:
        # - Can only query recent anomalies (last 90 days typically)
        # - End date should not be in the future

        # Adjust end date if it's in the future
        if end_date > today:
            logger.warning(f"Adjusting anomaly end date from {end_date} to {today}")
            print(f"{Fore.YELLOW}⚠️  Adjusting anomaly end date from {end_date} to {today}")
            end_date = today

        # Adjust start date if the range is too far back
        # AWS typically keeps anomaly data for last 90 days
        earliest_supported = today - timedelta(days=90)
        if start_date < earliest_supported:
            logger.warning(f"Adjusting anomaly start date from {start_date} to {earliest_supported} (90 day limit)")
            print(f"{Fore.YELLOW}⚠️  Adjusting anomaly start date from {start_date} to {earliest_supported}")
            start_date = earliest_supported

        # Ensure start is before end
        if start_date >= end_date:
            start_date = end_date - timedelta(days=30)
            logger.warning(f"Adjusted start date to {start_date} (30 days before end)")
            print(f"{Fore.YELLOW}⚠️  Adjusted start date to {start_date} (30 days before end)")

        logger.info(f"Final anomaly period: {start_date} to {end_date}")
        print(f"{Fore.LIGHTBLACK_EX}  Anomaly period: {start_date} to {end_date}")

        try:
            logger.debug("Calling Cost Explorer get_anomalies API...")
            response = cost_explorer.get_anomalies(
                DateInterval={
                    'StartDate': start_date.strftime('%Y-%m-%d'),
                    'EndDate': end_date.strftime('%Y-%m-%d')
                },
                MaxResults=tool_input.get('max_results', 50)
            )
            anomaly_count = len(response.get('Anomalies', []))
            logger.info(f"Found {anomaly_count} anomalies")
            logger.debug(f"Anomaly response: {json.dumps(response, indent=2, default=str)[:1000]}...")
            print(f"{Fore.GREEN}✓ Found {anomaly_count} anomalies")
            return response
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Anomaly detection API error: {error_msg}", exc_info=True)
            print(f"{Fore.RED}✗ Anomaly detection error: {error_msg}")
            return {
                'error': 'Cost Anomaly Detection unavailable',
                'message': f'Could not analyze anomalies for {start_date} to {end_date}. AWS Cost Anomaly Detection requires recent data (typically last 90 days). Consider using CUR data to identify unusual cost spikes manually.',
                'details': error_msg
            }

    elif tool_name == 'get_untagged_resources':
        print(f"{Fore.LIGHTBLACK_EX}🔍 Finding untagged resources...")

        required_tags = tool_input.get('required_tags', [])
        query = f"""
        SELECT
          "lineitem/resourceid" as resource_id,
          "product/productname" as service,
          ROUND(SUM("lineitem/unblendedcost"), 2) as cost
        FROM {config['curTable']}
        WHERE "lineitem/resourceid" != ''
          AND "lineitem/usagestartdate" >= DATE('{tool_input['start_date']}')
          AND "lineitem/usagestartdate" < DATE('{tool_input['end_date']}')
        GROUP BY "lineitem/resourceid", "product/productname"
        HAVING SUM("lineitem/unblendedcost") > 0
        ORDER BY cost DESC
        LIMIT 100
        """

        return execute_athena_query(query)

    elif tool_name == 'get_ri_sp_coverage':
        print(f"{Fore.LIGHTBLACK_EX}📊 Analyzing RI/SP coverage...")

        ri_coverage = cost_explorer.get_reservation_coverage(
            TimePeriod={
                'Start': tool_input['start_date'],
                'End': tool_input['end_date']
            },
            Granularity=tool_input.get('granularity', 'MONTHLY')
        )

        sp_coverage = cost_explorer.get_savings_plans_coverage(
            TimePeriod={
                'Start': tool_input['start_date'],
                'End': tool_input['end_date']
            },
            Granularity=tool_input.get('granularity', 'MONTHLY')
        )

        return {
            'reservedInstanceCoverage': ri_coverage,
            'savingsPlansCoverage': sp_coverage
        }

    elif tool_name == 'get_ec2_utilization':
        print(f"{Fore.LIGHTBLACK_EX}📊 Fetching EC2 utilization from CloudWatch...")
        instance_ids = tool_input['instance_ids']
        start_time = datetime.fromisoformat(tool_input['start_time'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(tool_input['end_time'].replace('Z', '+00:00'))

        # Ensure we're using UTC times
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        duration_days = (end_time - start_time).total_seconds() / (24 * 3600)

        # Adjust period based on duration (CloudWatch requirements)
        if duration_days > 15:
            period = 3600  # 1 hour (required for > 15 days)
        elif duration_days > 1:
            period = 300   # 5 minutes (basic monitoring)
        else:
            period = 60    # 1 minute (detailed monitoring if enabled)

        print(f"{Fore.LIGHTBLACK_EX}Duration: {duration_days:.1f} days, Period: {period}s")

        # Check instance state first
        try:
            instances_response = ec2.describe_instances(InstanceIds=instance_ids)
            instance_states = {}
            for reservation in instances_response['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    instance_states[instance_id] = {
                        'state': instance['State']['Name'],
                        'monitoring': instance['Monitoring']['State'],
                        'instance_type': instance['InstanceType']
                    }
                    print(f"{Fore.LIGHTBLACK_EX}  {instance_id}: {instance['State']['Name']}, Monitoring: {instance['Monitoring']['State']}")
        except Exception as e:
            print(f"{Fore.YELLOW}  ⚠️  Could not check instance states: {e}")
            instance_states = {}

        metrics = ['CPUUtilization', 'NetworkIn', 'NetworkOut']
        results = {}

        for instance_id in instance_ids:
            results[instance_id] = {}

            # Add instance state info
            if instance_id in instance_states:
                results[instance_id]['instance_info'] = instance_states[instance_id]

            # If instance is stopped, skip metrics query
            if instance_id in instance_states and instance_states[instance_id]['state'] == 'stopped':
                print(f"{Fore.YELLOW}  ⚠️  {instance_id} is stopped, skipping metrics")
                for metric_name in metrics:
                    results[instance_id][metric_name] = {
                        'datapoints': 0,
                        'average': None,
                        'maximum': None,
                        'minimum': None,
                        'note': 'Instance is stopped - no metrics available'
                    }
                continue

            for metric_name in metrics:
                try:
                    response = cloudwatch.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName=metric_name,
                        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=period,
                        Statistics=['Average', 'Maximum', 'Minimum']
                    )

                    datapoints = response['Datapoints']
                    print(f"{Fore.LIGHTBLACK_EX}  {metric_name}: {len(datapoints)} datapoints")

                    if len(datapoints) == 0:
                        # Try to diagnose why no data
                        diagnostic_msg = 'No data available'

                        # Check if detailed monitoring is needed
                        if period == 60 and instance_id in instance_states:
                            if instance_states[instance_id]['monitoring'] == 'disabled':
                                diagnostic_msg = 'Detailed monitoring (1-min) disabled. Enable detailed monitoring or use longer time range.'

                        # Check if time range is too recent
                        time_since_end = (datetime.now(timezone.utc) - end_time).total_seconds() / 60
                        if time_since_end < 5:
                            diagnostic_msg += ' Metrics may have 5-15 min delay.'

                        print(f"{Fore.YELLOW}  ⚠️  No {metric_name} data for {instance_id}: {diagnostic_msg}")
                        results[instance_id][metric_name] = {
                            'datapoints': 0,
                            'average': None,
                            'maximum': None,
                            'minimum': None,
                            'note': diagnostic_msg
                        }
                    else:
                        average = sum(dp['Average'] for dp in datapoints) / len(datapoints)
                        maximum = max(dp['Maximum'] for dp in datapoints)
                        minimum = min(dp['Minimum'] for dp in datapoints)

                        results[instance_id][metric_name] = {
                            'datapoints': len(datapoints),
                            'average': average,
                            'maximum': maximum,
                            'minimum': minimum
                        }

                        unit = '%' if metric_name == 'CPUUtilization' else 'bytes'
                        print(f"{Fore.LIGHTBLACK_EX}  ✓ {instance_id} {metric_name}: avg {average:.2f}{unit}")

                except Exception as error:
                    print(f"{Fore.RED}  ✗ Failed to get {metric_name} for {instance_id}: {str(error)}")
                    results[instance_id][metric_name] = {'error': str(error)}

        print(f"{Fore.GREEN}✓ Fetched utilization for {len(instance_ids)} instances")
        return results

    elif tool_name == 'correlate_cost_utilization':
        print(f"{Fore.LIGHTBLACK_EX}🔗 Correlating costs with utilization...")

        # Get instance costs from CUR
        instance_ids_str = "','".join(tool_input['instance_ids'])
        cost_query = f"""
        SELECT
          "lineitem/resourceid" as instance_id,
          ROUND(SUM("lineitem/unblendedcost"), 2) as total_cost,
          COUNT(*) as hours
        FROM {config['curTable']}
        WHERE "lineitem/resourceid" IN ('{instance_ids_str}')
          AND "lineitem/usagestartdate" >= DATE('{tool_input['start_date']}')
          AND "lineitem/usagestartdate" < DATE('{tool_input['end_date']}')
          AND "lineitem/productcode" = 'AmazonEC2'
        GROUP BY "lineitem/resourceid"
        """

        try:
            cost_data_result = execute_athena_query(cost_query)
            cost_data = {row['instance_id']: {'cost': float(row['total_cost']), 'hours': int(row['hours'])}
                        for row in cost_data_result['data']}
        except Exception as error:
            print(f"{Fore.YELLOW}⚠ CUR query failed, using Cost Explorer estimates")
            cost_data = {}

        # Get utilization data
        utilization_data = handle_tool_call('get_ec2_utilization', {
            'instance_ids': tool_input['instance_ids'],
            'start_time': f"{tool_input['start_date']}T00:00:00Z",
            'end_time': f"{tool_input['end_date']}T23:59:59Z"
        })

        # Combine and analyze
        analysis = []
        for instance_id in tool_input['instance_ids']:
            cost = cost_data.get(instance_id, {}).get('cost', 0)
            util = utilization_data.get(instance_id, {})

            if not util or 'CPUUtilization' not in util:
                print(f"{Fore.YELLOW}  ⚠️  No utilization data for {instance_id}")
                analysis.append({
                    'instanceId': instance_id,
                    'cost': cost,
                    'avgCpu': None,
                    'maxCpu': None,
                    'recommendation': 'No metrics available - instance may be stopped',
                    'potentialSavings': '0.00',
                    'datapoints': 0
                })
                continue

            cpu_util = util['CPUUtilization']

            if cpu_util.get('error'):
                print(f"{Fore.YELLOW}  ⚠️  Error getting metrics for {instance_id}: {cpu_util['error']}")
                analysis.append({
                    'instanceId': instance_id,
                    'cost': cost,
                    'avgCpu': None,
                    'maxCpu': None,
                    'recommendation': f"Error: {cpu_util['error']}",
                    'potentialSavings': '0.00',
                    'datapoints': 0
                })
                continue

            if cpu_util['average'] is None or cpu_util['datapoints'] == 0:
                print(f"{Fore.YELLOW}  ⚠️  No CPU datapoints for {instance_id}")
                analysis.append({
                    'instanceId': instance_id,
                    'cost': cost,
                    'avgCpu': None,
                    'maxCpu': None,
                    'recommendation': 'No data - instance stopped or just started',
                    'potentialSavings': '0.00',
                    'datapoints': 0
                })
                continue

            avg_cpu = cpu_util['average']
            max_cpu = cpu_util['maximum']
            datapoints = cpu_util['datapoints']

            recommendation = 'Appropriately sized'
            potential_savings = 0

            if avg_cpu < 20 and max_cpu < 40:
                recommendation = 'Underutilized - consider downsizing'
                potential_savings = cost * 0.5
            elif avg_cpu < 40 and max_cpu < 60:
                recommendation = 'Low utilization - review workload'
                potential_savings = cost * 0.25
            elif avg_cpu > 80:
                recommendation = 'High utilization - may need upsize'
                potential_savings = 0

            print(f"{Fore.LIGHTBLACK_EX}  ✓ {instance_id}: CPU {avg_cpu:.1f}% avg, {max_cpu:.1f}% max - {recommendation}")

            analysis.append({
                'instanceId': instance_id,
                'cost': cost,
                'avgCpu': f"{avg_cpu:.2f}",
                'maxCpu': f"{max_cpu:.2f}",
                'datapoints': datapoints,
                'recommendation': recommendation,
                'potentialSavings': f"{potential_savings:.2f}"
            })

        print(f"{Fore.GREEN}✓ Analyzed {len(analysis)} instances")
        total_savings = sum(float(a['potentialSavings']) for a in analysis)

        return {
            'analysis': analysis,
            'totalPotentialSavings': f"{total_savings:.2f}",
            'summary': f"Analyzed {len(analysis)} instances. Total potential savings: ${total_savings:.2f}"
        }

    elif tool_name == 'get_resource_utilization':
        logger.info("Fetching resource utilization metrics")
        print(f"{Fore.LIGHTBLACK_EX}📊 Fetching resource utilization...")

        namespace = tool_input.get('namespace', 'AWS/EC2')
        metric_name = tool_input['metric_name']
        dimensions = tool_input.get('dimensions', [])
        start_time = datetime.fromisoformat(tool_input['start_time'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(tool_input['end_time'].replace('Z', '+00:00'))
        period = tool_input.get('period', 3600)

        logger.debug(f"Namespace: {namespace}, Metric: {metric_name}")
        logger.debug(f"Dimensions: {dimensions}")
        logger.debug(f"Time range: {start_time} to {end_time}, Period: {period}s")

        response = cloudwatch.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=[{'Name': d['name'], 'Value': d['value']} for d in dimensions],
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=['Average', 'Maximum', 'Minimum', 'Sum']
        )

        datapoints = response['Datapoints']
        datapoints.sort(key=lambda x: x['Timestamp'])

        result = {
            'metric': metric_name,
            'namespace': namespace,
            'datapoints': len(datapoints),
            'statistics': {
                'average': sum(dp.get('Average', 0) for dp in datapoints) / len(datapoints) if datapoints else 0,
                'maximum': max((dp.get('Maximum', 0) for dp in datapoints), default=0),
                'minimum': min((dp.get('Minimum', 0) for dp in datapoints), default=0)
            },
            'datapointsData': datapoints
        }

        logger.info(f"Retrieved {len(datapoints)} datapoints for {metric_name}")
        print(f"{Fore.GREEN}✓ Retrieved {len(datapoints)} datapoints")
        return result

    elif tool_name == 'get_multi_resource_metrics':
        logger.info("Fetching metrics for multiple resources")
        print(f"{Fore.LIGHTBLACK_EX}📊 Fetching multi-resource metrics...")

        service_type = tool_input['service_type']
        resource_ids = tool_input['resource_ids']
        start_time = datetime.fromisoformat(tool_input['start_time'].replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(tool_input['end_time'].replace('Z', '+00:00'))

        logger.debug(f"Service: {service_type}, Resources: {len(resource_ids)}")

        # Service-specific metric configurations
        service_configs = {
            'rds': {
                'namespace': 'AWS/RDS',
                'dimension_name': 'DBInstanceIdentifier',
                'metrics': ['CPUUtilization', 'DatabaseConnections', 'FreeableMemory', 'ReadIOPS', 'WriteIOPS', 'ReadLatency', 'WriteLatency']
            },
            'lambda': {
                'namespace': 'AWS/Lambda',
                'dimension_name': 'FunctionName',
                'metrics': ['Invocations', 'Duration', 'Errors', 'Throttles', 'ConcurrentExecutions']
            },
            'ebs': {
                'namespace': 'AWS/EBS',
                'dimension_name': 'VolumeId',
                'metrics': ['VolumeReadBytes', 'VolumeWriteBytes', 'VolumeReadOps', 'VolumeWriteOps', 'VolumeThroughputPercentage', 'VolumeIdleTime']
            },
            'elb': {
                'namespace': 'AWS/ELB',
                'dimension_name': 'LoadBalancerName',
                'metrics': ['RequestCount', 'HealthyHostCount', 'UnHealthyHostCount', 'Latency', 'HTTPCode_Backend_2XX', 'HTTPCode_Backend_5XX']
            },
            'alb': {
                'namespace': 'AWS/ApplicationELB',
                'dimension_name': 'LoadBalancer',
                'metrics': ['RequestCount', 'TargetResponseTime', 'ActiveConnectionCount', 'HTTPCode_Target_2XX_Count', 'HTTPCode_Target_5XX_Count']
            },
            's3': {
                'namespace': 'AWS/S3',
                'dimension_name': 'BucketName',
                'metrics': ['BucketSizeBytes', 'NumberOfObjects']
            },
            'dynamodb': {
                'namespace': 'AWS/DynamoDB',
                'dimension_name': 'TableName',
                'metrics': ['ConsumedReadCapacityUnits', 'ConsumedWriteCapacityUnits', 'UserErrors', 'SystemErrors', 'ThrottledRequests']
            },
            'elasticache': {
                'namespace': 'AWS/ElastiCache',
                'dimension_name': 'CacheClusterId',
                'metrics': ['CPUUtilization', 'NetworkBytesIn', 'NetworkBytesOut', 'CurrConnections', 'Evictions', 'CacheHits', 'CacheMisses']
            }
        }

        if service_type not in service_configs:
            logger.error(f"Unsupported service type: {service_type}")
            raise Exception(f"Unsupported service_type: {service_type}. Supported: {list(service_configs.keys())}")

        config = service_configs[service_type]
        logger.info(f"Using config for {service_type}: {config['namespace']}")

        # Determine period based on time range
        duration_days = (end_time - start_time).total_seconds() / (24 * 3600)
        if duration_days > 15:
            period = 3600  # 1 hour
        elif duration_days > 1:
            period = 300   # 5 minutes
        else:
            period = 60    # 1 minute

        logger.debug(f"Duration: {duration_days:.1f} days, Period: {period}s")

        results = {}
        for resource_id in resource_ids:
            logger.debug(f"Fetching metrics for {resource_id}")
            results[resource_id] = {}

            for metric_name in config['metrics']:
                try:
                    response = cloudwatch.get_metric_statistics(
                        Namespace=config['namespace'],
                        MetricName=metric_name,
                        Dimensions=[{'Name': config['dimension_name'], 'Value': resource_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=period,
                        Statistics=['Average', 'Maximum', 'Minimum', 'Sum']
                    )

                    datapoints = response['Datapoints']

                    if len(datapoints) > 0:
                        results[resource_id][metric_name] = {
                            'datapoints': len(datapoints),
                            'average': sum(dp.get('Average', 0) for dp in datapoints) / len(datapoints),
                            'maximum': max((dp.get('Maximum', 0) for dp in datapoints), default=0),
                            'minimum': min((dp.get('Minimum', 0) for dp in datapoints), default=0),
                            'sum': sum(dp.get('Sum', 0) for dp in datapoints)
                        }
                        logger.debug(f"  {metric_name}: {len(datapoints)} datapoints")
                    else:
                        results[resource_id][metric_name] = {
                            'datapoints': 0,
                            'note': 'No data available'
                        }
                        logger.warning(f"  {metric_name}: No data")

                except Exception as error:
                    logger.error(f"Error fetching {metric_name} for {resource_id}: {error}")
                    results[resource_id][metric_name] = {'error': str(error)}

        logger.info(f"Fetched metrics for {len(resource_ids)} {service_type} resources")
        print(f"{Fore.GREEN}✓ Fetched metrics for {len(resource_ids)} {service_type} resources")

        return {
            'service_type': service_type,
            'resource_count': len(resource_ids),
            'metrics': results,
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            }
        }

    elif tool_name == 'execute_code':
        print(f"{Fore.LIGHTBLACK_EX}💻 Executing {tool_input['language']} code...")

        timestamp = int(time.time() * 1000)
        language = tool_input['language']

        if language == 'python':
            script_path = SCRIPTS_DIR / f"script_{timestamp}.py"
            script_path.write_text(tool_input['code'])
            command = f"python3 {script_path}"

        elif language in ['javascript', 'nodejs']:
            script_path = SCRIPTS_DIR / f"script_{timestamp}.cjs"

            # Add AWS SDK imports
            code_with_imports = f"""
// Auto-imported modules
const AWS = require('aws-sdk');
const fs = require('fs');
const path = require('path');

// Configure AWS
AWS.config.update({{
  region: '{AWS_REGION}',
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
}});

// User code
{tool_input['code']}
"""
            script_path.write_text(code_with_imports)
            command = f"node {script_path}"

        else:
            raise Exception(f"Unsupported language: {language}")

        print(f"{Fore.LIGHTBLACK_EX}Script saved: {script_path}")
        print(f"{Fore.LIGHTBLACK_EX}Executing: {command}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(WORKSPACE_DIR),
                env=os.environ.copy()
            )

            print(f"{Fore.GREEN}✓ Code executed successfully")

            if result.stdout:
                print(f"{Fore.LIGHTBLACK_EX}Output:\n{result.stdout[:500]}")
            if result.stderr:
                print(f"{Fore.YELLOW}Warnings:\n{result.stderr[:500]}")

            return {
                'success': True,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'scriptPath': str(script_path)
            }

        except subprocess.TimeoutExpired:
            print(f"{Fore.RED}✗ Code execution timed out")
            return {
                'success': False,
                'error': 'Execution timed out (30s limit)',
                'scriptPath': str(script_path)
            }
        except Exception as error:
            print(f"{Fore.RED}✗ Code execution failed: {str(error)}")
            return {
                'success': False,
                'error': str(error),
                'scriptPath': str(script_path)
            }

    elif tool_name == 'save_workflow':
        print(f"{Fore.LIGHTBLACK_EX}💾 Saving workflow: {tool_input['name']}")

        workflow = {
            'name': tool_input['name'],
            'description': tool_input['description'],
            'code': tool_input['code'],
            'language': tool_input['language'],
            'createdAt': datetime.now().isoformat(),
            'tags': tool_input.get('tags', [])
        }

        filename = tool_input['name'].lower().replace(' ', '_').replace('-', '_')
        filename = ''.join(c for c in filename if c.isalnum() or c == '_') + '.json'
        filepath = WORKFLOWS_DIR / filename

        with open(filepath, 'w') as f:
            json.dump(workflow, f, indent=2)

        print(f"{Fore.GREEN}✓ Workflow saved: {filepath}")

        return {
            'success': True,
            'filepath': str(filepath),
            'filename': filename
        }

    elif tool_name == 'list_workflows':
        if not WORKFLOWS_DIR.exists():
            return {'workflows': []}

        workflow_files = list(WORKFLOWS_DIR.glob('*.json'))
        workflows = []

        for filepath in workflow_files:
            try:
                with open(filepath, 'r') as f:
                    workflow = json.load(f)
                workflows.append({
                    'filename': filepath.name,
                    'name': workflow['name'],
                    'description': workflow['description'],
                    'language': workflow['language'],
                    'createdAt': workflow['createdAt'],
                    'tags': workflow.get('tags', [])
                })
            except Exception:
                continue

        print(f"{Fore.GREEN}✓ Found {len(workflows)} workflows")
        return {'workflows': workflows}

    elif tool_name == 'load_workflow':
        filepath = WORKFLOWS_DIR / tool_input['filename']

        if not filepath.exists():
            raise Exception(f"Workflow not found: {tool_input['filename']}")

        with open(filepath, 'r') as f:
            workflow = json.load(f)

        print(f"{Fore.GREEN}✓ Loaded workflow: {workflow['name']}")
        return workflow

    elif tool_name == 'create_kpi':
        from kpi_manager import KPIManager
        kpi_manager = KPIManager()

        logger.info(f"Creating KPI: {tool_input['name']}")

        # Generate KPI ID from name
        kpi_id = tool_input['name'].lower().replace(' ', '_').replace('-', '_')

        # Build KPI object
        kpi_data = {
            'id': kpi_id,
            'name': tool_input['name'],
            'description': tool_input['description'],
            'query_type': tool_input['query_type'],
            'query': tool_input['query'],
            'format': tool_input['format'],
            'icon': tool_input.get('icon', '📊'),
            'color': tool_input.get('color', '#a826b3'),
            'size': tool_input.get('size', 'medium'),
            'refresh_interval': tool_input.get('refresh_interval', 3600),
            'last_updated': None,
            'last_value': None,
            'trend': None
        }

        kpi_manager.create_kpi(kpi_data)
        logger.info(f"KPI created successfully: {kpi_id}")
        print(f"{Fore.GREEN}✓ Created KPI: {tool_input['name']} (ID: {kpi_id})")
        print(f"{Fore.LIGHTBLACK_EX}  View it at: http://localhost:8000/api/dashboard")

        # Notify dashboard about new KPI (will be picked up by broadcast mechanism)
        return {
            'kpi_id': kpi_id,
            'message': f"KPI '{tool_input['name']}' created successfully and added to dashboard",
            'dashboard_url': 'http://localhost:8000/api/dashboard',
            'action': 'kpi_created'  # Signal for dashboard refresh
        }

    elif tool_name == 'list_kpis':
        from kpi_manager import KPIManager
        kpi_manager = KPIManager()
        kpis = kpi_manager.list_kpis()

        print(f"{Fore.GREEN}✓ Found {len(kpis)} KPIs")
        for kpi in kpis:
            status = f"${kpi['last_value']}" if kpi['last_value'] and kpi['format'] == 'currency' else kpi['last_value']
            print(f"{Fore.LIGHTBLACK_EX}  {kpi['icon']} {kpi['name']} ({kpi['id']}): {status}")

        return {'kpis': kpis, 'count': len(kpis)}

    elif tool_name == 'update_kpi':
        from kpi_manager import KPIManager
        kpi_manager = KPIManager()

        kpi_id = tool_input['kpi_id']
        updates = tool_input['updates']

        kpi_manager.update_kpi(kpi_id, updates)
        print(f"{Fore.GREEN}✓ Updated KPI: {kpi_id}")

        return {
            'kpi_id': kpi_id,
            'message': f"KPI '{kpi_id}' updated successfully",
            'updates': updates
        }

    elif tool_name == 'delete_kpi':
        from kpi_manager import KPIManager
        kpi_manager = KPIManager()

        kpi_id = tool_input['kpi_id']
        kpi_manager.delete_kpi(kpi_id)
        print(f"{Fore.GREEN}✓ Deleted KPI: {kpi_id}")

        return {
            'kpi_id': kpi_id,
            'message': f"KPI '{kpi_id}' deleted successfully"
        }

    elif tool_name == 'refresh_kpi':
        from kpi_manager import KPIManager
        import requests

        kpi_id = tool_input['kpi_id']

        # Call the web server API to refresh the KPI
        try:
            response = requests.post(f'http://localhost:8000/api/kpis/{kpi_id}/refresh', timeout=60)
            response.raise_for_status()
            result = response.json()

            print(f"{Fore.GREEN}✓ Refreshed KPI: {kpi_id}")
            print(f"{Fore.LIGHTBLACK_EX}  Value: {result.get('value')}")
            print(f"{Fore.LIGHTBLACK_EX}  Updated: {result.get('updated')}")

            return result
        except requests.exceptions.ConnectionError:
            return {
                'error': 'Web server not running. Start it with: python3 web_server.py',
                'kpi_id': kpi_id
            }
        except Exception as e:
            return {
                'error': str(e),
                'kpi_id': kpi_id
            }

    elif tool_name == 'create_visualization':
        import plotly.graph_objects as go
        from datetime import datetime as dt_now

        logger.info("Creating visualization")
        title = tool_input['title']
        chart_type = tool_input['chart_type']
        data = tool_input['data']
        x_label = tool_input.get('x_label', '')
        y_label = tool_input.get('y_label', '')
        description = tool_input.get('description', '')
        color_scheme = tool_input.get('color_scheme', 'default')

        logger.debug(f"Chart type: {chart_type}, Title: {title}")
        logger.debug(f"Data structure: {json.dumps(data, indent=2, default=str)[:500]}")

        # Color schemes - using qualitative (categorical) colors for better visibility
        color_maps = {
            'default': ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52'],
            'blues': ['#4472C4', '#5B9BD5', '#70AD47', '#FFC000', '#ED7D31'],
            'reds': ['#C5504B', '#E15759', '#F28E2B', '#E74C3C', '#D35400'],
            'greens': ['#70AD47', '#4CAF50', '#2ECC71', '#27AE60', '#16A085'],
            'purples': ['#9966FF', '#B565D8', '#8B5CF6', '#A855F7', '#9333EA'],
            'viridis': ['#440154', '#31688E', '#35B779', '#FDE724', '#21908C'],
            'plasma': ['#0D0887', '#7E03A8', '#CC4678', '#F89540', '#F0F921'],
            'financial': ['#2E7D32', '#C62828', '#1565C0', '#F57C00', '#6A1B9A']
        }
        colors = color_maps.get(color_scheme, color_maps['default'])

        fig = None

        if chart_type == 'bar':
            logger.debug("Creating bar chart")
            fig = go.Figure(data=[go.Bar(x=data.get('x', []), y=data.get('y', []), marker_color=colors[0])])

        elif chart_type == 'grouped_bar':
            logger.debug("Creating grouped_bar chart")
            # Multiple bar series
            fig = go.Figure()
            y_data = data.get('y', [])
            logger.debug(f"y_data type: {type(y_data)}, is_dict: {isinstance(y_data, dict)}")

            if isinstance(y_data, dict):
                logger.debug(f"y_data keys: {list(y_data.keys())}")
                for i, (name, values) in enumerate(y_data.items()):
                    logger.debug(f"Adding trace {i}: {name} with {len(values) if isinstance(values, list) else 'non-list'} values")
                    fig.add_trace(go.Bar(name=name, x=data.get('x', []), y=values, marker_color=colors[i % len(colors)]))
                fig.update_layout(barmode='group')
                logger.info(f"Grouped bar chart created with {len(y_data)} series")
            else:
                logger.error(f"grouped_bar requires y as dict, got {type(y_data)}")
                raise Exception(f"grouped_bar chart requires 'y' data to be a dictionary with multiple series. Got {type(y_data).__name__} instead. Example: {{'y': {{'Series 1': [1,2,3], 'Series 2': [4,5,6]}}}}")

        elif chart_type == 'stacked_bar':
            logger.debug("Creating stacked_bar chart")
            fig = go.Figure()
            y_data = data.get('y', [])
            logger.debug(f"y_data type: {type(y_data)}, is_dict: {isinstance(y_data, dict)}")

            if isinstance(y_data, dict):
                logger.debug(f"y_data keys: {list(y_data.keys())}")
                for i, (name, values) in enumerate(y_data.items()):
                    logger.debug(f"Adding trace {i}: {name} with {len(values) if isinstance(values, list) else 'non-list'} values")
                    fig.add_trace(go.Bar(name=name, x=data.get('x', []), y=values, marker_color=colors[i % len(colors)]))
                fig.update_layout(barmode='stack')
                logger.info(f"Stacked bar chart created with {len(y_data)} series")
            else:
                logger.error(f"stacked_bar requires y as dict, got {type(y_data)}")
                raise Exception(f"stacked_bar chart requires 'y' data to be a dictionary with multiple series. Got {type(y_data).__name__} instead. Example: {{'y': {{'Series 1': [1,2,3], 'Series 2': [4,5,6]}}}}")

        elif chart_type == 'line':
            fig = go.Figure(data=[go.Scatter(x=data.get('x', []), y=data.get('y', []), mode='lines+markers', line=dict(color=colors[0], width=3))])

        elif chart_type == 'area':
            fig = go.Figure(data=[go.Scatter(x=data.get('x', []), y=data.get('y', []), fill='tozeroy', line=dict(color=colors[0]))])

        elif chart_type in ['pie', 'donut']:
            hole = 0.4 if chart_type == 'donut' else 0
            fig = go.Figure(data=[go.Pie(labels=data.get('labels', []), values=data.get('values', []), hole=hole, marker=dict(colors=colors))])

        elif chart_type == 'scatter':
            fig = go.Figure(data=[go.Scatter(x=data.get('x', []), y=data.get('y', []), mode='markers', marker=dict(size=10, color=colors[0]))])

        elif chart_type == 'treemap':
            fig = go.Figure(go.Treemap(
                labels=data.get('labels', []),
                parents=data.get('parents', [''] * len(data.get('labels', []))),
                values=data.get('values', []),
                marker=dict(
                    colors=colors,
                    colorscale='Viridis'
                )
            ))

        if fig:
            # Update layout
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

            # Save to workspace
            chart_filename = f"chart_{dt_now.now().strftime('%Y%m%d_%H%M%S')}.html"
            chart_path = WORKSPACE_DIR / "charts" / chart_filename
            chart_path.parent.mkdir(parents=True, exist_ok=True)

            fig.write_html(str(chart_path))

            print(f"{Fore.GREEN}✓ Created {chart_type} chart: {title}")
            print(f"{Fore.LIGHTBLACK_EX}  Saved to: {chart_path}")
            print(f"{Fore.LIGHTBLACK_EX}  View at: http://localhost:8000/charts/{chart_filename}")

            return {
                'chart_type': chart_type,
                'title': title,
                'description': description,
                'file_path': str(chart_path),
                'url': f'http://localhost:8000/charts/{chart_filename}',
                'filename': chart_filename
            }
        else:
            raise Exception(f"Failed to create chart of type: {chart_type}")

    else:
        raise Exception(f"Unknown tool: {tool_name}")


def get_finops_system_prompt() -> str:
    """Generate the FinOps system prompt"""
    today = datetime.now()

    common_columns_text = ""
    if CUR_SCHEMA:
        common_columns_text = f"""
COST COLUMNS:
{', '.join(CUR_SCHEMA['commonColumns']['cost'])}

TIME COLUMNS:
{', '.join(CUR_SCHEMA['commonColumns']['time'])}

SERVICE COLUMNS:
{', '.join(CUR_SCHEMA['commonColumns']['service'])}

RESOURCE COLUMNS:
{', '.join(CUR_SCHEMA['commonColumns']['resource'])}

USAGE COLUMNS:
{', '.join(CUR_SCHEMA['commonColumns']['usage'])}

ACCOUNT COLUMNS:
{', '.join(CUR_SCHEMA['commonColumns']['account'])}
"""
    else:
        common_columns_text = 'Schema not loaded. Common columns: "lineitem/unblendedcost", "lineitem/usagestartdate", "product/productname", "lineitem/resourceid"'

    return f"""You are an expert FinOps (Financial Operations) analyst with deep knowledge of cloud cost optimization, AWS billing, and financial management best practices.

# Current Date
Today is {today.strftime('%Y-%m-%d')} ({today.strftime('%B %Y')})

# Conversation Context
You maintain context across the conversation. You can reference previous queries, results, and analyses. When users ask follow-up questions like "show me more details" or "what about the others", use the conversation history to understand what they're referring to.

# Your Expertise
- Deep understanding of AWS Cost and Usage Reports (CUR)
- Expert in cost allocation, showback, and chargeback models
- Proficient in identifying cost optimization opportunities
- Knowledge of Reserved Instances, Savings Plans, and commitment-based discounts

# Available Tools
You have access to these tools for AWS cost analysis:

**PRIMARY TOOL (Use this for most queries):**
- query_cur_data: Execute SQL against CUR data in Athena for detailed, resource-level cost analysis. This is your PRIMARY tool - use it whenever possible for accurate, granular data.

**SECONDARY TOOLS (Use only when CUR query isn't suitable):**
- get_cost_by_service: Cost Explorer API - use ONLY for forecasting or when CUR is unavailable
- get_cost_by_tag: Analyze costs by tag via Cost Explorer
- get_untagged_resources: Find resources missing required tags (uses CUR)
- get_cost_forecast: Get AWS cost forecasts (Cost Explorer only)
- analyze_cost_anomalies: Detect unusual spending patterns
- get_ri_sp_coverage: Analyze RI/SP coverage

**UTILIZATION & OPTIMIZATION TOOLS:**
- get_ec2_utilization: Get EC2 instance utilization metrics from CloudWatch (CPU, Network)
- correlate_cost_utilization: Correlate EC2 costs with utilization for rightsizing recommendations
- get_multi_resource_metrics: **PRIMARY TOOL** for getting CloudWatch metrics for multiple RDS, Lambda, EBS, ELB, ALB, S3, DynamoDB, or ElastiCache resources. Automatically retrieves all relevant metrics for the service type.
- get_resource_utilization: Generic tool for any CloudWatch metric (use for custom metrics or services not covered by get_multi_resource_metrics)

**IMPORTANT - COST CORRELATION WORKFLOW:**
When analyzing costs for ANY service:
1. First, query CUR data to get resource IDs and costs
2. Then, use get_multi_resource_metrics (for supported services) or get_resource_utilization to fetch CloudWatch metrics
3. Correlate cost with utilization to identify optimization opportunities
4. Provide specific recommendations with estimated savings

Supported services for get_multi_resource_metrics:
- RDS: CPUUtilization, DatabaseConnections, FreeableMemory, ReadIOPS, WriteIOPS, Read/Write Latency
- Lambda: Invocations, Duration, Errors, Throttles, ConcurrentExecutions
- EBS: Read/Write Bytes/Ops, ThroughputPercentage, IdleTime
- ELB/ALB: RequestCount, HealthyHosts, Latency, HTTP response codes
- S3: BucketSizeBytes, NumberOfObjects
- DynamoDB: ConsumedCapacity, UserErrors, ThrottledRequests
- ElastiCache: CPUUtilization, Connections, Evictions, CacheHits/Misses

**CODE EXECUTION & WORKFLOW TOOLS:**
- execute_code: Execute custom Python or JavaScript/Node.js code for advanced analysis, data processing, or integrations
- save_workflow: Save reusable workflows for future use (e.g., monthly reports, optimization checks)
- list_workflows: View all saved workflows
- load_workflow: Load a saved workflow to view or execute

When to use code execution:
- Complex calculations beyond SQL capabilities
- Custom data transformations or aggregations
- Generating formatted reports (CSV, JSON, markdown)
- API integrations with external systems
- Custom alerting or notification logic
- Data visualization or chart generation
- Any analysis that benefits from procedural code

**VISUALIZATION TOOL:**
- create_visualization: Create interactive charts and visualizations from data

**IMPORTANT - AUTOMATIC VISUALIZATIONS:**
You MUST automatically create visualizations whenever you present data that would benefit from visual representation. DO NOT wait for users to ask for charts - proactively create them.

Create visualizations automatically for:
- Cost by service (bar/pie chart)
- Cost over time (line/area chart)
- Cost comparisons (grouped bar chart)
- Cost distribution (pie/donut/treemap chart)
- Resource utilization (line chart)
- Tag-based cost breakdown (bar/treemap chart)
- Top N costs (bar chart)
- Trends and forecasts (line/area chart)

Chart type selection guide:
- Bar: Best for comparing values across categories (services, accounts, regions)
- Line: Best for showing trends over time (daily/monthly costs)
- Pie/Donut: Best for showing parts of a whole (cost distribution)
- Area: Best for cumulative trends over time
- Treemap: Best for hierarchical data (nested cost breakdowns)
- Stacked/Grouped bar: Best for comparing multiple metrics across categories

After executing a query that returns data suitable for visualization:
1. Present the data in text/table format first
2. Immediately follow with create_visualization to generate an appropriate chart
3. Choose the most suitable chart type and color scheme
4. Include descriptive title and labels

# CUR Table Schema
Database: {config['curDatabase']}
Table: {config['curTable']}
Total Columns: {CUR_SCHEMA['totalColumns'] if CUR_SCHEMA else 'Unknown'}

**IMPORTANT: All column names use forward slashes (/) and MUST be quoted in SQL queries.**

Common columns by category:
{common_columns_text}

**TAGS COLUMN:**
- Tags are stored in the `raw_tags` column as a JSON object (no prefix on keys)
- For simple tag keys (alphanumeric): json_extract_scalar(raw_tags, '$.TagKey')
- For keys with hyphens/special chars: json_extract(raw_tags, '$["tag-key"]')
- json_extract returns quoted JSON strings, compare with '"value"' (includes quotes)
- Example simple: WHERE json_extract_scalar(raw_tags, '$.Environment') = 'production'
- Example with hyphens: WHERE json_extract(raw_tags, '$["goog-k8s-cluster-name"]') = '"gke123"'
- Example with colons: WHERE json_extract(raw_tags, '$["aws:eks:cluster-name"]') = '"dataplatform"'
- Common tags: Environment, Team, Project, goog-k8s-cluster-name, aws:eks:cluster-name

# Instructions
- **PREFER query_cur_data for all cost queries** - it has the most detailed, accurate data
- **CRITICAL**: Column names MUST use forward slashes and be quoted: "lineitem/unblendedcost" NOT lineitem_unblendedcost
- **TAGS**: Use `raw_tags` column. Use json_extract_scalar() for simple keys, json_extract() for keys with hyphens/colons (compare with '"value"')
- Example query: SELECT "product/productname", SUM("lineitem/unblendedcost") FROM {config['curTable']} WHERE "lineitem/usagestartdate" >= DATE('2024-01-01') GROUP BY "product/productname"
- Example tag query (simple): SELECT json_extract_scalar(raw_tags, '$.Environment') as env, SUM("lineitem/unblendedcost") as cost FROM {config['curTable']} WHERE json_extract_scalar(raw_tags, '$.Environment') IS NOT NULL GROUP BY env
- Example tag query (with hyphens): SELECT json_extract(raw_tags, '$["goog-k8s-cluster-name"]') as cluster FROM {config['curTable']} WHERE json_extract(raw_tags, '$["goog-k8s-cluster-name"]') = '"gke123"'
- Use get_cost_by_service ONLY when: (1) forecasting future costs, (2) CUR query fails
- When asked about "last month", calculate the previous calendar month based on today's date
- Use proper date ranges in YYYY-MM-DD format with DATE() function
- **For optimization questions**: Use correlate_cost_utilization to combine cost data with CloudWatch metrics for rightsizing recommendations
- When analyzing underutilized resources, always provide specific cost savings estimates
- Provide clear, actionable recommendations with specific numbers
- Explain trends and anomalies
- **VISUALIZATION REQUIREMENT**: Whenever you return data that can be visualized (costs, trends, comparisons), AUTOMATICALLY create a chart using create_visualization. Do this proactively without waiting for the user to ask."""


# Continue in next message due to length...
