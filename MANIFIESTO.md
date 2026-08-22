# M2 · closing the Water · the memory manifest

> Prove your memory has not changed, without writing down a single word of it.

A manifest is the list of what was in your memory at one instant. It does not
store your memories: it stores their **fingerprint**. You can hand someone the
manifest and they can check nothing was altered — and still learn nothing about
what you wrote.

## Use

```
python3 manifest.py --sign --out my-manifest.txt   # generate and sign
python3 manifest.py --verify my-manifest.txt       # check it still holds
python3 manifest.py                                 # print, unsigned
```

Default database: `~/.aurelius/memory.db`. Change it with `--db PATH`.

## What a verification means

**VALID** — two things at once: the manifest was not tampered with
(*integrity*), and your memory is still exactly as it was when you signed
(*currency*).

**INVALID · integrity** — someone edited the manifest file after it was
generated. The declared hash no longer matches its own body.

**INVALID · currency** — your memory moved on. **This is not a failure.** It
means you kept living: you added, archived or edited something after signing.
The manifest is history, not state. Sign a new one whenever you want a new
snapshot.

## Four rules this module does not negotiate

1. **The hash covers the body only.** The signature goes outside it, so signing
   cannot invalidate the seal it is signing.
2. **Signing never touches your memory.** Not a row, not a timestamp. This
   module opens the database to read.
3. **No name is a valid signature.** With nothing in your profile it writes
   `signed_by: NO_DATA`, and the manifest verifies. An anonymous signature is a
   signature; an invented one is not.
4. **Verifying is recalculating.** Nothing is trusted because it says so.

## Status (real, not aspirational)

- [x] 8/8 tests green · `python3 test_manifest.py`
- [x] Sabotage 3/3 detected · `python3 test_manifest.py --sabotaje`
- [x] Signing does not mutate the memory — asserted against every row
- [x] The manifest contains no memory text — asserted with a known secret
- [x] Empty memory signs and verifies: signing that there is nothing is legitimate
- [x] Header inside the signed region, so counts cannot be falsified
- [ ] Cryptographic signature with keys — deferred on purpose. This is a hash
      and a name, not a certificate. It proves *unchanged*, not *who*.

`manifest.py` imports `memory.py` from the product tree. It is not a copy of it.

## License

CC BY-SA 4.0 — [LICENSE-PROSE](LICENSE-PROSE).

Corregido el 2026-08-22. Esta linea decia `Apache-2.0`, y en este arbol no
existe ninguna licencia Apache: `LICENSE` es MIT y `LICENSE-PROSE` es
CC BY-SA 4.0.

Se elige CC BY-SA 4.0 y no MIT por coherencia, no por gusto: el README ya
licencia **todos** los `.md` bajo LICENSE-PROSE. Poner MIT aqui crearia la
tercera version del mismo dato, que es como empezo este problema.
