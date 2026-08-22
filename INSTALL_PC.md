# Installing Aurelius on a computer

Two paths. The first is for using Aurelius; the second, for taking it apart.

*Versión en español: [INSTALACION_PC.md](INSTALACION_PC.md).*

---

## Path 1 · the file you open with a double click

**One file, 14 MB. No Python to install, nothing else either.**

1. Download `aurelius`.
2. Open it with a double click.
3. Your browser opens on Aurelius. That is all.

To close it, close the black window that opened with it.

### What it does and what it does not, said before you find out

**It does:** creates your memory, asks you the first-run questions, keeps your
memories, and shows you the border — the filter that blanks out keys, paths and
addresses before any text leaves your machine.

**It does not, yet:** converse. That needs two large pieces that do not fit
inside and **are not downloaded without your say-so**:

| Piece | Size | Why it is outside |
|---|---|---|
| The engine | ~10 MB | It is somebody else's executable. This project signs data, not programs. |
| The brain | **2.3 GB** | It is offered with its licence and its fingerprint in front of you, and you accept it. |

Without them, **Aurelius asks and remembers but does not converse**. That is the
honest description, and this file does not promise more than it carries.

### Where your things live

In `~/.aurelius/memory.db`. **One file.** Copy it, carry it on a USB stick, or
delete it. Nothing leaves your machine unless you export it.

---

## Closed everything and cannot get back in?

It happened to the author. It is not your fault: until today there was no way
to reopen it without remembering a command.

1. Look for **Aurelius** in your applications menu. If it is there, click it.
2. If it is not, open a terminal:

```
cd ~/aurelius && bin/aurelius-servicio arranca
```

It will say `arrancado · http://127.0.0.1:8740`. Open that address in your
browser.

### If it says the port is busy

An earlier copy is still running. **Watch out here**, because there is a trap:
the server can be called two different things depending on how you started it.

```
bin/aurelius-servicio para      # the clean way: stops whatever is there
```

And if it is still busy, what is left is the packaged executable, which has a
different name:

```
pkill -f aurelius-pwa           # the server launched from the repository
pkill -f 'dist/aurelius'        # the single-file executable
```

**A plain `pkill -f aurelius-pwa` does not catch the executable.** It happened
four times during development: the old process kept answering, the new one died
at birth, and everything looked fine while the wrong version was being measured.

### How to tell whether it is alive

```
bin/aurelius-servicio estado
```

It gives the pid and whether it answers. If it says `parado`, start it.

---

## The icon in your applications menu

If you cloned the repository, one line puts Aurelius in the menu:

```
bin/instalar-pc
```

It creates the icon and tells you how to get back in if something hangs. It
covers both paths: with the repository, the icon starts from it; with only the
downloaded file, it starts that.

To remove it: `bin/instalar-pc --desinstalar`. It **does not touch your
memory** or the product — only the icon.

---

## Path 2 · from the source

For anyone who wants to read it, change it or audit it.

```
git clone https://github.com/piskyRpapalo/aurelius
cd aurelius
python3 aurelius.py             # create your memory
python3 aurelius.py --charla    # talk, if a brain is installed
bin/aurelius-servicio arranca   # the web face
```

Python 3.10 or newer. **No dependencies**: the standard library only. That is
not an abstract virtue — it is what makes the file in path 1 fit in 14 MB
instead of 400.

---

## How the file in path 1 is built

```
uv pip install pyinstaller
bash empaquetado/construir_pc.sh
```

It lands in `dist/aurelius`. The script declares the pieces the packager cannot
see on its own — see the comment in `empaquetado/lanzador.py`, which exists
because the first version built a binary that died with
`No module named 'json'`.

**If anything fails, it stops.** No half-installed house that looks whole.
