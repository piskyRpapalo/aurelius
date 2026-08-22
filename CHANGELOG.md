# Changelog

Every number here was measured on the machine that produced it. Where something
was not measured, it says so.

## v1.0.0 — 2026-08-22

First minimum viable product: a local-first memory companion, no cloud, no
telemetry, that starts empty and says so.

### Added

- **Memory in one file.** SQLite at `~/.aurelius/memory.db`. Copy it to a USB
  stick and your memory goes with you.
- **First-run ritual** — language, consent, and a memory that is only created
  after you say yes.
- **Border redaction.** The filter blanks keys, paths and private addresses
  before any text leaves the machine. Fails closed: no filter, no export.
- **The fuse.** Inspects what the model writes before you see it, by structural
  shape rather than forbidden words.
- **Violet dashboard** (`interface/dashboard.*`) with browser speech input,
  sliding drawers, and dark mode. Bilingual: it speaks the language your memory
  declares.
- **Privacy PWA** (`interface/app.*`) with the four border states — including
  fail-closed, which disables sending with no way to override.
- **Turn capture** with `consent` defaulting to 0. Ten captured turns give zero
  trainable pairs until you say otherwise, one at a time, and it can be
  withdrawn.
- **PC executable**, 14 MB, one file, double-click. It fits because the product
  is standard library only.
- **`--restore`**, symmetric to `--backup`: checks the copy, sets aside what is
  there, and only then replaces.
- **Persistence** — systemd user service on a computer, Termux:Boot detector on
  Android, and a shortcut script that reopens everything with one tap.
- **CI** on Python 3.10 through 3.14, every push.

### Measured

| | |
|---|---|
| Tests | **278 in 17 suites**, green |
| Local model | Qwen3-4B-Instruct Q4_K_M on a Doogee S110 |
| Generation | 2.93 ± 0.38 tok/s · about 3 tok/s |
| Border states | four, verified with real traffic on the phone |

### Fixed

- Service worker served a stale shell after the front page changed: the browser
  showed the old face while the server returned the new one. Cache is versioned
  now, and the file says to bump it whenever the shell changes.
- systemd restarted the service in a loop, 23 times, reading "exited cleanly"
  and "crashed" the same way. It now runs in the foreground under systemd.
- The dashboard declared two languages and had its strings hardcoded in one.
- Sprite licensing said `Apache-2.0`, which exists nowhere in this repository.
  Sprites are CC BY-SA 4.0, like the rest of the art.

### Known limits / Horizon

- **A LoRA that generalises the doctrine.** Seven cycles measured. It transfers
  across situations of a behaviour it was taught, and not at all across
  behaviours it never saw. The product gate stays red; the base model ships.
- **A native Android APK.** A WebView wrapper does not work: with no Python
  server behind it, it installs and shows a blank page. It needs the interpreter
  packaged in.
- **Persistence with no manual setup.** Android does not start Termux on its
  own. Termux:Boot and a battery exemption are granted from the settings, by
  hand.
