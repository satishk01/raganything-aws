#!/usr/bin/env python3
"""
Multimodal example of RAG Anything with AWS Bedrock integration

This example demonstrates:
1. Processing documents with images and tables
2. Multimodal queries with external content
3. Vision model integration with Claude
4. Advanced query techniques
"""

import asyncio
import os
import sys
import base64
from pathlib import Path
from io import BytesIO

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from raganything.bedrock_rag import BedrockRAGAnything
from raganything import RAGAnythingConfig
from raganything.bedrock import BedrockConfig


def create_sample_image_base64():
    """Create a simple sample image as base64 for testing"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple chart image
        img = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw a simple bar chart
        draw.rectangle([50, 50, 350, 250], outline='black', width=2)
        
        # Draw bars
        bars = [
            ("AI", 80, 'blue'),
            ("ML", 120, 'green'), 
            ("DL", 60, 'red'),
            ("NLP", 100, 'orange')
        ]
        
        bar_width = 60
        x_start = 80
        
        for i, (label, height, color) in enumerate(bars):
            x = x_start + i * 80
            y = 230 - height
            draw.rectangle([x, y, x + bar_width, 230], fill=color)
            draw.text((x + 10, 240), label, fill='black')
        
        # Add title
        draw.text((150, 20), "AI Technologies Usage", fill='black')
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_data = buffer.getvalue()
        
        return base64.b64encode(img_data).decode('utf-8')
        
    except ImportError:
        # If PIL is not available, return None
        return None


async def multimodal_bedrock_example():
    """Multimodal example using RAG Anything with AWS Bedrock"""
    
    print("🎨 RAG Anything with AWS Bedrock - Multimodal Example")
    print("=" * 65)
    
    try:
        # Step 1: Configure RAG Anything for multimodal processing
        rag_config = RAGAnythingConfig(
            working_dir="./bedrock_multimodal_storage",
            parser="mineru",
            parse_method="auto",
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
            context_window=2,  # Include more context for multimodal content
            max_context_tokens=3000,
        )
        
        # Step 2: Configure AWS Bedrock with vision capabilities
        bedrock_config = BedrockConfig(
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            claude_model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",  # Supports vision
            claude_haiku_model_id="anthropic.claude-3-haiku-20240307-v1:0",
            titan_embedding_model_id="amazon.titan-embed-text-v2:0",
            max_tokens=4096,
            temperature=0.7
        )
        
        print(f"📍 Using AWS Region: {bedrock_config.aws_region}")
        print(f"👁️  Vision Model: {bedrock_config.claude_model_id}")
        
        # Step 3: Initialize RAG Anything with Bedrock
        print("\n🔧 Initializing RAG Anything with multimodal Bedrock support...")
        rag = BedrockRAGAnything(
            config=rag_config,
            bedrock_config=bedrock_config
        )
        
        print("✅ Multimodal RAG Anything initialized successfully!")
        
        # Step 4: Validate Bedrock access
        print("\n🔍 Validating AWS Bedrock access...")
        if await rag.validate_bedrock_access():
            print("✅ Bedrock access validated successfully!")
        else:
            print("❌ Bedrock access validation failed!")
            return False
        
        # Step 5: Add multimodal sample content
        print("\n📊 Adding multimodal sample content...")
        
        multimodal_content = [
            {
                "type": "text",
                "text": """
                Machine Learning Performance Analysis Report
                
                This report analyzes the performance of different machine learning approaches
                across various metrics including accuracy, processing speed, and resource usage.
                The data shows significant improvements in deep learning approaches compared
                to traditional methods.
                """,
                "page_idx": 0
            },
            {
                "type": "table",
                "table_body": """
                | Model Type | Accuracy | Speed (ms) | Memory (GB) | Use Case |
                |------------|----------|------------|-------------|----------|
                | Linear Regression | 78% | 5 | 0.1 | Simple predictions |
                | Random Forest | 85% | 25 | 0.5 | Structured data |
                | Neural Network | 92% | 100 | 2.0 | Complex patterns |
                | Transformer | 96% | 200 | 8.0 | NLP tasks |
                | CNN | 94% | 150 | 4.0 | Image processing |
                """,
                "table_caption": ["Machine Learning Model Performance Comparison"],
                "table_footnote": ["Data collected from 1000 test samples"],
                "page_idx": 1
            },
            {
                "type": "equation",
                "text": "F1 = 2 × (precision × recall) / (precision + recall)",
                "latex": "F1 = 2 \\times \\frac{\\text{precision} \\times \\text{recall}}{\\text{precision} + \\text{recall}}",
                "equation_caption": "F1 Score Formula for Model Evaluation",
                "page_idx": 2
            },
            {
                "type": "text",
                "text": """
                Computer Vision Applications
                
                Computer vision has revolutionized many industries by enabling machines to
                interpret and understand visual information. Key applications include:
                
                - Medical imaging analysis for disease detection
                - Autonomous vehicle navigation systems  
                - Quality control in manufacturing
                - Facial recognition for security systems
                - Agricultural monitoring via satellite imagery
                
                The accuracy of computer vision models has improved dramatically with
                the advent of deep learning techniques.
                """,
                "page_idx": 3
            }
        ]
        
        await rag.insert_content_list(
            content_list=multimodal_content,
            file_path="ml_performance_report.pdf",
            doc_id="ml-report-multimodal-001"
        )
        
        print("✅ Multimodal content added successfully!")
        
        # Step 6: Test multimodal queries with external content
        print("\n🔍 Testing multimodal queries with external content...")
        
        # Query 1: Table analysis
        print("\n📊 Query 1: Analyzing external table data")
        table_query_result = await rag.aquery_with_multimodal(
            "Compare this new performance data with the models in the document. Which approach shows the best balance of accuracy and speed?",
            multimodal_content=[{
                "type": "table",
                "table_data": """Model,Accuracy,Speed_ms,Memory_GB
                BERT,94%,180,6.0
                GPT-3,97%,300,12.0
                RoBERTa,93%,160,5.5
                DistilBERT,89%,80,2.0""",
                "table_caption": "New NLP Model Performance Data"
            }],
            mode="hybrid"
        )
        print(f"💬 Analysis: {table_query_result[:300]}...")
        
        # Query 2: Equation explanation
        print("\n🧮 Query 2: Mathematical formula analysis")
        equation_query_result = await rag.aquery_with_multimodal(
            "Explain this formula and how it relates to the F1 score mentioned in the document",
            multimodal_content=[{
                "type": "equation",
                "latex": "\\text{Accuracy} = \\frac{TP + TN}{TP + TN + FP + FN}",
                "equation_caption": "Classification Accuracy Formula"
            }],
            mode="hybrid"
        )
        print(f"💬 Explanation: {equation_query_result[:300]}...")
        
        # Query 3: Image analysis (if PIL is available)
        sample_image_b64 = create_sample_image_base64()
        if sample_image_b64:
            print("\n🖼️  Query 3: Image analysis with vision model")
            
            # Create a temporary image file for testing
            temp_image_path = Path("temp_chart.png")
            with open(temp_image_path, "wb") as f:
                f.write(base64.b64decode(sample_image_b64))
            
            try:
                image_query_result = await rag.aquery_with_multimodal(
                    "Analyze this chart and compare it with the performance data in the document. What insights can you provide?",
                    multimodal_content=[{
                        "type": "image",
                        "img_path": str(temp_image_path),
                        "image_caption": ["AI Technologies Usage Chart"],
                        "image_footnote": ["Sample data visualization"]
                    }],
                    mode="hybrid"
                )
                print(f"💬 Image Analysis: {image_query_result[:300]}...")
                
            finally:
                # Clean up temporary image
                if temp_image_path.exists():
                    temp_image_path.unlink()
        else:
            print("\n🖼️  Skipping image analysis (PIL not available)")
        
        # Step 7: Test VLM enhanced queries
        print("\n👁️  Testing VLM enhanced queries...")
        
        # This would automatically use vision capabilities when images are in the retrieved context
        vlm_result = await rag.aquery(
            "What visual information is available in the documents and how does it support the textual content?",
            mode="hybrid",
            vlm_enhanced=True  # Force VLM enhancement
        )
        print(f"💬 VLM Enhanced: {vlm_result[:300]}...")
        
        # Step 8: Advanced multimodal query combining multiple content types
        print("\n🎯 Advanced multimodal query with multiple content types...")
        
        advanced_result = await rag.aquery_with_multimodal(
            "Based on this new research data, provide recommendations for choosing the best ML approach considering the trade-offs shown in both the document and this new information",
            multimodal_content=[
                {
                    "type": "table",
                    "table_data": """Metric,Linear,RF,NN,Transformer,CNN
                    Training_Time_Hours,0.1,2,8,24,12
                    Inference_Cost_USD,0.001,0.01,0.05,0.20,0.10
                    Interpretability,High,Medium,Low,Very_Low,Low
                    Scalability,High,Medium,High,Very_High,High""",
                    "table_caption": "Extended ML Model Comparison"
                },
                {
                    "type": "equation", 
                    "latex": "\\text{Cost-Benefit} = \\frac{\\text{Accuracy} \\times \\text{Business Value}}{\\text{Training Cost} + \\text{Inference Cost}}",
                    "equation_caption": "ML Model Cost-Benefit Analysis Formula"
                }
            ],
            mode="hybrid"
        )
        print(f"💬 Advanced Analysis: {advanced_result[:400]}...")
        
        # Step 9: Show processing statistics
        print("\n📈 Processing Statistics:")
        processor_info = rag.get_processor_info()
        print(f"  Status: {processor_info['status']}")
        print(f"  Available Processors: {list(processor_info['processors'].keys())}")
        print(f"  Models: {processor_info['models']}")
        
        bedrock_info = rag.get_bedrock_info()
        print(f"  Embedding Dimension: {bedrock_info['embedding_dimension']}")
        print(f"  Bedrock Region: {bedrock_info['bedrock_config']['region']}")
        
        print("\n🎉 Multimodal example completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in multimodal example: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def cleanup_multimodal_example():
    """Clean up multimodal example data"""
    print("\n🧹 Cleaning up multimodal example data...")
    
    import shutil
    storage_dir = Path("./bedrock_multimodal_storage")
    
    if storage_dir.exists():
        shutil.rmtree(storage_dir)
        print("✅ Cleaned up multimodal storage directory")


def main():
    """Main function"""
    print("Starting RAG Anything with AWS Bedrock multimodal example...")
    
    # Check environment
    if not os.getenv("AWS_REGION"):
        print("⚠️  AWS_REGION not set, using default: us-east-1")
    
    try:
        # Run the example
        success = asyncio.run(multimodal_bedrock_example())
        
        if success:
            print("\n✅ Multimodal example completed successfully!")
            print("\n📋 What was demonstrated:")
            print("  - Multimodal content processing (text, tables, equations)")
            print("  - External content analysis in queries")
            print("  - Vision model integration with Claude")
            print("  - VLM enhanced queries")
            print("  - Advanced multimodal reasoning")
            
            # Ask if user wants to clean up
            cleanup = input("\n🧹 Clean up example data? (y/N): ").lower().strip()
            if cleanup == 'y':
                asyncio.run(cleanup_multimodal_example())
        else:
            print("\n❌ Multimodal example failed!")
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