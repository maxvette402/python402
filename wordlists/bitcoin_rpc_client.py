"""
Bitcoin RPC Client for local node communication
Handles authentication, connection management, and Bitcoin-specific RPC calls
"""

import json
import logging
import time
from typing import List, Dict, Any, Optional
import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class BitcoinRPCError(Exception):
    """Custom exception for Bitcoin RPC errors"""
    def __init__(self, message: str, code: int = None, details: str = None):
        super().__init__(message)
        self.code = code
        self.details = details


class BitcoinRPCClient:
    """
    Bitcoin RPC Client for communicating with Bitcoin Core node
    """
    
    def __init__(self, host: str, port: int, user: str, password: str, 
                 timeout: int = 30, use_ssl: bool = False, ssl_verify: bool = True,
                 ssl_cert_path: str = None):
        """
        Initialize Bitcoin RPC client
        
        Args:
            host: Bitcoin node hostname/IP
            port: Bitcoin node RPC port
            user: RPC username
            password: RPC password
            timeout: Request timeout in seconds
            use_ssl: Whether to use HTTPS
            ssl_verify: Whether to verify SSL certificates
            ssl_cert_path: Path to SSL certificate file
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.timeout = timeout
        
        # Build RPC URL
        protocol = "https" if use_ssl else "http"
        self.url = f"{protocol}://{host}:{port}/"
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Authentication
        self.session.auth = HTTPBasicAuth(user, password)
        
        # SSL configuration
        if use_ssl:
            self.session.verify = ssl_verify
            if ssl_cert_path:
                self.session.verify = ssl_cert_path
        
        # Request headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'bitcoin-bip39-bruteforce/1.0'
        })
        
        self.logger = logging.getLogger(__name__)
    
    def _make_request(self, method: str, params: List[Any] = None) -> Dict[Any, Any]:
        """
        Make RPC request to Bitcoin node
        
        Args:
            method: RPC method name
            params: RPC method parameters
            
        Returns:
            RPC response data
            
        Raises:
            BitcoinRPCError: On RPC or connection errors
        """
        if params is None:
            params = []
        
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time()),
            "method": method,
            "params": params
        }
        
        try:
            self.logger.debug(f"RPC Request: {method} with params: {params}")
            
            response = self.session.post(
                self.url,
                data=json.dumps(payload),
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            if "error" in result and result["error"]:
                error = result["error"]
                raise BitcoinRPCError(
                    f"RPC Error in {method}: {error.get('message', 'Unknown error')}",
                    code=error.get('code'),
                    details=str(error)
                )
            
            self.logger.debug(f"RPC Response: {method} successful")
            return result.get("result")
            
        except requests.exceptions.RequestException as e:
            raise BitcoinRPCError(f"Connection error: {str(e)}")
        except json.JSONDecodeError as e:
            raise BitcoinRPCError(f"JSON decode error: {str(e)}")
        except Exception as e:
            raise BitcoinRPCError(f"Unexpected error: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        Test connection to Bitcoin node
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            info = self.get_blockchain_info()
            self.logger.info(f"Connected to Bitcoin Core {info.get('version', 'unknown')} "
                           f"on {info.get('chain', 'unknown')} network")
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def get_blockchain_info(self) -> Dict[str, Any]:
        """Get blockchain information"""
        return self._make_request("getblockchaininfo")
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        return self._make_request("getnetworkinfo")
    
    def is_synced(self) -> bool:
        """
        Check if node is fully synced
        
        Returns:
            True if node is synced, False otherwise
        """
        try:
            info = self.get_blockchain_info()
            return info.get("initialblockdownload", True) == False
        except Exception as e:
            self.logger.error(f"Error checking sync status: {str(e)}")
            return False
    
    def scan_txout_set(self, descriptors: List[str]) -> Dict[str, Any]:
        """
        Scan UTXO set for given descriptors
        
        Args:
            descriptors: List of output descriptors to scan for
            
        Returns:
            Scan results with UTXOs and total amounts
        """
        # Convert simple addresses to descriptors if needed
        desc_objects = []
        for desc in descriptors:
            if desc.startswith("addr("):
                desc_objects.append({"desc": desc})
            else:
                # Assume it's a simple address
                desc_objects.append({"desc": f"addr({desc})"})
        
        return self._make_request("scantxoutset", ["start", desc_objects])
    
    def get_address_info(self, address: str) -> Dict[str, Any]:
        """
        Get information about an address
        
        Args:
            address: Bitcoin address
            
        Returns:
            Address information
        """
        return self._make_request("getaddressinfo", [address])
    
    def validate_address(self, address: str) -> Dict[str, Any]:
        """
        Validate a Bitcoin address
        
        Args:
            address: Bitcoin address to validate
            
        Returns:
            Validation result
        """
        return self._make_request("validateaddress", [address])
    
    def get_received_by_address(self, address: str, min_conf: int = 1) -> float:
        """
        Get total amount received by address
        Note: This requires the address to be in the wallet
        
        Args:
            address: Bitcoin address
            min_conf: Minimum confirmations
            
        Returns:
            Total amount received in BTC
        """
        return self._make_request("getreceivedbyaddress", [address, min_conf])
    
    def list_unspent(self, min_conf: int = 1, max_conf: int = 9999999, 
                     addresses: List[str] = None) -> List[Dict[str, Any]]:
        """
        List unspent transaction outputs
        
        Args:
            min_conf: Minimum confirmations
            max_conf: Maximum confirmations
            addresses: List of addresses to filter by
            
        Returns:
            List of unspent outputs
        """
        params = [min_conf, max_conf]
        if addresses:
            params.append(addresses)
        return self._make_request("listunspent", params)
    
    def import_address(self, address: str, label: str = "", rescan: bool = False):
        """
        Import an address to watch-only wallet
        
        Args:
            address: Address to import
            label: Label for the address
            rescan: Whether to rescan the blockchain
        """
        return self._make_request("importaddress", [address, label, rescan])
    
    def batch_scan_addresses(self, addresses: List[str]) -> Dict[str, float]:
        """
        Efficiently scan multiple addresses for balances using scantxoutset
        
        Args:
            addresses: List of Bitcoin addresses to scan
            
        Returns:
            Dictionary mapping addresses to their balances in BTC
        """
        if not addresses:
            return {}
        
        self.logger.info(f"Scanning {len(addresses)} addresses for balances")
        
        try:
            # Use scantxoutset for efficient UTXO scanning
            result = self.scan_txout_set(addresses)
            
            balances = {}
            
            # Initialize all addresses with 0 balance
            for addr in addresses:
                balances[addr] = 0.0
            
            # Process found UTXOs
            if result and "unspents" in result:
                for utxo in result["unspents"]:
                    # Extract address from scriptPubKey or descriptor
                    if "desc" in utxo:
                        # Parse address from descriptor
                        desc = utxo["desc"]
                        if "addr(" in desc:
                            addr_start = desc.find("addr(") + 5
                            addr_end = desc.find(")", addr_start)
                            address = desc[addr_start:addr_end]
                            
                            amount = utxo.get("amount", 0)
                            balances[address] = balances.get(address, 0) + amount
            
            total_found = sum(1 for balance in balances.values() if balance > 0)
            self.logger.info(f"Found {total_found} addresses with balances")
            
            return balances
            
        except Exception as e:
            # TODO self.logger.error(f"Error in batch scan: {str(e)}")
            # Fallback to individual address validation
            self.logger.info("Falling back to individual address validation")
            balances = {}
            for addr in addresses:
                try:
                    validation = self.validate_address(addr)
                    balances[addr] = 0.0 if validation.get("isvalid", False) else None
                except Exception as addr_error:
                    self.logger.debug(f"Error validating {addr}: {str(addr_error)}")
                    balances[addr] = None
            return balances
