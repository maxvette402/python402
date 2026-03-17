import unittest
import json
from rpc_client import JsonRPCClient


class BitcoinRPCTests(unittest.TestCase):
    """Test suite for Bitcoin RPC Client"""

    def setUp(self):
        """Set up test client"""
        self.client = JsonRPCClient()

    def test_getblockchaininfo(self):
        """Test getblockchaininfo RPC call"""
        print("\n" + "=" * 60)
        print("Testing getblockchaininfo...")
        print("=" * 60)

        try:
            result = self.client.getblockchaininfo()

            print("SUCCESS! Blockchain info received:")
            print(json.dumps(result, indent=2))
            print("=" * 60)

            # Assertions to verify the result structure
            self.assertIsNotNone(result)
            self.assertIsInstance(result, dict)

            # Check for expected fields in blockchain info
            expected_fields = ['chain', 'blocks', 'bestblockhash', 'difficulty']
            for field in expected_fields:
                self.assertIn(field, result, f"Missing expected field: {field}")

            # Verify data types
            self.assertIsInstance(result.get('blocks'), int)
            self.assertIsInstance(result.get('bestblockhash'), str)
            self.assertIsInstance(result.get('chain'), str)

            print(f"✓ Chain: {result.get('chain')}")
            print(f"✓ Block height: {result.get('blocks')}")
            print(f"✓ Best block hash: {result.get('bestblockhash')}")

        except Exception as e:
            print(f"FAILED: {str(e)}")
            self.fail(f"getblockchaininfo test failed: {str(e)}")

    def test_getblockcount(self):
        """Test getblockcount RPC call"""
        print("\n" + "=" * 60)
        print("Testing getblockcount...")
        print("=" * 60)

        try:
            result = self.client.getblockcount()

            print(f"SUCCESS! Current block count: {result}")
            print("=" * 60)

            self.assertIsNotNone(result)
            self.assertIsInstance(result, int)
            self.assertGreaterEqual(result, 0)

        except Exception as e:
            print(f"FAILED: {str(e)}")
            self.fail(f"getblockcount test failed: {str(e)}")

    def test_getbestblockhash(self):
        """Test getbestblockhash RPC call"""
        print("\n" + "=" * 60)
        print("Testing getbestblockhash...")
        print("=" * 60)

        try:
            result = self.client.getbestblockhash()

            print(f"SUCCESS! Best block hash: {result}")
            print("=" * 60)

            self.assertIsNotNone(result)
            self.assertIsInstance(result, str)
            self.assertEqual(len(result), 64)  # Bitcoin block hashes are 64 hex characters

        except Exception as e:
            print(f"FAILED: {str(e)}")
            self.fail(f"getbestblockhash test failed: {str(e)}")

    def test_invalid_method(self):
        """Test handling of invalid RPC method"""
        print("\n" + "=" * 60)
        print("Testing invalid method handling...")
        print("=" * 60)

        with self.assertRaises(Exception) as context:
            self.client.request("invalidmethod")

        error_msg = str(context.exception)
        print(f"Expected error caught: {error_msg}")
        print("=" * 60)

        # Should contain RPC error information
        self.assertIn("RPC error", error_msg)


def run_connection_test():
    """Standalone connection test"""
    print("=" * 60)
    print("BITCOIN RPC CLIENT CONNECTION TEST")
    print("=" * 60)
    print("This test will verify connection to your Bitcoin Core node")
    print(f"Endpoint: {JsonRPCClient().url}")
    print("=" * 60)

    try:
        client = JsonRPCClient()

        # Test basic connectivity
        print("1. Testing basic connectivity...")
        blockchain_info = client.getblockchaininfo()
        print("   ✓ Connected successfully!")

        # Display key information
        print("\n2. Node Information:")
        print(f"   ✓ Network: {blockchain_info.get('chain', 'Unknown')}")
        print(f"   ✓ Block Height: {blockchain_info.get('blocks', 'Unknown')}")
        print(f"   ✓ Sync Progress: {blockchain_info.get('verificationprogress', 0) * 100:.2f}%")

        # Test multiple methods
        print("\n3. Testing additional RPC methods...")
        block_count = client.getblockcount()
        best_hash = client.getbestblockhash()
        print(f"   ✓ Block count: {block_count}")
        print(f"   ✓ Best block: {best_hash[:16]}...")

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! Your Bitcoin RPC client is working correctly.")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ CONNECTION FAILED: {str(e)}")
        print("\n" + "=" * 60)
        print("TROUBLESHOOTING TIPS:")
        print("1. Make sure Bitcoin Core is running")
        print("2. Check your RPC credentials in rpc_client.py")
        print("3. Verify Bitcoin Core RPC is enabled in bitcoin.conf")
        print("4. Ensure the RPC port (8332) is not blocked")
        print("=" * 60)

        return False


if __name__ == "__main__":
    # Run connection test first
    print("Running preliminary connection test...\n")

    if run_connection_test():
        print("\n" + "=" * 60)
        print("RUNNING FULL TEST SUITE")
        print("=" * 60)

        # Run full test suite
        unittest.main(verbosity=2)
    else:
        print("\nSkipping full test suite due to connection failure.")
        print("Please fix the connection issues and try again.")