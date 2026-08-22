<div align="center">

<img src="assets/aurelius-up.png" width="640"
     alt="Pixel-art sprite sheet, four frames on one strip: a white marble bust of a bearded classical figure against a flat grey ground. In the first frame the marble is whole; in the second thin cracks run across the face; in the third the marble breaks open to show dark machinery underneath and one lit amber eye; in the fourth more of the surface has come away and loose fragments float beside the head.">

# Aurelius

**Your memory, in one file you can carry. It starts empty and says so.**

<img src="https://img.shields.io/badge/Python-3.10%2B-2F6B4F?style=flat" alt="Python 3.10 or newer">
<img src="https://img.shields.io/badge/dependencies-standard%20library%20only-A9762B?style=flat" alt="Dependencies: standard library only">
<img src="https://img.shields.io/badge/storage-one%20local%20file-2F6B4F?style=flat" alt="Storage: one local file">
<img src="https://img.shields.io/badge/code-MIT-57534E?style=flat" alt="Code licence: MIT">
<img src="https://img.shields.io/badge/prose-CC%20BY--SA%204.0-57534E?style=flat" alt="Prose licence: CC BY-SA 4.0">

</div>

---

> **Sin un modelo local instalado, Aurelius no conversa: pregunta y recuerda.**
> Esa es la descripción honesta. El cerebro y la voz se descargan en el primer arranque, con tu consentimiento.


> Your memory, in one file you can carry. It starts empty and says so.

Aurelius wakes up with no memory. Instead of pretending otherwise, it tells you
what it does not have and asks you to help build it. What you write stays on
your machine, in a single file, in your own words.

## Two ways in

**If you just want to use it** — no terminal, no setup:

| | |
|---|---|
| **Computer** | one file, double-click it → [INSTALACION_PC.md](INSTALACION_PC.md) |
| **Android** | Termux today, and why there is no APK yet → [INSTALACION_ANDROID.md](INSTALACION_ANDROID.md) |

**If you want to read it, change it or audit it**, the rest of this file is for
you: clone, run, and every claim below carries the machine that produced it.

## What it does

- Starts in one of three honest states: **no schema**, **empty**, or **with data**. Those are three different things and it never confuses them.
- Guides you through a memory field by field: `what`, `why`, `where`, `learned`. Each question shows the field it is filling.
- Writes `NO_DATA` where you have no answer, and shows it. Never a blank cell.
- Shows your memory three ways: a table, an indented tree of links, and a count of how many gaps are left.
- Exports to markdown **redacted at the border**.

## What it does not do

- It does **not** redact what you store. Your machine, your data, your words. Redaction happens only when something leaves.
- It does **not** delete. Archiving is a column, not a folder.
- It does **not** need the network, a GPU, or any dependency beyond Python 3 and its standard library.
- It does **not** search yet. With a handful of memories, search is a solution to a problem you do not have.

## What the fuse does not catch

Aurelius inspects what the model writes before you ever see it as a command.
That inspector — the fuse — matches **structural shapes**: the form of a
destructive command, not a list of forbidden words. It reads the text with line
continuations and spacing normalised first, so breaking a command across lines
does not walk past it.

State plainly what that buys you, and what it does not:

- It is a **deny list of shapes**, and a deny list is never finished. It knows
  the shapes written into it and nothing else. A destructive command in a shape
  nobody anticipated goes straight through.
- It reads **form, not meaning**. It does not run the command, does not resolve
  variables, does not unwrap encodings, and cannot tell a real instruction from
  a quoted example. Something harmful wrapped in an indirection it does not
  model is something it does not see.
- **Not catching anything is not a verdict of safe.** It is the absence of a
  match, which is a different statement and a much weaker one.

The fuse **slows things down; it does not stand in for you.** It exists so that
the obvious case does not reach you disguised as a suggestion — not so that you
can stop reading. The last check is yours, and there is no version of this
program in which it stops being yours.

> **Aviso de Seguridad:** El fusible inspecciona la salida del modelo buscando
> comandos destructivos **por su forma**. No es completo, y conviene saber por
> dónde no llega: **no resuelve variables** (`$BORRAR /` pasa si la variable
> vale `rm -rf`), **no decodifica** base64 ni hex, y **no sigue indirecciones**
> como un alias. Tampoco conoce un comando peligroso que nadie haya listado
> todavía.
>
> Es la primera línea de defensa, no un filtro de alucinaciones. Frena; no
> sustituye a la persona. La última comprobación la haces tú.

