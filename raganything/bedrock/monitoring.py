"""
Monitoring and logging enhancements for AWS Bedrock integration
"""

import json
import time
import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

from .config import BedrockConfig


@dataclass
class BedrockMetrics:
    """Metrics for Bedrock operations"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_used: int = 0
    total_cost_estimate: float = 0.0
    average_response_time: float = 0.0
    requests_by_model: Dict[str, int] = field(default_factory=dict)
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    response_times: List[float] = field(default_factory=list)
    
    def add_request(self, model_id: str, success: bool, response_time: float, 
                   tokens_used: int = 0, error_type: str = None):
        """Add a request to metrics"""
        self.total_requests += 1
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            if error_type:
                self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
        
        self.response_times.append(response_time)
        self.average_response_time = sum(self.response_times) / len(self.response_times)
        
        self.requests_by_model[model_id] = self.requests_by_model.get(model_id, 0) + 1
        self.total_tokens_used += tokens_used
        
        # Estimate cost (rough estimates based on public pricing)
        cost_per_token = self._get_cost_per_token(model_id)
        self.total_cost_estimate += tokens_used * cost_per_token
    
    def _get_cost_per_token(self, model_id: str) -> float:
        """Get estimated cost per token for model"""
        # Rough estimates - actual pricing may vary
        cost_map = {
            'anthropic.claude-3-5-sonnet-20241022-v2:0': 0.000003,  # $3 per 1M tokens
            'anthropic.claude-3-haiku-20240307-v1:0': 0.00000025,   # $0.25 per 1M tokens
            'amazon.titan-embed-text-v2:0': 0.0000002,              # $0.2 per 1M tokens
        }
        return cost_map.get(model_id, 0.000001)  # Default estimate
    
    def get_success_rate(self) -> float:
        """Get success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': self.get_success_rate(),
            'total_tokens_used': self.total_tokens_used,
            'estimated_cost_usd': self.total_cost_estimate,
            'average_response_time': self.average_response_time,
            'requests_by_model': self.requests_by_model,
            'errors_by_type': self.errors_by_type
        }


class BedrockLogger:
    """Enhanced logger for Bedrock operations"""
    
    def __init__(self, name: str = "bedrock", log_level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Create formatter with AWS request ID support
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(aws_request_id)s] - %(message)s',
            defaults={'aws_request_id': 'N/A'}
        )
        
        # Add console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def log_request(self, operation: str, model_id: str, request_data: Dict[str, Any],
                   aws_request_id: str = None):
        """Log Bedrock request"""
        extra = {'aws_request_id': aws_request_id or 'N/A'}
        
        self.logger.info(
            f"Bedrock {operation} request - Model: {model_id}, "
            f"Tokens: {request_data.get('max_tokens', 'N/A')}",
            extra=extra
        )
        
        # Log request details at debug level
        self.logger.debug(f"Request data: {json.dumps(request_data, indent=2)}", extra=extra)
    
    def log_response(self, operation: str, model_id: str, response_data: Dict[str, Any],
                    response_time: float, aws_request_id: str = None):
        """Log Bedrock response"""
        extra = {'aws_request_id': aws_request_id or 'N/A'}
        
        tokens_used = self._extract_token_usage(response_data)
        
        self.logger.info(
            f"Bedrock {operation} response - Model: {model_id}, "
            f"Time: {response_time:.2f}s, Tokens: {tokens_used}",
            extra=extra
        )
        
        # Log response details at debug level
        self.logger.debug(f"Response data: {json.dumps(response_data, indent=2)}", extra=extra)
    
    def log_error(self, operation: str, model_id: str, error: Exception,
                 aws_request_id: str = None):
        """Log Bedrock error"""
        extra = {'aws_request_id': aws_request_id or 'N/A'}
        
        error_type = type(error).__name__
        error_code = getattr(error, 'response', {}).get('Error', {}).get('Code', 'Unknown')
        
        self.logger.error(
            f"Bedrock {operation} error - Model: {model_id}, "
            f"Type: {error_type}, Code: {error_code}, Message: {str(error)}",
            extra=extra
        )
    
    def _extract_token_usage(self, response_data: Dict[str, Any]) -> int:
        """Extract token usage from response"""
        # Try different response formats
        usage = response_data.get('usage', {})
        if usage:
            return usage.get('total_tokens', 0)
        
        # For Claude responses
        if 'usage' in response_data:
            return response_data['usage'].get('input_tokens', 0) + response_data['usage'].get('output_tokens', 0)
        
        return 0


