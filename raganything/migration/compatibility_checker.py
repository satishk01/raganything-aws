#!/usr/bin/env python3
"""
Compatibility checker for RAG Anything with AWS Bedrock migration
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import importlib.util

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompatibilityChecker:
    """Check compatibility for migrating to AWS Bedrock"""
    
    def __init__(self, installation_dir: str):
        self.installation_dir = Path(installation_dir)
        self.issues = []
        self.warnings = []
        self.recommendations = []
        
    def check_system_requirements(self) -> bool:
        """Check system requirements for Bedrock integration"""
        logger.info("Checking system requirements...")
        
        success = True
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 10):
            self.issues.append(f"Python {python_version.major}.{python_version.minor} is not supported. Requires Python 3.10+")
            success = False
        else:
            logger.info(f"✅ Python {python_version.major}.{python_version.minor} is supported")
        
        # Check required packages
        required_packages = [
            ('boto3', 'AWS SDK for Python'),
            ('botocore', 'AWS SDK core library'),
            ('asyncio', 'Async I/O support'),
        ]
        
        for package, description in required_packages:
            if not self._check_package_installed(package):
                self.issues.append(f"Required package '{package}' ({description}) is not installed")
                success = False
            else:
                logger.info(f"✅ {package} is installed")
        
        # Check optional but recommended packages
        optional_packages = [
            ('uvloop', 'High-performance event loop'),
            ('aiofiles', 'Async file operations'),
        ]
        
        for package, description in optional_packages:
            if not self._check_package_installed(package):
                self.recommendations.append(f"Install '{package}' for better performance ({description})")
            else:
                logger.info(f"✅ {package} is installed")
        
        return success
    
    def _check_package_installed(self, package_name: str) -> bool:
        """Check if a Python package is installed"""
        try:
            importlib.import_module(package_name)
            return True
        except ImportError:
            return False
    
    def check_aws_environment(self) -> bool:
        """Check AWS environment and credentials"""
        logger.info("Checking AWS environment...")
        
        success = True
        
        # Check AWS CLI
        if os.system("which aws > /dev/null 2>&1") != 0:
            self.warnings.append("AWS CLI is not installed - consider installing for easier management")
        else:
            logger.info("✅ AWS CLI is installed")
        
        # Check AWS credentials
        try:
            import boto3
            
            # Try to create a session
            session = boto3.Session()
            credentials = session.get_credentials()
            
            if credentials is None:
                self.issues.append("AWS credentials not found. Configure IAM role or AWS credentials.")
                success = False
            else:
                logger.info("✅ AWS credentials are configured")
                
                # Check if we can access STS (basic AWS connectivity)
                try:
                    sts = session.client('sts')
                    identity = sts.get_caller_identity()
                    logger.info(f"✅ AWS connectivity verified - Account: {identity.get('Account')}")
                except Exception as e:
                    self.issues.append(f"Cannot connect to AWS: {str(e)}")
                    success = False
        
        except ImportError:
            self.issues.append("boto3 is not installed - required for AWS Bedrock integration")
            success = False
        
        return success
    
    def check_bedrock_access(self) -> bool:
        """Check AWS Bedrock access and model availability"""
        logger.info("Checking AWS Bedrock access...")
        
        success = True
        
        try:
            import boto3
            
            # Get AWS region
            region = os.environ.get('AWS_REGION', 'us-east-1')
            
            # Create Bedrock client
            bedrock = boto3.client('bedrock', region_name=region)
            
            # List available models
            try:
                models = bedrock.list_foundation_models()
                available_models = [model['modelId'] for model in models['modelSummaries']]
                
                # Check required models
                required_models = [
                    'anthropic.claude-3-5-sonnet-20241022-v2:0',
                    'anthropic.claude-3-haiku-20240307-v1:0',
                    'amazon.titan-embed-text-v2:0'
                ]
                
                for model_id in required_models:
                    if model_id in available_models:
                        logger.info(f"✅ Model available: {model_id}")
                    else:
                        self.issues.append(f"Required model not available: {model_id}")
                        success = False
                
                # Test model access (if we have permissions)
                try:
                    bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
                    
                    # Try to invoke Claude Haiku (fastest model for testing)
                    test_payload = {
                        "messages": [{"role": "user", "content": "Hello"}],
                        "max_tokens": 10,
                        "anthropic_version": "bedrock-2023-05-31"
                    }
                    
                    response = bedrock_runtime.invoke_model(
                        modelId='anthropic.claude-3-haiku-20240307-v1:0',
                        body=json.dumps(test_payload),
                        contentType='application/json',
                        accept='application/json'
                    )
                    
                    logger.info("✅ Bedrock model invocation test successful")
                    
                except Exception as e:
                    if "AccessDeniedException" in str(e):
                        self.issues.append("Access denied to Bedrock models. Check IAM permissions.")
                        success = False
                    elif "ValidationException" in str(e):
                        logger.info("✅ Bedrock access confirmed (validation error expected)")
                    else:
                        self.warnings.append(f"Bedrock model test failed: {str(e)}")
                
            except Exception as e:
                self.issues.append(f"Cannot list Bedrock models: {str(e)}")
                success = False
        
        except ImportError:
            self.issues.append("boto3 is not installed - required for Bedrock access")
            success = False
        
        return success
    
    def check_existing_installation(self) -> bool:
        """Check existing RAG Anything installation"""
        logger.info("Checking existing RAG Anything installation...")
        
        success = True
        
        # Check if installation directory exists
        if not self.installation_dir.exists():
            self.issues.append(f"Installation directory does not exist: {self.installation_dir}")
            return False
        
        # Check for configuration files
        config_files = ['.env', 'config.json', 'settings.yaml']
        config_found = False
        
        for config_file in config_files:
            if (self.installation_dir / config_file).exists():
                config_found = True
                logger.info(f"✅ Found configuration file: {config_file}")
                break
        
        if not config_found:
            self.warnings.append("No configuration files found - migration will use defaults")
        
        # Check for vector database
        rag_storage = self.installation_dir / "rag_storage"
        if rag_storage.exists():
            # Check vector database size
            total_size = sum(f.stat().st_size for f in rag_storage.rglob('*') if f.is_file())
            size_mb = total_size / (1024 * 1024)
            logger.info(f"✅ Vector database found ({size_mb:.1f} MB)")
            
            if size_mb > 1000:  # 1GB
                self.warnings.append(f"Large vector database ({size_mb:.1f} MB) - migration may take time")
        else:
            self.warnings.append("No existing vector database found - starting fresh")
        
        # Check for existing models/dependencies
        if (self.installation_dir / "models").exists():
            self.recommendations.append("Remove local models directory after migration to save space")
        
        return success
    
    def check_disk_space(self) -> bool:
        """Check available disk space"""
        logger.info("Checking disk space...")
        
        success = True
        
        try:
            import shutil
            
            # Check space in installation directory
            total, used, free = shutil.disk_usage(self.installation_dir)
            free_gb = free / (1024**3)
            
            if free_gb < 5:
                self.issues.append(f"Insufficient disk space: {free_gb:.1f} GB available, need at least 5 GB")
                success = False
            elif free_gb < 10:
                self.warnings.append(f"Low disk space: {free_gb:.1f} GB available, recommend at least 10 GB")
            else:
                logger.info(f"✅ Sufficient disk space: {free_gb:.1f} GB available")
        
        except Exception as e:
            self.warnings.append(f"Could not check disk space: {str(e)}")
        
        return success
    
    def check_network_connectivity(self) -> bool:
        """Check network connectivity to AWS services"""
        logger.info("Checking network connectivity...")
        
        success = True
        
        # Test connectivity to AWS endpoints
        aws_endpoints = [
            'bedrock.us-east-1.amazonaws.com',
            'bedrock-runtime.us-east-1.amazonaws.com',
            'sts.amazonaws.com'
        ]
        
        for endpoint in aws_endpoints:
            if os.system(f"ping -c 1 {endpoint} > /dev/null 2>&1") != 0:
                self.warnings.append(f"Cannot reach {endpoint} - check network connectivity")
            else:
                logger.info(f"✅ Can reach {endpoint}")
        
        return success
    
    def generate_compatibility_report(self) -> str:
        """Generate a comprehensive compatibility report"""
        report = []
        report.append("# RAG Anything to AWS Bedrock Compatibility Report")
        report.append(f"Generated: {os.popen('date').read().strip()}")
        report.append(f"Installation Directory: {self.installation_dir}")
        report.append("")
        
        # Summary
        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        
        if total_issues == 0:
            report.append("## ✅ Compatibility Status: COMPATIBLE")
            report.append("Your system is ready for migration to AWS Bedrock.")
        else:
            report.append("## ❌ Compatibility Status: ISSUES FOUND")
            report.append(f"Found {total_issues} critical issues that must be resolved before migration.")
        
        report.append("")
        
        # Critical Issues
        if self.issues:
            report.append("## ❌ Critical Issues")
            report.append("These issues must be resolved before migration:")
            report.append("")
            for i, issue in enumerate(self.issues, 1):
                report.append(f"{i}. {issue}")
            report.append("")
        
        # Warnings
        if self.warnings:
            report.append("## ⚠️ Warnings")
            report.append("These issues should be addressed but won't prevent migration:")
            report.append("")
            for i, warning in enumerate(self.warnings, 1):
                report.append(f"{i}. {warning}")
            report.append("")
        
        # Recommendations
        if self.recommendations:
            report.append("## 💡 Recommendations")
            report.append("Consider these improvements for better performance:")
            report.append("")
            for i, rec in enumerate(self.recommendations, 1):
                report.append(f"{i}. {rec}")
            report.append("")
        
        # Next Steps
        report.append("## 🚀 Next Steps")
        if total_issues == 0:
            report.append("1. Resolve any warnings if desired")
            report.append("2. Run the migration tool: `python migrate_to_bedrock.py --source /path/to/current --target /opt/raganything`")
            report.append("3. Test the migrated installation")
        else:
            report.append("1. Resolve all critical issues listed above")
            report.append("2. Run this compatibility check again")
            report.append("3. Proceed with migration once all issues are resolved")
        
        return "\n".join(report)
    
    async def run_all_checks(self) -> bool:
        """Run all compatibility checks"""
        logger.info("🔍 Running RAG Anything to AWS Bedrock compatibility checks...")
        
        checks = [
            ("System Requirements", self.check_system_requirements),
            ("AWS Environment", self.check_aws_environment),
            ("Bedrock Access", self.check_bedrock_access),
            ("Existing Installation", self.check_existing_installation),
            ("Disk Space", self.check_disk_space),
            ("Network Connectivity", self.check_network_connectivity),
        ]
        
        overall_success = True
        
        for check_name, check_func in checks:
            logger.info(f"\n--- {check_name} ---")
            try:
                success = check_func()
                if not success:
                    overall_success = False
                    logger.error(f"❌ {check_name} check failed")
                else:
                    logger.info(f"✅ {check_name} check passed")
            except Exception as e:
                logger.error(f"❌ {check_name} check error: {str(e)}")
                self.issues.append(f"{check_name} check failed: {str(e)}")
                overall_success = False
        
        return overall_success


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Check compatibility for RAG Anything to AWS Bedrock migration")
    parser.add_argument("--installation-dir", required=True, help="Path to existing RAG Anything installation")
    parser.add_argument("--output", help="Output file for compatibility report")
    
    args = parser.parse_args()
    
    checker = CompatibilityChecker(args.installation_dir)
    
    # Run all checks
    success = asyncio.run(checker.run_all_checks())
    
    # Generate report
    report = checker.generate_compatibility_report()
    
    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"📋 Compatibility report saved to: {args.output}")
    else:
        print("\n" + "="*80)
        print(report)
        print("="*80)
    
    # Exit with appropriate code
    if success:
        print("\n🎉 Compatibility check passed! Ready for migration.")
        exit(0)
    else:
        print(f"\n❌ Compatibility check failed! Found {len(checker.issues)} critical issues.")
        exit(1)


if __name__ == "__main__":
    main()