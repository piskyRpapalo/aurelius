# Aurelius Mini — a pocket-sized, self-hostable Preceptor

**Status: plan, not measured.** This documents the *intended* recipe for a small,
fine-tuned Aurelius model that runs on a phone. Numbers here are targets and vendor
figures until this project measures them on real hardware — kept separate from
anything already measured (see `interface/models.json` for the measured anchor).

The goal: a Preceptor small enough to run **offline on a mid-range phone**, licensed
so it can actually be redistributed, so a learner owns the whole stack — not just the
app, but the mind inside it.

## 1. Base model — license first

- **Base: Qwen3.5-2B (Apache 2.0)**, or the current equivalent small **Apache-2.0 /
  MIT** instruct model. **Not Llama.** Llama's community license carries usage and
  redistribution restrictions that clash with a sovereignty project that wants to
  ship weights freely; a permissive license is a hard requirement, not a preference.
- Pin an **explicit instruct variant + quantization** — never a bare tag. A bare tag
  can resolve to a *Thinking* variant with non-disableable reasoning (documented
  footgun; same rule as `models.json`). Confirm the exact tag against the registry
  before trusting it.

## 2. Dataset — native chat template, not Alpaca

- Format every training example in the **base model's own native chat template**
  (its `<|im_start|>` / role-turn structure, applied via the tokenizer's
  `apply_chat_template`). **Do not use the Alpaca `### Instruction / ### Response`
  format.** Training in a template the model wasn't pre-trained on wastes capacity
  and degrades instruction-following, especially at 2B where there's little slack.
- Keep the Aurelius persona (Stoic Preceptor, IronClaw, the untrusted-data
  demarcation) in the **system turn**, consistently, so the fine-tune reinforces the
  safety doctrine rather than eroding it.

## 3. Training — needs a GPU

- **Fine-tuning requires a GPU.** **Unsloth on CPU does not train** — it accelerates
  training/inference on CUDA GPUs; there is no CPU training path that is remotely
  practical. Plan for a GPU box (rack node with a discrete GPU, or a rented cloud
  GPU for the training run only).
- Inference is a different question — a quantized 2B *runs* on CPU/phone fine. Only
  the **training step** is GPU-bound. Don't conflate the two.

## 4. Distribution — a Release asset, not Git LFS

- Ship the quantized weights (GGUF, target **< 2 GB**) as a **GitHub Release asset**,
  or on the **Hugging Face Hub**. **Do not commit weights via Git LFS** — LFS bloats
  clones, burns quota, and couples a binary artifact to source history. A Release
  asset / HF repo is the right home for a versioned binary.
- Publish the **SHA-256** of the artifact next to it, so a learner can verify what
  they downloaded (consistent with the sign-what-you-hold doctrine of The Path).

## 5. Android runtime — PocketPal / ChatterUI / Termux

- Run the GGUF on Android with **PocketPal**, **ChatterUI**, or **`llama.cpp` under
  Termux**. **Not MLC Chat** — MLC uses its own compiled model format and toolchain,
  which fragments the "one GGUF, many runtimes" story and is heavier to support.
- Sticking to GGUF + `llama.cpp`-family runtimes keeps the *same* artifact usable on
  the phone and on the rack.

## 6. RAG budget — small on purpose

- On-device retrieval must stay **tight: at most 2–3 chunks, ~1000 tokens** of
  retrieved context total. A 2B model on a phone has a small effective context and
  limited reasoning headroom; stuffing more retrieved text in *lowers* answer quality
  and slows generation. Retrieve less, retrieve better.

## Honest limits

- Everything above is a **recipe, not a benchmark.** Quality, speed, and memory of
  Aurelius Mini are **unmeasured** until trained and run on real devices; when they
  are, record the measured figures with their provenance (as `models.json` does) and
  never relabel a target as a measurement.
- A 2B model is **weaker** than the 30B-class anchor. That is an explicit trade for
  portability and ownership — the app should say so, not hide it (honest sensors,
  applied to our own model).
