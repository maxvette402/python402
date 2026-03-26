# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A collection of Bitcoin/crypto Python tools: price monitoring, Bitcoin Core RPC client, mempool WebSocket monitoring, exchange API clients, and BIP-39 seed phrase utilities.

## Running Applications

```sh
# App Prices - initialize DB first, then run
python3 app_prices/app_prices_init.py
python3 app_prices/app_prices.py

# RPC Client - connect to a local Bitcoin node
python3 rpc_client/rpc_client.py

# Mempool WebSocket monitor
python3 mempoolspace/mempoolspace_ws.py

# BIP-39 brute force tool
cd wordlists
cp .env.example .env  # configure RPC credentials
python3 bitcoin_bruteforce_main.py -s "word1 word2 ? word4 ..." -t segwit

# PM2 process manager (app_prices)
pm2 start app_prices/app_prices.py --interpreter python3
pm2 logs app_prices
```

## Running Tests

```sh
# RPC client tests (from repo root or rpc_client/)
python3 -m unittest rpc_client/rpc_client_test.py
python3 -m unittest rpc_client_test.BitcoinRPCTests   # single class

# BIP-39 brute force tests
python3 -m pytest wordlists/bitcoin_bruteforce_tests.py
```

## Architecture

### app_prices/
Async price aggregation service. Polls Binance and Crypto.com APIs every second via `aioschedule`, computes variation percentages, and stores results in SQLite at `~/opt/sqlite/prices.sqlite`. Uses two tables: `prices` (raw ticks) and `variation` (computed deltas).

### rpc_client/
JSON-RPC 2.0 client for Bitcoin Core with Basic Auth. Talks to `http://127.0.0.1:8332`. Credentials and endpoint are module-level constants (`ENDPOINT`, `USER`, `PASSWORD`). The `JsonRPCClient` class wraps `getblockchaininfo`, `getbestblockhash`, `getblockcount`, `getnetworkinfo`.

### mempoolspace/
WebSocket client for `wss://mempool.space/api/v1/ws`. Uses `websocket` + `rel` for auto-reconnection. Two scripts: general mempool stream and address-specific transaction tracking.

### crypto/
HTTP wrapper modules for exchange REST APIs:
- `bnc_api_client/` → Binance (`https://api.binance.com/api/v3/`)
- `cdc_api_client/` → Crypto.com (`https://api.crypto.com/v2/public/`)

These are also imported by `app_prices/` for live price data.

### wordlists/
BIP-39 seed phrase recovery tool. `bitcoin_bruteforce_main.py` accepts a partial mnemonic with `?` placeholders and iterates combinations from a wordlist (default: `bip39_italian.txt`). Uses `bip_utils` for BIP44/84/86 key derivation (Legacy/SegWit/Taproot), then calls `scantxoutset` on a local Bitcoin node via `bitcoin_rpc_client.py`. Configured via `.env`; see `.env.example` for all options.

## Key Dependencies

| Package | Purpose |
|---|---|
| `aioschedule` | Async task scheduling (app_prices) |
| `colorama` | Colored terminal output |
| `websocket`, `rel` | WebSocket + auto-reconnect (mempoolspace) |
| `bip_utils` | BIP32/44/84/86 key derivation |
| `mnemonic` | BIP-39 seed phrase handling |
| `click` | CLI for brute force tool |
| `python-dotenv` | `.env` loading |

No `pyproject.toml` or `setup.py` — install dependencies directly with `pip3 install <package>`.
