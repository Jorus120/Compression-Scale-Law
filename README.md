# Compression Scaling Law (CSL) — Compact Release

**What is CSL?**  
A simple, interpretable way to **flag instability windows** in a time series. It looks for periods where multiple properties
change together — variance ↑, short-term persistence ↑, and spectral entropy ↓ — which are exactly the windows where
forecasts and controls tend to fail.

**Two flavours you can adopt immediately**
- **Canonical CSL (publishable):** quantize → lossless compress → compare against matched surrogates (IAAFT) across window sizes;
  fit a power law to extra compressibility; the slope gives **α** (hidden order index).
- **Lightweight proxy (ops-ready):** compute an instability proxy (e.g., variance ratio or coherence tilt), form **CSL(t) = Level × Slope**,
  and trigger alerts with a rolling quantile (budgeted), e.g., ~12 alerts / 5 years for monthly data.

> CSL is best used as an **early‑warning guardrail**, not as a point-event predictor.

---

## Quick replication (no heavy dependencies)
1. Pick a regularly sampled series (monthly works well).
2. Compute an instability proxy α(t):  
   - **Variance‑ratio:** α₁(t) = Var(6) / Var(24), ranked or z‑scored, or  
   - **Coherence‑tilt (proxy for canonical):** estimate scale tilt inside a 48‑sample window.
3. Build **Level** and **Slope** on α(t):  
   - Level: \(L(t) = [\alpha(t) - \text{median}_{13m}(\alpha)]_+\)  
   - Slope: \(S(t) = [\alpha(t) - \alpha(t-12)]_+\)
4. **CSL score:** \(\text{CSL}(t) = L(t) \times S(t)\)
5. **Budgeted threshold:** alert if CSL(t) > rolling (1 − p) quantile of past CSL values  
   (monthly: p ≈ 12/60 → about 12 alerts per 5 years; warm‑up ~36 months).
6. Record interpretable probes for each alert: Var(6), VarRatio(6/24), AC(1), Ljung–Box proxy, spectral entropy, band powers.

See **docs/CSL_Compact_Explainer.pdf** for a 2–3 page explanation and figures.

---

## What it’s good for
- **Model governance / risk gating:** widen CIs, require human sign‑off, or use robust settings under alerts.
- **Adaptive retraining:** only retrain when CSL stays elevated.
- **Observability triage:** quick “why now?” via probes.
- **Scientific change‑hunting:** highlight regime transitions (ENSO, sunspots, hydrology).

**What it is not:** an exact trough/top predictor.

---

## Canonical CSL (definition in one block)
1) Window the series (L ∈ {48, 64, …, 192}), 2) µ‑law 8‑bit quantize, 3) lossless compress (DEFLATE/bzip2/LZMA),
4) build **surrogates** (IAAFT; preserves spectrum/marginal), 5) compress surrogates identically,
6) for each L compute average code‑length contrast ∆(L), define \( \kappa(L) = -L\cdot\Delta(L) \),
7) fit \( \log \kappa(L) = a + b \log L \) and set **α = 1 − b**.

Interpretation: α ≈ 1 (near‑null), α < 1 (scale‑reinforcing hidden order), α > 1 (rare/divergent).

---

## Files
- `docs/CSL_Compact_Explainer.pdf` — 2–3 page explainer (everything you need to adopt CSL).
- `examples/synthetic_series.csv` — a tiny toy series with a variance‑burst regime change.
- `LICENSE` — MIT (broad reuse).
- `CITATION.cff` — How to cite.
- `CONTRIBUTING.md` — Short guidance for issues and small additions (keep it compact).

---

## License
MIT — see `LICENSE`.

---

## How to cite
If you use CSL in a report or post, please cite this repository and the explainer PDF.
