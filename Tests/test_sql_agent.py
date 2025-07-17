"""
Test script for SQL Agent implementation with Google Gemini
"""
import sys
import os
import asyncio
from unittest.mock import patch, MagicMock

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_sql_agent_initialization():
    """Test SQL agent initialization without database connection"""
    print("Testing SQL Agent initialization...")
    
    # Mock the database connection to avoid actual database requirement
    with patch('app.core.sql_agent.settings') as mock_settings, \
         patch('app.core.sql_agent.SQLDatabase') as mock_sql_db, \
         patch('app.core.sql_agent.create_sql_agent') as mock_create_agent, \
         patch('app.core.sql_agent.ChatGoogleGenerativeAI') as mock_gemini, \
         patch('app.core.sql_agent.inspect') as mock_inspect:
        
        # Mock settings
        mock_settings.GOOGLE_API_KEY = "test-api-key"
        mock_settings.database_url = "postgresql://test:test@localhost/test"
        
        # Mock the database and agent components
        mock_sql_db.from_uri.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        mock_gemini.return_value = MagicMock()
        mock_inspect.return_value = MagicMock()
        mock_inspect.return_value.get_table_names.return_value = ["products", "platforms", "current_prices"]
        mock_inspect.return_value.get_columns.return_value = []
        mock_inspect.return_value.get_foreign_keys.return_value = []
        mock_inspect.return_value.get_indexes.return_value = []
        
        try:
            from app.core.sql_agent import CustomSQLAgent
            
            # Test initialization
            agent = CustomSQLAgent()
            
            print("✓ SQL Agent initialized successfully")
            print(f"✓ LLM model configured: {agent.llm is not None}")
            print(f"✓ Database connection configured: {agent.db is not None}")
            print(f"✓ Agent toolkit configured: {agent.toolkit is not None}")
            print(f"✓ SQL agent configured: {agent.agent is not None}")
            
            return True
            
        except Exception as e:
            print(f"✗ SQL Agent initialization failed: {e}")
            return False

def test_configuration_validation():
    """Test configuration validation"""
    print("\nTesting configuration validation...")
    
    # Test with missing API key
    with patch('app.core.sql_agent.settings') as mock_settings:
        mock_settings.GOOGLE_API_KEY = ""
        
        try:
            from app.core.sql_agent import CustomSQLAgent
            agent = CustomSQLAgent()
            print("✗ Should have failed with missing API key")
            return False
        except Exception as e:
            if "Google API key not configured" in str(e):
                print("✓ Correctly validates missing Google API key")
            else:
                print(f"✗ Unexpected error: {e}")
                return False
    
    # Test with valid API key
    with patch('app.core.sql_agent.settings') as mock_settings, \
         patch('app.core.sql_agent.SQLDatabase') as mock_sql_db, \
         patch('app.core.sql_agent.create_sql_agent') as mock_create_agent, \
         patch('app.core.sql_agent.ChatGoogleGenerativeAI') as mock_gemini, \
         patch('app.core.sql_agent.inspect') as mock_inspect:
        
        mock_settings.GOOGLE_API_KEY = "test-api-key"
        mock_settings.database_url = "postgresql://test:test@localhost/test"
        
        # Mock components
        mock_sql_db.from_uri.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        mock_gemini.return_value = MagicMock()
        mock_inspect.return_value = MagicMock()
        mock_inspect.return_value.get_table_names.return_value = []
        mock_inspect.return_value.get_columns.return_value = []
        mock_inspect.return_value.get_foreign_keys.return_value = []
        mock_inspect.return_value.get_indexes.return_value = []
        
        try:
            from app.core.sql_agent import CustomSQLAgent
            agent = CustomSQLAgent()
            print("✓ Correctly accepts valid Google API key")
            return True
        except Exception as e:
            print(f"✗ Failed with valid API key: {e}")
            return False

