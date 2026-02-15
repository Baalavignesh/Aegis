# Clean, Minimal Data Display — Aegis Frontend

Inspiration: **Robinhood** (clear numbers, subtle cards, plenty of white space), **Binance** (organized tables, status indicators), **AWS / MongoDB** (dashboard panels, clear section headers, readable metrics). Goal: **unique but clean** — no gimmicks, no overwhelming layouts.

---

## Principles

- **Typography first**: Clear hierarchy (section title → label → value). Consistent font sizes and weights.
- **Metrics as panels**: Like AWS/MongoDB — each metric in a simple, bordered panel; optional subtle count-up when value changes.
- **Status at a glance**: Small colored dot or thin left border (Robinhood/Binance style), not heavy visuals.
- **Motion**: Light touch only — short fade or stagger on load, maybe smooth number change; no flashy entrances or “command center” effects.

---

## 1. Stats (Dashboard)

- **Keep the card grid** (current 5 cards). Optionally:
  - Slightly tighter, consistent padding; label in muted uppercase or regular small; value as the focus.
  - **Subtle count-up** for numeric values when data refreshes (Robinhood-style).
- **Risk**: Keep as text label (LOW/MEDIUM/HIGH) with color; optional thin **progress bar** in the same card instead of or next to text.
- **No**: Gauges, radial charts, tickers, or “command strip” that changes the whole layout.

---

## 2. Agents list (Dashboard + Agents page)

- **Dashboard**: Keep current list — one row per agent: name, status dot, owner; right side: action count + risk.
- **Optional polish**: Thin **left border** (e.g. 3px) green/red by status; or a **thin risk bar** (narrow horizontal bar by risk %) so it’s scannable like Binance.
- **Agents page**: Keep **card grid**. Optional:
  - **Risk bar**: Thin bar under or beside the risk label (percentage as bar width).
  - **Hover**: Slight lift or border emphasis only (minimal).
- **No**: Bento grid, node graph, stacked cards, heavy animation.

---

## 3. Recent activity / Audit log

- **Keep list layout**. Optional:
  - **Status as left border**: 3–4px solid left border (green / yellow / red) per row instead of or in addition to dot.
  - **New row**: Very subtle fade-in when a new entry appears (short duration).
- **No**: Full timeline with line, terminal style, river/stream, ticker.

---

## 4. Approvals

- **Keep cards** with Approve/Deny buttons.
- **Optional**: When user approves or denies, **light exit animation** (fade + slight slide) so the card leaves the list smoothly; next card stays in place.
- **No**: Swipe, single-focus queue, drag-to-side.

---

## 5. Agent detail

- **Profile**: Keep current layout (header, status, stats grid). Optional: Risk as a **small progress bar** next to the label instead of only text.
- **Tools**: Keep current grouping (Allowed / Blocked / Review). Optional: Slightly clearer spacing; no need for tags animation.
- **Feed**: Same as activity — list with optional left border by status; optional subtle highlight when a new event appears for this agent.

---

## 6. Global

- **Optional**: Very short **fade-in** on page load for main content (e.g. 200ms); or **light stagger** (e.g. 30ms delay between stat cards) so the page doesn’t feel static.
- **Numbers**: Use **count-up** only for key metrics (e.g. stats, agent counts) so updates feel live but not distracting.
- **Loading**: Simple skeleton or spinner; no heavy shimmer unless it’s a single, subtle pattern.

---

## Summary

- **Do**: Refined cards, clear labels, optional thin status/risk bars, subtle count-up, light fade/stagger, minimal hover.
- **Avoid**: Gauges, radial charts, timelines with lines, terminal/ticker, bento/node graph, swipe, big layout changes.

This keeps the existing vibe while making data clearer and the UI a bit more polished and “big-dashboard” (Robinhood / Binance / AWS / MongoDB) without feeling extreme.
