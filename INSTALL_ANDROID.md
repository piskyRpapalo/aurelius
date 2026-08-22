# Installing Aurelius on an Android phone

**State, as of 2026-08-22: there are two paths, and only one of them exists.**
Said first, so nobody downloads what is not there.

*Versión en español: [INSTALACION_ANDROID.md](INSTALACION_ANDROID.md).*

| | State |
|---|---|
| **Termux** · one line, and Aurelius talks | **works today** |
| **APK** · install and open, no terminal | **does not exist yet** — see §4 |

---

## §1 · The path that works today · Termux

It asks you to type once. After that you do not need the terminal to use it.

1. Install **Termux** from F-Droid *(not from Google Play: that version is
   abandoned and fails)*.
2. Open it and type:

```
pkg install -y git
git clone --depth 1 https://github.com/piskyRpapalo/aurelius ~/aurelius
cd ~/aurelius && bash bin/instalar-android
```

3. When it finishes:

```
python3 aurelius.py                  # create your memory
bin/crear-acceso-directo-android     # the shortcut (optional, recommended)
bin/aurelius-servicio arranca        # the web face
```

4. Open your phone's browser at **http://127.0.0.1:8740**

### The icon on your home screen

Two ways, and they solve different halves.

**A shortcut that starts everything.** `bin/crear-acceso-directo-android`
writes a script that starts the server *and* opens the browser in one go. To
see it as an icon you need **Termux:Widget** (F-Droid): long-press the home
screen → Widgets → Termux → choose *Aurelius*. If Termux:Widget is not
installed, the script says so and tells you what to do — it does not create an
icon that would never appear.

**A browser shortcut.** With the face open in Chrome: menu **⋮ → Add to Home
screen**. That gives a real icon that opens Aurelius full screen, with no
browser bar. What it does **not** do is start the server: if it is not
running, the icon opens a page that will not load. That is why the first way
exists.

---

## §2 · Closed everything and cannot get back in?

It happened to the author. Until today there was no way to reopen it without
remembering a command, and that is a wall for anyone who did not build it.

### If you made the shortcut

Tap the **Aurelius** icon on your home screen. It starts the server and opens
the browser in one go.

### If you did not

1. Open **Termux**.
2. Type:

```
cd ~/aurelius && bin/aurelius-servicio arranca
```

3. Open your phone's browser at **http://127.0.0.1:8740**

### If it says the port is busy

An earlier copy is still running:

```
bin/aurelius-servicio para
```

And if it is still busy:

```
pkill -f aurelius-pwa
```

### How to tell whether it is alive

```
bin/aurelius-servicio estado
```

### After restarting the phone

Android does not start Termux on its own. Either tap the icon, or open Termux
and type the command above. For it to start by itself you need **Termux:Boot**
and an exemption from battery optimisation — both are granted from the
settings, by hand. No script can grant itself either one.

---

## §3 · What gets downloaded, and when

Nothing heavy arrives without your acceptance. On first run Aurelius offers,
with its licence and its fingerprint in front of you:

- the **brain**, 2.3 GB — without it, it asks and remembers but does not converse;
- the **voice**, 60 MB — optional; without it the button says so.

Measured on a Doogee S110: **about 3 tokens per second**. A short answer takes
minutes, and the interface warns you. It has not frozen.

---

## §4 · Why there is no APK yet

What was asked for is an APK that installs in one click and opens Aurelius. **A
WebView wrapper does not do that**, and it is worth understanding why before
commissioning one:

A WebView pointing at `127.0.0.1:8740` only shows something **if a server is
listening there**. That server is Python. An Android application does not run
Python unless it carries it inside. So an APK that is only a WebView would
install, open, and show a blank page — **worse than having nothing**, because it
looks broken instead of absent.

A real APK has to package the Python interpreter alongside the product. That is
an application project, not a wrapper, and it needs an Android build chain —
which is **not installed on the machine this is built on today** (only
`platform-tools`; no Java, no Gradle, no SDK tools).

**What can be promised without lying:** §1 plus the shortcut gives you, today,
an Aurelius that opens from an icon on your home screen.