class BedrockMonitor:
    """Comprehensive monitoring for Bedrock operations"""
    
    def __init__(self, config: BedrockConfig):
        self.config = config
        self.metrics = BedrockMetrics()
        self.logger = BedrockLogger()
        self.cloudwatch = None
        self.start_time = time.time()
        
        # Initialize CloudWatch client if available
        try:
            self.cloudwatch = boto3.client('cloudwatch', region_name=config.aws_region)
        except Exception as e:
            self.logger.logger.warning(f"CloudWatch client initialization failed: {e}")
    
    async def record_request(self, operation: str, model_id: str, request_data: Dict[str, Any],
                           aws_request_id: str = None) -> str:
        """Record the start of a Bedrock request"""
        request_id = aws_request_id or f"req_{int(time.time() * 1000)}"
        
        self.logger.log_request(operation, model_id, request_data, request_id)
        
        return request_id
    
    async def record_response(self, operation: str, model_id: str, response_data: Dict[str, Any],
                            response_time: float, request_id: str = None):
        """Record a successful Bedrock response"""
        tokens_used = self._extract_token_usage(response_data)
        
        self.metrics.add_request(
            model_id=model_id,
            success=True,
            response_time=response_time,
            tokens_used=tokens_used
        )
        
        self.logger.log_response(operation, model_id, response_data, response_time, request_id)
        
        # Send metrics to CloudWatch
        await self._send_cloudwatch_metrics(operation, model_id, response_time, tokens_used, True)
    
    async def record_error(self, operation: str, model_id: str, error: Exception,
                          response_time: float, request_id: str = None):
        """Record a Bedrock error"""
        error_type = type(error).__name__
        
        self.metrics.add_request(
            model_id=model_id,
            success=False,
            response_time=response_time,
            error_type=error_type
        )
        
        self.logger.log_error(operation, model_id, error, request_id)
        
        # Send error metrics to CloudWatch
        await self._send_cloudwatch_metrics(operation, model_id, response_time, 0, False, error_type)
    
    async def _send_cloudwatch_metrics(self, operation: str, model_id: str, response_time: float,
                                     tokens_used: int, success: bool, error_type: str = None):
        """Send metrics to CloudWatch"""
        if not self.cloudwatch:
            return
        
        try:
            metric_data = []
            timestamp = datetime.utcnow()
            
            # Response time metric
            metric_data.append({
                'MetricName': 'ResponseTime',
                'Dimensions': [
                    {'Name': 'Operation', 'Value': operation},
                    {'Name': 'ModelId', 'Value': model_id}
                ],
                'Value': response_time,
                'Unit': 'Seconds',
                'Timestamp': timestamp
            })
            
            # Success/failure metric
            metric_data.append({
                'MetricName': 'RequestCount',
                'Dimensions': [
                    {'Name': 'Operation', 'Value': operation},
                    {'Name': 'ModelId', 'Value': model_id},
                    {'Name': 'Status', 'Value': 'Success' if success else 'Error'}
                ],
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': timestamp
            })
            
            # Token usage metric
            if tokens_used > 0:
                metric_data.append({
                    'MetricName': 'TokensUsed',
                    'Dimensions': [
                        {'Name': 'Operation', 'Value': operation},
                        {'Name': 'ModelId', 'Value': model_id}
                    ],
                    'Value': tokens_used,
                    'Unit': 'Count',
                    'Timestamp': timestamp
                })
            
            # Error type metric
            if error_type:
                metric_data.append({
                    'MetricName': 'ErrorCount',
                    'Dimensions': [
                        {'Name': 'Operation', 'Value': operation},
                        {'Name': 'ModelId', 'Value': model_id},
                        {'Name': 'ErrorType', 'Value': error_type}
                    ],
                    'Value': 1,
                    'Unit': 'Count',
                    'Timestamp': timestamp
                })
            
            # Send metrics in batches
            await asyncio.to_thread(
                self.cloudwatch.put_metric_data,
                Namespace='RAGAnything/Bedrock',
                MetricData=metric_data
            )
            
        except Exception as e:
            self.logger.logger.warning(f"Failed to send CloudWatch metrics: {e}")
    
    def _extract_token_usage(self, response_data: Dict[str, Any]) -> int:
        """Extract token usage from response"""
        return self.logger._extract_token_usage(response_data)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        summary = self.metrics.get_summary()
        
        # Add runtime information
        runtime = time.time() - self.start_time
        summary.update({
            'monitoring_runtime_seconds': runtime,
            'requests_per_minute': (self.metrics.total_requests / runtime) * 60 if runtime > 0 else 0,
            'average_cost_per_request': (
                self.metrics.total_cost_estimate / self.metrics.total_requests 
                if self.metrics.total_requests > 0 else 0
            )
        })
        
        return summary
    
    async def create_cloudwatch_dashboard(self, dashboard_name: str = "RAGAnything-Bedrock"):
        """Create CloudWatch dashboard for Bedrock metrics"""
        if not self.cloudwatch:
            self.logger.logger.warning("CloudWatch client not available for dashboard creation")
            return False
        
        try:
            dashboard_body = {
                "widgets": [
                    {
                        "type": "metric",
                        "x": 0,
                        "y": 0,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                ["RAGAnything/Bedrock", "ResponseTime", "Operation", "complete"],
                                [".", ".", ".", "embed"],
                                [".", ".", ".", "analyze_image"]
                            ],
                            "period": 300,
                            "stat": "Average",
                            "region": self.config.aws_region,
                            "title": "Average Response Time by Operation"
                        }
                    },
                    {
                        "type": "metric",
                        "x": 12,
                        "y": 0,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                ["RAGAnything/Bedrock", "RequestCount", "Status", "Success"],
                                [".", ".", ".", "Error"]
                            ],
                            "period": 300,
                            "stat": "Sum",
                            "region": self.config.aws_region,
                            "title": "Request Success/Error Count"
                        }
                    },
                    {
                        "type": "metric",
                        "x": 0,
                        "y": 6,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                ["RAGAnything/Bedrock", "TokensUsed", "ModelId", 
                                 "anthropic.claude-3-5-sonnet-20241022-v2:0"],
                                [".", ".", ".", "anthropic.claude-3-haiku-20240307-v1:0"],
                                [".", ".", ".", "amazon.titan-embed-text-v2:0"]
                            ],
                            "period": 300,
                            "stat": "Sum",
                            "region": self.config.aws_region,
                            "title": "Token Usage by Model"
                        }
                    },
                    {
                        "type": "metric",
                        "x": 12,
                        "y": 6,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                ["RAGAnything/Bedrock", "ErrorCount", "ErrorType", "ThrottlingException"],
                                [".", ".", ".", "ValidationException"],
                                [".", ".", ".", "AccessDeniedException"]
                            ],
                            "period": 300,
                            "stat": "Sum",
                            "region": self.config.aws_region,
                            "title": "Error Count by Type"
                        }
                    }
                ]
            }
            
            await asyncio.to_thread(
                self.cloudwatch.put_dashboard,
                DashboardName=dashboard_name,
                DashboardBody=json.dumps(dashboard_body)
            )
            
            self.logger.logger.info(f"CloudWatch dashboard '{dashboard_name}' created successfully")
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Failed to create CloudWatch dashboard: {e}")
            return False
    
    async def setup_cloudwatch_alarms(self):
        """Set up CloudWatch alarms for Bedrock monitoring"""
        if not self.cloudwatch:
            self.logger.logger.warning("CloudWatch client not available for alarm setup")
            return False
        
        alarms = [
            {
                'AlarmName': 'RAGAnything-Bedrock-HighErrorRate',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 2,
                'MetricName': 'RequestCount',
                'Namespace': 'RAGAnything/Bedrock',
                'Period': 300,
                'Statistic': 'Sum',
                'Threshold': 10.0,
                'ActionsEnabled': True,
                'AlarmDescription': 'High error rate in Bedrock requests',
                'Dimensions': [
                    {'Name': 'Status', 'Value': 'Error'}
                ],
                'Unit': 'Count'
            },
            {
                'AlarmName': 'RAGAnything-Bedrock-HighResponseTime',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 2,
                'MetricName': 'ResponseTime',
                'Namespace': 'RAGAnything/Bedrock',
                'Period': 300,
                'Statistic': 'Average',
                'Threshold': 10.0,
                'ActionsEnabled': True,
                'AlarmDescription': 'High response time for Bedrock requests',
                'Unit': 'Seconds'
            },
            {
                'AlarmName': 'RAGAnything-Bedrock-HighTokenUsage',
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': 1,
                'MetricName': 'TokensUsed',
                'Namespace': 'RAGAnything/Bedrock',
                'Period': 3600,  # 1 hour
                'Statistic': 'Sum',
                'Threshold': 100000.0,  # 100K tokens per hour
                'ActionsEnabled': True,
                'AlarmDescription': 'High token usage in Bedrock requests',
                'Unit': 'Count'
            }
        ]
        
        try:
            for alarm in alarms:
                await asyncio.to_thread(
                    self.cloudwatch.put_metric_alarm,
                    **alarm
                )
                self.logger.logger.info(f"Created CloudWatch alarm: {alarm['AlarmName']}")
            
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Failed to create CloudWatch alarms: {e}")
            return False


def create_bedrock_monitor(config: BedrockConfig) -> BedrockMonitor:
    """Factory function to create a Bedrock monitor"""
    return BedrockMonitor(config)


# Decorator for monitoring Bedrock operations
def monitor_bedrock_operation(operation_name: str):
    """Decorator to automatically monitor Bedrock operations"""
    def decorator(func: Callable):
        async def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'monitor') or not self.monitor:
                return await func(self, *args, **kwargs)
            
            model_id = kwargs.get('model_id', getattr(self.config, 'claude_model_id', 'unknown'))
            request_data = kwargs.copy()
            
            # Record request start
            request_id = await self.monitor.record_request(operation_name, model_id, request_data)
            
            start_time = time.time()
            try:
                result = await func(self, *args, **kwargs)
                response_time = time.time() - start_time
                
                # Record successful response
                response_data = {'result': str(result)[:100]}  # Truncated for logging
                await self.monitor.record_response(
                    operation_name, model_id, response_data, response_time, request_id
                )
                
                return result
                
            except Exception as e:
                response_time = time.time() - start_time
                
                # Record error
                await self.monitor.record_error(
                    operation_name, model_id, e, response_time, request_id
                )
                
                raise
        
        return wrapper
    return decorator