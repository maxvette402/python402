#!/usr/bin/env python3
"""
Test Suite for Bitcoin BIP-39 Brute Force Tool
Comprehensive unit and integration tests for all components
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bitcoin_rpc_client import BitcoinRPCClient, BitcoinRPCError
    from bitcoin_bip39_bruteforce import (
        BruteForceConfig, AddressGenerator, BIP39BruteForcer
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required modules are available")
    sys.exit(1)


class TestBitcoinRPCClient(unittest.TestCase):
    """Test Bitcoin RPC Client functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = BitcoinRPCClient(
            host="127.0.0.1",
            port=8332,
            user="testuser",
            password="testpass",
            timeout=10
        )
    
    def test_client_initialization(self):
        """Test RPC client initialization"""
        self.assertEqual(self.client.host, "127.0.0.1")
        self.assertEqual(self.client.port, 8332)
        self.assertEqual(self.client.user, "testuser")
        self.assertEqual(self.client.password, "testpass")
        self.assertEqual(self.client.url, "http://127.0.0.1:8332/")
    
    def test_ssl_initialization(self):
        """Test SSL configuration"""
        ssl_client = BitcoinRPCClient(
            host="127.0.0.1",
            port=8332,
            user="testuser",
            password="testpass",
            use_ssl=True,
            ssl_verify=False
        )
        self.assertEqual(ssl_client.url, "https://127.0.0.1:8332/")
    
    @patch('requests.Session.post')
    def test_successful_rpc_request(self, mock_post):
        """Test successful RPC request"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": {"blocks": 800000, "chain": "main"},
            "error": None,
            "id": 1
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = self.client._make_request("getblockchaininfo")
        
        self.assertEqual(result["blocks"], 800000)
        self.assertEqual(result["chain"], "main")
    
    @patch('requests.Session.post')
    def test_rpc_error_handling(self, mock_post):
        """Test RPC error handling"""
        # Mock error response
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": None,
            "error": {"code": -32601, "message": "Method not found"},
            "id": 1
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        with self.assertRaises(BitcoinRPCError) as context:
            self.client._make_request("nonexistent_method")
        
        self.assertIn("Method not found", str(context.exception))
    
    @patch('requests.Session.post')
    def test_connection_error_handling(self, mock_post):
        """Test connection error handling"""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with self.assertRaises(BitcoinRPCError) as context:
            self.client._make_request("getblockchaininfo")
        
        self.assertIn("Connection error", str(context.exception))
    
    @patch('requests.Session.post')
    def test_batch_scan_addresses(self, mock_post):
        """Test batch address scanning"""
        # Mock scantxoutset response
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": {
                "success": True,
                "txouts": 2,
                "height": 800000,
                "bestblock": "0000000000000000000",
                "unspents": [
                    {
                        "txid": "abc123",
                        "vout": 0,
                        "scriptPubKey": "76a914...",
                        "desc": "addr(1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa)",
                        "amount": 0.00100000,
                        "height": 123456
                    },
                    {
                        "txid": "def456",
                        "vout": 1,
                        "scriptPubKey": "00147f9b...",
                        "desc": "addr(bc1q07dmhwag4a8zy4x5jq8uqczhc82wd9hg5p6pwz)",
                        "amount": 0.00050000,
                        "height": 123457
                    }
                ],
                "total_amount": 0.00150000
            },
            "error": None,
            "id": 1
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        addresses = [
            "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "bc1q07dmhwag4a8zy4x5jq8uqczhc82wd9hg5p6pwz",
            "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"
        ]
        
        balances = self.client.batch_scan_addresses(addresses)
        
        self.assertEqual(balances["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"], 0.001)
        self.assertEqual(balances["bc1q07dmhwag4a8zy4x5jq8uqczhc82wd9hg5p6pwz"], 0.0005)
        self.assertEqual(balances["3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"], 0.0)


class TestBruteForceConfig(unittest.TestCase):
    """Test configuration management"""
    
    def setUp(self):
        """Set up test environment file"""
        self.temp_env = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
        self.temp_env.write("""
