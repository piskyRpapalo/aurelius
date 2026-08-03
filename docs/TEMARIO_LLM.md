# LLM Curriculum — Corrections of Record

Aurelius teaches how local language models actually work. Before the LLM
curriculum ("temario") is integrated into the missions, four corrections are
**mandatory** — one doctrinal error, one missing mechanism, and three smaller
fixes. They were approved as canon; this document is where they live on disk, so
the curriculum integration is bound by them and can be checked against them.

This is teaching *source*: the missions draw from it. Where a topic already has a
canon home (prompt injection → [`SAFE_PROMPTS.md`](SAFE_PROMPTS.md)), this file
points there instead of restating it.

---

## 1 · Doctrinal error — prompt injection is not solved by "inert text"

**Wrong (do not teach this):** *"Prompt injection is mitigated by treating all
external input strictly as inert text."*

That is a **false floor**. Treating external content as data is a *layer*, not a
guarantee — a language model is not perfectly robust, and a clever enough payload
or a weaker model can still be steered. If Aurelius teaches "inert text = safe,"
it graduates users who believe they are protected by a boundary that can yield.

**Right:** demarcation is **defense in depth**, and the real safety floor is
**architectural**: the model has no hands. Aurelius *proposes*; the human *runs
and signs* every command (IronClaw). Even a fully successful injection can only
*suggest*, never *act* — no shell, no value, no state change on the model's own
initiative. The wrapper raises the bar; the human-in-the-loop is the guarantee.

Full doctrine, with the choke point and the CI regression that enforces it:
[`SAFE_PROMPTS.md`](SAFE_PROMPTS.md). The curriculum must present the boundary as
a layer over an architectural floor — never as the floor itself.

---

## 2 · Missing mechanism — predict before you reveal

A well-timed tooltip is still *exposition*, not *retrieval*. Reading "this model
needs 18 GB" teaches far less than **guessing first and being wrong by a known
amount**.

**Mechanism:** before the Oráculo reveals the RAM a machine has (or a model
demands), Aurelius asks the user how much they think it is. The gap between the
prediction and the measurement is where the learning happens — the *generation
effect* and *desirable difficulties* (Bjork): a retrieval attempt, even a failed
one, encodes the correct value far better than passive reading.

This is not decoration. It changes the onboarding hardware step from "here is
your RAM" to "guess your RAM → here it is → here is how far off you were."
Implemented at the M0 onboarding hardware gate (`camino.js`, the M0 module):
the detected value is fetched but **withheld** until the user commits a guess,
then revealed alongside the signed delta.

---

## 3 · Three smaller fixes

### 3a · LLaMA is open-*weight*, not "open weights, full stop"

LLaMA ships its **weights** under a **restrictive license** — it is open-*weight*,
not an "open weights ecosystem" with no strings attached. This is not pedantry:
it is exactly the lesson that led this project to choose **Qwen**. Teach the
distinction between *open weights* and *open license*, and name the license
constraint as the reason a permissively-licensed model was preferred.

### 3b · RLHF — the humans rank; the RL optimizes a reward model

RLHF is commonly mis-taught as "humans reward the model directly." They do not.
The chain is:

1. Humans **rank/order** candidate responses (which is better).
2. Those rankings train a **reward model** that predicts human preference.
3. Reinforcement learning then optimizes the language model **against the reward
   model** — not against the humans directly.

The distinction matters: the policy is chasing a *learned proxy* of human
preference, which is why reward-model error (and reward hacking) is a real
failure mode, not a footnote.

### 3c · Calibration — why a model is confident when it is wrong

The single most important concept for a beginner running a **local** model, and
it is missing. A model's fluency and confidence are **not** evidence of
correctness: it can be maximally confident precisely when it is wrong, because it
was trained to produce plausible continuations, not to know what it does not
know. Without calibration, a beginner trusts the output at exactly the moment
they should not. Teach it early, and teach the habit that follows: verify claims
that carry cost, treat confident tone as *style*, not *proof*.

---

*Approved 2026-08-02 (Appendix B). Committed to disk 2026-08-03 — nothing is
canon until it exists in the repo.*
