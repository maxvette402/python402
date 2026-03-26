# RPC Client

Python JSON-RPC 2.0 client for Bitcoin Core. Connects to a local node via HTTP Basic Auth.

### Configuration

Edit the constants at the top of `rpc_client.py`:

```python
ENDPOINT = "http://127.0.0.1:8332"
USER     = "bitcoin-rpc-user"
PASSWORD = "bitcoin-rpc-password"
TIMEOUT  = 30
```

These must match the `rpcuser` / `rpcpassword` values in your `bitcoin.conf`.

### Run

```sh
# Connect and print blockchain info
python3 rpc_client.py

# Run unit tests
python3 -m unittest rpc_client_test
python3 -m unittest rpc_client_test.BitcoinRPCTests
```

### Available Methods

| Method | Returns |
|---|---|
| `getblockchaininfo()` | Chain name, block height, sync progress |
| `getbestblockhash()` | Hash of the latest block |
| `getblockcount()` | Current block height (int) |
| `getnetworkinfo()` | Version, connections, network details |

### Custom Calls

Use `client.request(method, params)` for any other RPC method:

```python
client = JsonRPCClient()
result = client.request("getblock", ["<blockhash>"])
```