BITCOIN_RPC_HOST=192.168.1.100
BITCOIN_RPC_PORT=8333
BITCOIN_RPC_USER=bitcoinrpc
BITCOIN_RPC_PASSWORD=secretpassword123
BITCOIN_RPC_TIMEOUT=45
BITCOIN_NETWORK=testnet
BITCOIN_RPC_USE_SSL=true
BITCOIN_RPC_SSL_VERIFY=false
LOG_LEVEL=WARNING
MAX_COMBINATIONS_WARNING=500000
BATCH_SIZE=50
ADDRESSES_TO_SCAN=10
        """.strip())
        self.temp_env.close()
    
    def tearDown(self):
        """Clean up temporary files"""
        os.unlink(self.temp_env.name)
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('dotenv.load_dotenv')
    def test_default_configuration(self, mock_load_dotenv):
        """Test default configuration values"""
        config = BruteForceConfig()
        
        self.assertEqual(config.rpc_host, '127.0.0.1')
        self.assertEqual(config.rpc_port, 8332)
        self.assertEqual(config.network, 'mainnet')
        self.assertEqual(config.log_level, 'INFO')
        self.assertEqual(config.batch_size, 100)
    
    @patch.dict(os.environ, {
        'BITCOIN_RPC_HOST': '192.168.1.100',
        'BITCOIN_RPC_PORT': '8333',
        'BITCOIN_NETWORK': 'testnet',
        'LOG_LEVEL': 'DEBUG'
    })
    def test_environment_override(self):
        """Test environment variable override"""
        config = BruteForceConfig()
        
        self.assertEqual(config.rpc_host, '192.168.1.100')
        self.assertEqual(config.rpc_port, 8333)
        self.assertEqual(config.network, 'testnet')
        self.assertEqual(config.log_level, 'DEBUG')


class TestAddressGenerator(unittest.TestCase):
    """Test Bitcoin address generation"""
    
    def setUp(self):
        """Set up test seed phrase"""
        # Valid test seed phrase (DO NOT USE IN PRODUCTION)
        self.test_seed = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        self.test_passphrase = ""
    
    def test_legacy_address_generation(self):
        """Test legacy address generation"""
        addresses = AddressGenerator.generate_addresses(
            self.test_seed, self.test_passphrase, 'legacy', 5
        )
        
        self.assertEqual(len(addresses), 5)
        # Legacy addresses start with '1'
        for addr in addresses:
            self.assertTrue(addr.startswith('1'))
    
    def test_segwit_address_generation(self):
        """Test SegWit address generation"""
        addresses = AddressGenerator.generate_addresses(
            self.test_seed, self.test_passphrase, 'segwit', 5
        )
        
        self.assertEqual(len(addresses), 5)
        # SegWit addresses start with 'bc1q'
        for addr in addresses:
            self.assertTrue(addr.startswith('bc1q'))
    
    def test_taproot_address_generation(self):
        """Test Taproot address generation"""
        addresses = AddressGenerator.generate_addresses(
            self.test_seed, self.test_passphrase, 'taproot', 3
        )
        
        self.assertEqual(len(addresses), 3)
        # Taproot addresses start with 'bc1p'
        for addr in addresses:
            self.assertTrue(addr.startswith('bc1p'))
    
    def test_invalid_address_type(self):
        """Test invalid address type handling"""
        with self.assertRaises(ValueError):
            AddressGenerator.generate_addresses(
                self.test_seed, self.test_passphrase, 'invalid_type', 1
            )
    
    def test_passphrase_affects_addresses(self):
        """Test that passphrase affects generated addresses"""
        addresses1 = AddressGenerator.generate_addresses(
            self.test_seed, "", 'segwit', 1
        )
        addresses2 = AddressGenerator.generate_addresses(
            self.test_seed, "passphrase123", 'segwit', 1
        )
        
        self.assertNotEqual(addresses1[0], addresses2[0])


class TestBIP39BruteForcer(unittest.TestCase):
    """Test BIP-39 brute force functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary wordlist file
        self.temp_wordlist = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        test_words = ["abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract"]
        self.temp_wordlist.write("\n".join(test_words))
        self.temp_wordlist.close()
        
        # Mock configuration
        self.mock_config = Mock()
        self.mock_config.rpc_host = "127.0.0.1"
        self.mock_config.rpc_port = 8332
        self.mock_config.rpc_user = "testuser"
        self.mock_config.rpc_password = "testpass"
        self.mock_config.rpc_timeout = 30
        self.mock_config.use_ssl = False
        self.mock_config.ssl_verify = True
        self.mock_config.ssl_cert_path = ""
        self.mock_config.log_level = "INFO"
        self.mock_config.log_file = ""
        self.mock_config.wordlist_file = self.temp_wordlist.name
        self.mock_config.max_combinations_warning = 1000
        self.mock_config.addresses_to_scan = 5
        self.mock_config.scan_delay_ms = 0
    
    def tearDown(self):
        """Clean up temporary files"""
        os.unlink(self.temp_wordlist.name)
    
    @patch('bitcoin_bip39_bruteforce.BitcoinRPCClient')
    def test_brute_forcer_initialization(self, mock_rpc_client):
        """Test brute forcer initialization"""
        brute_forcer = BIP39BruteForcer(self.mock_config)
        
        self.assertIsNotNone(brute_forcer.wordlist)
        self.assertEqual(len(brute_forcer.wordlist), 8)
        self.assertIn("abandon", brute_forcer.wordlist)
    
    def test_parse_partial_seed_valid(self):
        """Test parsing valid partial seed"""
        brute_forcer = BIP39BruteForcer(self.mock_config)
        
        partial_seed = "abandon abandon ? abandon abandon abandon abandon abandon abandon abandon abandon ?"
        words, missing_positions = brute_forcer.parse_partial_seed(partial_seed)
        
        self.assertEqual(len(words), 12)
        self.assertEqual(missing_positions, [2, 11])
        self.assertEqual(words[0], "abandon")
        self.assertEqual(words[2], "?")
    
    def test_parse_partial_seed_no_missing(self):
        """Test parsing seed with no missing words"""
        brute_forcer = BIP39BruteForcer(self.mock_config)
        
        partial_seed = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        
        with self.assertRaises(ValueError) as context:
            brute_forcer.parse_partial_seed(partial_seed)
        
        self.assertIn("No missing words found", str(context.exception))
    
    def test_parse_partial_seed_invalid_length(self):
        """Test parsing seed with invalid length"""
        brute_forcer = BIP39BruteForcer(self.mock_config)
        
        partial_seed = "abandon abandon ? abandon abandon"  # Only 5 words
        
        with self.assertRaises(ValueError) as context:
            brute_forcer.parse_partial_seed(partial_seed)
        
        self.assertIn("Invalid seed length", str(context.exception))
    
    @patch('bitcoin_bip39_bruteforce.BitcoinRPCClient')
    def test_generate_combinations(self, mock_rpc_client):
        """Test combination generation"""
        brute_forcer = BIP39BruteForcer(self.mock_config)
        
        words = ["abandon", "?", "about"]
        missing_positions = [1]
        
        combinations = list(brute_forcer.generate_combinations(words, missing_positions))
        
        # Should generate one combination for each word in wordlist
        self.assertEqual(len(combinations), len(brute_forcer.wordlist))
        
        # Each combination should have the missing word filled
        for combo in combinations:
            self.assertEqual(len(combo), 3)
            self.assertEqual(combo[0], "abandon")
            self.assertEqual(combo[2], "about")
            self.assertIn(combo[1], brute_forcer.wordlist)
    
    @patch('bitcoin_bip39_bruteforce.BitcoinRPCClient')
    @patch('bitcoin_bip39_bruteforce.AddressGenerator.generate_addresses')
    def test_scan_seed_phrase_with_balance(self, mock_generate_addresses, mock_rpc_client):
        """Test seed phrase scanning with positive balance"""
        # Setup mocks
        mock_addresses = ["bc1qtest1", "bc1qtest2"]
        mock_generate_addresses.return_value = mock_addresses
        
        mock_rpc_instance = Mock()
        mock_rpc_instance.batch_scan_addresses.return_value = {
            "bc1qtest1": 0.001,
            "bc1qtest2": 0.0
        }
        mock_rpc_client.return_value = mock_rpc_instance
        
        brute_forcer = BIP39BruteForcer(self.mock_config)
        brute_forcer.rpc_client = mock_rpc_instance
        
        result = brute_forcer.scan_seed_phrase(
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
            "",
            "segwit"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['total_balance'], 0.001)
        self.assertIn("bc1qtest1", result['funded_addresses'])
    
    @patch('bitcoin_bip39_bruteforce.BitcoinRPCClient')
    @patch('bitcoin_bip39_bruteforce.AddressGenerator.generate_addresses')
    def test_scan_seed_phrase_no_balance(self, mock_generate_addresses, mock_rpc_client):
        """Test seed phrase scanning with no balance"""
        # Setup mocks
        mock_addresses = ["bc1qtest1", "bc1qtest2"]
        mock_generate_addresses.return_value = mock_addresses
        
        mock_rpc_instance = Mock()
        mock_rpc_instance.batch_scan_addresses.return_value = {
            "bc1qtest1": 0.0,
            "bc1qtest2": 0.0
        }
        mock_rpc_client.return_value = mock_rpc_instance
        
        brute_forcer = BIP39BruteForcer(self.mock_config)
        brute_forcer.rpc_client = mock_rpc_instance
        
        result = brute_forcer.scan_seed_phrase(
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
            "",
            "segwit"
        )
        
        self.assertIsNone(result)


