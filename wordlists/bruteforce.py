import requests
import time
from itertools import product
from mnemonic import Mnemonic
from bip_utils import (
    Bip39SeedGenerator,
    Bip44, Bip44Coins,
    Bip84, Bip84Coins,
    Bip86, Bip86Coins,
    Bip44Changes
)

mnemo = Mnemonic("italian")
with open("bip39_italian.txt", "r", encoding="utf-8") as f:
    wordlist = [w.strip() for w in f.readlines()]

# Input seed
partial_seed = input("Inserisci la seed parziale (usa '?' per ogni parola mancante): ").strip()
words = partial_seed.split()
missing_indexes = [i for i, w in enumerate(words) if w == "?"]

if len(missing_indexes) == 0:
    print("Errore: devi indicare almeno una parola mancante con '?'")
    exit(1)

# Input passphrase
use_passphrase = input("Vuoi provare una passphrase? (sì/no): ").strip().lower()
if use_passphrase in ["sì", "si"]:
    passphrases_input = input("Inserisci una o più passphrase separate da virgola: ").strip()
    passphrases = [p.strip() for p in passphrases_input.split(",")]
else:
    passphrases = [""]

# Selezione tipo di indirizzo
print("\nSeleziona il tipo di indirizzo da scansionare:")
print("1 = Legacy (1...)")
print("2 = SegWit (bc1q...)")
print("3 = Taproot (bc1p...)")
address_type_input = input("Scelta: ").strip()

if address_type_input == "1":
    address_types = [(Bip44Coins.BITCOIN, "Legacy (P2PKH)", Bip44)]
elif address_type_input == "2":
    address_types = [(Bip84Coins.BITCOIN, "Native SegWit (bc1q)", Bip84)]
elif address_type_input == "3":
    address_types = [(Bip86Coins.BITCOIN, "Taproot (bc1p)", Bip86)]
else:
    print("Errore: selezione tipo indirizzo non valida.")
    exit(1)

# Numero di indirizzi
try:
    num_addresses = int(input("Quanti indirizzi vuoi scansionare (es: 20)? ").strip())
except ValueError:
    print("Errore: inserire un numero valido.")
    exit(1)

total_combinations = len(wordlist) ** len(missing_indexes)
print(f"Proverò {total_combinations:,} combinazioni possibili (x {len(passphrases)} passphrase). Inizio...")

def get_balance(address):
    url = f"https://blockstream.info/api/address/{address}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        funded = data.get("chain_stats", {}).get("funded_txo_sum", 0)
        spent = data.get("chain_stats", {}).get("spent_txo_sum", 0)
        return funded - spent
    except Exception as e:
        print(f"Errore API su {address}: {e}")
        return 0

found = False

for combo in product(wordlist, repeat=len(missing_indexes)):
    if found:
        break

    candidate_words = words.copy()
    for idx, replacement in zip(missing_indexes, combo):
        candidate_words[idx] = replacement

    candidate_seed = " ".join(candidate_words)
    if not mnemo.check(candidate_seed):
        continue

    for passphrase in passphrases:
        print(f"\nSeed valida trovata: {candidate_seed} - Passphrase: '{passphrase}' - controllo saldo...")

        seed_bytes = Bip39SeedGenerator(candidate_seed).Generate(passphrase)

        for coin_type, label, bip_class in address_types:
            print(f"  ➤ Verifica standard: {label}")
            bip = bip_class.FromSeed(seed_bytes, coin_type)

            for i in range(num_addresses):
                try:
                    addr = bip.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i).PublicKey().ToAddress()
                    print(f"    → {addr}")
                    balance = get_balance(addr)
                    if balance > 0:
                        print("\n💰 SALDO TROVATO!")
                        print(f"Seed: {candidate_seed}")
                        print(f"Passphrase: {passphrase}")
                        print(f"Indirizzo: {addr}")
                        print(f"Saldo: {balance} satoshi")
                        found = True
                        break
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Errore generazione indirizzo: {e}")
                    continue
            if found:
                break
        if found:
            break

if not found:
    print("\nNessun saldo trovato.")