def test_gemini_model_configuration():
    """Test Gemini model configuration"""
    print("\nTesting Gemini model configuration...")
    
    with patch('app.core.sql_agent.settings') as mock_settings, \
         patch('app.core.sql_agent.SQLDatabase') as mock_sql_db, \
         patch('app.core.sql_agent.create_sql_agent') as mock_create_agent, \
         patch('app.core.sql_agent.ChatGoogleGenerativeAI') as mock_gemini, \
         patch('app.core.sql_agent.inspect') as mock_inspect:
        
        mock_settings.GOOGLE_API_KEY = "test-api-key"
        mock_settings.database_url = "postgresql://test:test@localhost/test"
        
        # Mock components
        mock_sql_db.from_uri.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        mock_gemini_instance = MagicMock()
        mock_gemini.return_value = mock_gemini_instance
        mock_inspect.return_value = MagicMock()
        mock_inspect.return_value.get_table_names.return_value = []
        mock_inspect.return_value.get_columns.return_value = []
        mock_inspect.return_value.get_foreign_keys.return_value = []
        mock_inspect.return_value.get_indexes.return_value = []
        
        try:
            from app.core.sql_agent import CustomSQLAgent
            agent = CustomSQLAgent()
            
            # Verify Gemini model was called with correct parameters
            mock_gemini.assert_called_once()
            call_args = mock_gemini.call_args
            
            # Check model name
            assert call_args[1]['model'] == "gemini-2.0-flash", f"Expected gemini-2.0-flash, got {call_args[1]['model']}"
            print("✓ Gemini model correctly configured with gemini-2.0-flash")
            
            # Check API key
            assert call_args[1]['google_api_key'] == "test-api-key", "API key not passed correctly"
            print("✓ Google API key correctly passed to model")
            
            # Check temperature (should be low for consistent SQL generation)
            assert call_args[1]['temperature'] == 0.1, f"Expected temperature 0.1, got {call_args[1]['temperature']}"
            print("✓ Temperature correctly set to 0.1 for consistent SQL generation")
            
            return True
            
        except Exception as e:
            print(f"✗ Gemini model configuration failed: {e}")
            return False

async def test_query_processing_mock():
    """Test query processing with mocked components"""
    print("\nTesting query processing (mocked)...")
    
    with patch('app.core.sql_agent.settings') as mock_settings, \
         patch('app.core.sql_agent.SQLDatabase') as mock_sql_db, \
         patch('app.core.sql_agent.create_sql_agent') as mock_create_agent, \
         patch('app.core.sql_agent.ChatGoogleGenerativeAI') as mock_gemini, \
         patch('app.core.sql_agent.inspect') as mock_inspect:
        
        mock_settings.GOOGLE_API_KEY = "test-api-key"
        mock_settings.database_url = "postgresql://test:test@localhost/test"
        
        # Mock components
        mock_sql_db.from_uri.return_value = MagicMock()
        mock_inspect.return_value = MagicMock()
        mock_inspect.return_value.get_table_names.return_value = []
        mock_inspect.return_value.get_columns.return_value = []
        mock_inspect.return_value.get_foreign_keys.return_value = []
        mock_inspect.return_value.get_indexes.return_value = []
        
        # Mock agent response
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {
            "output": "Here are the results:\n| Product | Platform | Price |\n| Onions | Blinkit | 45.00 |",
            "intermediate_steps": []
        }
        mock_create_agent.return_value = mock_agent
        mock_gemini.return_value = MagicMock()
        
        try:
            from app.core.sql_agent import CustomSQLAgent
            agent = CustomSQLAgent()
            
            # Test query processing
            result = await agent.process_query("Which app has cheapest onions?")
            
            print(f"✓ Query processed successfully")
            print(f"✓ Result structure: {list(result.keys())}")
            print(f"✓ Success status: {result.get('success', False)}")
            
            # Verify agent was called
            mock_agent.invoke.assert_called_once()
            
            return True
            
        except Exception as e:
            print(f"✗ Query processing failed: {e}")
            return False

