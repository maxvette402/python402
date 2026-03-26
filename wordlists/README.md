# Wordlists / BIP-39 Brute Force

Recovers a Bitcoin wallet from a partial BIP-39 seed phrase. Missing words are marked with `?`; the tool iterates every combination from the wordlist, derives addresses, and scans a local Bitcoin Core node for balances using `scantxoutset`.

The default wordlist is the Italian BIP-39 list (`bip39_italian.txt`, 2048 words).

### Dependencies

```sh
pip3 install -r bitcoin_bruteforce_requirements.txt
# or manually:
pip3 install click python-dotenv mnemonic bip-utils
```

### Setup

```sh
cp .env.example .env
# Edit .env with your Bitcoin RPC credentials
```

`.env` key settings:

```ini
BITCOIN_RPC_HOST=127.0.0.1
BITCOIN_RPC_PORT=8332
BITCOIN_RPC_USER=your_user
BITCOIN_RPC_PASSWORD=your_password
BITCOIN_NETWORK=mainnet       # mainnet | testnet | regtest
ADDRESSES_TO_SCAN=20          # addresses derived per seed
WORDLIST_FILE=bip39_italian.txt
```

### Run

```sh
# Verify config and node connection
python3 bitcoin_bruteforce_main.py --config-check

# Recover a 12-word seed with 1 unknown word
python3 bitcoin_bruteforce_main.py \
  -s "word1 word2 ? word4 word5 word6 word7 word8 word9 word10 word11 word12" \
  -t segwit

# Try multiple passphrases
python3 bitcoin_bruteforce_main.py \
  -s "word1 ? word3 ..." \
  -t segwit \
  -p "" -p "mypassphrase"
```

Address type (`-t`) options: `legacy` (1...), `segwit` (bc1q...), `taproot` (bc1p...)

### Tests

```sh
python3 -m pytest bitcoin_bruteforce_tests.py
```

### Performance note

Each `?` multiplies combinations by 2048. Two unknowns = ~4M combinations; the tool warns above 1M and asks for confirmation. Tune `SCAN_DELAY_MS` and `BATCH_SIZE` in `.env` to balance speed vs. node load.
