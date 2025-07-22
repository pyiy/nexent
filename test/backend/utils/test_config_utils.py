import unittest
import json
import os
import time
from unittest.mock import patch, MagicMock, mock_open, ANY
from datetime import datetime

# Mock database modules before importing the module under test
import sys
sys.modules['database.tenant_config_db'] = MagicMock()
sys.modules['database.model_management_db'] = MagicMock()

from backend.utils.config_utils import (
    safe_value,
    safe_list,
    get_env_key,
    get_model_name_from_config,
    get_model_factory_type,
    ConfigManager,
    TenantConfigManager,
    tenant_config_manager
)


class TestConfigUtils(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_safe_value_with_none(self):
        """Test safe_value function with None input"""
        result = safe_value(None)
        self.assertEqual(result, "")

    def test_safe_value_with_string(self):
        """Test safe_value function with string input"""
        result = safe_value("test_string")
        self.assertEqual(result, "test_string")

    def test_safe_value_with_integer(self):
        """Test safe_value function with integer input"""
        result = safe_value(123)
        self.assertEqual(result, "123")

    def test_safe_list_with_none(self):
        """Test safe_list function with None input"""
        result = safe_list(None)
        self.assertEqual(result, "[]")

    def test_safe_list_with_empty_list(self):
        """Test safe_list function with empty list"""
        result = safe_list([])
        self.assertEqual(result, "[]")

    def test_safe_list_with_list(self):
        """Test safe_list function with list input"""
        test_list = ["item1", "item2", 123]
        result = safe_list(test_list)
        expected = json.dumps(test_list)
        self.assertEqual(result, expected)

    def test_get_env_key_camel_case(self):
        """Test get_env_key function with camelCase input"""
        result = get_env_key("camelCase")
        self.assertEqual(result, "CAMEL_CASE")

    def test_get_env_key_with_numbers(self):
        """Test get_env_key function with numbers"""
        result = get_env_key("test123Value")
        self.assertEqual(result, "TEST123_VALUE")

    def test_get_model_name_from_config_none(self):
        """Test get_model_name_from_config with None input"""
        result = get_model_name_from_config(None)
        self.assertEqual(result, "")

    def test_get_model_name_from_config_with_repo(self):
        """Test get_model_name_from_config with model_repo"""
        config = {
            "model_repo": "openai",
            "model_name": "gpt-4"
        }
        result = get_model_name_from_config(config)
        self.assertEqual(result, "openai/gpt-4")

    def test_get_model_name_from_config_without_repo(self):
        """Test get_model_name_from_config without model_repo"""
        config = {
            "model_repo": "",
            "model_name": "gpt-4"
        }
        result = get_model_name_from_config(config)
        self.assertEqual(result, "gpt-4")

    @patch('backend.utils.config_utils.MODEL_ENGINE_HOST', 'http://model-engine.com')
    def test_get_model_factory_type_with_model_engine(self):
        """Test get_model_factory_type with MODEL_ENGINE_HOST in URL"""
        result = get_model_factory_type("http://model-engine.com/api")
        self.assertEqual(result, "restful")

    def test_get_model_factory_type_with_open_router(self):
        """Test get_model_factory_type with open/router in URL"""
        result = get_model_factory_type("https://open/router/ai/api")
        self.assertEqual(result, "restful")

    def test_get_model_factory_type_with_openai(self):
        """Test get_model_factory_type with OpenAI URL"""
        result = get_model_factory_type("https://api.openai.com/v1")
        self.assertEqual(result, "openai")


class TestConfigManager(unittest.TestCase):
    
    def setUp(self):
        self.test_env_file = "test.env"
        self.config_manager = ConfigManager(self.test_env_file)

    def tearDown(self):
        if os.path.exists(self.test_env_file):
            os.remove(self.test_env_file)

    def test_init_with_default_env_file(self):
        """Test ConfigManager initialization with default env file"""
        manager = ConfigManager()
        self.assertEqual(manager.env_file, ".env")

    @patch('os.path.exists')
    @patch('os.path.getmtime')
    @patch('backend.utils.config_utils.load_dotenv')
    def test_load_config_file_not_exists(self, mock_load_dotenv, mock_getmtime, mock_exists):
        """Test load_config when file doesn't exist"""
        mock_exists.return_value = False
        
        self.config_manager.load_config()
        
        mock_load_dotenv.assert_not_called()

    @patch('os.path.exists')
    @patch('os.path.getmtime')
    @patch('backend.utils.config_utils.load_dotenv')
    @patch('os.environ')
    def test_load_config_file_modified(self, mock_environ, mock_load_dotenv, mock_getmtime, mock_exists):
        """Test load_config when file has been modified"""
        mock_exists.return_value = True
        mock_getmtime.return_value = 2000
        mock_environ.items.return_value = [("TEST_KEY", "test_value")]
        self.config_manager.last_modified_time = 1000
        
        self.config_manager.load_config()
        
        mock_load_dotenv.assert_called_once_with(self.test_env_file, override=True)
        self.assertEqual(self.config_manager.config_cache, {"TEST_KEY": "test_value"})

    def test_get_config_default(self):
        """Test get_config with default value"""
        result = self.config_manager.get_config("NONEXISTENT_KEY", "default_value")
        self.assertEqual(result, "default_value")

    @patch('backend.utils.config_utils.set_key')
    def test_set_config(self, mock_set_key):
        """Test set_config method"""
        self.config_manager.set_config("TEST_KEY", "test_value")
        
        self.assertEqual(self.config_manager.config_cache["TEST_KEY"], "test_value")
        mock_set_key.assert_called_once_with(self.test_env_file, "TEST_KEY", "test_value")

    @patch('os.path.exists')
    @patch('os.path.getmtime')
    @patch('backend.utils.config_utils.load_dotenv')
    def test_force_reload(self, mock_load_dotenv, mock_getmtime, mock_exists):
        """Test force_reload method"""
        mock_exists.return_value = True
        mock_getmtime.return_value = 1000
        
        result = self.config_manager.force_reload()
        
        self.assertEqual(result, {"status": "success", "message": "Configuration reloaded"})
        # After force_reload, last_modified_time should be updated to the file's modification time
        self.assertEqual(self.config_manager.last_modified_time, 1000)


class TestTenantConfigManager(unittest.TestCase):
    
    def setUp(self):
        self.tenant_manager = TenantConfigManager()
        self.tenant_id = "test_tenant"
        self.user_id = "test_user"

    def test_get_cache_key(self):
        """Test _get_cache_key method"""
        result = self.tenant_manager._get_cache_key("tenant1", "key1")
        self.assertEqual(result, "tenant1:key1")

    @patch('backend.utils.config_utils.get_all_configs_by_tenant_id')
    def test_load_config_invalid_tenant_id(self, mock_get_configs):
        """Test load_config with invalid tenant_id"""
        result = self.tenant_manager.load_config("")
        self.assertEqual(result, {})
        mock_get_configs.assert_not_called()

    @patch('backend.utils.config_utils.get_all_configs_by_tenant_id')
    def test_load_config_with_configs(self, mock_get_configs):
        """Test load_config with valid configs"""
        mock_configs = [
            {"config_key": "key1", "config_value": "value1"},
            {"config_key": "key2", "config_value": "value2"}
        ]
        mock_get_configs.return_value = mock_configs
        
        result = self.tenant_manager.load_config(self.tenant_id)
        
        expected = {"key1": "value1", "key2": "value2"}
        self.assertEqual(result, expected)
        
        # Check cache was updated
        cache_key = self.tenant_manager._get_cache_key(self.tenant_id, "key1")
        self.assertEqual(self.tenant_manager.config_cache[cache_key], "value1")

    @patch('backend.utils.config_utils.get_model_by_model_id')
    @patch('backend.utils.config_utils.get_all_configs_by_tenant_id')
    def test_get_model_config_success(self, mock_get_configs, mock_get_model):
        """Test get_model_config with successful model retrieval"""
        mock_configs = [{"config_key": "LLM_ID", "config_value": "123"}]
        mock_get_configs.return_value = mock_configs
        
        mock_model_config = {"model_name": "gpt-4", "api_key": "fake-key"}
        mock_get_model.return_value = mock_model_config
        
        result = self.tenant_manager.get_model_config("LLM_ID", tenant_id=self.tenant_id)
        
        self.assertEqual(result, mock_model_config)
        mock_get_model.assert_called_once_with(model_id=123, tenant_id=self.tenant_id)

    @patch('backend.utils.config_utils.get_all_configs_by_tenant_id')
    def test_get_model_config_no_tenant_id(self, mock_get_configs):
        """Test get_model_config without tenant_id"""
        result = self.tenant_manager.get_model_config("LLM_ID")
        
        self.assertEqual(result, {})
        mock_get_configs.assert_not_called()

    @patch('backend.utils.config_utils.get_all_configs_by_tenant_id')
    def test_get_app_config_success(self, mock_get_configs):
        """Test get_app_config with successful retrieval"""
        mock_configs = [{"config_key": "APP_KEY", "config_value": "app_value"}]
        mock_get_configs.return_value = mock_configs
        
        result = self.tenant_manager.get_app_config("APP_KEY", tenant_id=self.tenant_id)
        
        self.assertEqual(result, "app_value")

    @patch('backend.utils.config_utils.insert_config')
    @patch('backend.utils.config_utils.get_all_configs_by_tenant_id')
    def test_set_single_config_success(self, mock_get_configs, mock_insert_config):
        """Test set_single_config with successful insertion"""
        mock_get_configs.return_value = []
        
        self.tenant_manager.set_single_config(
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            key="TEST_KEY",
            value="test_value"
        )
        
        mock_insert_config.assert_called_once()
        call_args = mock_insert_config.call_args[0][0]
        self.assertEqual(call_args["user_id"], self.user_id)
        self.assertEqual(call_args["tenant_id"], self.tenant_id)
        self.assertEqual(call_args["config_key"], "TEST_KEY")
        self.assertEqual(call_args["config_value"], "test_value")

    @patch('backend.utils.config_utils.delete_config_by_tenant_config_id')
    @patch('backend.utils.config_utils.get_single_config_info')
    @patch('backend.utils.config_utils.get_all_configs_by_tenant_id')
    def test_delete_single_config_success(self, mock_get_configs, mock_get_single_config, mock_delete_config):
        """Test delete_single_config with successful deletion"""
        mock_get_configs.return_value = []
        mock_get_single_config.return_value = {"tenant_config_id": 123}
        
        self.tenant_manager.delete_single_config(tenant_id=self.tenant_id, key="TEST_KEY")
        
        mock_get_single_config.assert_called_once_with(self.tenant_id, "TEST_KEY")
        mock_delete_config.assert_called_once_with(123)

    @patch('backend.utils.config_utils.update_config_by_tenant_config_id_and_data')
    @patch('backend.utils.config_utils.get_single_config_info')
    def test_update_single_config_success(self, mock_get_single_config, mock_update_config):
        """Test update_single_config with successful update"""
        mock_get_single_config.return_value = {"tenant_config_id": 123}
        
        self.tenant_manager.update_single_config(tenant_id=self.tenant_id, key="TEST_KEY")
        
        mock_get_single_config.assert_called_once_with(self.tenant_id, "TEST_KEY")
        mock_update_config.assert_called_once()
        call_args = mock_update_config.call_args[0]
        self.assertEqual(call_args[0], 123)  # tenant_config_id
        self.assertIn("updated_by", call_args[1])
        self.assertIn("update_time", call_args[1])

    def test_clear_cache_specific_tenant(self):
        """Test clear_cache for specific tenant"""
        # Set up cache with multiple tenants
        self.tenant_manager.config_cache = {
            "tenant1:key1": "value1",
            "tenant1:key2": "value2",
            "tenant2:key1": "value3"
        }
        self.tenant_manager.cache_expiry = {
            "tenant1:key1": 1000,
            "tenant1:key2": 1000,
            "tenant2:key1": 1000
        }
        
        self.tenant_manager.clear_cache("tenant1")
        
        # Check that only tenant1 cache was cleared
        self.assertNotIn("tenant1:key1", self.tenant_manager.config_cache)
        self.assertNotIn("tenant1:key2", self.tenant_manager.config_cache)
        self.assertIn("tenant2:key1", self.tenant_manager.config_cache)

    def test_clear_cache_all_tenants(self):
        """Test clear_cache for all tenants"""
        # Set up cache
        self.tenant_manager.config_cache = {
            "tenant1:key1": "value1",
            "tenant2:key1": "value2"
        }
        self.tenant_manager.cache_expiry = {
            "tenant1:key1": 1000,
            "tenant2:key1": 1000
        }
        
        self.tenant_manager.clear_cache()
        
        # Check that all cache was cleared
        self.assertEqual(len(self.tenant_manager.config_cache), 0)
        self.assertEqual(len(self.tenant_manager.cache_expiry), 0)


class TestGlobalInstances(unittest.TestCase):
    
    def test_tenant_config_manager_instance(self):
        """Test that tenant_config_manager is properly instantiated"""
        from backend.utils.config_utils import tenant_config_manager
        
        self.assertIsInstance(tenant_config_manager, TenantConfigManager)
        self.assertEqual(tenant_config_manager.CACHE_DURATION, 86400)


if __name__ == '__main__':
    unittest.main() 