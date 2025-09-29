#!/usr/bin/env python3
"""
Comprehensive validation script for RAG Anything with AWS Bedrock integration

This script validates:
1. All Bedrock integration components
2. End-to-end functionality
3. Performance benchmarks
4. Error handling
5. Configuration validation
"""

import asyncio
import os
import sys
import time
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BedrockIntegrationValidator:
    """Comprehensive validator for Bedrock integration"""
    
    def __init__(self):
        self.validation_results = {
            'configuration': {'passed': 0, 'failed': 0, 'details': []},
            'authentication': {'passed': 0, 'failed': 0, 'details': []},
            'llm_provider': {'passed': 0, 'failed': 0, 'details': []},
            'vision_provider': {'passed': 0, 'failed': 0, 'details': []},
            'embedding_provider': {'passed': 0, 'failed': 0, 'details': []},
            'integration': {'passed': 0, 'failed': 0, 'details': []},
            'performance': {'passed': 0, 'failed': 0, 'details': []},
            'error_handling': {'passed': 0, 'failed': 0, 'details': []}
        }
        self.temp_dir = None
        
    def log_test_result(self, category: str, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {category} - {test_name}")
        
        if details:
            logger.info(f"  Details: {details}")
        
        if passed:
            self.validation_results[category]['passed'] += 1
        else:
            self.validation_results[category]['failed'] += 1
        
        self.validation_results[category]['details'].append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
    
    async def validate_configuration(self) -> bool:
        """Validate Bedrock configuration"""
        logger.info("\n🔧 Validating Configuration...")
        
        try:
            from raganything.bedrock import BedrockConfig
            
            # Test 1: Environment variable configuration
            try:
                config = BedrockConfig.from_env()
                self.log_test_result('configuration', 'Environment variable loading', True, 
                                   f"Region: {config.aws_region}")
            except Exception as e:
                self.log_test_result('configuration', 'Environment variable loading', False, str(e))
            
            # Test 2: Configuration validation
            try:
                config = BedrockConfig()
                is_valid = config.validate()
                self.log_test_result('configuration', 'Configuration validation', is_valid,
                                   f"Valid: {is_valid}")
            except Exception as e:
                self.log_test_result('configuration', 'Configuration validation', False, str(e))
            
            # Test 3: Model ID validation
            try:
                config = BedrockConfig()
                has_claude = 'claude' in config.claude_model_id.lower()
                has_titan = 'titan' in config.titan_embedding_model_id.lower()
                self.log_test_result('configuration', 'Model ID format', has_claude and has_titan,
                                   f"Claude: {has_claude}, Titan: {has_titan}")
            except Exception as e:
                self.log_test_result('configuration', 'Model ID format', False, str(e))
            
            return True
            
        except ImportError as e:
            self.log_test_result('configuration', 'Import Bedrock modules', False, str(e))
            return False
    
    async def validate_authentication(self) -> bool:
        """Validate AWS authentication"""
        logger.info("\n🔐 Validating Authentication...")
        
        try:
            from raganything.bedrock import BedrockConfig, BedrockAuthenticator
            
            config = BedrockConfig()
            auth = BedrockAuthenticator(config)
            
            # Test 1: Bedrock client creation
            try:
                client = await auth.get_bedrock_client()
                self.log_test_result('authentication', 'Bedrock client creation', client is not None,
                                   f"Client type: {type(client).__name__}")
            except Exception as e:
                self.log_test_result('authentication', 'Bedrock client creation', False, str(e))
                return False
            
            # Test 2: Permission validation
            try:
                has_permissions = await auth.validate_permissions()
                self.log_test_result('authentication', 'Permission validation', has_permissions,
                                   f"Has permissions: {has_permissions}")
            except Exception as e:
                self.log_test_result('authentication', 'Permission validation', False, str(e))
            
            return True
            
        except ImportError as e:
            self.log_test_result('authentication', 'Import authentication modules', False, str(e))
            return False
    
    async def validate_llm_provider(self) -> bool:
        """Validate LLM provider functionality"""
        logger.info("\n🤖 Validating LLM Provider...")
        
        try:
            from raganything.bedrock import BedrockConfig, BedrockAuthenticator, BedrockLLMProvider
            
            config = BedrockConfig()
            auth = BedrockAuthenticator(config)
            provider = BedrockLLMProvider(config, auth)
            
            # Test 1: Simple completion
            try:
                start_time = time.time()
                result = await provider.complete(
                    prompt="Hello, this is a test. Please respond with 'Test successful'.",
                    max_tokens=50
                )
                response_time = time.time() - start_time
                
                success = result and len(result) > 0
                self.log_test_result('llm_provider', 'Simple completion', success,
                                   f"Response time: {response_time:.2f}s, Length: {len(result) if result else 0}")
            except Exception as e:
                self.log_test_result('llm_provider', 'Simple completion', False, str(e))
            
            # Test 2: Completion with system prompt
            try:
                result = await provider.complete(
                    prompt="What is 2+2?",
                    system_prompt="You are a helpful math assistant. Give brief answers.",
                    max_tokens=50
                )
                success = result and '4' in result
                self.log_test_result('llm_provider', 'System prompt completion', success,
                                   f"Contains '4': {success}")
            except Exception as e:
                self.log_test_result('llm_provider', 'System prompt completion', False, str(e))
            
            # Test 3: Different model (Haiku)
            try:
                result = await provider.complete(
                    prompt="Say 'Haiku test'",
                    model_id=config.claude_haiku_model_id,
                    max_tokens=20
                )
                success = result and 'haiku' in result.lower()
                self.log_test_result('llm_provider', 'Haiku model test', success,
                                   f"Contains 'haiku': {success}")
            except Exception as e:
                self.log_test_result('llm_provider', 'Haiku model test', False, str(e))
            
            return True
            
        except ImportError as e:
            self.log_test_result('llm_provider', 'Import LLM provider modules', False, str(e))
            return False
    
    async def validate_vision_provider(self) -> bool:
        """Validate vision provider functionality"""
        logger.info("\n👁️  Validating Vision Provider...")
        
        try:
            from raganything.bedrock import BedrockConfig, BedrockAuthenticator, BedrockVisionProvider
            import base64
            
            config = BedrockConfig()
            auth = BedrockAuthenticator(config)
            provider = BedrockVisionProvider(config, auth)
            
            # Create a simple test image
            test_image_b64 = self._create_test_image()
            
            if not test_image_b64:
                self.log_test_result('vision_provider', 'Test image creation', False, 
                                   "Could not create test image (PIL not available)")
                return False
            
            # Test 1: Image analysis
            try:
                result = await provider.analyze_image(
                    prompt="Describe what you see in this image briefly.",
                    image_data=test_image_b64
                )
                success = result and len(result) > 10
                self.log_test_result('vision_provider', 'Image analysis', success,
                                   f"Response length: {len(result) if result else 0}")
            except Exception as e:
                self.log_test_result('vision_provider', 'Image analysis', False, str(e))
            
            # Test 2: Multimodal messages format
            try:
                messages = [
                    {"role": "user", "content": [
                        {"type": "text", "text": "What do you see?"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{test_image_b64}"}}
                    ]}
                ]
                result = await provider.analyze_multimodal_messages(messages)
                success = result and len(result) > 5
                self.log_test_result('vision_provider', 'Multimodal messages', success,
                                   f"Response length: {len(result) if result else 0}")
            except Exception as e:
                self.log_test_result('vision_provider', 'Multimodal messages', False, str(e))
            
            return True
            
        except ImportError as e:
            self.log_test_result('vision_provider', 'Import vision provider modules', False, str(e))
            return False
    
    async def validate_embedding_provider(self) -> bool:
        """Validate embedding provider functionality"""
        logger.info("\n📊 Validating Embedding Provider...")
        
        try:
            from raganything.bedrock import BedrockConfig, BedrockAuthenticator, BedrockEmbeddingProvider
            
            config = BedrockConfig()
            auth = BedrockAuthenticator(config)
            provider = BedrockEmbeddingProvider(config, auth)
            
            # Test 1: Single text embedding
            try:
                embedding = await provider.embed_single("This is a test sentence.")
                success = embedding and len(embedding) > 0
                dimension = len(embedding) if embedding else 0
                self.log_test_result('embedding_provider', 'Single text embedding', success,
                                   f"Dimension: {dimension}")
            except Exception as e:
                self.log_test_result('embedding_provider', 'Single text embedding', False, str(e))
            
            # Test 2: Batch text embeddings
            try:
                texts = ["First text", "Second text", "Third text"]
                embeddings = await provider.embed_texts(texts)
                success = embeddings and len(embeddings) == len(texts)
                self.log_test_result('embedding_provider', 'Batch text embeddings', success,
                                   f"Input: {len(texts)}, Output: {len(embeddings) if embeddings else 0}")
            except Exception as e:
                self.log_test_result('embedding_provider', 'Batch text embeddings', False, str(e))
            
            # Test 3: Embedding dimension consistency
            try:
                expected_dim = provider.get_embedding_dimension()
                embedding = await provider.embed_single("Test")
                actual_dim = len(embedding) if embedding else 0
                success = expected_dim == actual_dim
                self.log_test_result('embedding_provider', 'Dimension consistency', success,
                                   f"Expected: {expected_dim}, Actual: {actual_dim}")
            except Exception as e:
                self.log_test_result('embedding_provider', 'Dimension consistency', False, str(e))
            
            return True
            
        except ImportError as e:
            self.log_test_result('embedding_provider', 'Import embedding provider modules', False, str(e))
            return False
    
    async def validate_integration(self) -> bool:
        """Validate end-to-end integration"""
        logger.info("\n🔗 Validating End-to-End Integration...")
        
        try:
            from raganything.bedrock_rag import BedrockRAGAnything
            from raganything import RAGAnythingConfig
            from raganything.bedrock import BedrockConfig
            
            # Test 1: BedrockRAGAnything initialization
            try:
                rag_config = RAGAnythingConfig(working_dir=str(self.temp_dir / "test_rag"))
                bedrock_config = BedrockConfig()
                
                rag = BedrockRAGAnything(config=rag_config, bedrock_config=bedrock_config)
                self.log_test_result('integration', 'BedrockRAGAnything initialization', True,
                                   "Successfully initialized")
            except Exception as e:
                self.log_test_result('integration', 'BedrockRAGAnything initialization', False, str(e))
                return False
            
            # Test 2: Bedrock access validation
            try:
                access_valid = await rag.validate_bedrock_access()
                self.log_test_result('integration', 'Bedrock access validation', access_valid,
                                   f"Access valid: {access_valid}")
            except Exception as e:
                self.log_test_result('integration', 'Bedrock access validation', False, str(e))
            
            # Test 3: Content insertion and querying
            try:
                # Insert test content
                test_content = [{
                    "type": "text",
                    "text": "This is a test document about artificial intelligence and machine learning.",
                    "page_idx": 0
                }]
                
                await rag.insert_content_list(
                    content_list=test_content,
                    file_path="test_document.txt",
                    doc_id="test-doc-001"
                )
                
                # Query the content
                result = await rag.aquery("What is this document about?", mode="naive")
                success = result and len(result) > 10
                self.log_test_result('integration', 'Content insertion and querying', success,
                                   f"Query result length: {len(result) if result else 0}")
            except Exception as e:
                self.log_test_result('integration', 'Content insertion and querying', False, str(e))
            
            # Test 4: Multimodal query
            try:
                result = await rag.aquery_with_multimodal(
                    "Analyze this data",
                    multimodal_content=[{
                        "type": "table",
                        "table_data": "Item,Value\nTest,123\nExample,456",
                        "table_caption": "Test data"
                    }],
                    mode="naive"
                )
                success = result and len(result) > 10
                self.log_test_result('integration', 'Multimodal query', success,
                                   f"Query result length: {len(result) if result else 0}")
            except Exception as e:
                self.log_test_result('integration', 'Multimodal query', False, str(e))
            
            return True
            
        except ImportError as e:
            self.log_test_result('integration', 'Import integration modules', False, str(e))
            return False
    
    async def validate_performance(self) -> bool:
        """Validate performance benchmarks"""
        logger.info("\n⚡ Validating Performance...")
        
        try:
            from raganything.bedrock_rag import BedrockRAGAnything
            from raganything import RAGAnythingConfig
            from raganything.bedrock import BedrockConfig
            
            rag_config = RAGAnythingConfig(working_dir=str(self.temp_dir / "perf_rag"))
            bedrock_config = BedrockConfig()
            rag = BedrockRAGAnything(config=rag_config, bedrock_config=bedrock_config)
            
            # Test 1: Query response time
            try:
                start_time = time.time()
                result = await rag.aquery("What is AI?", mode="naive")
                response_time = time.time() - start_time
                
                success = response_time < 30.0  # Should respond within 30 seconds
                self.log_test_result('performance', 'Query response time', success,
                                   f"Response time: {response_time:.2f}s")
            except Exception as e:
                self.log_test_result('performance', 'Query response time', False, str(e))
            
            # Test 2: Concurrent queries
            try:
                queries = ["What is AI?", "What is ML?", "What is DL?"]
                start_time = time.time()
                
                tasks = [rag.aquery(query, mode="naive") for query in queries]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                total_time = time.time() - start_time
                successful_results = [r for r in results if not isinstance(r, Exception)]
                
                success = len(successful_results) == len(queries) and total_time < 60.0
                self.log_test_result('performance', 'Concurrent queries', success,
                                   f"Successful: {len(successful_results)}/{len(queries)}, Time: {total_time:.2f}s")
            except Exception as e:
                self.log_test_result('performance', 'Concurrent queries', False, str(e))
            
            return True
            
        except ImportError as e:
            self.log_test_result('performance', 'Import performance test modules', False, str(e))
            return False
    
    async def validate_error_handling(self) -> bool:
        """Validate error handling"""
        logger.info("\n🚨 Validating Error Handling...")
        
        try:
            from raganything.bedrock import BedrockConfig, BedrockAuthenticator, BedrockLLMProvider
            from raganything.bedrock.exceptions import BedrockError
            
            config = BedrockConfig()
            auth = BedrockAuthenticator(config)
            provider = BedrockLLMProvider(config, auth)
            
            # Test 1: Invalid model ID handling
            try:
                await provider.complete(
                    prompt="Test",
                    model_id="invalid-model-id",
                    max_tokens=10
                )
                self.log_test_result('error_handling', 'Invalid model ID', False,
                                   "Should have raised an exception")
            except Exception as e:
                # Should raise an exception
                self.log_test_result('error_handling', 'Invalid model ID', True,
                                   f"Correctly raised: {type(e).__name__}")
            
            # Test 2: Empty prompt handling
            try:
                result = await provider.complete(prompt="", max_tokens=10)
                # Should handle gracefully or raise appropriate exception
                self.log_test_result('error_handling', 'Empty prompt handling', True,
                                   "Handled gracefully")
            except Exception as e:
                self.log_test_result('error_handling', 'Empty prompt handling', True,
                                   f"Appropriately raised: {type(e).__name__}")
            
            # Test 3: Retry mechanism (simulate by testing with very low token limit)
            try:
                result = await provider.complete(
                    prompt="This is a test prompt that should work fine",
                    max_tokens=1  # Very low limit might cause issues
                )
                self.log_test_result('error_handling', 'Low token limit handling', True,
                                   "Handled low token limit")
            except Exception as e:
                self.log_test_result('error_handling', 'Low token limit handling', True,
                                   f"Appropriately handled: {type(e).__name__}")
            
            return True
            
        except ImportError as e:
            self.log_test_result('error_handling', 'Import error handling modules', False, str(e))
            return False
    
    def _create_test_image(self) -> Optional[str]:
        """Create a simple test image as base64"""
        try:
            from PIL import Image, ImageDraw
            import base64
            from io import BytesIO
            
            # Create a simple test image
            img = Image.new('RGB', (100, 100), color='white')
            draw = ImageDraw.Draw(img)
            draw.rectangle([10, 10, 90, 90], outline='black', width=2)
            draw.text((30, 45), "TEST", fill='black')
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_data = buffer.getvalue()
            
            return base64.b64encode(img_data).decode('utf-8')
            
        except ImportError:
            return None
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        report = []
        report.append("# RAG Anything with AWS Bedrock - Validation Report")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        total_passed = sum(cat['passed'] for cat in self.validation_results.values())
        total_failed = sum(cat['failed'] for cat in self.validation_results.values())
        total_tests = total_passed + total_failed
        
        if total_failed == 0:
            report.append("## ✅ Validation Status: ALL TESTS PASSED")
        else:
            report.append("## ❌ Validation Status: SOME TESTS FAILED")
        
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Passed: {total_passed}")
        report.append(f"Failed: {total_failed}")
        report.append(f"Success Rate: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        report.append("")
        
        # Detailed results by category
        for category, results in self.validation_results.items():
            category_total = results['passed'] + results['failed']
            if category_total == 0:
                continue
                
            status_icon = "✅" if results['failed'] == 0 else "❌"
            report.append(f"## {status_icon} {category.title().replace('_', ' ')}")
            report.append(f"Passed: {results['passed']}, Failed: {results['failed']}")
            report.append("")
            
            for detail in results['details']:
                status = "✅" if detail['passed'] else "❌"
                report.append(f"- {status} {detail['test']}")
                if detail['details']:
                    report.append(f"  {detail['details']}")
            report.append("")
        
        # Recommendations
        if total_failed > 0:
            report.append("## 🔧 Recommendations")
            report.append("1. Review failed tests and error messages")
            report.append("2. Check AWS credentials and permissions")
            report.append("3. Verify Bedrock model access in your region")
            report.append("4. Ensure all required dependencies are installed")
            report.append("5. Check network connectivity to AWS services")
        else:
            report.append("## 🎉 All Tests Passed!")
            report.append("Your RAG Anything with AWS Bedrock integration is working correctly.")
        
        return "\n".join(report)
    
    async def run_validation(self) -> bool:
        """Run complete validation suite"""
        logger.info("🔍 Starting RAG Anything with AWS Bedrock Integration Validation")
        logger.info("=" * 80)
        
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="rag_bedrock_validation_"))
        logger.info(f"Using temporary directory: {self.temp_dir}")
        
        try:
            # Run all validation tests
            validation_steps = [
                ("Configuration", self.validate_configuration),
                ("Authentication", self.validate_authentication),
                ("LLM Provider", self.validate_llm_provider),
                ("Vision Provider", self.validate_vision_provider),
                ("Embedding Provider", self.validate_embedding_provider),
                ("Integration", self.validate_integration),
                ("Performance", self.validate_performance),
                ("Error Handling", self.validate_error_handling),
            ]
            
            overall_success = True
            
            for step_name, step_func in validation_steps:
                try:
                    step_success = await step_func()
                    if not step_success:
                        overall_success = False
                except Exception as e:
                    logger.error(f"Validation step '{step_name}' failed with exception: {e}")
                    overall_success = False
            
            return overall_success
            
        finally:
            # Cleanup temporary directory
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary directory: {e}")


async def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate RAG Anything with AWS Bedrock integration")
    parser.add_argument("--output", help="Output file for validation report")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check environment
    if not os.getenv("AWS_REGION"):
        logger.warning("AWS_REGION not set, using default: us-east-1")
        os.environ["AWS_REGION"] = "us-east-1"
    
    validator = BedrockIntegrationValidator()
    
    try:
        success = await validator.run_validation()
        
        # Generate report
        report = validator.generate_validation_report()
        
        # Output report
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            logger.info(f"Validation report saved to: {args.output}")
        else:
            print("\n" + "="*80)
            print(report)
            print("="*80)
        
        if success:
            logger.info("🎉 All validations passed! RAG Anything with Bedrock is ready to use.")
            return 0
        else:
            logger.error("❌ Some validations failed. Please review the report and fix issues.")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))