#!/usr/bin/env python3
"""
Bitcoin BIP-39 Brute Force Tool with Local Node Integration
Performs brute force attack on partial BIP-39 seed phrases using local Bitcoin Core node
"""

import os
import sys
import time
import logging
from typing import List, Dict, Tuple, Optional, Iterator
from itertools import product
from pathlib import Path

# Third-party imports
import click
from dotenv import load_dotenv
from mnemonic import Mnemonic
from bip_utils import (
    Bip39SeedGenerator, Bip44, Bip44Coins, Bip84, Bip84Coins, 
    Bip86, Bip86Coins, Bip44Changes
)

# Local imports
from bitcoin_rpc_client import BitcoinRPCClient, BitcoinRPCError


class BruteForceConfig:
    """Configuration class for brute force parameters"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Bitcoin RPC Configuration
        self.rpc_host = os.getenv('BITCOIN_RPC_HOST', '127.0.0.1')
        self.rpc_port = int(os.getenv('BITCOIN_RPC_PORT', '8332'))
        self.rpc_user = os.getenv('BITCOIN_RPC_USER', '')
        self.rpc_password = os.getenv('BITCOIN_RPC_PASSWORD', '')
        self.rpc_timeout = int(os.getenv('BITCOIN_RPC_TIMEOUT', '30'))
        self.network = os.getenv('BITCOIN_NETWORK', 'mainnet')
        
        # Security Configuration
        self.use_ssl = os.getenv('BITCOIN_RPC_USE_SSL', 'false').lower() == 'true'
        self.ssl_verify = os.getenv('BITCOIN_RPC_SSL_VERIFY', 'true').lower() == 'true'
        self.ssl_cert_path = os.getenv('BITCOIN_RPC_SSL_CERT_PATH', '')
        
        # Logging Configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.log_file = os.getenv('LOG_FILE', 'bitcoin_rpc.log')
        
        # Brute Force Configuration
        self.max_combinations_warning = int(os.getenv('MAX_COMBINATIONS_WARNING', '1000000'))
        self.batch_size = int(os.getenv('BATCH_SIZE', '100'))
        self.addresses_to_scan = int(os.getenv('ADDRESSES_TO_SCAN', '20'))
        self.scan_delay_ms = int(os.getenv('SCAN_DELAY_MS', '100'))
        
        # BIP-39 Configuration
        self.wordlist_file = os.getenv('WORDLIST_FILE', 'bip39_italian.txt')
        self.default_passphrase = os.getenv('DEFAULT_PASSPHRASE', '')


class AddressGenerator:
    """Generates Bitcoin addresses from seed phrases using different derivation paths"""
    
    # Address type mappings
    ADDRESS_TYPES = {
        'legacy': (Bip44Coins.BITCOIN, "Legacy (P2PKH)", Bip44),
        'segwit': (Bip84Coins.BITCOIN, "Native SegWit (bc1q)", Bip84),
        'taproot': (Bip86Coins.BITCOIN, "Taproot (bc1p)", Bip86)
    }
    
    @staticmethod
    def generate_addresses(seed_phrase: str, passphrase: str, address_type: str, 
                          num_addresses: int) -> List[str]:
        """
        Generate Bitcoin addresses from seed phrase
        
        Args:
            seed_phrase: BIP-39 mnemonic seed phrase
            passphrase: Optional passphrase for seed
            address_type: Type of addresses to generate (legacy, segwit, taproot)
            num_addresses: Number of addresses to generate
            
        Returns:
            List of Bitcoin addresses
        """
        if address_type not in AddressGenerator.ADDRESS_TYPES:
            raise ValueError(f"Unsupported address type: {address_type}")
        
        coin_type, label, bip_class = AddressGenerator.ADDRESS_TYPES[address_type]
        
        try:
            # Generate seed from mnemonic
            seed_bytes = Bip39SeedGenerator(seed_phrase).Generate(passphrase)
            
            # Initialize BIP derivation
            bip = bip_class.FromSeed(seed_bytes, coin_type)
            
            addresses = []
            for i in range(num_addresses):
                addr = bip.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i).PublicKey().ToAddress()
                addresses.append(addr)
            
            return addresses
            
        except Exception as e:
            raise ValueError(f"Failed to generate addresses: {str(e)}")


class BIP39BruteForcer:
    """Main brute force engine for BIP-39 seed phrases"""
    
    def __init__(self, config: BruteForceConfig):
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize Bitcoin RPC client
        self.rpc_client = BitcoinRPCClient(
            host=config.rpc_host,
            port=config.rpc_port,
            user=config.rpc_user,
            password=config.rpc_password,
            timeout=config.rpc_timeout,
            use_ssl=config.use_ssl,
            ssl_verify=config.ssl_verify,
            ssl_cert_path=config.ssl_cert_path
        )
        
        # Initialize mnemonic handler
        self.mnemo = Mnemonic("italian")
        
        # Load wordlist
        self.wordlist = self._load_wordlist()
        
        self.logger.info("BIP-39 Brute Forcer initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('bitcoin_bruteforce')
        logger.setLevel(getattr(logging, self.config.log_level))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # File handler
        if self.config.log_file:
            file_handler = logging.FileHandler(self.config.log_file)
            file_handler.setLevel(getattr(logging, self.config.log_level))
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def _load_wordlist(self) -> List[str]:
        """Load BIP-39 wordlist from file"""
        wordlist_path = Path(self.config.wordlist_file)
        
        if not wordlist_path.exists():
            raise FileNotFoundError(f"Wordlist file not found: {wordlist_path}")
        
        try:
            with open(wordlist_path, 'r', encoding='utf-8') as f:
                wordlist = [word.strip() for word in f.readlines() if word.strip()]
            
            self.logger.info(f"Loaded {len(wordlist)} words from {wordlist_path}")
            return wordlist
            
        except Exception as e:
            raise IOError(f"Failed to load wordlist: {str(e)}")
    
    def test_node_connection(self) -> bool:
        """Test connection to Bitcoin node"""
        self.logger.info("Testing Bitcoin node connection...")
        
        try:
            if not self.rpc_client.test_connection():
                self.logger.error("Failed to connect to Bitcoin node")
                return False
            
            # Check sync status
            if not self.rpc_client.is_synced():
                self.logger.warning("Bitcoin node is not fully synced - results may be incomplete")
                response = input("Continue anyway? (y/n): ").strip().lower()
                if response != 'y':
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Node connection error: {str(e)}")
            return False
    
    def parse_partial_seed(self, partial_seed: str) -> Tuple[List[str], List[int]]:
        """
        Parse partial seed phrase and identify missing word positions
        
        Args:
            partial_seed: Seed phrase with '?' for missing words
            
        Returns:
            Tuple of (word_list, missing_positions)
        """
        words = partial_seed.strip().split()
        missing_positions = [i for i, word in enumerate(words) if word == '?']
        
        if not missing_positions:
            raise ValueError("No missing words found. Use '?' to mark missing positions.")
        
        if len(words) not in [12, 15, 18, 21, 24]:
            raise ValueError(f"Invalid seed length: {len(words)}. Must be 12, 15, 18, 21, or 24 words.")
        
        self.logger.info(f"Parsed seed: {len(words)} words, {len(missing_positions)} missing")
        return words, missing_positions
    
    def generate_combinations(self, words: List[str], missing_positions: List[int]) -> Iterator[List[str]]:
        """
        Generate all possible word combinations for missing positions
        
        Args:
            words: Partial word list
            missing_positions: Positions of missing words
            
        Yields:
            Complete word combinations
        """
        total_combinations = len(self.wordlist) ** len(missing_positions)
        
        if total_combinations > self.config.max_combinations_warning:
            self.logger.warning(f"Large number of combinations: {total_combinations:,}")
            response = input("This may take a very long time. Continue? (y/n): ").strip().lower()
            if response != 'y':
                return
        
        self.logger.info(f"Generating {total_combinations:,} combinations...")
        
        for combination in product(self.wordlist, repeat=len(missing_positions)):
            candidate_words = words.copy()
            for pos, word in zip(missing_positions, combination):
                candidate_words[pos] = word
            yield candidate_words
    
    def scan_seed_phrase(self, seed_phrase: str, passphrase: str, 
                        address_type: str) -> Optional[Dict[str, any]]:
        """
        Scan a complete seed phrase for balances
        
        Args:
            seed_phrase: Complete BIP-39 seed phrase
            passphrase: Passphrase for seed generation
            address_type: Type of addresses to generate
            
        Returns:
            Dictionary with results if balance found, None otherwise
        """
        try:
            # Generate addresses
            addresses = AddressGenerator.generate_addresses(
                seed_phrase, passphrase, address_type, self.config.addresses_to_scan
            )
            
            # Scan addresses for balances
            balances = self.rpc_client.batch_scan_addresses(addresses)
            
            # Check for positive balances
            funded_addresses = {addr: balance for addr, balance in balances.items() 
                              if balance and balance > 0}
            
            if funded_addresses:
                total_balance = sum(funded_addresses.values())
                return {
                    'seed_phrase': seed_phrase,
                    'passphrase': passphrase,
                    'address_type': address_type,
                    'funded_addresses': funded_addresses,
                    'total_balance': total_balance
                }
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error scanning seed '{seed_phrase}': {str(e)}")
            return None
    
    def brute_force(self, partial_seed: str, passphrases: List[str], 
                   address_types: List[str]) -> Optional[Dict[str, any]]:
        """
        Perform brute force attack on partial seed phrase
        
        Args:
            partial_seed: Partial seed with missing words marked as '?'
            passphrases: List of passphrases to try
            address_types: List of address types to check
            
        Returns:
            Dictionary with results if successful, None otherwise
        """
        # Parse input
        words, missing_positions = self.parse_partial_seed(partial_seed)
        
        self.logger.info("Starting brute force attack...")
        start_time = time.time()
        combinations_tested = 0
        
        try:
            for combination in self.generate_combinations(words, missing_positions):
                seed_phrase = " ".join(combination)
                
                # Validate seed phrase
                if not self.mnemo.check(seed_phrase):
                    combinations_tested += 1
                    continue
                
                self.logger.info(f"Testing valid seed: {seed_phrase}")
                
                # Test each passphrase
                for passphrase in passphrases:
                    # Test each address type
                    for address_type in address_types:
                        result = self.scan_seed_phrase(seed_phrase, passphrase, address_type)
                        
                        if result:
                            elapsed_time = time.time() - start_time
                            self.logger.info(f"🎉 SUCCESS! Found balance after {elapsed_time:.2f}s "
                                           f"({combinations_tested:,} combinations tested)")
                            return result
                
                combinations_tested += 1
                
                # Progress logging
                if combinations_tested % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = combinations_tested / elapsed if elapsed > 0 else 0
                    self.logger.info(f"Tested {combinations_tested:,} combinations "
                                   f"({rate:.1f}/sec)")
                
                # Rate limiting
                if self.config.scan_delay_ms > 0:
                    time.sleep(self.config.scan_delay_ms / 1000.0)
        
        except KeyboardInterrupt:
            self.logger.info("Brute force interrupted by user")
        except Exception as e:
            self.logger.error(f"Brute force error: {str(e)}")
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Brute force completed. {combinations_tested:,} combinations tested "
                        f"in {elapsed_time:.2f}s")
        return None


@click.command()
@click.option('--partial-seed', '-s', required=True, 
              help='Partial seed phrase with ? for missing words')
@click.option('--passphrase', '-p', multiple=True, 
              help='Passphrase(s) to try (can be used multiple times)')
@click.option('--address-type', '-t', 
              type=click.Choice(['legacy', 'segwit', 'taproot']), 
              default='segwit', help='Address type to generate')
@click.option('--config-check', is_flag=True, 
              help='Test configuration and exit')
def main(partial_seed: str, passphrase: tuple, address_type: str, config_check: bool):
    """
    Bitcoin BIP-39 Brute Force Tool
    
    Example usage:
    python bitcoin_bip39_bruteforce.py -s "word1 word2 ? word4 ? word6 word7 word8 word9 word10 word11 word12"
    """
    try:
        # Load configuration
        config = BruteForceConfig()
        
        # Validate required configuration
        if not config.rpc_user or not config.rpc_password:
            click.echo("Error: Bitcoin RPC credentials not configured in .env file", err=True)
            sys.exit(1)
        
        # Initialize brute forcer
        brute_forcer = BIP39BruteForcer(config)
        
        # Test node connection
        if not brute_forcer.test_node_connection():
            click.echo("Error: Cannot connect to Bitcoin node", err=True)
            sys.exit(1)
        
        if config_check:
            click.echo("✅ Configuration and node connection OK")
            return
        
        # Prepare passphrases
        passphrases = list(passphrase) if passphrase else [config.default_passphrase]
        address_types = [address_type]
        
        click.echo(f"🚀 Starting brute force with:")
        click.echo(f"   Partial seed: {partial_seed}")
        click.echo(f"   Passphrases: {len(passphrases)} to test")
        click.echo(f"   Address type: {address_type}")
        click.echo(f"   Node: {config.rpc_host}:{config.rpc_port}")
        click.echo("")
        
        # Perform brute force
        result = brute_forcer.brute_force(partial_seed, passphrases, address_types)
        
        if result:
            click.echo("\n🎉 SUCCESS! Wallet found with balance:")
            click.echo(f"Valid Seed Phrase: {result['seed_phrase']}")
            click.echo(f"Passphrase: '{result['passphrase']}'")
            click.echo(f"Address Type: {result['address_type']}")
            click.echo(f"Total Balance: {result['total_balance']:.8f} BTC")
            click.echo("\nFunded addresses:")
            for addr, balance in result['funded_addresses'].items():
                click.echo(f"  {addr}: {balance:.8f} BTC")
        else:
            click.echo("\n❌ No wallet with balance found")
    
    except Exception as e:
        click.echo(f"Fatal error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
