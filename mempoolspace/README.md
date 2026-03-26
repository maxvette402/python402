# Mempool Space

WebSocket client for the [mempool.space](https://mempool.space/docs/api/websocket) public API. Streams live Bitcoin mempool and block data with automatic reconnection via `rel`.

### Dependencies

```sh
pip3 install websocket-client rel
```

> **macOS SSL fix:** If you get `CERTIFICATE_VERIFY_FAILED`, run `Install Certificates.command` from the Python 3.x folder in Finder.

### Run

```sh
# Stream blocks, stats, mempool-blocks, live-2h-chart, watch-mempool
python3 mempoolspace_ws.py

# Track transactions for a specific address
python3 mempoolspace_ws_track-address.py
```

To track a different address, edit the `track-address` value in `mempoolspace_ws_track-address.py`:

```python
message = {'track-address': 'bc1q...'}
```

### WebSocket Subscriptions

`mempoolspace_ws.py` subscribes to these streams on connect:

| Stream | Data |
|---|---|
| `blocks` | New confirmed blocks |
| `stats` | Mempool fee stats |
| `mempool-blocks` | Projected next blocks |
| `live-2h-chart` | 2-hour fee chart |
| `watch-mempool` | Mempool changes |

Stop with `Ctrl+C`.
