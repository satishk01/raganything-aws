#!/usr/bin/env python3
"""
Migration utility to convert existing RAG Anything installations to use AWS Bedrock
"""

import os
import json
import shutil
import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BedrockMigrationTool:
    """Tool to migrate existing RAG Anything installations to AWS Bedrock"""
    
    def __init__(self, source_dir: str, target_dir: str, backup_dir: str = None):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.backup_dir = Path(backup_dir) if backup_dir else self.source_dir / "backup"
        
        # Migration configuration
        self.config_mappings = {
            # OpenAI to Bedrock mappings
            'LLM_BINDING_API_KEY': None,  # Remove - using IAM roles
            'LLM_BINDING_HOST': None,     # Remove - using Bedrock
            'LLM_MODEL': 'BEDROCK_CLAUDE_MODEL_ID',
            'EMBEDDING_MODEL': 'BEDROCK_TITAN_EMBEDDING_MODEL_ID',
            'EMBEDDING_BINDING_HOST': None,  # Remove - using Bedrock
            'EMBEDDING_BINDING_API_KEY': None,  # Remove - using IAM roles
            
            # Add new Bedrock configurations
            'AWS_REGION': 'us-east-1',
            'BEDROCK_CLAUDE_MODEL_ID': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
            'BEDROCK_CLAUDE_HAIKU_MODEL_ID': 'anthropic.claude-3-haiku-20240307-v1:0',
            'BEDROCK_TITAN_EMBEDDING_MODEL_ID': 'amazon.titan-embed-text-v2:0',
            'BEDROCK_MAX_TOKENS': '4096',
            'BEDROCK_TEMPERATURE': '0.7',
            'BEDROCK_RETRY_MAX_ATTEMPTS': '3',
            'BEDROCK_RETRY_BACKOFF_FACTOR': '2.0',
        }
        
    def create_backup(self) -> bool:
        """Create backup of existing installation"""
        try:
            logger.info(f"Creating backup at {self.backup_dir}")
            
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup configuration files
            config_files = [
                '.env',
                'config.json',
                'settings.yaml',
                'raganything.conf'
            ]
            
            for config_file in config_files:
                source_file = self.source_dir / config_file
                if source_file.exists():
                    shutil.copy2(source_file, self.backup_dir / config_file)
                    logger.info(f"Backed up {config_file}")
            
            # Backup vector database
            rag_storage = self.source_dir / "rag_storage"
            if rag_storage.exists():
                shutil.copytree(rag_storage, self.backup_dir / "rag_storage")
                logger.info("Backed up vector database")
            
            # Backup logs
            logs_dir = self.source_dir / "logs"
            if logs_dir.exists():
                shutil.copytree(logs_dir, self.backup_dir / "logs")
                logger.info("Backed up logs")
            
            logger.info("✅ Backup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Backup failed: {str(e)}")
            return False
    
    def migrate_configuration(self) -> bool:
        """Migrate configuration files to Bedrock format"""
        try:
            logger.info("Migrating configuration files...")
            
            # Read existing configuration
            existing_config = self._read_existing_config()
            
            # Create new Bedrock configuration
            bedrock_config = self._create_bedrock_config(existing_config)
            
            # Write new configuration
            target_config_file = self.target_dir / "config" / ".env"
            target_config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_config_file, 'w') as f:
                f.write("# RAG Anything with AWS Bedrock Configuration\n")
                f.write("# Migrated from existing installation\n\n")
                
                for key, value in bedrock_config.items():
                    f.write(f"{key}={value}\n")
            
            logger.info(f"✅ Configuration migrated to {target_config_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration migration failed: {str(e)}")
            return False
    
    def _read_existing_config(self) -> Dict[str, str]:
        """Read existing configuration from various sources"""
        config = {}
        
        # Try to read from .env file
        env_file = self.source_dir / ".env"
        if env_file.exists():
            config.update(self._parse_env_file(env_file))
        
        # Try to read from environment variables
        for key in os.environ:
            if key.startswith(('LLM_', 'EMBEDDING_', 'WORKING_DIR', 'OUTPUT_DIR')):
                config[key] = os.environ[key]
        
        # Try to read from config.json
        config_json = self.source_dir / "config.json"
        if config_json.exists():
            with open(config_json, 'r') as f:
                json_config = json.load(f)
                config.update(json_config)
        
        return config
    
    def _parse_env_file(self, env_file: Path) -> Dict[str, str]:
        """Parse .env file"""
        config = {}
        
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"\'')
        
        return config
    
    def _create_bedrock_config(self, existing_config: Dict[str, str]) -> Dict[str, str]:
        """Create Bedrock configuration from existing config"""
        bedrock_config = {}
        
        # Map existing configurations
        for old_key, new_key in self.config_mappings.items():
            if old_key in existing_config and new_key:
                bedrock_config[new_key] = existing_config[old_key]
        
        # Add default Bedrock configurations
        defaults = {
            'AWS_REGION': 'us-east-1',
            'BEDROCK_CLAUDE_MODEL_ID': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
            'BEDROCK_CLAUDE_HAIKU_MODEL_ID': 'anthropic.claude-3-haiku-20240307-v1:0',
            'BEDROCK_TITAN_EMBEDDING_MODEL_ID': 'amazon.titan-embed-text-v2:0',
            'BEDROCK_MAX_TOKENS': '4096',
            'BEDROCK_TEMPERATURE': '0.7',
            'BEDROCK_RETRY_MAX_ATTEMPTS': '3',
            'BEDROCK_RETRY_BACKOFF_FACTOR': '2.0',
        }
        
        for key, value in defaults.items():
            if key not in bedrock_config:
                bedrock_config[key] = value
        
        # Preserve existing RAG Anything settings
        preserve_keys = [
            'WORKING_DIR',
            'OUTPUT_DIR',
            'PARSER',
            'PARSE_METHOD',
            'ENABLE_IMAGE_PROCESSING',
            'ENABLE_TABLE_PROCESSING',
            'ENABLE_EQUATION_PROCESSING',
            'MAX_CONCURRENT_FILES',
            'CONTEXT_WINDOW',
            'MAX_CONTEXT_TOKENS',
            'LOG_LEVEL',
            'LOG_DIR',
        ]
        
        for key in preserve_keys:
            if key in existing_config:
                bedrock_config[key] = existing_config[key]
            elif key == 'WORKING_DIR':
                bedrock_config[key] = str(self.target_dir / "data" / "rag_storage")
            elif key == 'OUTPUT_DIR':
                bedrock_config[key] = str(self.target_dir / "data" / "output")
            elif key == 'LOG_DIR':
                bedrock_config[key] = str(self.target_dir / "logs")
        
        return bedrock_config
    
    def migrate_data(self) -> bool:
        """Migrate vector database and other data"""
        try:
            logger.info("Migrating data files...")
            
            # Create target data directory
            target_data_dir = self.target_dir / "data"
            target_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Migrate vector database
            source_rag_storage = self.source_dir / "rag_storage"
            target_rag_storage = target_data_dir / "rag_storage"
            
            if source_rag_storage.exists():
                if target_rag_storage.exists():
                    shutil.rmtree(target_rag_storage)
                shutil.copytree(source_rag_storage, target_rag_storage)
                logger.info("✅ Vector database migrated")
            
            # Migrate output directory
            source_output = self.source_dir / "output"
            target_output = target_data_dir / "output"
            
            if source_output.exists():
                if target_output.exists():
                    shutil.rmtree(target_output)
                shutil.copytree(source_output, target_output)
                logger.info("✅ Output directory migrated")
            
            # Migrate cache directory
            source_cache = self.source_dir / "cache"
            target_cache = self.target_dir / "cache"
            
            if source_cache.exists():
                if target_cache.exists():
                    shutil.rmtree(target_cache)
                shutil.copytree(source_cache, target_cache)
                logger.info("✅ Cache directory migrated")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Data migration failed: {str(e)}")
            return False
    
    def validate_migration(self) -> bool:
        """Validate the migration was successful"""
        try:
            logger.info("Validating migration...")
            
            # Check configuration file exists
            config_file = self.target_dir / "config" / ".env"
            if not config_file.exists():
                logger.error("Configuration file not found")
                return False
            
            # Check vector database exists
            rag_storage = self.target_dir / "data" / "rag_storage"
            if not rag_storage.exists():
                logger.warning("Vector database not found - this is OK for new installations")
            
            # Check configuration is valid
            config = self._parse_env_file(config_file)
            required_keys = [
                'AWS_REGION',
                'BEDROCK_CLAUDE_MODEL_ID',
                'BEDROCK_TITAN_EMBEDDING_MODEL_ID'
            ]
            
            for key in required_keys:
                if key not in config:
                    logger.error(f"Required configuration key missing: {key}")
                    return False
            
            logger.info("✅ Migration validation successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration validation failed: {str(e)}")
            return False
    
    def create_migration_report(self) -> str:
        """Create a migration report"""
        report = []
        report.append("# RAG Anything to AWS Bedrock Migration Report")
        report.append(f"Migration Date: {os.popen('date').read().strip()}")
        report.append(f"Source Directory: {self.source_dir}")
        report.append(f"Target Directory: {self.target_dir}")
        report.append(f"Backup Directory: {self.backup_dir}")
        report.append("")
        
        report.append("## Configuration Changes")
        report.append("The following configuration changes were made:")
        report.append("")
        
        # Read old and new configurations
        old_config = self._read_existing_config()
        new_config_file = self.target_dir / "config" / ".env"
        new_config = self._parse_env_file(new_config_file) if new_config_file.exists() else {}
        
        report.append("### Removed (OpenAI/Ollama specific):")
        removed_keys = ['LLM_BINDING_API_KEY', 'LLM_BINDING_HOST', 'EMBEDDING_BINDING_API_KEY', 'EMBEDDING_BINDING_HOST']
        for key in removed_keys:
            if key in old_config:
                report.append(f"- {key}")
        
        report.append("")
        report.append("### Added (AWS Bedrock specific):")
        bedrock_keys = [k for k in new_config.keys() if k.startswith('BEDROCK_') or k == 'AWS_REGION']
        for key in bedrock_keys:
            report.append(f"- {key}={new_config.get(key, '')}")
        
        report.append("")
        report.append("## Next Steps")
        report.append("1. Review the migrated configuration in: " + str(self.target_dir / "config" / ".env"))
        report.append("2. Ensure AWS credentials are configured (IAM role or AWS CLI)")
        report.append("3. Test the Bedrock integration: python /opt/raganything/scripts/test_bedrock.py")
        report.append("4. Start the service: systemctl start raganything")
        report.append("")
        report.append("## Rollback Instructions")
        report.append("If you need to rollback:")
        report.append(f"1. Stop the service: systemctl stop raganything")
        report.append(f"2. Restore from backup: cp -r {self.backup_dir}/* {self.source_dir}/")
        report.append(f"3. Restart with old configuration")
        
        return "\n".join(report)
    
    async def run_migration(self) -> bool:
        """Run the complete migration process"""
        logger.info("🚀 Starting RAG Anything to AWS Bedrock migration...")
        
        # Step 1: Create backup
        if not self.create_backup():
            return False
        
        # Step 2: Create target directory structure
        self.target_dir.mkdir(parents=True, exist_ok=True)
        (self.target_dir / "config").mkdir(exist_ok=True)
        (self.target_dir / "logs").mkdir(exist_ok=True)
        (self.target_dir / "data").mkdir(exist_ok=True)
        (self.target_dir / "cache").mkdir(exist_ok=True)
        (self.target_dir / "scripts").mkdir(exist_ok=True)
        
        # Step 3: Migrate configuration
        if not self.migrate_configuration():
            return False
        
        # Step 4: Migrate data
        if not self.migrate_data():
            return False
        
        # Step 5: Validate migration
        if not self.validate_migration():
            return False
        
        # Step 6: Create migration report
        report = self.create_migration_report()
        report_file = self.target_dir / "migration_report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"✅ Migration completed successfully!")
        logger.info(f"📋 Migration report saved to: {report_file}")
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Migrate RAG Anything to AWS Bedrock")
    parser.add_argument("--source", required=True, help="Source directory of existing installation")
    parser.add_argument("--target", required=True, help="Target directory for Bedrock installation")
    parser.add_argument("--backup", help="Backup directory (default: source/backup)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without making changes")
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
        # TODO: Implement dry run functionality
        return
    
    migration_tool = BedrockMigrationTool(
        source_dir=args.source,
        target_dir=args.target,
        backup_dir=args.backup
    )
    
    success = asyncio.run(migration_tool.run_migration())
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print(f"📁 New installation location: {args.target}")
        print(f"💾 Backup location: {migration_tool.backup_dir}")
        print(f"📋 Migration report: {args.target}/migration_report.md")
    else:
        print("\n❌ Migration failed!")
        print(f"💾 Backup is available at: {migration_tool.backup_dir}")
        exit(1)


if __name__ == "__main__":
    main()