#!/usr/bin/env python3
"""
Performance Comparison Demo: RAG Anything with AWS Bedrock vs OpenAI

This demo compares:
1. Response times between different models
2. Quality of responses
3. Cost implications
4. Throughput differences
5. Feature capabilities
"""

import asyncio
import os
import sys
import time
import statistics
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from raganything.bedrock_rag import BedrockRAGAnything
from raganything import RAGAnything, RAGAnythingConfig
from raganything.bedrock import BedrockConfig


class PerformanceComparison:
    """Performance comparison between Bedrock and OpenAI implementations"""
    
    def __init__(self):
        self.bedrock_rag = None
        self.openai_rag = None
        self.test_queries = [
            "What is artificial intelligence and how does it work?",
            "Explain the differences between machine learning and deep learning",
            "What are the main applications of AI in healthcare?",
            "How does natural language processing work?",
            "What are the ethical considerations in AI development?",
            "Describe the process of training a neural network",
            "What is the role of data in machine learning?",
            "How do recommendation systems work?",
            "What are the challenges in computer vision?",
            "Explain the concept of reinforcement learning"
        ]
        self.results = {
            'bedrock': {'times': [], 'responses': [], 'errors': []},
            'openai': {'times': [], 'responses': [], 'errors': []}
        }
    
    async def setup_bedrock_rag(self) -> bool:
        """Set up RAG Anything with Bedrock"""
        print("🔧 Setting up RAG Anything with AWS Bedrock...")
        
        try:
            rag_config = RAGAnythingConfig(
                working_dir="./comparison_bedrock_storage",
                parser="mineru",
                parse_method="auto",
                enable_image_processing=True,
                enable_table_processing=True,
                enable_equation_processing=True,
            )
            
            bedrock_config = BedrockConfig(
                aws_region=os.getenv("AWS_REGION", "us-east-1"),
                claude_model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
                claude_haiku_model_id="anthropic.claude-3-haiku-20240307-v1:0",
                titan_embedding_model_id="amazon.titan-embed-text-v2:0",
                max_tokens=4096,
                temperature=0.7
            )
            
            self.bedrock_rag = BedrockRAGAnything(
                config=rag_config,
                bedrock_config=bedrock_config
            )
            
            if await self.bedrock_rag.validate_bedrock_access():
                print("✅ Bedrock RAG setup successful")
                return True
            else:
                print("❌ Bedrock access validation failed")
                return False
                
        except Exception as e:
            print(f"❌ Bedrock setup failed: {str(e)}")
            return False
    
    async def setup_openai_rag(self) -> bool:
        """Set up RAG Anything with OpenAI (simulated for comparison)"""
        print("🔧 Setting up RAG Anything with OpenAI (simulated)...")
        
        # Note: This is a simulated setup since we're focusing on Bedrock
        # In a real comparison, you would set up actual OpenAI integration
        try:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                print("⚠️  OPENAI_API_KEY not found - using simulated responses")
                return False
            
            # This would be the actual OpenAI setup
            # For this demo, we'll simulate it
            print("✅ OpenAI RAG setup successful (simulated)")
            return True
            
        except Exception as e:
            print(f"❌ OpenAI setup failed: {str(e)}")
            return False
    
    async def add_sample_content(self):
        """Add sample content for testing"""
        print("📝 Adding sample content for comparison...")
        
        sample_content = [
            {
                "type": "text",
                "text": """
                Artificial Intelligence Comprehensive Guide
                
                Artificial Intelligence (AI) is a transformative technology that enables machines 
                to perform tasks that typically require human intelligence. This includes learning, 
                reasoning, problem-solving, perception, and language understanding.
                
                Key AI Technologies:
                
                1. Machine Learning (ML)
                   - Supervised Learning: Learning from labeled data
                   - Unsupervised Learning: Finding patterns in unlabeled data
                   - Reinforcement Learning: Learning through trial and error
                
                2. Deep Learning
                   - Neural Networks: Inspired by the human brain
                   - Convolutional Neural Networks (CNNs): For image processing
                   - Recurrent Neural Networks (RNNs): For sequential data
                   - Transformers: For natural language processing
                
                3. Natural Language Processing (NLP)
                   - Text analysis and understanding
                   - Language generation and translation
                   - Sentiment analysis and entity recognition
                   - Question answering systems
                
                4. Computer Vision
                   - Image recognition and classification
                   - Object detection and tracking
                   - Facial recognition systems
                   - Medical image analysis
                
                Applications in Healthcare:
                - Medical diagnosis and imaging
                - Drug discovery and development
                - Personalized treatment plans
                - Robotic surgery assistance
                - Electronic health record analysis
                
                Ethical Considerations:
                - Bias and fairness in AI systems
                - Privacy and data protection
                - Transparency and explainability
                - Job displacement concerns
                - Autonomous decision-making responsibility
                
                The future of AI holds immense potential for solving complex global challenges
                while requiring careful consideration of ethical implications and societal impact.
                """,
                "page_idx": 0
            }
        ]
        
        # Add content to Bedrock RAG
        if self.bedrock_rag:
            await self.bedrock_rag.insert_content_list(
                content_list=sample_content,
                file_path="ai_comprehensive_guide.txt",
                doc_id="ai-guide-comparison-001"
            )
            print("✅ Content added to Bedrock RAG")
    
    async def run_bedrock_queries(self) -> Dict[str, Any]:
        """Run test queries on Bedrock RAG"""
        print("\n🚀 Running queries on AWS Bedrock...")
        
        bedrock_results = {
            'times': [],
            'responses': [],
            'errors': [],
            'model_info': {}
        }
        
        # Test different Claude models
        models_to_test = [
            {
                'name': 'Claude 3.5 Sonnet',
                'model_id': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
                'description': 'High-quality responses'
            },
            {
                'name': 'Claude 3 Haiku', 
                'model_id': 'anthropic.claude-3-haiku-20240307-v1:0',
                'description': 'Fast responses'
            }
        ]
        
        for model_info in models_to_test:
            print(f"\n🤖 Testing {model_info['name']} ({model_info['description']})")
            model_results = {
                'times': [],
                'responses': [],
                'errors': []
            }
            
            # Update model configuration
            self.bedrock_rag.bedrock_config.claude_model_id = model_info['model_id']
            
            for i, query in enumerate(self.test_queries[:5], 1):  # Test first 5 queries
                print(f"  Query {i}: {query[:50]}...")
                
                start_time = time.time()
                try:
                    response = await self.bedrock_rag.aquery(query, mode="hybrid")
                    response_time = time.time() - start_time
                    
                    model_results['times'].append(response_time)
                    model_results['responses'].append({
                        'query': query,
                        'response': response,
                        'length': len(response)
                    })
                    
                    print(f"    ✅ Response time: {response_time:.2f}s")
                    
                except Exception as e:
                    error_time = time.time() - start_time
                    model_results['errors'].append({
                        'query': query,
                        'error': str(e),
                        'time': error_time
                    })
                    print(f"    ❌ Error: {str(e)}")
                
                # Small delay between queries
                await asyncio.sleep(0.5)
            
            bedrock_results['model_info'][model_info['name']] = model_results
        
        return bedrock_results
    
    async def simulate_openai_queries(self) -> Dict[str, Any]:
        """Simulate OpenAI queries for comparison"""
        print("\n🔄 Simulating OpenAI queries for comparison...")
        
        # Simulated OpenAI results based on typical performance
        openai_results = {
            'times': [],
            'responses': [],
            'errors': [],
            'model_info': {
                'GPT-4': {
                    'times': [2.1, 2.3, 1.9, 2.5, 2.0],  # Simulated response times
                    'responses': [
                        {
                            'query': query,
                            'response': f"[Simulated GPT-4 response to: {query}] This would be a comprehensive response from GPT-4 covering the key aspects of the question with detailed explanations and examples.",
                            'length': 250
                        } for query in self.test_queries[:5]
                    ],
                    'errors': []
                },
                'GPT-3.5-Turbo': {
                    'times': [0.8, 0.9, 0.7, 1.1, 0.8],  # Faster simulated times
                    'responses': [
                        {
                            'query': query,
                            'response': f"[Simulated GPT-3.5 response to: {query}] This would be a good response from GPT-3.5 Turbo with relevant information.",
                            'length': 180
                        } for query in self.test_queries[:5]
                    ],
                    'errors': []
                }
            }
        }
        
        print("✅ OpenAI simulation completed")
        return openai_results
    
    def analyze_performance(self, bedrock_results: Dict, openai_results: Dict):
        """Analyze and compare performance metrics"""
        print("\n📊 Performance Analysis")
        print("=" * 60)
        
        # Bedrock Analysis
        print("\n🔵 AWS Bedrock Results:")
        for model_name, results in bedrock_results['model_info'].items():
            if results['times']:
                avg_time = statistics.mean(results['times'])
                min_time = min(results['times'])
                max_time = max(results['times'])
                success_rate = len(results['responses']) / (len(results['responses']) + len(results['errors'])) * 100
                
                print(f"  {model_name}:")
                print(f"    Average Response Time: {avg_time:.2f}s")
                print(f"    Min/Max Response Time: {min_time:.2f}s / {max_time:.2f}s")
                print(f"    Success Rate: {success_rate:.1f}%")
                print(f"    Queries Processed: {len(results['responses'])}")
                
                if results['responses']:
                    avg_length = statistics.mean([r['length'] for r in results['responses']])
                    print(f"    Average Response Length: {avg_length:.0f} characters")
        
        # OpenAI Analysis (Simulated)
        print("\n🟢 OpenAI Results (Simulated):")
        for model_name, results in openai_results['model_info'].items():
            if results['times']:
                avg_time = statistics.mean(results['times'])
                min_time = min(results['times'])
                max_time = max(results['times'])
                
                print(f"  {model_name}:")
                print(f"    Average Response Time: {avg_time:.2f}s")
                print(f"    Min/Max Response Time: {min_time:.2f}s / {max_time:.2f}s")
                print(f"    Success Rate: 100.0% (simulated)")
                print(f"    Queries Processed: {len(results['responses'])}")
                
                if results['responses']:
                    avg_length = statistics.mean([r['length'] for r in results['responses']])
                    print(f"    Average Response Length: {avg_length:.0f} characters")
        
        # Comparison Summary
        print("\n⚖️  Comparison Summary:")
        
        # Get Bedrock Claude 3.5 Sonnet results
        sonnet_results = bedrock_results['model_info'].get('Claude 3.5 Sonnet', {})
        haiku_results = bedrock_results['model_info'].get('Claude 3 Haiku', {})
        gpt4_results = openai_results['model_info'].get('GPT-4', {})
        gpt35_results = openai_results['model_info'].get('GPT-3.5-Turbo', {})
        
        comparisons = [
            ("Quality Models", "Claude 3.5 Sonnet", sonnet_results, "GPT-4", gpt4_results),
            ("Speed Models", "Claude 3 Haiku", haiku_results, "GPT-3.5-Turbo", gpt35_results)
        ]
        
        for category, bedrock_model, bedrock_data, openai_model, openai_data in comparisons:
            print(f"\n  {category} Comparison:")
            
            if bedrock_data.get('times') and openai_data.get('times'):
                bedrock_avg = statistics.mean(bedrock_data['times'])
                openai_avg = statistics.mean(openai_data['times'])
                
                print(f"    {bedrock_model}: {bedrock_avg:.2f}s average")
                print(f"    {openai_model}: {openai_avg:.2f}s average")
                
                if bedrock_avg < openai_avg:
                    improvement = ((openai_avg - bedrock_avg) / openai_avg) * 100
                    print(f"    🏆 {bedrock_model} is {improvement:.1f}% faster")
                else:
                    difference = ((bedrock_avg - openai_avg) / openai_avg) * 100
                    print(f"    🏆 {openai_model} is {difference:.1f}% faster")
        
        # Feature Comparison
        print(f"\n🎯 Feature Comparison:")
        print(f"  AWS Bedrock Advantages:")
        print(f"    ✅ No API keys needed (IAM role-based)")
        print(f"    ✅ Data stays in your AWS account")
        print(f"    ✅ Integration with AWS services")
        print(f"    ✅ Multiple model choices (Claude, Titan)")
        print(f"    ✅ Built-in security and compliance")
        
        print(f"  OpenAI Advantages:")
        print(f"    ✅ Mature ecosystem and tooling")
        print(f"    ✅ Extensive documentation and community")
        print(f"    ✅ Regular model updates")
        print(f"    ✅ Proven performance at scale")
        
        # Cost Analysis (Estimated)
        print(f"\n💰 Cost Analysis (Estimated):")
        print(f"  Note: Actual costs depend on usage patterns and pricing tiers")
        print(f"  AWS Bedrock:")
        print(f"    - Pay per token/request model")
        print(f"    - No monthly minimums")
        print(f"    - Volume discounts available")
        print(f"  OpenAI:")
        print(f"    - Pay per token model")
        print(f"    - Different pricing for different models")
        print(f"    - Usage-based billing")
    
    async def cleanup_comparison_data(self):
        """Clean up comparison data"""
        print("\n🧹 Cleaning up comparison data...")
        
        import shutil
        
        cleanup_dirs = [
            "./comparison_bedrock_storage",
            "./comparison_openai_storage"
        ]
        
        for dir_path in cleanup_dirs:
            if Path(dir_path).exists():
                shutil.rmtree(dir_path)
                print(f"  ✅ Removed {dir_path}")
    
    async def run_comparison(self):
        """Run the complete performance comparison"""
        print("⚖️  RAG Anything Performance Comparison: AWS Bedrock vs OpenAI")
        print("=" * 70)
        
        try:
            # Setup
            bedrock_ready = await self.setup_bedrock_rag()
            openai_ready = await self.setup_openai_rag()
            
            if not bedrock_ready:
                print("❌ Cannot proceed without Bedrock setup")
                return False
            
            # Add sample content
            await self.add_sample_content()
            
            # Run comparisons
            bedrock_results = await self.run_bedrock_queries()
            openai_results = await self.simulate_openai_queries()
            
            # Analyze results
            self.analyze_performance(bedrock_results, openai_results)
            
            print(f"\n🎉 Performance comparison completed!")
            return True
            
        except Exception as e:
            print(f"\n❌ Comparison failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main function"""
    print("Starting RAG Anything performance comparison...")
    
    # Check environment
    if not os.getenv("AWS_REGION"):
        print("⚠️  AWS_REGION not set, using default: us-east-1")
    
    comparison = PerformanceComparison()
    
    try:
        success = await comparison.run_comparison()
        
        if success:
            cleanup = input("\n🧹 Clean up comparison data? (y/N): ").lower().strip()
            if cleanup == 'y':
                await comparison.cleanup_comparison_data()
            
            print("\n✅ Performance comparison completed successfully!")
            print("\n📋 Key Takeaways:")
            print("  - AWS Bedrock offers strong privacy and security benefits")
            print("  - Claude models provide competitive performance")
            print("  - IAM role-based authentication simplifies deployment")
            print("  - Multiple model options allow optimization for different use cases")
            print("  - Integration with AWS ecosystem provides additional value")
            
            return 0
        else:
            print("\n❌ Performance comparison failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Comparison interrupted by user")
        await comparison.cleanup_comparison_data()
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))