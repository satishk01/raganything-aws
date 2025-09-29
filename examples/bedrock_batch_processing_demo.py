#!/usr/bin/env python3
"""
Batch Processing Demo for RAG Anything with AWS Bedrock

This demo shows how to:
1. Process multiple documents efficiently
2. Handle large document sets
3. Monitor processing progress
4. Optimize performance for batch operations
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from raganything.bedrock_rag import BedrockRAGAnything
from raganything import RAGAnythingConfig
from raganything.bedrock import BedrockConfig


class BatchProcessingDemo:
    """Demo class for batch processing with RAG Anything and Bedrock"""
    
    def __init__(self):
        self.rag = None
        self.processing_stats = {
            'total_documents': 0,
            'processed_documents': 0,
            'failed_documents': 0,
            'total_processing_time': 0,
            'average_processing_time': 0,
            'documents_per_minute': 0
        }
        
    async def setup_rag(self):
        """Set up RAG Anything with optimized batch processing configuration"""
        print("🔧 Setting up RAG Anything for batch processing...")
        
        # Configure for batch processing optimization
        rag_config = RAGAnythingConfig(
            working_dir="./bedrock_batch_storage",
            parser="mineru",
            parse_method="auto",
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
            max_concurrent_files=4,  # Process multiple files concurrently
            context_window=1,  # Reduce context for faster processing
            max_context_tokens=1500,  # Smaller context for speed
        )
        
        # Configure Bedrock for batch processing
        bedrock_config = BedrockConfig(
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            claude_model_id="anthropic.claude-3-haiku-20240307-v1:0",  # Use Haiku for speed
            claude_haiku_model_id="anthropic.claude-3-haiku-20240307-v1:0",
            titan_embedding_model_id="amazon.titan-embed-text-v2:0",
            max_tokens=2048,  # Smaller token limit for faster processing
            temperature=0.3,  # Lower temperature for consistent results
            retry_config=None  # Will use defaults
        )
        
        self.rag = BedrockRAGAnything(
            config=rag_config,
            bedrock_config=bedrock_config
        )
        
        # Validate setup
        if await self.rag.validate_bedrock_access():
            print("✅ RAG Anything configured for batch processing")
            return True
        else:
            print("❌ Failed to validate Bedrock access")
            return False
    
    def create_sample_documents(self, num_docs: int = 10) -> List[Path]:
        """Create sample documents for batch processing demo"""
        print(f"📄 Creating {num_docs} sample documents...")
        
        sample_dir = Path("./sample_documents")
        sample_dir.mkdir(exist_ok=True)
        
        document_templates = [
            {
                "title": "Artificial Intelligence Overview",
                "content": """
                Artificial Intelligence (AI) represents one of the most significant technological 
                advances of our time. AI systems can perform tasks that typically require human 
                intelligence, such as visual perception, speech recognition, decision-making, 
                and language translation.
                
                Key AI Technologies:
                - Machine Learning: Algorithms that improve through experience
                - Deep Learning: Neural networks with multiple layers
                - Natural Language Processing: Understanding and generating human language
                - Computer Vision: Interpreting and understanding visual information
                
                Applications span across healthcare, finance, transportation, and entertainment.
                """
            },
            {
                "title": "Machine Learning Fundamentals",
                "content": """
                Machine Learning (ML) is a subset of artificial intelligence that focuses on 
                algorithms that can learn and make decisions from data without being explicitly 
                programmed for every scenario.
                
                Types of Machine Learning:
                1. Supervised Learning: Learning with labeled examples
                2. Unsupervised Learning: Finding patterns in unlabeled data
                3. Reinforcement Learning: Learning through interaction and feedback
                
                Common algorithms include linear regression, decision trees, neural networks,
                and support vector machines. The choice depends on the problem type and data characteristics.
                """
            },
            {
                "title": "Cloud Computing and AWS",
                "content": """
                Cloud computing has revolutionized how organizations deploy and manage IT infrastructure.
                Amazon Web Services (AWS) is a leading cloud platform offering over 200 services.
                
                Core AWS Services:
                - EC2: Elastic Compute Cloud for virtual servers
                - S3: Simple Storage Service for object storage
                - RDS: Relational Database Service
                - Lambda: Serverless computing platform
                - Bedrock: Managed foundation models service
                
                Benefits include scalability, cost-effectiveness, and global availability.
                """
            },
            {
                "title": "Data Science and Analytics",
                "content": """
                Data Science combines statistics, programming, and domain expertise to extract
                insights from data. It involves collecting, cleaning, analyzing, and interpreting
                large datasets to inform business decisions.
                
                Data Science Process:
                1. Problem Definition
                2. Data Collection and Cleaning
                3. Exploratory Data Analysis
                4. Model Building and Validation
                5. Deployment and Monitoring
                
                Tools include Python, R, SQL, Jupyter notebooks, and various visualization libraries.
                """
            },
            {
                "title": "Cybersecurity Essentials",
                "content": """
                Cybersecurity protects digital systems, networks, and data from digital attacks.
                As organizations become more digital, cybersecurity becomes increasingly critical.
                
                Key Security Principles:
                - Confidentiality: Protecting information from unauthorized access
                - Integrity: Ensuring data accuracy and completeness
                - Availability: Ensuring systems are accessible when needed
                
                Common threats include malware, phishing, ransomware, and social engineering.
                Defense strategies involve firewalls, encryption, access controls, and security awareness training.
                """
            }
        ]
        
        created_files = []
        
        for i in range(num_docs):
            template = document_templates[i % len(document_templates)]
            filename = f"document_{i+1:03d}_{template['title'].lower().replace(' ', '_')}.txt"
            filepath = sample_dir / filename
            
            # Add document-specific content
            content = f"Document #{i+1}\n"
            content += f"Title: {template['title']}\n"
            content += f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            content += template['content']
            content += f"\n\nDocument ID: DOC-{i+1:03d}"
            content += f"\nProcessing Batch: BATCH-001"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            created_files.append(filepath)
        
        print(f"✅ Created {len(created_files)} sample documents in {sample_dir}")
        return created_files
    
    async def process_documents_batch(self, document_paths: List[Path]) -> Dict[str, Any]:
        """Process documents in batch with progress monitoring"""
        print(f"\n🚀 Starting batch processing of {len(document_paths)} documents...")
        
        start_time = time.time()
        self.processing_stats['total_documents'] = len(document_paths)
        
        # Process documents using the batch processing capability
        try:
            await self.rag.process_folder_complete(
                folder_path=str(document_paths[0].parent),
                output_dir="./batch_output",
                file_extensions=[".txt", ".pdf", ".docx"],
                recursive=False,
                max_workers=4  # Process 4 documents concurrently
            )
            
            end_time = time.time()
            total_time = end_time - start_time
            
            self.processing_stats.update({
                'processed_documents': len(document_paths),
                'failed_documents': 0,
                'total_processing_time': total_time,
                'average_processing_time': total_time / len(document_paths),
                'documents_per_minute': (len(document_paths) / total_time) * 60
            })
            
            print(f"✅ Batch processing completed successfully!")
            
        except Exception as e:
            print(f"❌ Batch processing failed: {str(e)}")
            self.processing_stats['failed_documents'] = len(document_paths)
            raise
        
        return self.processing_stats
    
    async def demonstrate_batch_queries(self):
        """Demonstrate various query patterns on the batch-processed documents"""
        print("\n🔍 Demonstrating batch query capabilities...")
        
        # Query patterns for batch-processed content
        queries = [
            {
                "query": "What are the main topics covered across all documents?",
                "mode": "global",
                "description": "Global analysis across all documents"
            },
            {
                "query": "Compare the different AI technologies mentioned",
                "mode": "hybrid", 
                "description": "Hybrid search combining local and global context"
            },
            {
                "query": "What are the benefits of cloud computing?",
                "mode": "local",
                "description": "Local search for specific information"
            },
            {
                "query": "Summarize the key security principles",
                "mode": "hybrid",
                "description": "Security-focused query"
            },
            {
                "query": "What is the data science process?",
                "mode": "local",
                "description": "Process-focused query"
            }
        ]
        
        query_results = []
        
        for i, query_info in enumerate(queries, 1):
            print(f"\n📋 Query {i}: {query_info['description']}")
            print(f"   Question: {query_info['query']}")
            print(f"   Mode: {query_info['mode']}")
            
            start_time = time.time()
            
            try:
                result = await self.rag.aquery(
                    query_info['query'],
                    mode=query_info['mode']
                )
                
                query_time = time.time() - start_time
                
                print(f"   ⏱️  Response time: {query_time:.2f}s")
                print(f"   💬 Answer: {result[:200]}...")
                
                query_results.append({
                    'query': query_info['query'],
                    'mode': query_info['mode'],
                    'response_time': query_time,
                    'result_length': len(result)
                })
                
            except Exception as e:
                print(f"   ❌ Query failed: {str(e)}")
                query_results.append({
                    'query': query_info['query'],
                    'mode': query_info['mode'],
                    'error': str(e)
                })
            
            # Small delay between queries
            await asyncio.sleep(0.5)
        
        return query_results
    
    async def performance_analysis(self, query_results: List[Dict]):
        """Analyze performance metrics from batch processing"""
        print("\n📊 Performance Analysis")
        print("=" * 50)
        
        # Processing statistics
        print("📈 Document Processing Statistics:")
        print(f"  Total Documents: {self.processing_stats['total_documents']}")
        print(f"  Successfully Processed: {self.processing_stats['processed_documents']}")
        print(f"  Failed: {self.processing_stats['failed_documents']}")
        print(f"  Total Processing Time: {self.processing_stats['total_processing_time']:.2f}s")
        print(f"  Average Time per Document: {self.processing_stats['average_processing_time']:.2f}s")
        print(f"  Documents per Minute: {self.processing_stats['documents_per_minute']:.1f}")
        
        # Query statistics
        successful_queries = [q for q in query_results if 'error' not in q]
        if successful_queries:
            avg_query_time = sum(q['response_time'] for q in successful_queries) / len(successful_queries)
            avg_result_length = sum(q['result_length'] for q in successful_queries) / len(successful_queries)
            
            print(f"\n🔍 Query Performance Statistics:")
            print(f"  Total Queries: {len(query_results)}")
            print(f"  Successful Queries: {len(successful_queries)}")
            print(f"  Average Query Time: {avg_query_time:.2f}s")
            print(f"  Average Result Length: {avg_result_length:.0f} characters")
            
            # Query mode analysis
            mode_stats = {}
            for query in successful_queries:
                mode = query['mode']
                if mode not in mode_stats:
                    mode_stats[mode] = {'count': 0, 'total_time': 0}
                mode_stats[mode]['count'] += 1
                mode_stats[mode]['total_time'] += query['response_time']
            
            print(f"\n🎯 Query Mode Performance:")
            for mode, stats in mode_stats.items():
                avg_time = stats['total_time'] / stats['count']
                print(f"  {mode}: {stats['count']} queries, avg {avg_time:.2f}s")
        
        # Bedrock configuration info
        bedrock_info = self.rag.get_bedrock_info()
        print(f"\n⚙️  Bedrock Configuration:")
        print(f"  Region: {bedrock_info['bedrock_config']['region']}")
        print(f"  Claude Model: {bedrock_info['bedrock_config']['claude_model']}")
        print(f"  Embedding Dimension: {bedrock_info['embedding_dimension']}")
        print(f"  Max Tokens: {bedrock_info['bedrock_config']['max_tokens']}")
        print(f"  Temperature: {bedrock_info['bedrock_config']['temperature']}")
    
    async def cleanup_demo_data(self):
        """Clean up demo data"""
        print("\n🧹 Cleaning up demo data...")
        
        import shutil
        
        # Clean up directories
        cleanup_dirs = [
            "./sample_documents",
            "./bedrock_batch_storage", 
            "./batch_output"
        ]
        
        for dir_path in cleanup_dirs:
            if Path(dir_path).exists():
                shutil.rmtree(dir_path)
                print(f"  ✅ Removed {dir_path}")
    
    async def run_demo(self, num_documents: int = 10):
        """Run the complete batch processing demo"""
        print("🎬 RAG Anything with AWS Bedrock - Batch Processing Demo")
        print("=" * 65)
        
        try:
            # Step 1: Setup
            if not await self.setup_rag():
                return False
            
            # Step 2: Create sample documents
            document_paths = self.create_sample_documents(num_documents)
            
            # Step 3: Process documents in batch
            processing_stats = await self.process_documents_batch(document_paths)
            
            # Step 4: Demonstrate queries
            query_results = await self.demonstrate_batch_queries()
            
            # Step 5: Performance analysis
            await self.performance_analysis(query_results)
            
            print(f"\n🎉 Batch processing demo completed successfully!")
            print(f"📊 Processed {processing_stats['processed_documents']} documents")
            print(f"⏱️  Total time: {processing_stats['total_processing_time']:.2f}s")
            print(f"🚀 Throughput: {processing_stats['documents_per_minute']:.1f} docs/min")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Demo failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main function to run the batch processing demo"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Anything Bedrock Batch Processing Demo")
    parser.add_argument("--num-docs", type=int, default=10, help="Number of documents to process")
    parser.add_argument("--cleanup", action="store_true", help="Clean up demo data after completion")
    
    args = parser.parse_args()
    
    # Check environment
    if not os.getenv("AWS_REGION"):
        print("⚠️  AWS_REGION not set, using default: us-east-1")
    
    demo = BatchProcessingDemo()
    
    try:
        success = await demo.run_demo(args.num_docs)
        
        if success:
            if args.cleanup:
                await demo.cleanup_demo_data()
            else:
                cleanup = input("\n🧹 Clean up demo data? (y/N): ").lower().strip()
                if cleanup == 'y':
                    await demo.cleanup_demo_data()
            
            print("\n✅ Demo completed successfully!")
            return 0
        else:
            print("\n❌ Demo failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
        await demo.cleanup_demo_data()
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))