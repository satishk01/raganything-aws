#!/usr/bin/env python3
"""
Basic example of RAG Anything with AWS Bedrock integration

This example demonstrates:
1. Setting up RAG Anything with AWS Bedrock
2. Processing a document
3. Performing basic queries
4. Using different Claude models
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from raganything.bedrock_rag import BedrockRAGAnything
from raganything import RAGAnythingConfig
from raganything.bedrock import BedrockConfig


async def basic_bedrock_example():
    """Basic example of using RAG Anything with AWS Bedrock"""
    
    print("🚀 RAG Anything with AWS Bedrock - Basic Example")
    print("=" * 60)
    
    try:
        # Step 1: Configure RAG Anything
        rag_config = RAGAnythingConfig(
            working_dir="./bedrock_rag_storage",
            parser="mineru",
            parse_method="auto",
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
        )
        
        # Step 2: Configure AWS Bedrock
        bedrock_config = BedrockConfig(
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            claude_model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            claude_haiku_model_id="anthropic.claude-3-haiku-20240307-v1:0",
            titan_embedding_model_id="amazon.titan-embed-text-v2:0",
            max_tokens=4096,
            temperature=0.7
        )
        
        print(f"📍 Using AWS Region: {bedrock_config.aws_region}")
        print(f"🤖 Claude Model: {bedrock_config.claude_model_id}")
        print(f"📊 Embedding Model: {bedrock_config.titan_embedding_model_id}")
        
        # Step 3: Initialize RAG Anything with Bedrock
        print("\n🔧 Initializing RAG Anything with Bedrock...")
        rag = BedrockRAGAnything(
            config=rag_config,
            bedrock_config=bedrock_config
        )
        
        print("✅ RAG Anything initialized successfully!")
        
        # Step 4: Validate Bedrock access
        print("\n🔍 Validating AWS Bedrock access...")
        if await rag.validate_bedrock_access():
            print("✅ Bedrock access validated successfully!")
        else:
            print("❌ Bedrock access validation failed!")
            return False
        
        # Step 5: Add some sample content for testing
        print("\n📝 Adding sample content...")
        sample_content = [
            {
                "type": "text",
                "text": """
                Artificial Intelligence and Machine Learning
                
                Artificial Intelligence (AI) is a broad field of computer science focused on creating 
                systems that can perform tasks that typically require human intelligence. Machine Learning (ML) 
                is a subset of AI that enables systems to learn and improve from experience without being 
                explicitly programmed.
                
                Key concepts in AI/ML include:
                - Neural Networks: Computing systems inspired by biological neural networks
                - Deep Learning: ML techniques using neural networks with multiple layers
                - Natural Language Processing: AI's ability to understand and generate human language
                - Computer Vision: AI's ability to interpret and understand visual information
                
                Applications of AI/ML are widespread across industries including healthcare, finance, 
                transportation, and entertainment.
                """,
                "page_idx": 0
            },
            {
                "type": "text", 
                "text": """
                AWS Bedrock Overview
                
                Amazon Bedrock is a fully managed service that offers a choice of high-performing 
                foundation models (FMs) from leading AI companies like AI21 Labs, Anthropic, Cohere, 
                Meta, Stability AI, and Amazon via a single API.
                
                Key features of AWS Bedrock:
                - Multiple foundation models available
                - Serverless experience with no infrastructure to manage
                - Built-in security and privacy controls
                - Fine-tuning capabilities for custom use cases
                - Integration with other AWS services
                
                Bedrock supports various model types including text generation, embeddings, 
                and multimodal models for processing both text and images.
                """,
                "page_idx": 1
            }
        ]
        
        await rag.insert_content_list(
            content_list=sample_content,
            file_path="sample_ai_content.txt",
            doc_id="sample-ai-doc-001"
        )
        
        print("✅ Sample content added successfully!")
        
        # Step 6: Perform basic queries
        print("\n🔍 Testing basic queries...")
        
        queries = [
            "What is artificial intelligence?",
            "What are the key features of AWS Bedrock?",
            "How does machine learning relate to AI?",
            "What applications does AI have in different industries?"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n📋 Query {i}: {query}")
            
            # Use hybrid mode for comprehensive results
            result = await rag.aquery(query, mode="hybrid")
            print(f"💬 Answer: {result[:200]}...")
            
            # Add a small delay between queries
            await asyncio.sleep(1)
        
        # Step 7: Test different models
        print("\n🚀 Testing different Claude models...")
        
        # Test with Claude Sonnet (default)
        print("\n🧠 Using Claude 3.5 Sonnet:")
        sonnet_result = await rag.aquery(
            "Explain the difference between AI and ML in simple terms",
            mode="hybrid"
        )
        print(f"💬 Sonnet: {sonnet_result[:150]}...")
        
        # Test with Claude Haiku (faster)
        print("\n⚡ Using Claude 3 Haiku:")
        # Note: In a real implementation, you'd modify the LLM function to use Haiku
        # For this example, we'll simulate it
        haiku_result = await rag.aquery(
            "What is AWS Bedrock in one sentence?",
            mode="naive",  # Use simpler mode for faster response
            use_haiku=True  # This would be handled in the actual implementation
        )
        print(f"💬 Haiku: {haiku_result[:150]}...")
        
        # Step 8: Show configuration info
        print("\n📊 Bedrock Configuration Info:")
        bedrock_info = rag.get_bedrock_info()
        for key, value in bedrock_info.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
        
        print("\n🎉 Basic example completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in basic example: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def cleanup_example():
    """Clean up example data"""
    print("\n🧹 Cleaning up example data...")
    
    import shutil
    storage_dir = Path("./bedrock_rag_storage")
    
    if storage_dir.exists():
        shutil.rmtree(storage_dir)
        print("✅ Cleaned up storage directory")


def main():
    """Main function"""
    print("Starting RAG Anything with AWS Bedrock basic example...")
    
    # Check environment
    if not os.getenv("AWS_REGION"):
        print("⚠️  AWS_REGION not set, using default: us-east-1")
    
    try:
        # Run the example
        success = asyncio.run(basic_bedrock_example())
        
        if success:
            print("\n✅ Example completed successfully!")
            
            # Ask if user wants to clean up
            cleanup = input("\n🧹 Clean up example data? (y/N): ").lower().strip()
            if cleanup == 'y':
                asyncio.run(cleanup_example())
        else:
            print("\n❌ Example failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Example interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())