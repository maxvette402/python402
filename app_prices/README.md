# App Prices

Polls Binance and Crypto.com every second, computes price variation since first tick, and stores results in SQLite.

### Dependencies

```sh
pip3 install aioschedule colorama requests
```

### Setup

```sh
# Initialize the database (run once)
python3 app_prices_init.py

# Start the price monitor
python3 app_prices.py
```

Toggle sources at the top of `app_prices.py`:
```python
USE_CDC = True   # Crypto.com
USE_BNC = False  # Binance
```

The database is created at `~/opt/sqlite/prices.sqlite`.

### PM2

```sh
pm2 start app_prices.py --interpreter python3
pm2 logs app_prices
pm2 restart app_prices
pm2 stop app_prices
pm2 delete all
```

### Useful SQL

```sql
-- All records ordered by source and instrument
SELECT id, source, instrument, price_from, price_to, variation, created
  FROM prices
 ORDER BY source, instrument, created ASC;

-- Records for a specific pair
SELECT * FROM prices
 WHERE source = 'CDC' AND instrument = '1INCH_USDT'
 ORDER BY created ASC;

-- Count per pair
SELECT source, instrument, count(*)
  FROM prices
 GROUP BY source, instrument
 ORDER BY instrument;

-- Variations above 1% or below -1%
SELECT * FROM variation
 WHERE variation >= 1 OR variation <= -1
 ORDER BY created ASC;

-- Top performers
SELECT * FROM variation
 WHERE variation >= 1
 ORDER BY variation DESC;
```
