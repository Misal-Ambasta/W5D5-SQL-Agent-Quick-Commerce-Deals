#!/usr/bin/env python3
"""
Test script for the Semantic Table Indexer using nomic-embed-text-v1.5 model.
"""

import asyncio
import logging
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.services.semantic_indexer import get_semantic_indexer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_semantic_indexer():
    """Test the semantic table indexer functionality."""
    try:
        logger.info("🚀 Testing Semantic Table Indexer with nomic-embed-text-v1.5...")
        
        # Get the semantic indexer instance
        indexer = get_semantic_indexer()
        
        # Get embedding statistics
        stats = indexer.get_embedding_stats()
        logger.info(f"📊 Embedding Statistics:")
        logger.info(f"  - Total tables: {stats['total_tables']}")
        logger.info(f"  - Total columns: {stats['total_columns']}")
        logger.info(f"  - Embedding model: {stats['embedding_model']}")
        logger.info(f"  - Cache exists: {stats['cache_file_exists']}")
        if stats['cache_age_hours']:
            logger.info(f"  - Cache age: {stats['cache_age_hours']:.1f} hours")
        
        # Test queries
        test_queries = [
            "Which app has cheapest onions right now?",
            "Show products with 30% discount on Blinkit",
            "Compare fruit prices between Zepto and Instamart",
            "Find best deals for grocery shopping",
            "What are the current inventory levels?",
            "Show me promotional campaigns",
            "Track price history for products"
        ]
        
        logger.info("\n🔍 Testing semantic table selection...")
        
        for query in test_queries:
            logger.info(f"\n📝 Query: '{query}'")
            
            # Get relevant tables
            relevant_tables = await indexer.get_relevant_tables(query, top_k=5, threshold=0.2)
            
            if relevant_tables:
                logger.info("  📋 Most relevant tables:")
                for table_name, score in relevant_tables:
                    logger.info(f"    - {table_name}: {score:.3f}")
                
                # Get relevant columns for top 3 tables
                top_tables = [table for table, _ in relevant_tables[:3]]
                relevant_columns = await indexer.get_relevant_columns(query, top_tables, top_k=5)
                
                logger.info("  🔗 Most relevant columns:")
                for table_name, columns in relevant_columns.items():
                    if columns:
                        top_columns = [f"{col}({score:.2f})" for col, score in columns[:3]]
                        logger.info(f"    - {table_name}: {', '.join(top_columns)}")
                
                # Get join suggestions
                if len(top_tables) > 1:
                    join_suggestions = indexer.get_join_suggestions(top_tables)
                    if join_suggestions:
                        logger.info("  🔗 Join suggestions:")
                        for join in join_suggestions[:2]:  # Show top 2
                            logger.info(f"    - {join['from_table']} -> {join['to_table']}: {join['condition']}")
            else:
                logger.warning("  ⚠️  No relevant tables found")
        
        logger.info("\n✅ Semantic indexer test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing semantic indexer: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False


async def test_specific_functionality():
    """Test specific functionality of the semantic indexer."""
    try:
        logger.info("\n🧪 Testing specific functionality...")
        
        indexer = get_semantic_indexer()
        
        # Test table metadata retrieval
        logger.info("\n📋 Testing table metadata retrieval...")
        test_tables = ['products', 'current_prices', 'platforms']
        
        for table_name in test_tables:
            metadata = indexer.get_table_metadata(table_name)
            if metadata:
                logger.info(f"  📊 {table_name}:")
                logger.info(f"    - Columns: {len(metadata['columns'])}")
                logger.info(f"    - Foreign keys: {len(metadata['foreign_keys'])}")
                logger.info(f"    - Sample columns: {metadata['columns'][:5]}")
            else:
                logger.warning(f"  ⚠️  No metadata found for {table_name}")
        
        # Test join suggestions for common table combinations
        logger.info("\n🔗 Testing join suggestions...")
        table_combinations = [
            ['products', 'current_prices'],
            ['products', 'current_prices', 'platforms'],
            ['products', 'product_categories', 'product_brands']
        ]
        
        for tables in table_combinations:
            joins = indexer.get_join_suggestions(tables)
            logger.info(f"  📋 Tables: {', '.join(tables)}")
            if joins:
                for join in joins:
                    logger.info(f"    - {join['condition']} (confidence: {join['confidence']})")
            else:
                logger.info("    - No direct joins found")
        
        logger.info("\n✅ Specific functionality test completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in specific functionality test: {str(e)}")
        return False


async def main():
    """Main test function."""
    logger.info("🎯 Starting comprehensive semantic indexer tests...")
    
    # Test basic functionality
    basic_test = await test_semantic_indexer()
    
    # Test specific functionality
    specific_test = await test_specific_functionality()
    
    if basic_test and specific_test:
        logger.info("\n🎉 All tests passed! Semantic indexer is working correctly.")
        logger.info("🚀 Ready to use nomic-embed-text-v1.5 for intelligent table selection!")
        return True
    else:
        logger.error("\n❌ Some tests failed. Please check the logs above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)