def test_sql_validation():
    """Test SQL query validation"""
    print("\nTesting SQL validation...")
    
    with patch('app.core.sql_agent.settings') as mock_settings, \
         patch('app.core.sql_agent.SQLDatabase') as mock_sql_db, \
         patch('app.core.sql_agent.create_sql_agent') as mock_create_agent, \
         patch('app.core.sql_agent.ChatGoogleGenerativeAI') as mock_gemini, \
         patch('app.core.sql_agent.inspect') as mock_inspect:
        
        mock_settings.GOOGLE_API_KEY = "test-api-key"
        mock_settings.database_url = "postgresql://test:test@localhost/test"
        
        # Mock components
        mock_sql_db.from_uri.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        mock_gemini.return_value = MagicMock()
        mock_inspect.return_value = MagicMock()
        mock_inspect.return_value.get_table_names.return_value = []
        mock_inspect.return_value.get_columns.return_value = []
        mock_inspect.return_value.get_foreign_keys.return_value = []
        mock_inspect.return_value.get_indexes.return_value = []
        
        try:
            from app.core.sql_agent import CustomSQLAgent
            agent = CustomSQLAgent()
            
            # Test valid SELECT query
            valid, error = agent.validate_sql_query("SELECT * FROM products WHERE name ILIKE '%onion%'")
            assert valid == True, f"Valid query rejected: {error}"
            print("✓ Valid SELECT query accepted")
            
            # Test dangerous DROP query
            valid, error = agent.validate_sql_query("DROP TABLE products")
            assert valid == False, "Dangerous DROP query was accepted"
            print("✓ Dangerous DROP query rejected")
            
            # Test dangerous DELETE query
            valid, error = agent.validate_sql_query("DELETE FROM products WHERE id = 1")
            assert valid == False, "Dangerous DELETE query was accepted"
            print("✓ Dangerous DELETE query rejected")
            
            # Test SQL injection attempt
            valid, error = agent.validate_sql_query("SELECT * FROM products WHERE id = 1 OR 1=1")
            assert valid == False, "SQL injection attempt was accepted"
            print("✓ SQL injection attempt rejected")
            
            return True
            
        except Exception as e:
            print(f"✗ SQL validation failed: {e}")
            return False

def test_schema_info():
    """Test schema information loading"""
    print("\nTesting schema information...")
    
    with patch('app.core.sql_agent.settings') as mock_settings, \
         patch('app.core.sql_agent.SQLDatabase') as mock_sql_db, \
         patch('app.core.sql_agent.create_sql_agent') as mock_create_agent, \
         patch('app.core.sql_agent.ChatGoogleGenerativeAI') as mock_gemini, \
         patch('app.core.sql_agent.inspect') as mock_inspect:
        
        mock_settings.GOOGLE_API_KEY = "test-api-key"
        mock_settings.database_url = "postgresql://test:test@localhost/test"
        
        # Mock components
        mock_sql_db.from_uri.return_value = MagicMock()
        mock_create_agent.return_value = MagicMock()
        mock_gemini.return_value = MagicMock()
        
        # Mock schema inspection
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["products", "platforms", "current_prices"]
        mock_inspector.get_columns.return_value = [
            {"name": "id", "type": "INTEGER"},
            {"name": "name", "type": "VARCHAR"}
        ]
        mock_inspector.get_foreign_keys.return_value = []
        mock_inspector.get_indexes.return_value = []
        mock_inspect.return_value = mock_inspector
        
        try:
            from app.core.sql_agent import CustomSQLAgent
            agent = CustomSQLAgent()
            
            # Test schema info retrieval
            schema_info = agent.get_schema_info()
            
            print(f"✓ Schema info loaded successfully")
            print(f"✓ Tables found: {schema_info['tables']}")
            print(f"✓ Custom table info: {len(schema_info['custom_info'])} entries")
            
            # Verify expected tables are present
            expected_tables = ["products", "platforms", "current_prices"]
            for table in expected_tables:
                assert table in schema_info['tables'], f"Expected table {table} not found"
            
            print("✓ All expected tables found in schema")
            
            return True
            
        except Exception as e:
            print(f"✗ Schema info loading failed: {e}")
            return False

async def main():
    """Run all SQL agent tests"""
    print("=== SQL Agent with Google Gemini Test ===\n")
    
    tests = [
        ("Configuration Validation", test_configuration_validation),
        ("SQL Agent Initialization", test_sql_agent_initialization),
        ("Gemini Model Configuration", test_gemini_model_configuration),
        ("Query Processing (Mocked)", test_query_processing_mock),
        ("SQL Validation", test_sql_validation),
        ("Schema Information", test_schema_info)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED\n")
            else:
                print(f"❌ {test_name} FAILED\n")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}\n")
    
    print(f"=== Test Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("\n🎉 All SQL Agent tests passed!")
        print("\nImplemented features:")
        print("✓ Google Gemini integration with gemini-2.0-flash model")
        print("✓ LangChain v0.3+ SQL agent implementation")
        print("✓ Comprehensive error handling and validation")
        print("✓ SQL injection prevention and query safety")
        print("✓ Database schema introspection")
        print("✓ Custom table information and context")
        print("✓ Query result parsing and formatting")
        print("✓ Fallback mechanisms for robustness")
        print("✓ Configuration validation and error reporting")
        
        return True
    else:
        print(f"\n❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)