#!/usr/bin/env python3
"""
Script to build semantic embeddings for the database schema using nomic-embed-text-v1.5.
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


def main():
    """Build semantic embeddings for the database schema."""
    try:
        logger.info("🚀 Building semantic embeddings using nomic-embed-text-v1.5...")
        
        # Get the semantic indexer instance
        indexer = get_semantic_indexer()
        
        # Force refresh of embeddings
        logger.info("🔄 Refreshing embeddings...")
        indexer.refresh_embeddings()
        
        # Get updated statistics
        stats = indexer.get_embedding_stats()
        logger.info(f"✅ Embeddings built successfully!")
        logger.info(f"📊 Final Statistics:")
        logger.info(f"  - Total tables: {stats['total_tables']}")
        logger.info(f"  - Total columns: {stats['total_columns']}")
        logger.info(f"  - Embedding model: {stats['embedding_model']}")
        logger.info(f"  - Cache exists: {stats['cache_file_exists']}")
        
        if stats['total_tables'] > 0:
            logger.info("🎉 Semantic embeddings are ready for use!")
            return True
        else:
            logger.error("❌ No tables were indexed. Check database connection.")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error building embeddings: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)