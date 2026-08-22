# Aurelius · the technical file

Everything a reader who audits needs, moved out of `README.md` on 2026-08-22 so
that the front page could be read by someone who is not auditing. **Nothing was
softened on the way out** — the numbers, the limits and the refusals are the
same ones, in the same words.

Back to the front page: [README.md](README.md).

---

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


---

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


---

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


---

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


---

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

