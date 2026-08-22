# Contributing / Contribuir

Short version: the code is in Spanish, the tests must be able to fail, and the
last word on doctrine is the author's.

Versión corta: el código está en español, las pruebas tienen que poder fallar,
y la última palabra sobre doctrina es del autor.

---

## Language / El idioma

**Variable names, function names and comments are in Spanish.** That is a
decision, not an accident: the people who maintain this read Spanish, and code
that explains itself in the maintainer's language gets read.

**The user interface is bilingual** — EN and ES, in parallel columns, in
`textos.py`. A missing translation is a missing key, and case 10 of
`test_idioma.py` finds it before a person does.

**Los nombres de variables y funciones, y los comentarios, van en español.** No
es un descuido: quien mantiene esto lee español, y el código que se explica en
el idioma de quien lo mantiene se lee.

**La interfaz es bilingüe** — EN y ES, en columnas paralelas, en `textos.py`.

---

## Running the tests / Correr las pruebas

```
./bin/pruebas            # everything, sabotage runs included
./bin/pruebas --rapido   # skips the sabotage runs (they copy the tree; slow)
```

There is **no** `bin/pruebas sabotaje` subcommand: the sabotage runs are part of
the default run, and `--rapido` is what skips them.

No existe `bin/pruebas sabotaje`: los sabotajes van en la tanda por defecto, y
lo que los salta es `--rapido`.

### What sabotage mode is for / Para qué sirve el sabotaje

A test suite that passes proves nothing on its own — it might be asserting
things that are true no matter what the code does. So the suite breaks the code
on purpose and **demands that the tests go red**. If a saboteur goes undetected,
that is reported as a failure of the suite, not of the code.

Una tanda que pasa no demuestra nada por sí sola: podría estar comprobando
cosas que son ciertas haga lo que haga el código. Por eso la suite rompe el
código a propósito y **exige que las pruebas se pongan rojas**.

---

## Writing a test / Escribir una prueba

Three rules, and they come from scars in this repository:

1. **Name the rupture.** A test says what breaks if it fails. "I want it to say
   hello" is not a rupture; "if the user injects a prompt, the model must not
   obey" is.
2. **Do not assert on shape.** `assertEqual(counters, {...})` is not a sentence.
   Ask yourself what sentence in plain language you want to keep true, and check
   that. A test that goes red when the code *improves* was measuring shape.
3. **A fixture that looks like a credential is composed at runtime.** The
   hygiene guard never exempts the provider-token rule, not even with a pragma,
   and it is right: a fixture shaped like a leak is indistinguishable from a
   leak to any grep that comes later. See `test_frontera.py`.

---

## Proposing a change / Proponer un cambio

**Pull requests for code, not issues.** An issue that describes code is a
description; a PR is the thing itself, and it runs against the suite.

Issues are welcome for questions, measured bugs, and anything you cannot fix
yourself.

CI runs `./bin/pruebas` on Python 3.10 through 3.14 on every push. If it is red
there, it is red.

---

## What not to touch / Lo que no se toca

- **`LORE.md` and `ARQUETIPO.md`.** They are signed material.
- **Doctrine.** The signed cases, the exact phrasings, and the rules of the
  border belong to the author. If you find something that deserves a doctrinal
  change, say so in an issue — do not write it into the tree.
- **No third-party dependencies.** The product is standard library only. That
  is what makes the desktop build fit in 14 MB. If you believe something needs
  a dependency, that is a conversation, not a commit.

---

## Commit messages / Mensajes de commit

Spanish, and they explain **why**, not what — the diff already says what. The
history of this repository is a notebook: when a change comes from a measurement
or from something breaking, that goes in the message, with its number.