class IntegrationTests(unittest.TestCase):
    """Integration tests for full system functionality"""
    
    def setUp(self):
        """Set up integration test environment"""
        # These tests require a running Bitcoin node
        # Skip if not available
        self.bitcoin_available = self._check_bitcoin_node()
    
    def _check_bitcoin_node(self) -> bool:
        """Check if Bitcoin node is available for testing"""
        try:
            # Try to connect to default regtest node
            client = BitcoinRPCClient(
                host="127.0.0.1",
                port=18443,  # Default regtest port
                user="test",
                password="test",
                timeout=5
            )
            return client.test_connection()
        except Exception:
            return False
    
    def test_full_integration_regtest(self):
        """Test full integration with regtest node"""
        if not self.bitcoin_available:
            self.skipTest("Bitcoin regtest node not available")
        
        # This test would require setting up a regtest environment
        # with known addresses and balances
        pass
    
    def test_error_recovery(self):
        """Test error recovery and fallback mechanisms"""
        # Test connection timeout
        client = BitcoinRPCClient(
            host="127.0.0.1",
            port=99999,  # Non-existent port
            user="test",
            password="test",
            timeout=1
        )
        
        self.assertFalse(client.test_connection())


class SecurityTests(unittest.TestCase):
    """Security-focused tests"""
    
    def test_no_credential_leakage(self):
        """Test that credentials don't appear in logs or errors"""
        client = BitcoinRPCClient(
            host="127.0.0.1",
            port=8332,
            user="secret_user",
            password="super_secret_password",
            timeout=1
        )
        
        # Simulate connection error
        with patch('requests.Session.post') as mock_post:
            import requests
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            try:
                client._make_request("getinfo")
            except BitcoinRPCError as e:
                error_message = str(e)
                self.assertNotIn("secret_user", error_message)
                self.assertNotIn("super_secret_password", error_message)
    
    def test_ssl_certificate_validation(self):
        """Test SSL certificate validation"""
        # Test that SSL verification is properly configured
        ssl_client = BitcoinRPCClient(
            host="127.0.0.1",
            port=8332,
            user="test",
            password="test",
            use_ssl=True,
            ssl_verify=True
        )
        
        self.assertTrue(ssl_client.session.verify)
    
    def test_input_sanitization(self):
        """Test input sanitization for seed phrases"""
        from bitcoin_bip39_bruteforce import BIP39BruteForcer
        
        config = Mock()
        config.wordlist_file = "nonexistent.txt"
        
        # Test that file not found is handled gracefully
        with self.assertRaises(FileNotFoundError):
            BIP39BruteForcer(config)


def run_test_suite():
    """Run the complete test suite"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestBitcoinRPCClient,
        TestBruteForceConfig,
        TestAddressGenerator,
        TestBIP39BruteForcer,
        IntegrationTests,
        SecurityTests
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Bitcoin BIP-39 Brute Force - Test Suite")
    print("=" * 50)
    
    success = run_test_suite()
    sys.exit(0 if success else 1)
