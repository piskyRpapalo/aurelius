# Aurelius

A **local-first learning companion** that teaches technical sovereignty through
playable missions. Named after Marcus Aurelius — the emperor who governed himself
in the middle of chaos without fearing it. Aurelius runs on your own hardware,
talks to a **local model** (no cloud), and walks you along *The Path* from running
your first offline model to holding your own cryptographic key.

It is a standalone organism, separate from the Hexelion dashboard, so its
multilingualism never contaminates that project's strict language law.

## 📐 Architectural Boundaries

Aurelius is deliberately fenced off, and the fences change how it behaves:

- **Language ownership** — the multi-locale toggle lives *here*, in Aurelius. The
  Hexelion dashboard's language law is strict and immutable (its command skin is
  English, its garden skin is French, its internal doctrine is Spanish). Adding a
  toggle there would break that law — which is exactly why Aurelius is its own
  repo. Its i18n (7 locales) is free to change without touching the other project.
- **Human-in-the-loop signing (IronClaw)** — Aurelius *proposes* commands; the
  human runs and signs them by hand. It never executes a value operation for you;
  it teaches you to do it yourself. Every mission ends with the learner signing
  what they created.
- **State separation, not authentication** — progress is stored per sovereign so a
  second learner never overwrites the first. This is separation for trusted people
  on a private network, **not** auth: real authentication is future work, and it's
  labeled as such in the code.

## 🧠 Stack

`Python` (state server) · `Ollama` + `Qwen` (local instruct model, streaming) ·
vanilla JS/HTML face · `Playwright` (viewport suite) · local vector memory for the
RAG mission.

## ✅ Status (real, not aspirational)

- [x] i18n scaffolding — 7 locales (`en` `es` `fr` human-verified; `pt` `de` `el` `ru` machine-translated and flagged, falling back to English rather than shipping bad doctrine)
- [x] Local model integration — streaming chat against a local Ollama/Qwen model
- [x] Stoic persona + adjustable verbosity (brief / normal / detailed)
- [x] The Path missions **M0–M2** playable end-to-end with persistent state
  - [x] M0 · The Totem (identity, sealed by hash)
  - [x] M1 · The Fire (run a model offline, sign the result)
  - [x] M2 · The Water (local RAG memory, sign the manifest)
- [x] Per-sovereign state separation (multi-user for trusted learners)
- [x] Sovereign inventory surfaced from the host's own hardware audit
- [ ] The Path missions **M3–M5** (Refuge · Signal · Pact)
- [ ] Real authentication (today: state separation only)
- [ ] Test suite runnable standalone (Playwright configured; dependency install pending)

<details>
<summary>The Path (mission map)</summary>

| Mission | Theme | What the learner does |
|---|---|---|
| **M0** | The Totem | Create an avatar identity, sealed by hash |
| **M1** | The Fire | Run a local model **offline**, save and sign its answer |
| **M2** | The Water | Build a local vector memory (RAG) and sign the manifest |
| **M3** | The Refuge | Self-host / go offline *(horizon)* |
| **M4** | The Signal | Local peer transfer *(horizon)* |
| **M5** | The Pact | Own cryptographic key *(horizon)* |

The scaffold retires as the learner climbs — help that never fades breeds
dependence, not sovereignty.

</details>
