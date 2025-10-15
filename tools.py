"""
Tool definitions for the FinOps Agent
"""

AVAILABLE_TOOLS = [
    {
        "name": "query_cur_data",
        "description": """PRIMARY TOOL: Execute SQL query against AWS Cost and Usage Report (CUR) data in Athena. This provides the most detailed, accurate cost data at resource level. Use this for ALL cost analysis queries.

CRITICAL COLUMN NAMING RULES:
- ALL column names use forward slashes (/) and MUST be quoted
- Wrong: lineitem_unblendedcost, product_productname
- Correct: "lineitem/unblendedcost", "product/productname"

TAGS COLUMN:
- Tags stored in `raw_tags` as JSON (no prefix on keys)
- Simple keys (alphanumeric): json_extract_scalar(raw_tags, '$.TagKey')
- Keys with hyphens/colons: json_extract(raw_tags, '$["tag-key"]')
- json_extract returns quoted strings - compare with '"value"' (includes quotes)
- Example simple: WHERE json_extract_scalar(raw_tags, '$.Environment') = 'production'
- Example hyphen: WHERE json_extract(raw_tags, '$["goog-k8s-cluster-name"]') = '"gke123"'
- Example colon: WHERE json_extract(raw_tags, '$["aws:eks:cluster-name"]') = '"dataplatform"'

Examples:
- Basic: SELECT "product/productname", ROUND(SUM("lineitem/unblendedcost"), 2) as cost FROM raw_aws_amnic WHERE "lineitem/usagestartdate" >= DATE('2024-09-01') GROUP BY "product/productname" ORDER BY cost DESC LIMIT 10
- Tags (simple): SELECT json_extract_scalar(raw_tags, '$.Environment') as env, SUM("lineitem/unblendedcost") as cost FROM raw_aws_amnic WHERE json_extract_scalar(raw_tags, '$.Environment') IS NOT NULL GROUP BY env ORDER BY cost DESC
- Tags (hyphen): SELECT json_extract(raw_tags, '$["goog-k8s-cluster-name"]') as cluster, SUM("lineitem/unblendedcost") as cost FROM raw_aws_amnic WHERE json_extract(raw_tags, '$["goog-k8s-cluster-name"]') IS NOT NULL GROUP BY cluster""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": 'SQL query to execute against the CUR table. MUST use double quotes around ALL column names with slashes like "lineitem/unblendedcost", "product/productname", etc.'
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_cost_by_service",
        "description": "SECONDARY: Use Cost Explorer API to get costs grouped by service. ONLY use this if: (1) you need forecasting, (2) CUR query fails, or (3) user explicitly asks for Cost Explorer data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                "granularity": {
                    "type": "string",
                    "enum": ["DAILY", "MONTHLY", "HOURLY"],
                    "description": "Time granularity"
                }
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "get_cost_by_tag",
        "description": "Analyze costs grouped by a specific tag using Cost Explorer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tag_key": {"type": "string", "description": "Tag key to group by"},
                "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                "granularity": {
                    "type": "string",
                    "enum": ["DAILY", "MONTHLY"],
                    "description": "Time granularity"
                }
            },
            "required": ["tag_key", "start_date", "end_date"]
        }
    },
    {
        "name": "analyze_cost_anomalies",
        "description": "Detect cost anomalies using AWS Cost Anomaly Detection.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                "max_results": {"type": "number", "description": "Maximum anomalies to return"}
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "get_untagged_resources",
        "description": "Find resources missing required tags using CUR data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "required_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of required tag keys"
                },
                "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "End date YYYY-MM-DD"}
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "get_ri_sp_coverage",
        "description": "Analyze Reserved Instance and Savings Plans coverage.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                "granularity": {
                    "type": "string",
                    "enum": ["DAILY", "MONTHLY"],
                    "description": "Time granularity"
                }
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "get_ec2_utilization",
        "description": "Get EC2 instance utilization metrics from CloudWatch (CPU, Network). Use this to analyze actual resource usage and identify underutilized instances.",
        "input_schema": {
            "type": "object",
            "properties": {
                "instance_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of EC2 instance IDs to analyze"
                },
                "start_time": {"type": "string", "description": "Start time in ISO format"},
                "end_time": {"type": "string", "description": "End time in ISO format"}
            },
            "required": ["instance_ids", "start_time", "end_time"]
        }
    },
    {
        "name": "correlate_cost_utilization",
        "description": "Correlate EC2 costs with utilization metrics to identify optimization opportunities. Combines CUR cost data with CloudWatch metrics to provide rightsizing recommendations and potential savings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "instance_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of EC2 instance IDs to analyze"
                },
                "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "End date YYYY-MM-DD"}
            },
            "required": ["instance_ids", "start_date", "end_date"]
        }
    },
    {
        "name": "get_resource_utilization",
        "description": "Get CloudWatch metrics for any AWS resource (RDS, ELB, Lambda, etc.). Useful for analyzing utilization patterns across different services.",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {
                    "type": "string",
                    "description": "CloudWatch namespace (e.g., AWS/EC2, AWS/RDS, AWS/Lambda)"
                },
                "metric_name": {
                    "type": "string",
                    "description": "Metric name (e.g., CPUUtilization, DatabaseConnections)"
                },
                "dimensions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": "string"}
                        }
                    },
                    "description": "Dimensions to filter (e.g., [{'name': 'InstanceId', 'value': 'i-123'}])"
                },
                "start_time": {"type": "string", "description": "Start time in ISO format"},
                "end_time": {"type": "string", "description": "End time in ISO format"},
                "period": {"type": "number", "description": "Period in seconds (default: 3600)"}
            },
            "required": ["metric_name", "start_time", "end_time"]
        }
    },
    {
        "name": "get_multi_resource_metrics",
        "description": "Get comprehensive CloudWatch metrics for multiple resources of the same service type. Automatically retrieves all relevant metrics for RDS, Lambda, EBS, ELB, ALB, S3, DynamoDB, or ElastiCache. Use this to efficiently analyze utilization across multiple resources and correlate with costs. This is the PRIMARY tool for analyzing non-EC2 service utilization.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_type": {
                    "type": "string",
                    "enum": ["rds", "lambda", "ebs", "elb", "alb", "s3", "dynamodb", "elasticache"],
                    "description": "Type of AWS service. Supported: rds (RDS databases), lambda (Lambda functions), ebs (EBS volumes), elb (Classic Load Balancers), alb (Application Load Balancers), s3 (S3 buckets), dynamodb (DynamoDB tables), elasticache (ElastiCache clusters)"
                },
                "resource_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of resource identifiers. Format depends on service: RDS=DBInstanceIdentifier, Lambda=FunctionName, EBS=VolumeId, ELB=LoadBalancerName, ALB=LoadBalancer ARN, S3=BucketName, DynamoDB=TableName, ElastiCache=CacheClusterId"
                },
                "start_time": {
                    "type": "string",
                    "description": "Start time in ISO format (e.g., 2024-01-01T00:00:00Z)"
                },
                "end_time": {
                    "type": "string",
                    "description": "End time in ISO format (e.g., 2024-01-31T23:59:59Z)"
                }
            },
            "required": ["service_type", "resource_ids", "start_time", "end_time"]
        }
    },
    {
        "name": "execute_code",
        "description": "Execute custom Python or JavaScript/Node.js code for advanced analysis, data transformation, or custom workflows. The code has access to AWS SDK (pre-configured with credentials), file system, and can save results to workspace/data/. Use this for: complex calculations, custom data processing, generating reports, API integrations, or any analytical work that needs custom code.",
        "input_schema": {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "enum": ["python", "javascript", "nodejs"],
                    "description": "Programming language (python or javascript/nodejs)"
                },
                "code": {
                    "type": "string",
                    "description": "Code to execute. For Node.js, AWS SDK is pre-imported and configured. Use console.log() for output."
                },
                "description": {
                    "type": "string",
                    "description": "Brief description of what this code does"
                }
            },
            "required": ["language", "code"]
        }
    },
    {
        "name": "save_workflow",
        "description": "Save a code workflow for future reuse. Workflows are custom analysis scripts that can be executed later. Examples: monthly cost report generator, optimization checker, custom alert logic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Workflow name (e.g., 'Monthly Cost Report')"},
                "description": {"type": "string", "description": "What this workflow does"},
                "code": {"type": "string", "description": "The code to save"},
                "language": {
                    "type": "string",
                    "enum": ["python", "javascript", "nodejs"],
                    "description": "Programming language"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for categorization (e.g., ['reporting', 'ec2', 'optimization'])"
                }
            },
            "required": ["name", "description", "code", "language"]
        }
    },
    {
        "name": "list_workflows",
        "description": "List all saved workflows. Returns workflow names, descriptions, and metadata.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "load_workflow",
        "description": "Load a saved workflow by filename to view or execute it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Workflow filename (from list_workflows)"}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "create_kpi",
        "description": "Create a new KPI (Key Performance Indicator) and add it to the dashboard. KPIs can query CUR data via Athena SQL or use Cost Explorer APIs. Use this when users want to track specific metrics on the dashboard. For tag-based KPIs, use json_extract_scalar(raw_tags, '$.TagKey') to access tags from the raw_tags JSON column.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Display name (e.g., 'S3 Monthly Cost')"},
                "description": {"type": "string", "description": "What this KPI measures"},
                "query_type": {
                    "type": "string",
                    "enum": ["cur", "cost_explorer"],
                    "description": "Query type: 'cur' for Athena SQL queries or 'cost_explorer' for API calls"
                },
                "query": {
                    "type": "string",
                    "description": "For cur: SQL query with {table} placeholder. For cost_explorer: API method name (get_ri_coverage, get_anomalies_count). Must use double quotes for CUR columns like \"lineitem/unblendedcost\". For tag filters, use json_extract_scalar(raw_tags, '$.resourceTags/TagKey') = 'value'"
                },
                "format": {
                    "type": "string",
                    "enum": ["currency", "number", "percentage", "text"],
                    "description": "Display format for the value"
                },
                "icon": {"type": "string", "description": "Emoji icon (e.g., 💰, 📊, 🎯)"},
                "color": {"type": "string", "description": "Hex color (e.g., #a826b3, #33ccff)"},
                "size": {
                    "type": "string",
                    "enum": ["small", "medium", "large"],
                    "description": "Card size on dashboard"
                },
                "refresh_interval": {"type": "number", "description": "Auto-refresh interval in seconds (default: 3600)"}
            },
            "required": ["name", "description", "query_type", "query", "format"]
        }
    },
    {
        "name": "list_kpis",
        "description": "List all KPIs on the dashboard with their current values and metadata.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "update_kpi",
        "description": "Update an existing KPI's configuration (name, query, format, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "kpi_id": {"type": "string", "description": "KPI identifier"},
                "updates": {
                    "type": "object",
                    "description": "Fields to update (name, description, query, format, icon, color, size, refresh_interval)"
                }
            },
            "required": ["kpi_id", "updates"]
        }
    },
    {
        "name": "delete_kpi",
        "description": "Remove a KPI from the dashboard.",
        "input_schema": {
            "type": "object",
            "properties": {
                "kpi_id": {"type": "string", "description": "KPI identifier to delete"}
            },
            "required": ["kpi_id"]
        }
    },
    {
        "name": "refresh_kpi",
        "description": "Manually refresh a KPI to get the latest value.",
        "input_schema": {
            "type": "object",
            "properties": {
                "kpi_id": {"type": "string", "description": "KPI identifier to refresh"}
            },
            "required": ["kpi_id"]
        }
    },
    {
        "name": "create_visualization",
        "description": "Create interactive charts and visualizations from query results. Use this to visualize cost data, trends, comparisons, and distributions. Supports bar charts, line charts, pie charts, area charts, and more. Charts are saved as HTML files and can be viewed in the web UI.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Chart title"},
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "line", "pie", "area", "scatter", "stacked_bar", "grouped_bar", "donut", "treemap"],
                    "description": "Type of chart to create. Use 'grouped_bar' or 'stacked_bar' for comparing multiple series side-by-side or stacked."
                },
                "data": {
                    "type": "object",
                    "description": """Chart data format depends on chart type:
- Simple charts (bar, line, area, scatter): {x: [labels], y: [values]}
- Pie/donut charts: {labels: [...], values: [...]}
- Grouped/stacked bar charts: {x: [labels], y: {'Series 1': [values], 'Series 2': [values], ...}}
- Treemap: {labels: [...], values: [...], parents: [...]}

IMPORTANT for grouped_bar and stacked_bar: The 'y' field MUST be a dictionary where each key is a series name and each value is an array of numbers."""
                },
                "x_label": {"type": "string", "description": "X-axis label (optional)"},
                "y_label": {"type": "string", "description": "Y-axis label (optional)"},
                "description": {"type": "string", "description": "Description of what this chart shows"},
                "color_scheme": {
                    "type": "string",
                    "enum": ["default", "blues", "reds", "greens", "purples", "viridis", "plasma", "financial"],
                    "description": "Color scheme for the chart. 'financial' is optimized for cost data (green=profit, red=loss, blue=neutral)"
                }
            },
            "required": ["title", "chart_type", "data"]
        }
    },
    {
        "name": "get_cost_forecast",
        "description": """Get AWS cost forecast using AWS Cost Explorer. Predicts future costs based on historical usage patterns.

Use this tool when users ask about:
- Future cost predictions
- Next month's estimated costs
- Budget planning for upcoming periods
- Cost projections

Example queries:
- "What will my costs be next month?"
- "Forecast AWS spending for the next 3 months"
- "Predict costs for Q1 2026"

Note: Forecast is based on historical data and current trends. Actual costs may vary.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Forecast start date (YYYY-MM-DD). Must be in the future."
                },
                "end_date": {
                    "type": "string",
                    "description": "Forecast end date (YYYY-MM-DD)"
                },
                "metric": {
                    "type": "string",
                    "enum": ["UNBLENDED_COST", "BLENDED_COST", "AMORTIZED_COST"],
                    "description": "Cost metric to forecast"
                },
                "granularity": {
                    "type": "string",
                    "enum": ["DAILY", "MONTHLY"],
                    "description": "Forecast granularity"
                }
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "get_cost_anomalies",
        "description": """Detect and retrieve cost anomalies using AWS Cost Anomaly Detection. Identifies unusual spending patterns.

Use this tool when users ask about:
- Unexpected cost spikes
- Unusual spending patterns
- Cost anomalies or outliers
- Recent billing surprises

Returns:
- List of detected anomalies
- Anomaly details (impact, root cause, service)
- Time period of anomalies

Example queries:
- "Show me any cost anomalies this month"
- "Were there any unusual charges recently?"
- "Detect spending anomalies in the last 30 days"

Note: Requires AWS Cost Anomaly Detection to be enabled.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Search start date (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "Search end date (YYYY-MM-DD)"
                },
                "monitor_arn": {
                    "type": "string",
                    "description": "Optional specific anomaly monitor ARN"
                }
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "get_rightsizing_recommendations",
        "description": """Get EC2 and Lambda rightsizing recommendations from AWS Compute Optimizer. Identifies over-provisioned resources.

Use this tool when users ask about:
- Rightsizing opportunities
- Over-provisioned instances
- Cost optimization recommendations
- Instance type recommendations
- Potential cost savings

Returns:
- EC2 instance recommendations (instance type, size changes)
- Lambda function recommendations (memory optimization)
- Estimated monthly savings
- Current vs recommended configurations

Example queries:
- "Show me rightsizing opportunities"
- "What EC2 instances can I optimize?"
- "How much can I save by rightsizing?"
- "Give me cost optimization recommendations"

Note: Requires AWS Compute Optimizer to be enabled and have at least 30 days of data.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "resource_type": {
                    "type": "string",
                    "enum": ["ec2", "lambda", "all"],
                    "description": "Type of resources to get recommendations for"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_budgets_status",
        "description": """Get AWS Budgets and their current status. Shows budget limits, actual spend, and forecasted spend.

Use this tool when users ask about:
- Budget status and tracking
- Budget alerts and thresholds
- How much of the budget is used
- Budget forecasts

Returns:
- List of budgets
- Budget amounts and limits
- Actual vs budgeted amounts
- Forecast vs budget comparison
- Alert status

Example queries:
- "Show me my AWS budgets"
- "Am I over budget this month?"
- "What's the status of my budgets?"
- "How much budget do I have left?"

Note: Returns budgets configured in AWS Budgets service.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "string",
                    "description": "AWS account ID (defaults to current account)"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_dimension_values",
        "description": """Get available values for a Cost Explorer dimension. Useful for filtering and grouping cost data.

Use this tool when users ask about:
- Available services in their account
- Regions being used
- Linked accounts
- Available resource tags
- Instance types in use

Supported dimensions:
- SERVICE: AWS services being used
- REGION: AWS regions
- LINKED_ACCOUNT: AWS accounts in organization
- INSTANCE_TYPE: EC2 instance types
- USAGE_TYPE: Detailed usage types
- OPERATION: API operations
- And more...

Example queries:
- "What AWS services am I using?"
- "List all regions where I have resources"
- "Show me all linked accounts"
- "What EC2 instance types are running?"

Note: This helps discover filterable dimensions for detailed cost analysis.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "dimension": {
                    "type": "string",
                    "enum": ["SERVICE", "REGION", "LINKED_ACCOUNT", "INSTANCE_TYPE", "USAGE_TYPE", "OPERATION", "AVAILABILITY_ZONE", "PLATFORM", "TENANCY"],
                    "description": "Dimension to get values for"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date (YYYY-MM-DD)"
                },
                "search_string": {
                    "type": "string",
                    "description": "Optional search filter for dimension values"
                }
            },
            "required": ["dimension", "start_date", "end_date"]
        }
    }
]
