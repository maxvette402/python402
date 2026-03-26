# Crypto.com API Client

Python client for the [Crypto.com Exchange REST API](https://exchange-docs.crypto.com/spot/index.html).

### Dependencies

```sh
pip3 install requests python-dotenv
```

### Run

```sh
cd ~/python402/crypto/cdc_api_client

python3 cdc_get_ticker.py
python3 cdc_get_account_summary.py
python3 get_instruments.py
python3 get_book.py
python3 get_candlestick.py   # parser TODO
python3 get_trades.py        # parser TODO
```

### Reference

- [Introduction](https://exchange-docs.crypto.com/spot/index.html#introduction)
- [Digital signature](https://exchange-docs.crypto.com/spot/index.html?python#digital-signature)
- [get-instruments](https://exchange-docs.crypto.com/spot/index.html#public-get-instruments)
- [get-account-summary](https://exchange-docs.crypto.com/spot/index.html#private-get-account-summary)
- [Inspiration](https://github.com/IgorJakovljevic/crypto-com-api)
