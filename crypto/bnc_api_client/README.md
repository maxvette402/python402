# Binance API Client

Python client for the [Binance REST API](https://binance-docs.github.io/apidocs/spot/en/).

### Dependencies

```sh
pip3 install requests python-dotenv
```

### Run

```sh
cd ~/python402/crypto/bnc_api_client

python3 bnc_get_ticker.py
python3 bnc_get_avg_price.py
python3 bnc_get_account_summary.py
python3 bnc_get_open_orders.py
python3 bnc_get_staking_product_list.py
python3 bnc_get_exchangeInfo.py
python3 bnc_post_new_order.py
```

### Useful Endpoints

```
# Public (no auth)
https://api.binance.com/api/v3/ticker/24hr
https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT

# Status
https://api.binance.com/sapi/v1/system/status

# Testnet
https://testnet.binance.vision/sapi/v1/system/status
```

### Reference

- [Spot API docs](https://binance-docs.github.io/apidocs/spot/en/#general-api-information)
- [Signature examples](https://github.com/binance-exchange/binance-signature-examples/tree/master/python)