## Use

```
python3 aurelius.py                # the seven-step session
python3 aurelius.py --view         # just look
python3 aurelius.py --export       # markdown, redacted
AURELIUS_RITMO=0 python3 aurelius.py   # same session, no pauses
```

Default location: `~/.aurelius/memory.db`. Change it with `--db RUTA`. Copy that
file and your memory comes with you.

## Install, from nothing

```
git clone https://github.com/piskyRpapalo/aurelius.git && cd aurelius && python3 aurelius.py
```

That is the whole installation. There is no package to add, no service to start
and no account to make: Python 3 and its standard library are the only
requirements, and both are already on most machines. The first run asks your
language, then offers to create your memory — nothing is written before you say
so.

Voice is optional and separate. Without it, everything works and the Speak
button says plainly that this copy has no voice.

### On a phone (Android · Termux)

Install [Termux](https://termux.dev) — from F-Droid, not the Play Store — and
paste one line:

```
pkg install -y git && git clone --depth 1 https://github.com/piskyRpapalo/aurelius.git ~/aurelius && bash ~/aurelius/bin/instalar-android
```

It installs what it needs, gets the engine from Termux's own repository, and
then Aurelius offers you the brain and the voice with their licence and their
checksum in front of you. You accept those; the script does not decide for you.

**What a phone is good at, measured and not guessed** (Doogee S110, 2026-08-19,
`llama-bench` on the 4B model): generation **2.93 ± 0.38 tokens per second**,
against 14.5 on a small desktop. A short answer takes about half a minute. The
Vulkan backend package installs and loads, but this device reports
`no devices found`, so there is no graphics acceleration to gain here.

Writing, recalling, sealing and exporting are as fast as anywhere. Conversation
is the slow part, and now you know how slow before you install it.

The maintainer put it in his own words, and they stay in his:

> En el teléfono, conversar con Aurelius no es una charla: es una carta. La
> generación va a ~3 tokens por segundo; un turno con el tope por defecto
> (80 tokens) tarda uno o dos minutos. No hay presión de respuesta inmediata
> porque no hay servidor que te espere. Solo tu hardware, tu memoria, y el
> tiempo que tú le das.

## Requirements

| Requirement | How to check it | If it is missing |
|---|---|---|
| Python 3.10+ | `python3 -V` | it does not start — the only mandatory one |
| `llama-completion` | `command -v llama-completion` | no conversation with the model; everything else works |
| `piper` | `command -v piper` | the Speak button says that this copy has no voice |

Only the first row is required. The other two remove one capability each and
leave the rest of the program intact: that is the design, not an accident of
it. A copy of Aurelius with neither `llama-completion` nor `piper` still asks, still
writes, still shows and still exports — and it tells you which of the two it is
running without, instead of failing somewhere later and letting you guess.

## The face

```
python3 cara.py                     # writes cara.html from your memory
python3 cara.py --aplicar aurelius-formulario.json
```

`cara.py` reads your memory and writes **one HTML file**: the sprites, both
languages and your own memories are inside it. Open it with a double click —
there is no server to start, and it makes no network calls at all. Copy it to a
USB stick and it says exactly the same thing on a machine with no cable.

That forces one honest asymmetry, worth stating out loud: the face **reads**
your memory at the moment it is generated, and to **write** it hands you a form
file that you save and apply yourself. Nothing is written from the browser
behind your back — you can open the form and read it before it touches
anything.

Inside: the Slate (everything your memory holds, gaps declared, and two ways to
take it with you) and the Path (the eight steps). Frame maps and the animation
contract are in [ASSETS.md](ASSETS.md).

The two sprite sheets above and in `assets/` are four frames on one strip. This
page shows the whole strip, unanimated: a README cannot run the animation, and a
still that pretended to be one frame would be hiding what the file actually is.

## Language / Idioma

The first question of the session is which language to speak — English or
Español — and it is asked in both, because at that point you have not chosen
yet. Everything after it, including the questions, the views and the closing,
is in the language you picked.

The answer is kept in your profile next to `device` and `name`, so a second
session does not ask again. Not answering is an answer too: it stays `NO_DATA`
and the session runs in English. `NO_DATA` here means *nobody chose*, which is
a different thing from *chose English* — the profile keeps them apart.

## Pace: `AURELIUS_RITMO`

Aurelius speaks with a cadence — it types at a readable speed and pauses at
punctuation. That is a default, not a requirement. Set `AURELIUS_RITMO=0` and
every wait disappears; `1.0` is the normal pace, and any number in between
scales it.

```
AURELIUS_RITMO=0 python3 aurelius.py
```

Turn it off if you are in a hurry, driving Aurelius from a script, or reading
with a screen reader — a pause that helps one person is noise to another. **The
text is identical in both modes.** Cadence can change *when* something is said,
never *what* is said; a tone that alters the content is not tone. The pace also
switches itself off when output is not a terminal, so piping and scripting are
byte-for-byte reproducible without setting anything.

## Border: redaction is required, not optional

`--export` looks for a `guardrails` module providing `redactar_salida(text) ->
(text, [{policy, count}])`. **If it is not there, export is blocked** and
nothing is printed. Failing closed is deliberate: a filter that breaks and lets
the text through is worse than no filter, because you would believe you were
protected.

The findings report **class and count only** — `API_KEY x1` — never the matched
value. A report that echoed the secret would put it back in the place the
redaction just removed it from.

## Running the face on a phone, and what survives a reboot

The web face is not part of the downloadable product. Like the bridge, it lives
in `bin/`, you start it by hand, and no module imports it. A clone that has it
never runs it.

```
bin/aurelius-servicio arranca     # starts it, and verifies it answers
bin/aurelius-servicio estado      # is it alive, and does it respond?
bin/aurelius-servicio para        # stops it
```

`arranca` refuses to start a second one. A stale process still holding the port
makes the new one die at birth — and because the old one *does* answer,
everything looks fine while you measure the wrong version. That has happened
three times here, on three different ports, and the symptom lied every time.

**It does not survive a reboot, and does not pretend to.** Android will not
start Termux on its own. Reboot survival needs the **Termux:Boot** app,
installed from F-Droid, plus exempting Termux from battery optimisation. Both
are done by hand, on the screen — no script can grant itself either. Until then
the honest instruction is the one above: after a reboot, open Termux and run
`arranca`.

## Status (real, not aspirational)

- [x] Three states, distinguished and tested
- [x] Round-trip byte-identical, accents and newlines included
- [x] `NO_DATA` stored, shown and counted
- [x] Table, tree and gap count
- [x] Archive without delete
- [x] WAL journal: an interrupted write leaves no half rows
- [x] Store raw / export redacted, tested in both directions
- [x] Export blocked with no filter
- [x] `guardrails` module shipped in this folder — `guardrails.py` and `test_guardrails.py`
- [x] Manifest signature — `manifest.py` and `test_manifest.py`, versioned since the close of M3
- [ ] Full-text search — left out on purpose

`python3 test_memory.py` — 25/25 green. The whole tree is `bin/pruebas`.

## Python: the range that was actually run

| Version | Where | Tree | Result |
|---|---|---|---|
| 3.10.12 | Ubuntu 22.04 | `73f7bc6` | 217/217 |
| 3.10.12 | standalone build (`uv`) | current | 225/225 |
| 3.11.16 | standalone build (`uv`) | current | 225/225 |
| 3.12.13 | standalone build (`uv`) | current | 225/225 |
| 3.13.15 | standalone build (`uv`) | current | 225/225 |
| 3.14.4 | Ubuntu 26.04, system | current | 225/225 |

Those are the runs that **happened**, end to end, sabotage modes included —
**five points, not an interval with two ends and a guess in the middle.** The
first row is kept separate on purpose: it is a real measurement of an older
tree and has not been repeated since, so it is reported as what it is instead
of being folded into today's number.

What the table still does **not** claim: the four `uv` rows pin the interpreter,
not the distribution — they all ran on one machine. A second machine is a
different measurement, and there is one: an independent sandbox reproduced
224/224 on 3.10.12 at commit `5a86cc6`.

To run it on another version yourself:

```
uv run --python 3.12 ./bin/pruebas ; echo "salida=$?"
```

**Not** `uv run --python 3.12 python3 -m unittest discover`. That runs 145 of
the 254 tests for the reason described above — `discover` does not find the
five suites with their own runner — and it prints its report to stderr while
the cases print to stdout, so a `tail` on the output shows the end of a museum
escape and no test count at all. It exits 0. A green that covers 64% and says
nothing about it is the exact failure `bin/pruebas` exists to prevent.

Outside that range Aurelius **declares and keeps going**:

```
NOTA · Python 3.9.7. La tanda de pruebas se ha corrido en 3.10.12 / 3.14.4, no en esta.
NOTE · Python 3.9.7. The test run has been done on 3.10.12 / 3.14.4, not on this one.
```

It does not refuse to start. Outside the tested range does not mean broken — it
means there is no data, and turning a missing measurement into a verdict is
exactly what this program does not do anywhere else. The note goes to stderr,
so piping output stays clean. The range lives in `interprete.py`, in one place,
so this table and the program cannot drift apart.

## Verification

To check that everything works on your machine:

    bin/pruebas

It runs the 19 suites — **254 tests** — and the two sabotage modes. It prints
the per-suite breakdown and **which interpreter it ran on**, so the number can
be checked instead of believed: a figure without its machine is a rumour with
decimals.

Do not use `python3 -m unittest discover` for this. It sees 8 of the 19 suites:
the other five bring their own runner and `discover` does not find them, so it
says `OK` having run barely half. An OK that covers half is not an OK, and that
is why `bin/pruebas` exists.

The two sabotages (`test_idioma.py --sabotaje`, `test_fuga.py --sabotaje`)
break the product on purpose in a copy of the tree and **require the tests to
go red**. That is what separates a suite that proves something from one that
merely keeps it company: 4/4 and 6/6 breakages caught.

The tests do not touch your `~/.aurelius/`, do not open the microphone and do
not send anything to the speaker — see `silencio.py`.

What is verified and what is **not**: [LIMITES_DEL_CRITERIO.md](LIMITES_DEL_CRITERIO.md).
Third mission close-out: [CIERRE_M3.md](CIERRE_M3.md). Pragmas that switch a
guard off: [EXCEPCIONES.md](EXCEPCIONES.md).

## Lore names (kept in Spanish)

Some names stay in Spanish because that is how they were created. They are
names, not documentation:

- **"el Preceptor"** — the character you talk to.
- **"M1 · el Fuego", "M2 · el Agua", "M3 · la Piedra"** — mission titles.
- **`bin/pruebas`, `silencio.py`, `descarga.py`, `voz.py`** and the rest of the
  file and command names — renaming them would break every path, link and
  test in this repository, and in the close-out documents that cite them.

Two more things are in Spanish **by design**, and are not oversights:

- The Spanish half of the interface (`textos.py`). This is a bilingual
  product: it greets you in English by default and speaks Spanish if you ask
  it to. `test_idioma.py` requires it to say `¿Creo mi memoria ahora?` when
  the session is Spanish.
- The comments and docstrings inside the code. The reasoning of this project
  is written in Spanish; the interface it presents to the world is in English.

## Contact

**[Open an issue](https://github.com/piskyRpapalo/aurelius/issues)** — that is
the working channel today, and the one that gets an answer.

For anything that should not be public before it is fixed, `SECURITY.md` has
the private route and the response targets it actually commits to.

A direct channel to the author's own hardware is planned. It is not live.

## License

Dual license, one file each — the text that governs is theirs, not this summary:

- Code: MIT — [LICENSE](LICENSE)
- Prose and lore: CC BY-SA 4.0 — [LICENSE-PROSE](LICENSE-PROSE)
- Sprites (`assets/*.png`): CC BY-SA 4.0 — [LICENSE-PROSE](LICENSE-PROSE)

**Scope of the MIT license.** This MIT license applies to all Python source
code (`*.py`), shell scripts (`*.sh`), and configuration files in this
repository.

The prose, documentation, and lore (including but not limited to `README.md`
and all `.md` files) are licensed separately under CC BY-SA 4.0 (see
LICENSE-PROSE).

**The sprites travel with the prose, not with the code.** `assets/*.png` were
made by the author on their own machine: no stock bank, no third-party
watermark, no inherited conditions. They are art, so they are licensed like the
rest of the art here — CC BY-SA 4.0, the same file as the prose. Remix them,
credit the source, share alike.

Signed 2026-08-22. Until then this line read `NO_DATA`, because `ASSETS.md`
claimed an Apache-2.0 licence that exists nowhere in this repository, and a
licence invented in a README is worse than an absent one.

This paragraph used to live at the bottom of `LICENSE` itself. It was moved
here so that `LICENSE` holds the canonical MIT text and nothing else: GitHub
identifies a licence by comparing that file against the canonical wording, and
an appendix — however true — made it report `Other` instead of MIT. The terms
did not change; only where they are written.
