# Bitcoin BIP-39 Brute Force Tool

A professional-grade Bitcoin BIP-39 seed phrase brute force tool that connects directly to your local Bitcoin Core node. This tool provides privacy-focused, high-performance seed phrase recovery using local blockchain data.

## 🚀 Features

- **Local Bitcoin Node Integration**: Direct RPC connection to Bitcoin Core
- **Multiple Address Types**: Support for Legacy, SegWit, and Taproot addresses
- **Batch Processing**: Efficient UTXO scanning with `scantxoutset`
- **Italian BIP-39 Support**: Built-in Italian wordlist support
- **Comprehensive Testing**: Full unit and integration test coverage
- **Security-First**: No external API calls, all data stays local
- **Configurable**: Extensive `.env` configuration options
- **Professional Logging**: Detailed logging with configurable levels

## 📋 Requirements

- **Bitcoin Core Node**: Fully synced Bitcoin Core node (mainnet, testnet, or regtest)
- **Python 3.8+**: Modern Python installation
- **Storage**: Sufficient disk space for Bitcoin blockchain (~500GB for mainnet)
- **Memory**: 4GB+ RAM recommended for optimal performance
- **Network**: Local network access to Bitcoin node

## 🛠️ Installation

### 1. Clone and Setup

```bash
# Clone the repository (or copy the files)
git clone <your-repo> bitcoin-bip39-bruteforce
cd bitcoin-bip39-bruteforce

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Bitcoin Node

Ensure your Bitcoin Core node is running with RPC enabled. Add to your `bitcoin.conf`:

```ini
# RPC Configuration
rpcuser=your_rpc_username
rpcpassword=your_strong_rpc_password
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
rpcport=8332

# Optional: Enable transaction index for better performance
txindex=1

# For testnet (optional)
#testnet=1
#rpcport=18332
```

### 3. Configure Environment

Copy and customize the `.env` file:

```bash
cp .env.example .env
nano .env  # Edit with your settings
```

**Required Configuration:**
```bash
BITCOIN_RPC_HOST=127.0.0.1
BITCOIN_RPC_PORT=8332
BITCOIN_RPC_USER=your_rpc_username
BITCOIN_RPC_PASSWORD=your_strong_rpc_password
```

### 4. Verify Setup

Test your configuration:

```bash
python3 bitcoin_bip39_bruteforce.py --config-check
```

## 🎯 Usage

### Basic Usage

```bash
# Brute force with missing words marked as '?'
python3 bitcoin_bip39_bruteforce.py -s "parola1 parola2 ? parola4 ? parola6 parola7 parola8 parola9 parola10 parola11 parola12"
```

### Advanced Options

```bash
# Specify address type
python3 bitcoin_bip39_bruteforce.py -s "your partial seed here" -t segwit

# Multiple passphrases
python3 bitcoin_bip39_bruteforce.py -s "your partial seed here" -p "" -p "passphrase123" -p "mypassword"

# Legacy addresses
python3 bitcoin_bip39_bruteforce.py -s "your partial seed here" -t legacy
```

### Command Line Options

- `-s, --partial-seed`: Partial seed phrase with `?` for missing words (required)
- `-p, --passphrase`: Passphrase to try (can be used multiple times)
- `-t, --address-type`: Address type (`legacy`, `segwit`, `taproot`) - default: `segwit`
- `--config-check`: Test configuration and exit

### Address Types

| Type | Description | Address Format | Example |
|------|-------------|----------------|---------|
| `legacy` | P2PKH (BIP44) | Starts with `1` | `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` |
| `segwit` | Native SegWit (BIP84) | Starts with `bc1q` | `bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4` |
| `taproot` | Taproot (BIP86) | Starts with `bc1p` | `bc1p5cyxnuxmeuwuvkwfem96lqzszd02n6xdcjrs20cac6yqjjwudpxqkedrcr` |

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BITCOIN_RPC_HOST` | `127.0.0.1` | Bitcoin node hostname |
| `BITCOIN_RPC_PORT` | `8332` | Bitcoin node RPC port |
| `BITCOIN_RPC_USER` | - | RPC username (required) |
| `BITCOIN_RPC_PASSWORD` | - | RPC password (required) |
| `BITCOIN_NETWORK` | `mainnet` | Network type (mainnet/testnet/regtest) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `ADDRESSES_TO_SCAN` | `20` | Number of addresses to generate per seed |
| `BATCH_SIZE` | `100` | Batch size for address scanning |
| `MAX_COMBINATIONS_WARNING` | `1000000` | Warn for large combination sets |

### Performance Tuning

```bash
# For faster scanning (more addresses)
ADDRESSES_TO_SCAN=50

# For larger batch processing
BATCH_SIZE=200

# Reduce delay between requests
SCAN_DELAY_MS=50

# Enable debug logging
LOG_LEVEL=DEBUG
```

## 🧪 Testing

### Run All Tests

```bash
python3 