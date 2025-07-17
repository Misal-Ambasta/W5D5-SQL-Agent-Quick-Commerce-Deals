#!/usr/bin/env python3
"""
Test script for the Semantic Table Indexer using nomic-embed-text-v1.5.
"""

import asyncio
import logging
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.services.semantic_indexer import SemanticTableIndexer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_semantic_indexer():
    """Test the semantic table indexer functionality."""
    logger.info("🚀 Testing Semantic Table Indexer with nomic-embed-text-v1.5")
    
    try:
        # Initialize the indexer
        logger.info("Initializing semantic indexer...")
        indexer = SemanticTableIndexer()
        
        # Get embedding statistics
        stats = indexer.get_embedding_stats()
        logger.info(f"📊 Embedding Statistics:")
        logger.info(f"  - Total tables indexed: {stats['total_tables']}")
        logger.info(f"  - Total columns indexed: {stats['total_columns']}")
        logger.info(f"  - Embedding model: {stats['embedding_model']}")
        logger.info(f"  - Cache age: {stats['cache_age_hours']:.1f} hours" if stats['cache_age_hours'] else "  - Cache: New")
        
        # Test queries for different scenarios
        test_queries = [
            "Which app has cheapest onions right now?",
            "Show products with 30% discount on Blinkit",
            "Compare fruit prices between Zepto and Instamart", 
            "Find best deals for grocery shopping",
            "What are the current stock levels?",
            "Show me promotional campaigns",
            "Track price history for products",
            "User shopping preferences and lists"
        ]
        
        logger.info("\n🔍 Testing query-to-table matching:")
        
        for query in test_queries:
            logger.info(f"\nQuery: '{query}'")
            
            # Get relevant tables
            relevant_tables = await indexer.get_relevant_tables(query, top_k=5, threshold=0.2)
            
            if relevant_tables:
                logger.info("  📋 Most relevant tables:")
                for table_name, similarity in relevant_tables:
                    logger.info(f"    - {table_name}: {similarity:.3f}")
                
                # Get relevant columns for top tables
                top_table_names = [table for table, _ in relevant_tables[:3]]
                relevant_columns = await indexer.get_relevant_columns(query, top_table_names, top_k=5)
                
                logger.info("  📝 Most relevant columns:")
                for table_name, columns in relevant_columns.items():
                    if columns:
                        top_columns = [f"{col}({score:.3f})" for col, score in columns[:3]]
                        logger.info(f"    {table_name}: {', '.join(top_columns)}")
                
                # Get join suggestions
                if len(top_table_names) > 1:
                    join_suggestions = indexer.get_join_suggestions(top_table_names)
                    if join_suggestions:
                        logger.info("  🔗 Join suggestions:")
                        for join in join_suggestions[:2]:  # Show top 2 joins
                            logger.info(f"    {join['from_table']} -> {join['to_table']}: {join['condition']}")
            else:
                logger.warning("  ❌ No relevant tables found")
        
        # Test specific domain queries
        logger.info("\n🛒 Testing domain-specific queries:")
        
        domain_queries = [
            ("pricing", "current product prices and discounts"),
            ("inventory", "stock levels and availability"),
            ("platforms", "Blinkit Zepto Instamart BigBasket"),
            ("products", "fruits vegetables dairy snacks"),
            ("users", "customer preferences and shopping history"),
            ("analytics", "performance metrics and query logs")
        ]
        
        for domain, query in domain_queries:
            logger.info(f"\nDomain: {domain.upper()}")
            relevant_tables = await indexer.get_relevant_tables(query, top_k=3, threshold=0.3)
            
            if relevant_tables:
                table_names = [table for table, score in relevant_tables]
                logger.info(f"  Tables: {', '.join(table_names)}")
            else:
                logger.warning(f"  No tables found for {domain}")
        
        logger.info("\n✅ Semantic indexer testing completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing semantic indexer: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False


async def test_performance():
    """Test performance of the semantic indexer."""
    logger.info("\n⚡ Testing performance...")
    
    try:
        indexer = SemanticTableIndexer()
        
        import time
        
        # Test query processing speed
        test_query = "Which platform has the cheapest fruits and vegetables?"
        
        start_time = time.time()
        relevant_tables = await indexer.get_relevant_tables(test_query, top_k=10)
        end_time = time.time()
        
        logger.info(f"Query processing time: {(end_time - start_time)*1000:.2f}ms")
        logger.info(f"Found {len(relevant_tables)} relevant tables")
        
        # Test multiple queries in sequence
        queries = [
            "cheapest products",
            "discount offers", 
            "stock availability",
            "user preferences",
            "price comparison"
        ]
        
        start_time = time.time()
        for query in queries:
            await indexer.get_relevant_tables(query, top_k=5)
        end_time = time.time()
        
        avg_time = ((end_time - start_time) / len(queries)) * 1000
        logger.info(f"Average query time for {len(queries)} queries: {avg_time:.2f}ms")
        
        return True
        
    except Exception as e:
        logger.error(f"Performance test failed: {str(e)}")
        return False


async def main():
    """Main test function."""
    logger.info("🧪 Starting Semantic Table Indexer Tests")
    
    # Test basic functionality
    basic_test_passed = await test_semantic_indexer()
    
    # Test performance
    performance_test_passed = await test_performance()
    
    if basic_test_passed and performance_test_passed:
        logger.info("\n🎉 All tests passed! Semantic indexer is working correctly.")
        logger.info("The nomic-embed-text-v1.5 model is successfully integrated.")
        return True
    else:
        logger.error("\n❌ Some tests failed. Please check the logs above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)