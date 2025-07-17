"""
Semantic Table Indexer for Quick Commerce Deals platform.
Uses nomic-embed-text-v1.5 model via langchain-nomic for intelligent table selection.
"""

import json
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import pickle
import os
from pathlib import Path

from langchain_nomic import NomicEmbeddings
from sqlalchemy import text, inspect
from sqlalchemy.orm import sessionmaker
from sklearn.metrics.pairwise import cosine_similarity

from app.db.database import engine
from app.core.cache import cache_manager, CacheNamespace

logger = logging.getLogger(__name__)


class SemanticTableIndexer:
    """
    Semantic indexer for database tables using nomic-embed-text-v1.5 embeddings.
    Provides intelligent table selection for natural language queries.
    """
    
    def __init__(self, database_uri: str = None, cache_dir: str = "cache/embeddings"):
        """
        Initialize the semantic table indexer.
        
        Args:
            database_uri: Database connection URI (uses default if None)
            cache_dir: Directory to cache embeddings
        """
        self.engine = engine if database_uri is None else engine
        self.Session = sessionmaker(bind=self.engine)
        
        # Initialize Nomic embeddings model
        self.embeddings_model = NomicEmbeddings(
            model="nomic-embed-text-v1.5"
        )
        
        # Cache setup
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage for embeddings and metadata
        self.table_embeddings: Dict[str, np.ndarray] = {}
        self.column_embeddings: Dict[str, Dict[str, np.ndarray]] = {}
        self.table_metadata: Dict[str, Dict] = {}
        self.embedding_cache_file = self.cache_dir / "table_embeddings.pkl"
        
        # Load or build embeddings
        self._load_or_build_embeddings()
    
    def _load_or_build_embeddings(self):
        """Load cached embeddings or build new ones if cache is stale."""
        try:
            if self._is_cache_valid():
                logger.info("Loading cached embeddings...")
                self._load_cached_embeddings()
            else:
                logger.info("Building new semantic embeddings...")
                self._build_semantic_embeddings()
                self._save_embeddings_cache()
        except Exception as e:
            logger.error(f"Error loading/building embeddings: {str(e)}")
            # Fallback to building new embeddings
            self._build_semantic_embeddings()
            self._save_embeddings_cache()
    
    def _is_cache_valid(self) -> bool:
        """Check if cached embeddings are still valid (less than 24 hours old)."""
        if not self.embedding_cache_file.exists():
            return False
        
        cache_age = datetime.now() - datetime.fromtimestamp(
            self.embedding_cache_file.stat().st_mtime
        )
        return cache_age < timedelta(hours=24)
    
    def _load_cached_embeddings(self):
        """Load embeddings from cache file."""
        with open(self.embedding_cache_file, 'rb') as f:
            cache_data = pickle.load(f)
            self.table_embeddings = cache_data['table_embeddings']
            self.column_embeddings = cache_data['column_embeddings']
            self.table_metadata = cache_data['table_metadata']
        
        logger.info(f"Loaded embeddings for {len(self.table_embeddings)} tables")
    
    def _save_embeddings_cache(self):
        """Save embeddings to cache file."""
        cache_data = {
            'table_embeddings': self.table_embeddings,
            'column_embeddings': self.column_embeddings,
            'table_metadata': self.table_metadata,
            'created_at': datetime.now().isoformat()
        }
        
        with open(self.embedding_cache_file, 'wb') as f:
            pickle.dump(cache_data, f)
        
        logger.info(f"Saved embeddings cache for {len(self.table_embeddings)} tables")
    
    def _build_semantic_embeddings(self):
        """Build semantic embeddings for all database tables and columns."""
        logger.info("Building semantic embeddings for database schema...")
        
        # Get database schema information
        inspector = inspect(self.engine)
        table_names = inspector.get_table_names()
        
        logger.info(f"Found {len(table_names)} tables to index")
        
        for table_name in table_names:
            try:
                self._build_table_embeddings(table_name, inspector)
            except Exception as e:
                logger.error(f"Error building embeddings for table {table_name}: {str(e)}")
                continue
        
        logger.info(f"Successfully built embeddings for {len(self.table_embeddings)} tables")
    
    def _build_table_embeddings(self, table_name: str, inspector):
        """Build embeddings for a specific table."""
        # Get table metadata
        columns = inspector.get_columns(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        indexes = inspector.get_indexes(table_name)
        
        # Build table description for embedding
        table_description = self._create_table_description(
            table_name, columns, foreign_keys, indexes
        )
        
        # Generate embedding for table
        table_embedding = self.embeddings_model.embed_query(table_description)
        self.table_embeddings[table_name] = np.array(table_embedding)
        
        # Store table metadata
        self.table_metadata[table_name] = {
            'columns': [col['name'] for col in columns],
            'column_types': {col['name']: str(col['type']) for col in columns},
            'foreign_keys': foreign_keys,
            'indexes': indexes,
            'description': table_description
        }
        
        # Build column embeddings
        self.column_embeddings[table_name] = {}
        for column in columns:
            column_description = self._create_column_description(
                table_name, column['name'], column
            )
            column_embedding = self.embeddings_model.embed_query(column_description)
            self.column_embeddings[table_name][column['name']] = np.array(column_embedding)
        
        logger.debug(f"Built embeddings for table: {table_name}")
    
    def _create_table_description(self, table_name: str, columns: List[Dict], 
                                foreign_keys: List[Dict], indexes: List[Dict]) -> str:
        """Create a descriptive text for table embedding."""
        # Convert table name to readable format
        readable_name = table_name.replace('_', ' ').title()
        
        # Get column names and types
        column_info = []
        for col in columns:
            col_type = str(col['type']).lower()
            if 'varchar' in col_type or 'text' in col_type:
                column_info.append(f"{col['name']} (text)")
            elif 'int' in col_type:
                column_info.append(f"{col['name']} (number)")
            elif 'decimal' in col_type or 'numeric' in col_type:
                column_info.append(f"{col['name']} (price/amount)")
            elif 'bool' in col_type:
                column_info.append(f"{col['name']} (yes/no)")
            elif 'timestamp' in col_type or 'date' in col_type:
                column_info.append(f"{col['name']} (date/time)")
            else:
                column_info.append(f"{col['name']}")
        
        # Build relationships info
        relationships = []
        for fk in foreign_keys:
            ref_table = fk['referred_table'].replace('_', ' ')
            relationships.append(f"related to {ref_table}")
        
        # Create comprehensive description
        description_parts = [
            f"Table: {readable_name}",
            f"Contains: {', '.join(column_info[:10])}",  # Limit to first 10 columns
        ]
        
        if relationships:
            description_parts.append(f"Relationships: {', '.join(relationships)}")
        
        # Add domain-specific context based on table name
        domain_context = self._get_domain_context(table_name)
        if domain_context:
            description_parts.append(f"Purpose: {domain_context}")
        
        return ". ".join(description_parts)
    
    def _create_column_description(self, table_name: str, column_name: str, column: Dict) -> str:
        """Create a descriptive text for column embedding."""
        readable_column = column_name.replace('_', ' ').title()
        readable_table = table_name.replace('_', ' ').title()
        
        col_type = str(column['type']).lower()
        
        # Determine column purpose based on name and type
        if column_name.endswith('_id'):
            purpose = "identifier"
        elif 'price' in column_name or 'cost' in column_name or 'amount' in column_name:
            purpose = "monetary value"
        elif 'date' in column_name or 'time' in column_name:
            purpose = "date or time"
        elif 'name' in column_name or 'title' in column_name:
            purpose = "name or title"
        elif 'description' in column_name:
            purpose = "description or details"
        elif 'status' in column_name or 'active' in column_name:
            purpose = "status or state"
        elif 'count' in column_name or 'quantity' in column_name:
            purpose = "quantity or count"
        else:
            purpose = "data field"
        
        return f"{readable_column} in {readable_table} table - {purpose}"
    
    def _get_domain_context(self, table_name: str) -> str:
        """Get domain-specific context for table based on name."""
        domain_contexts = {
            'products': 'stores product catalog information including names, brands, categories',
            'platforms': 'contains quick commerce platform information like Blinkit, Zepto, Instamart',
            'current_prices': 'tracks real-time product prices across different platforms',
            'price_history': 'maintains historical pricing data for trend analysis',
            'discounts': 'stores active discount offers and promotional deals',
            'promotional_campaigns': 'manages marketing campaigns and special offers',
            'inventory_levels': 'tracks stock availability and inventory quantities',
            'availability_status': 'monitors real-time product availability',
            'product_categories': 'organizes products into hierarchical categories',
            'product_brands': 'contains brand information for products',
            'users': 'stores user account and profile information',
            'search_history': 'tracks user search patterns and queries',
            'price_alerts': 'manages user price notification preferences',
            'shopping_lists': 'stores user shopping lists and preferences',
            'delivery_estimates': 'contains delivery time and cost information',
            'query_logs': 'tracks system query performance and usage',
            'performance_metrics': 'monitors system performance statistics'
        }
        
        return domain_contexts.get(table_name, '')
    
    async def get_relevant_tables(self, query: str, top_k: int = 10, 
                                threshold: float = 0.3) -> List[Tuple[str, float]]:
        """
        Get most relevant tables for a natural language query.
        
        Args:
            query: Natural language query
            top_k: Maximum number of tables to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (table_name, similarity_score) tuples
        """
        if not self.table_embeddings:
            logger.warning("No table embeddings available")
            return []
        
        try:
            # Create cache key for this query
            import hashlib
            query_params = f"{query}_{top_k}_{threshold}"
            cache_key = hashlib.md5(query_params.encode()).hexdigest()
            
            # Try to get from cache first
            cached_result = await cache_manager.get(
                cache_key, 
                namespace=CacheNamespace.TABLE_EMBEDDINGS.value
            )
            if cached_result:
                logger.debug(f"Retrieved relevant tables from cache for query: '{query[:50]}...'")
                return cached_result
            
            # Generate embedding for the query
            query_embedding = np.array(self.embeddings_model.embed_query(query))
            
            # Calculate similarities with all tables
            similarities = []
            for table_name, table_embedding in self.table_embeddings.items():
                similarity = cosine_similarity(
                    query_embedding.reshape(1, -1),
                    table_embedding.reshape(1, -1)
                )[0][0]
                
                if similarity >= threshold:
                    similarities.append((table_name, float(similarity)))
            
            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            relevant_tables = similarities[:top_k]
            
            # Cache the result
            await cache_manager.set(
                cache_key,
                relevant_tables,
                ttl=1800,  # 30 minutes
                namespace=CacheNamespace.TABLE_EMBEDDINGS.value,
                tags=["table_similarity", "embeddings"]
            )
            
            logger.info(f"Found {len(relevant_tables)} relevant tables for query: '{query[:50]}...'")
            for table, score in relevant_tables[:5]:  # Log top 5
                logger.debug(f"  {table}: {score:.3f}")
            
            return relevant_tables
            
        except Exception as e:
            logger.error(f"Error getting relevant tables: {str(e)}")
            return []
    
    async def get_relevant_columns(self, query: str, table_names: List[str], 
                                 top_k: int = 20) -> Dict[str, List[Tuple[str, float]]]:
        """
        Get most relevant columns for specific tables.
        
        Args:
            query: Natural language query
            table_names: List of table names to search within
            top_k: Maximum number of columns per table
            
        Returns:
            Dictionary mapping table names to list of (column_name, similarity_score)
        """
        if not self.column_embeddings:
            return {}
        
        try:
            query_embedding = np.array(self.embeddings_model.embed_query(query))
            relevant_columns = {}
            
            for table_name in table_names:
                if table_name not in self.column_embeddings:
                    continue
                
                table_columns = []
                for column_name, column_embedding in self.column_embeddings[table_name].items():
                    similarity = cosine_similarity(
                        query_embedding.reshape(1, -1),
                        column_embedding.reshape(1, -1)
                    )[0][0]
                    
                    table_columns.append((column_name, float(similarity)))
                
                # Sort and take top_k
                table_columns.sort(key=lambda x: x[1], reverse=True)
                relevant_columns[table_name] = table_columns[:top_k]
            
            return relevant_columns
            
        except Exception as e:
            logger.error(f"Error getting relevant columns: {str(e)}")
            return {}
    
    def get_table_metadata(self, table_name: str) -> Optional[Dict]:
        """Get metadata for a specific table."""
        return self.table_metadata.get(table_name)
    
    def get_join_suggestions(self, table_names: List[str]) -> List[Dict]:
        """
        Suggest optimal join paths between tables.
        
        Args:
            table_names: List of table names to find joins for
            
        Returns:
            List of join suggestions with table pairs and join conditions
        """
        join_suggestions = []
        
        for i, table1 in enumerate(table_names):
            for table2 in table_names[i+1:]:
                # Check for direct foreign key relationships
                table1_meta = self.table_metadata.get(table1, {})
                table2_meta = self.table_metadata.get(table2, {})
                
                # Check if table1 has FK to table2
                for fk in table1_meta.get('foreign_keys', []):
                    if fk['referred_table'] == table2:
                        join_suggestions.append({
                            'from_table': table1,
                            'to_table': table2,
                            'join_type': 'INNER JOIN',
                            'condition': f"{table1}.{fk['constrained_columns'][0]} = {table2}.{fk['referred_columns'][0]}",
                            'confidence': 1.0
                        })
                
                # Check if table2 has FK to table1
                for fk in table2_meta.get('foreign_keys', []):
                    if fk['referred_table'] == table1:
                        join_suggestions.append({
                            'from_table': table2,
                            'to_table': table1,
                            'join_type': 'INNER JOIN',
                            'condition': f"{table2}.{fk['constrained_columns'][0]} = {table1}.{fk['referred_columns'][0]}",
                            'confidence': 1.0
                        })
        
        return join_suggestions
    
    def refresh_embeddings(self):
        """Force refresh of all embeddings."""
        logger.info("Refreshing semantic embeddings...")
        self._build_semantic_embeddings()
        self._save_embeddings_cache()
        logger.info("Embeddings refreshed successfully")
    
    def get_embedding_stats(self) -> Dict:
        """Get statistics about the embedding index."""
        return {
            'total_tables': len(self.table_embeddings),
            'total_columns': sum(len(cols) for cols in self.column_embeddings.values()),
            'cache_file_exists': self.embedding_cache_file.exists(),
            'cache_age_hours': (
                (datetime.now() - datetime.fromtimestamp(self.embedding_cache_file.stat().st_mtime)).total_seconds() / 3600
                if self.embedding_cache_file.exists() else None
            ),
            'embedding_model': "nomic-embed-text-v1.5"
        }


# Singleton instance for global use
_semantic_indexer_instance = None

def get_semantic_indexer() -> SemanticTableIndexer:
    """Get singleton instance of SemanticTableIndexer."""
    global _semantic_indexer_instance
    if _semantic_indexer_instance is None:
        _semantic_indexer_instance = SemanticTableIndexer()
    return _semantic_indexer_instance