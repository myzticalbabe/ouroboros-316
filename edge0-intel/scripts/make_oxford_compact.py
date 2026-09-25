#!/usr/bin/env python3
# coding: utf-8
"""make_oxford_compact.py — render COMPACT.md into cinematic scroll pages.

Emits several *themes* of the same document so the look can be compared, then
captured frame-deterministically by `scripts/scroll_video.js`.

Generated, never transcribed: members / covenant / non-goals are parsed out of
COMPACT.md, and the emoji are pulled from the mesh repo's own emotional-emoji
vocabulary (`azazael/src/CODEX/CORE/emoji_maker.py`) — same glyph, same
`css_class`, same `animation` name — so the video cannot drift from the
document, and the page cannot drift from the emoji protocol. Every animation
name used here gets its own `@keyframes` in the emitted CSS.

Why the page is capturable at all:

  1. Self-contained: no network, no web fonts (display serif is Cambria/Georgia
     on Windows, UI sans is Segoe UI). A `file://` load is enough.
  2. Section reveals are *scroll-driven* (`animation-timeline: view()`), a pure
     function of scroll offset, not IntersectionObserver callbacks — so frame N
     is identical on every run.
  3. Ambience is *seekable*: `window.CAINClock.seek(t)` pauses every animation
     and sets `currentTime`, letting a capture choose `t` instead of waiting.
     Canonical implementation: `azazael/src/CODEX/CORE/scene_clock.py`; carried
     inline here because the Compact keeps the powers separate (the forge does
     not import the mesh at render time).

Usage:
    python scripts/make_oxford_compact.py --all
    python scripts/make_oxford_compact.py --theme prism
    python scripts/make_oxford_compact.py --list
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_COMPACT = HERE.parent / "COMPACT.md"
DEFAULT_PERSONAS = HERE.parent / "PEBBLES_BAMBAM.md"
OUT_DIR = HERE.parent / "variants"

# --------------------------------------------------------------------------- #
# Parse COMPACT.md
# --------------------------------------------------------------------------- #

_MEMBER_RE = re.compile(r"^-\s+\*\*(?P<name>[^*]+)\*\*(?P<rest>.*)$")
_COVENANT_RE = re.compile(r"^(?P<num>\d+)\.\s+(?P<body>.+)$")
_NAMED_RE = re.compile(r"^(?P<t>.*?)\s*\(named\s+(?P<d>[^)]+)\)\s*$")


def _flatten(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_compact(md: str) -> dict:
    """Parse COMPACT.md into {title, named, tagline, members, covenant, non_goals}."""
    out: dict = {"title": "The Oxford Compact", "named": "", "tagline": "",
                 "members": [], "covenant": [], "non_goals": ""}
    section: str | None = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal buf
        if not buf:
            return
        block = _flatten(" ".join(buf))
        buf = []
        if not block:
            return
        if section == "members":
            m = _MEMBER_RE.match(block)
            if m:
                rest = m.group("rest").strip()
                scope = ""
                sm = re.match(r"^\((?P<scope>[^)]+)\)\s*:?\s*(?P<desc>.*)$", rest)
                if sm:
                    scope, rest = sm.group("scope").strip(), sm.group("desc").strip()
                out["members"].append({"name": m.group("name").strip(), "scope": scope,
                                       "desc": rest.lstrip(": ").strip()})
        elif section == "covenant":
            m = _COVENANT_RE.match(block)
            if m:
                out["covenant"].append({"n": int(m.group("num")), "body": m.group("body")})
        elif section == "non_goals":
            out["non_goals"] = (out["non_goals"] + " " + block).strip()
        elif section is None and not out["tagline"]:
            out["tagline"] = block

    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("# "):
            flush()
            head = line[2:].strip()
            nm = _NAMED_RE.match(head)
            out["title"] = (nm.group("t") if nm else head).strip()
            out["named"] = (nm.group("d") if nm else "").strip()
            section = None
            continue
        if line.startswith("## "):
            flush()
            section = {"members": "members", "covenant": "covenant",
                       "non-goals": "non_goals", "non goals": "non_goals"}.get(
                line[3:].strip().lower())
            continue
        if not line.strip():
            flush()
            continue
        # COMPACT.md lists items with no blank line between them, so a new item
        # start must flush the previous one or the whole list parses as one.
        stripped = line.strip()
        starts_item = (section == "members" and stripped.startswith("- ")) or (
            section == "covenant" and bool(re.match(r"^\d+\.", stripped)))
        if starts_item:
            flush()
        buf.append(stripped)
    flush()
    return out


# --------------------------------------------------------------------------- #
# Personas — parsed from PEBBLES_BAMBAM.md (same rule as COMPACT.md: read,
# never transcribed, so the page cannot drift from the spec it illustrates).
# --------------------------------------------------------------------------- #

_PERSONA_RE = re.compile(r"^- \*\*(?P<name>[^—]+?) — (?P<epithet>[^.]+)\.\*\* (?P<body>.+)$")


def parse_personas(md: str) -> dict:
    """Parse PEBBLES_BAMBAM.md -> {pebbles:{name,epithet,body}, bambam:{...}, router}.

    Only the `### Definitions` bullets and the first two sentences of the
    `### Router rule` paragraph are taken — enough to caption the figures
    without copying the spec wholesale.
    """
    out: dict = {"router": ""}
    section: str | None = None
    buf: list[str] = []

    def flush() -> None:
        if not buf:
            return
        block = _flatten(" ".join(buf))
        buf.clear()
        if section == "defs":
            m = _PERSONA_RE.match(block)
            if m:
                name = m.group("name").strip()
                out[name.lower().replace("-", "")] = {
                    "name": name,
                    "epithet": m.group("epithet").strip(),
                    "body": m.group("body").strip(),
                }
        elif section == "router" and not out["router"]:
            sentences = block.split(". ")
            out["router"] = ". ".join(sentences[:2]).rstrip(".") + "."

    for raw in md.splitlines():
        line = raw.strip()
        if line.startswith("### "):
            flush()
            head = line[4:].strip().lower()
            section = "defs" if head == "definitions" else (
                "router" if head == "router rule" else None)
            continue
        if section is None:
            continue
        if not line:
            flush()
            continue
        if line.startswith("- "):
            flush()
        buf.append(line)
    flush()
    return out


# --------------------------------------------------------------------------- #
# Emotional emoji — verbatim from azazael/src/CODEX/CORE/emoji_maker.py
# (char, css_class, animation). Animation names must all be emitted below.
# --------------------------------------------------------------------------- #

EMOJI = {
    "determined": ("😤", "emoji-determined", "fire"),
    "curious":    ("🤔", "emoji-think", "hmm"),
    "handshake":  ("🤝", "emoji-shake", "meet"),
    "sparkles":   ("✨", "emoji-sparkle", "twinkle"),
    "heart":      ("❤️", "emoji-heart", "heartbeat"),
    "fire":       ("🔥", "emoji-fire", "flicker"),
    "relieved":   ("😌", "emoji-relieved", "sigh"),
    "sleep":      ("😴", "emoji-sleep", "zzz"),
    "shocked":    ("😲", "emoji-shock", "popIn"),
    "party":      ("🥳", "emoji-party", "confetti"),
    "thumbup":    ("👍", "emoji-thumbup", "bob"),
    "pray":       ("🙏", "emoji-pray", "gentlePulse"),
    "muscle":     ("💪", "emoji-flex", "grow"),
    "dizzy":      ("😵", "emoji-dizzy", "spin"),
    "clap":       ("👏", "emoji-clap", "clap"),
}

#: Every animation name referenced above -> its @keyframes body.
EMOJI_KEYFRAMES = {
    "fire":        "0%,100%{transform:translateY(0) scale(1);filter:brightness(1)}"
                   "50%{transform:translateY(-3px) scale(1.06);filter:brightness(1.25)}",
    "hmm":         "0%,100%{transform:rotate(0) translateX(0)}30%{transform:rotate(-6deg) translateX(-2px)}"
                   "65%{transform:rotate(4deg) translateX(2px)}",
    "meet":        "0%,100%{transform:translateX(0) scale(1)}50%{transform:translateX(3px) scale(1.08)}",
    "twinkle":     "0%,100%{opacity:.55;transform:scale(.9) rotate(0)}50%{opacity:1;transform:scale(1.15) rotate(12deg)}",
    "heartbeat":   "0%,100%{transform:scale(1)}18%{transform:scale(1.18)}36%{transform:scale(1)}54%{transform:scale(1.1)}",
    "flicker":     "0%,100%{opacity:.75;filter:brightness(1)}45%{opacity:1;filter:brightness(1.35)}70%{opacity:.85}",
    "sigh":        "0%,100%{transform:translateY(0)}50%{transform:translateY(3px) scale(.97)}",
    "zzz":         "0%,100%{transform:rotate(-8deg) scale(.94);opacity:.6}50%{transform:rotate(-8deg) scale(1.06);opacity:1}",
    "popIn":       "0%{transform:scale(.6);opacity:0}60%{transform:scale(1.16);opacity:1}100%{transform:scale(1)}",
    "confetti":    "0%,100%{transform:rotate(-10deg) translateY(0)}25%{transform:rotate(8deg) translateY(-4px)}"
                   "75%{transform:rotate(-6deg) translateY(-1px)}",
    "bob":         "0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}",
    "gentlePulse": "0%,100%{opacity:.8;transform:scale(1)}50%{opacity:1;transform:scale(1.05)}",
    "grow":        "0%,100%{transform:scale(1)}50%{transform:scale(1.14)}",
    "spin":        "0%{transform:rotate(0)}100%{transform:rotate(360deg)}",
    "clap":        "0%,100%{transform:translateY(0) rotate(0)}40%{transform:translateY(-5px) rotate(-8deg)}"
                   "80%{transform:translateY(-1px) rotate(4deg)}",
}


def _keyframes_css() -> str:
    """Emit every animation name the emoji reference (no phantom names)."""
    return "\n".join(
        f"  @keyframes {name} {{ {body} }}" for name, body in EMOJI_KEYFRAMES.items()
    )


# --------------------------------------------------------------------------- #
# Themes
# --------------------------------------------------------------------------- #

THEMES: dict[str, dict] = {
    # Heritage: ink + gold, editorial serif, restrained glass.
    "oxford": {
        "label": "Oxford Heritage",
        "blurb": "Ink and gold, editorial serif, restrained frosted glass.",
        "bg": "radial-gradient(120% 90% at 20% 0%, #101a2c 0%, #070b13 55%, #04060b 100%)",
        "chip": "#070b13",
        "blob_op": ".26", "blob_blur": "96px", "grid": "rgba(240,214,122,.15)", "grid_size": "96px",
        "fg": "#f5eddc", "muted": "rgba(245,237,220,.82)", "faint": "rgba(245,237,220,.5)",
        "gold": "#d4af37", "accent": "#f0d67a",
        "forge": "#34d399", "mesh": "#22d3ee", "audit": "#e0b352",
        "panel_bg": "rgba(255,255,255,.045)", "panel_edge": "rgba(255,255,255,.10)",
        "panel_blur": "16px", "panel_radius": "22px",
        "display": 'Cambria, Georgia, "Times New Roman", serif',
        "ui": '"Segoe UI", "Helvetica Neue", Arial, sans-serif',
        "title_grad": "linear-gradient(180deg,#fff 8%,#f0d67a 52%,#9a7b23 100%)",
        "extra": "", "scanlines": False, "gap_scale": "1",
    },
    # Maximal glassmorphism: bright gradient mesh, heavy frost, vivid facets.
    "prism": {
        "label": "Prism Glass",
        "blurb": "Maximal glassmorphism on a vivid gradient mesh; heavy frost.",
        "bg": "linear-gradient(140deg,#1b1050 0%,#12203f 38%,#062733 70%,#0a1030 100%)",
        "chip": "#0b1226",
        "blob_op": ".55", "blob_blur": "70px", "grid": "rgba(255,255,255,.14)", "grid_size": "72px",
        "fg": "#f7f9ff", "muted": "rgba(247,249,255,.9)", "faint": "rgba(247,249,255,.6)",
        "gold": "#a78bfa", "accent": "#7dd3fc",
        "forge": "#4ade80", "mesh": "#38bdf8", "audit": "#f0abfc",
        "panel_bg": "rgba(255,255,255,.09)", "panel_edge": "rgba(255,255,255,.22)",
        "panel_blur": "26px", "panel_radius": "28px",
        "display": 'Cambria, Georgia, "Times New Roman", serif',
        "ui": '"Segoe UI", "Helvetica Neue", Arial, sans-serif',
        "title_grad": "linear-gradient(120deg,#ffffff 0%,#a5f3fc 40%,#f0abfc 78%,#a78bfa 100%)",
        "extra": ".power{box-shadow:0 30px 80px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.35);}", "scanlines": False,
        "gap_scale": "1",
    },
    # Deep space telemetry: cyan/violet on black, hairline detailing.
    "aurora": {
        "label": "Aurora Telemetry",
        "blurb": "Deep-space neon, hairline instrumentation, telemetry labels.",
        "bg": "radial-gradient(90% 70% at 70% 10%, #06202b 0%, #050a16 55%, #02040a 100%)",
        "chip": "#04101a",
        "blob_op": ".38", "blob_blur": "84px", "grid": "rgba(34,211,238,.16)", "grid_size": "56px",
        "fg": "#dff6ff", "muted": "rgba(223,246,255,.84)", "faint": "rgba(223,246,255,.48)",
        "gold": "#22d3ee", "accent": "#a5f3fc",
        "forge": "#5eead4", "mesh": "#22d3ee", "audit": "#c4b5fd",
        "panel_bg": "rgba(34,211,238,.055)", "panel_edge": "rgba(34,211,238,.28)",
        "panel_blur": "14px", "panel_radius": "16px",
        "display": 'Cambria, Georgia, "Times New Roman", serif',
        "ui": '"Cascadia Mono", "Consolas", "Segoe UI", monospace',
        "title_grad": "linear-gradient(180deg,#ffffff 0%,#a5f3fc 55%,#0891b2 100%)",
        "extra": ".eyebrow{font-family:Cascadia Mono,Consolas,monospace;}.power-scope{font-family:Cascadia Mono,Consolas,monospace;}",
        "scanlines": False, "gap_scale": "1",
    },
    # Editorial light: warm paper, dark ink, gentle frost — print-like.
    "parchment": {
        "label": "Parchment Light",
        "blurb": "Warm paper and dark ink; light-theme frosted panels.",
        "bg": "radial-gradient(120% 90% at 30% 0%, #fffdf7 0%, #f6efe0 45%, #e8dcc4 100%)",
        "chip": "#fdfaf1",
        "blob_op": ".20", "blob_blur": "110px", "grid": "rgba(120,90,30,.10)", "grid_size": "88px",
        "fg": "#231c10", "muted": "rgba(35,28,16,.86)", "faint": "rgba(35,28,16,.55)",
        "gold": "#8a6a12", "accent": "#b3871a",
        "forge": "#0f7a52", "mesh": "#0e6c86", "audit": "#9a6a12",
        "panel_bg": "rgba(255,255,255,.55)", "panel_edge": "rgba(60,45,15,.18)",
        "panel_blur": "12px", "panel_radius": "16px",
        "display": 'Cambria, Georgia, "Times New Roman", serif',
        "ui": '"Segoe UI", "Helvetica Neue", Arial, sans-serif',
        "title_grad": "linear-gradient(180deg,#231c10 0%,#8a6a12 70%,#5c4608 100%)",
        "extra": ".vignette{background:radial-gradient(120% 80% at 50% 30%,transparent 45%,rgba(120,100,60,.30) 100%);}"
                 ".grid{opacity:.35;}",
        "scanlines": False, "gap_scale": "1",
    },
    # Technical dark: monospace, scanlines, colour used only as signal.
    "carbon": {
        "label": "Carbon Terminal",
        "blurb": "Monospace telemetry, scanlines, colour used only as signal.",
        "bg": "linear-gradient(180deg,#050708 0%,#0a0e12 60%,#050708 100%)",
        "chip": "#07090b",
        "blob_op": ".16", "blob_blur": "120px", "grid": "rgba(148,163,184,.14)", "grid_size": "48px",
        "fg": "#e6edf3", "muted": "rgba(230,237,243,.78)", "faint": "rgba(230,237,243,.42)",
        "gold": "#9aa4b2", "accent": "#e6edf3",
        "forge": "#3fb950", "mesh": "#58a6ff", "audit": "#d29922",
        "panel_bg": "rgba(255,255,255,.028)", "panel_edge": "rgba(255,255,255,.12)",
        "panel_blur": "8px", "panel_radius": "10px",
        "display": '"Cascadia Mono", "Consolas", "Courier New", monospace',
        "ui": '"Cascadia Mono", "Consolas", "Segoe UI", monospace',
        "title_grad": "linear-gradient(180deg,#ffffff 0%,#9aa4b2 100%)",
        "extra": ".title{letter-spacing:-.03em;}", "scanlines": True, "gap_scale": "1",
    },
}
THEME_ORDER = ["oxford", "prism", "aurora", "parchment", "carbon"]

# --------------------------------------------------------------------------- #
# Scene clock (canonical: azazael/src/CODEX/CORE/scene_clock.py)
# --------------------------------------------------------------------------- #

SCENE_CLOCK_JS = """
(function () {
  const state = { t: 0, ready: false };
  function anims() { try { return document.getAnimations(); } catch (e) { return []; } }

  /*
   * A scroll-driven animation (animation-timeline: view() / scroll()) takes its
   * time from the scroll offset, not from a clock. Pausing one, or assigning
   * currentTime, pins it wherever it happens to be — which, for every .reveal
   * element in this document, is the `from` keyframe at opacity 0. Seeking
   * them blanks the whole page after the hero, so they are handed straight
   * back to the scroll and only time-based animations are ever touched.
   */
  function scrollDriven(a) {
    try {
      const tl = a.timeline;
      if (!tl) return false;
      if (typeof ScrollTimeline !== 'undefined' && tl instanceof ScrollTimeline) return true;
      return 'source' in tl;   // ScrollTimeline exposes .source; DocumentTimeline does not
    } catch (e) { return false; }
  }
  function timed() { return anims().filter(a => !scrollDriven(a)); }

  window.CAINClock = {
    version: '1.1.0',
    state: state,
    isScrollDriven: scrollDriven,
    counts() {
      const all = anims();
      const sd = all.filter(scrollDriven).length;
      return { total: all.length, scrollDriven: sd, timed: all.length - sd };
    },
    pauseAll() { timed().forEach(a => { try { a.pause(); } catch (e) {} }); return this; },
    seek(t) {
      state.t = t;
      window.__CAIN_TIME__ = t;
      document.documentElement.style.setProperty('--cain-t', String(t));
      timed().forEach(a => { try { a.currentTime = t * 1000; } catch (e) {} });
      return this;
    },
    resumeAll() { timed().forEach(a => { try { a.play(); } catch (e) {} }); return this; },
    freeze() { this.pauseAll(); this.seek(0); return this; }
  };
  window.__SCENE_READY__ = true;
  state.ready = true;
})();
"""

# --------------------------------------------------------------------------- #
# Content blocks
# --------------------------------------------------------------------------- #

POWERS = [
    ("forge", "OXFORD SHARDFOUNDRY", "BUILDS", "evolution", "determined",
     "Evolves tensor-shard populations into champion models. Builds, never executes mesh tasks."),
    ("mesh", "AZAZAEL NEURAL MESH", "RUNS", "execution", "handshake",
     "Executing triage, monitoring, and action. Runs drivers, never grades them."),
    ("audit", "THE AUDIT OFFICE", "VERIFIES", "certification", "curious",
     "Evals, SVI, gates, ledgers, integrity, safety posture. Builds neither genomes nor runs worms; it admits or rejects."),
]

ARTICLE_EMOJI = ["handshake", "sparkles", "clap", "muscle", "pray", "curious"]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


# --------------------------------------------------------------------------- #
# Persona figures — original vector illustrations (not WB artwork).
# Shaded gradient volumes rather than flat doodles: skin/hair/cloth gradients
# lit from the upper left, layered face features, soft ground shadow. The
# clothing is leopard print (stone-age spotted hide) for both figures.
# `uid` prefixes every id — the same figure appears twice per page (hero +
# Dispatch), and duplicate ids would make url(#...) resolve to the wrong fill.
# --------------------------------------------------------------------------- #


def _pebbles_svg(uid: str) -> str:
    u = uid
    return f"""<svg class="persona-art pebbles" viewBox="0 0 220 300" role="img"
       aria-label="Pebbles, the clever director">
  <defs>
    <!-- photoreal pass (2026-09-24): form-shading + terminator gradient, ambient
         occlusion, two-light speculars, lidded eyes with limbal ring and double
         catchlight. Filters are all static — one rasterization per screenshot,
         nothing for CAINClock to pin. Geometry and palette are unchanged from
         the flat version, so pixel spot-checks and the leopard pattern hold. -->
    <linearGradient id="{u}pb-skin" x1="48" y1="30" x2="182" y2="290" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#fff3e4"/><stop offset=".34" stop-color="#fbdcbb"/>
      <stop offset=".7" stop-color="#f2c19a"/><stop offset="1" stop-color="#cd875e"/>
    </linearGradient>
    <linearGradient id="{u}pb-term" x1="62" y1="60" x2="168" y2="250" gradientUnits="userSpaceOnUse">
      <stop offset=".42" stop-color="#9c4f30" stop-opacity="0"/>
      <stop offset=".86" stop-color="#9c4f30" stop-opacity=".26"/>
      <stop offset="1" stop-color="#7d3a22" stop-opacity=".34"/>
    </linearGradient>
    <linearGradient id="{u}pb-hair" x1="72" y1="26" x2="150" y2="132" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#ffb277"/><stop offset=".45" stop-color="#e2551f"/><stop offset="1" stop-color="#8f2410"/>
    </linearGradient>
    <pattern id="{u}pb-leo" width="34" height="34" patternUnits="userSpaceOnUse" patternTransform="rotate(-8)">
      <rect width="34" height="34" fill="#eab973"/>
      <path d="M11,12c-4,-4 -12,-2 -12,3c0,5 6,7 10,4" fill="none" stroke="#3a2312" stroke-width="4.4" stroke-linecap="round"/>
      <path d="M27,27c-4,-4 -12,-2 -12,3c0,5 6,7 10,4" fill="none" stroke="#241608" stroke-width="4.4" stroke-linecap="round"/>
      <circle cx="26" cy="9" r="3.2" fill="#3a2312"/><circle cx="8" cy="28" r="2.8" fill="#241608"/>
    </pattern>
    <radialGradient id="{u}pb-blush">
      <stop offset="0" stop-color="#ef7f6d" stop-opacity=".55"/><stop offset="1" stop-color="#ef7f6d" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="{u}pb-iris" cx=".42" cy=".36" r=".75">
      <stop offset="0" stop-color="#b4854d"/><stop offset=".45" stop-color="#84552a"/>
      <stop offset=".82" stop-color="#5a3417"/><stop offset="1" stop-color="#2a1608"/>
    </radialGradient>
    <linearGradient id="{u}pb-sclera" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#cdc4c8"/><stop offset=".42" stop-color="#f6f1f0"/>
      <stop offset="1" stop-color="#fffdf9"/>
    </linearGradient>
    <linearGradient id="{u}pb-lip" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#c9584f"/><stop offset="1" stop-color="#e0817a"/>
    </linearGradient>
    <linearGradient id="{u}pb-bone" x1="0" y1="0" x2="0" y2="14" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#fffdf4"/><stop offset=".55" stop-color="#f1e9d4"/><stop offset="1" stop-color="#d6c9ab"/>
    </linearGradient>
    <filter id="{u}pb-soft" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="4"/></filter>
    <filter id="{u}pb-mid" x="-70%" y="-70%" width="240%" height="240%"><feGaussianBlur stdDeviation="2.4"/></filter>
    <filter id="{u}pb-tiny" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="1.1"/></filter>
    <filter id="{u}pb-wide" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="8"/></filter>
  </defs>
  <!-- contact shadow: wide ambient pool + tight occlusion core -->
  <ellipse cx="110" cy="289" rx="62" ry="12" fill="#0a0605" opacity=".26" filter="url(#{u}pb-wide)"/>
  <ellipse cx="110" cy="287" rx="44" ry="7" fill="#000" opacity=".34" filter="url(#{u}pb-soft)"/>
  <!-- legs: form gradient, medial shadow, knee sheen -->
  <rect x="84" y="200" width="25" height="72" rx="12.5" fill="url(#{u}pb-skin)"/>
  <path d="M96,206 q4,32 1,64" stroke="#9c4f30" stroke-opacity=".3" stroke-width="9" fill="none" stroke-linecap="round" filter="url(#{u}pb-mid)"/>
  <ellipse cx="90" cy="236" rx="5" ry="10" fill="#fff" opacity=".16" filter="url(#{u}pb-mid)"/>
  <rect x="113" y="200" width="25" height="72" rx="12.5" fill="url(#{u}pb-skin)"/>
  <path d="M124,206 q-2,32 1,64" stroke="#7d3a22" stroke-opacity=".3" stroke-width="9" fill="none" stroke-linecap="round" filter="url(#{u}pb-mid)"/>
  <ellipse cx="131" cy="236" rx="5" ry="10" fill="#fff" opacity=".14" filter="url(#{u}pb-mid)"/>
  <!-- feet + toe shading -->
  <ellipse cx="84" cy="276" rx="22" ry="10" fill="url(#{u}pb-skin)"/>
  <path d="M70,279 q14,6 28,0" stroke="#9c4f30" stroke-opacity=".28" stroke-width="5" fill="none" filter="url(#{u}pb-mid)"/>
  <ellipse cx="138" cy="276" rx="22" ry="10" fill="url(#{u}pb-skin)"/>
  <path d="M124,279 q14,6 28,0" stroke="#7d3a22" stroke-opacity=".3" stroke-width="5" fill="none" filter="url(#{u}pb-mid)"/>
  <!-- arms: rim light on the lit side, AO on the shadow side -->
  <path d="M80,154 C72,176 68,198 66,216" stroke="url(#{u}pb-skin)" stroke-width="25" stroke-linecap="round" fill="none"/>
  <path d="M74,158 C67,178 63,198 61,214" stroke="#fff" stroke-opacity=".3" stroke-width="5" stroke-linecap="round" fill="none" filter="url(#{u}pb-tiny)"/>
  <path d="M87,160 C80,180 76,198 74,214" stroke="#7d3a22" stroke-opacity=".28" stroke-width="6" stroke-linecap="round" fill="none" filter="url(#{u}pb-mid)"/>
  <path d="M140,156 C156,152 168,145 177,137" stroke="url(#{u}pb-skin)" stroke-width="26" stroke-linecap="round" fill="none"/>
  <path d="M142,150 C157,146 169,139 178,131" stroke="#fff" stroke-opacity=".28" stroke-width="5" stroke-linecap="round" fill="none" filter="url(#{u}pb-tiny)"/>
  <!-- hands: finger creases -->
  <circle cx="65" cy="224" r="13.5" fill="url(#{u}pb-skin)"/>
  <path d="M58,219 q6,7 4,14 M63,217 q6,8 4,16" stroke="#9c4f30" stroke-opacity=".35" stroke-width="1.6" fill="none" stroke-linecap="round"/>
  <circle cx="180" cy="133" r="14" fill="url(#{u}pb-skin)"/>
  <path d="M174,127 q3,7 1,13 M180,125 q3,7 1,13 M186,126 q2,6 0,12" stroke="#7d3a22" stroke-opacity=".32" stroke-width="1.6" fill="none" stroke-linecap="round"/>
  <!-- torso: core light left, terminator right, AO under the jaw -->
  <path d="M93,138c-16,5 -24,24 -24,50c0,30 10,54 24,60h22c14,-6 24,-30 24,-60c0,-26 -8,-45 -24,-50z" fill="url(#{u}pb-skin)"/>
  <path d="M93,138c-16,5 -24,24 -24,50c0,30 10,54 24,60h22c14,-6 24,-30 24,-60c0,-26 -8,-45 -24,-50z" fill="url(#{u}pb-term)"/>
  <path d="M82,152 q-6,42 4,84" stroke="#fff" stroke-opacity=".22" stroke-width="7" fill="none" stroke-linecap="round" filter="url(#{u}pb-mid)"/>
  <path d="M99,140 q11,7 22,0" stroke="#7d3a22" stroke-opacity=".4" stroke-width="8" fill="none" stroke-linecap="round" filter="url(#{u}pb-mid)"/>
  <!-- tunic: pattern, fold AO, sheen, hem occlusion -->
  <path d="M96,146 C84,151 78,166 78,188 C77,212 80,232 85,242 L137,242 C142,232 145,212 144,188 C143,166 137,151 125,146 Z" fill="url(#{u}pb-leo)"/>
  <path d="M96,146 C84,151 78,166 78,188 C77,212 80,232 85,242" fill="none" stroke="#000" stroke-opacity=".14" stroke-width="6"/>
  <path d="M99,150 C92,170 91,206 95,236" stroke="#000" stroke-opacity=".17" stroke-width="9" fill="none" stroke-linecap="round" filter="url(#{u}pb-mid)"/>
  <path d="M118,154 C122,180 122,212 119,238" stroke="#000" stroke-opacity=".13" stroke-width="8" fill="none" stroke-linecap="round" filter="url(#{u}pb-mid)"/>
  <path d="M129,152c6,14 8,36 7,58" stroke="#fff" stroke-opacity=".24" stroke-width="7" fill="none" stroke-linecap="round" filter="url(#{u}pb-tiny)"/>
  <path d="M87,238h48" stroke="#000" stroke-opacity=".2" stroke-width="7" stroke-linecap="round"/>
  <path d="M96,147 C104,154 118,154 125,147" stroke="#3a2312" stroke-opacity=".35" stroke-width="5" fill="none" stroke-linecap="round" filter="url(#{u}pb-tiny)"/>
  <!-- neck + jaw occlusion -->
  <path d="M99,118h22v20c0,9 -22,9 -22,0z" fill="url(#{u}pb-skin)"/>
  <path d="M99,124c6,8 16,8 22,0v7c-6,8 -16,8 -22,0z" fill="#000" opacity=".16"/>
  <path d="M100,121 c6,7 15,7 21,0" stroke="#7d3a22" stroke-opacity=".38" stroke-width="6" fill="none" filter="url(#{u}pb-tiny)"/>
  <!-- ears with concha shadow -->
  <ellipse cx="63" cy="98" rx="9" ry="12" fill="url(#{u}pb-skin)"/>
  <path d="M64,93 q-4,5 0,11" stroke="#9c4f30" stroke-opacity=".5" stroke-width="3" fill="none" stroke-linecap="round" filter="url(#{u}pb-tiny)"/>
  <ellipse cx="157" cy="98" rx="9" ry="12" fill="url(#{u}pb-skin)"/>
  <path d="M156,93 q4,5 0,11" stroke="#7d3a22" stroke-opacity=".55" stroke-width="3" fill="none" stroke-linecap="round" filter="url(#{u}pb-tiny)"/>
  <!-- head: base + terminator + key-light highlight -->
  <path d="M110,44c30,0 48,21 48,50c0,29 -21,50 -48,50c-27,0 -48,-21 -48,-50c0,-29 18,-50 48,-50z" fill="url(#{u}pb-skin)"/>
  <path d="M110,44c30,0 48,21 48,50c0,29 -21,50 -48,50c-27,0 -48,-21 -48,-50c0,-29 18,-50 48,-50z" fill="url(#{u}pb-term)"/>
  <ellipse cx="92" cy="76" rx="22" ry="18" fill="#fff" opacity=".18" filter="url(#{u}pb-soft)"/>
  <ellipse cx="84" cy="108" rx="16" ry="11" fill="url(#{u}pb-blush)"/>
  <ellipse cx="136" cy="108" rx="16" ry="11" fill="url(#{u}pb-blush)"/>
  <path d="M64,76c7,-19 25,-31 46,-31" stroke="#fff" stroke-opacity=".24" stroke-width="7" fill="none" stroke-linecap="round"/>
  <!-- hair: mass, lowlights, strand highlights, specular band, scalp AO -->
  <path d="M62,100 C58,56 80,32 110,32 C140,32 162,56 158,100
           C153,86 147,78 141,73 C133,84 117,89 103,85
           C91,81 84,73 80,64 C74,73 68,86 62,100 Z" fill="url(#{u}pb-hair)"/>
  <path d="M70,92 C74,66 90,48 114,44" stroke="#8f2410" stroke-opacity=".55" stroke-width="3" fill="none" stroke-linecap="round"/>
  <path d="M78,96 C82,72 96,56 118,50" stroke="#8f2410" stroke-opacity=".4" stroke-width="2.4" fill="none" stroke-linecap="round"/>
  <path d="M67,94 C71,68 88,50 112,42" stroke="#ffc78e" stroke-opacity=".7" stroke-width="2.6" fill="none" stroke-linecap="round"/>
  <path d="M126,44 C130,26 146,15 159,19 C150,25 146,36 145,47 Z" fill="url(#{u}pb-hair)"/>
  <path d="M133,41 C139,29 148,23 156,22" stroke="#ffb27a" stroke-opacity=".55" stroke-width="4" fill="none" stroke-linecap="round"/>
  <path d="M64,96 C74,100 92,104 106,101" stroke="#7d3a22" stroke-opacity=".35" stroke-width="6" fill="none" stroke-linecap="round" filter="url(#{u}pb-tiny)"/>
  <g transform="translate(116,32) rotate(-10)">
    <ellipse cx="26" cy="16" rx="22" ry="7" fill="#000" opacity=".22" filter="url(#{u}pb-tiny)"/>
    <rect x="8" y="4" width="34" height="8" rx="4" fill="url(#{u}pb-bone)"/>
    <circle cx="8" cy="4" r="6.5" fill="url(#{u}pb-bone)"/><circle cx="8" cy="12" r="6.5" fill="url(#{u}pb-bone)"/>
    <circle cx="42" cy="4" r="6.5" fill="url(#{u}pb-bone)"/><circle cx="42" cy="12" r="6.5" fill="url(#{u}pb-bone)"/>
    <path d="M11,14h28" stroke="#c4b48f" stroke-width="1.6" opacity=".8" fill="none"/>
    <path d="M16,6 q6,4 12,1 M28,11 q5,-4 10,-1" stroke="#c4b48f" stroke-width="1" opacity=".7" fill="none" stroke-linecap="round"/>
    <path d="M14,3 q14,-3 24,1" stroke="#fff" stroke-opacity=".8" stroke-width="1.6" fill="none" stroke-linecap="round"/>
  </g>
  <!-- eyes: lidded sclera, radial iris, limbal ring, lid shadow, double
       catchlight (soft key + sharp fill), waterline, lash line, flicks -->
  <ellipse cx="95" cy="102" rx="9.5" ry="11" fill="url(#{u}pb-sclera)"/>
  <ellipse cx="125" cy="102" rx="9.5" ry="11" fill="url(#{u}pb-sclera)"/>
  <ellipse cx="95" cy="95.5" rx="9" ry="5.5" fill="#5a4650" opacity=".3" filter="url(#{u}pb-tiny)"/>
  <ellipse cx="125" cy="95.5" rx="9" ry="5.5" fill="#5a4650" opacity=".3" filter="url(#{u}pb-tiny)"/>
  <circle cx="96" cy="103" r="6.4" fill="url(#{u}pb-iris)"/>
  <circle cx="126" cy="103" r="6.4" fill="url(#{u}pb-iris)"/>
  <g stroke="#e8c48d" stroke-opacity=".3" stroke-width=".9" stroke-linecap="round">
    <path d="M96,97.4 v-0.01 M91.5,105.5 l-1.4,1 M100.5,105.5 l1.4,1"/>
    <path d="M126,97.4 v-0.01 M121.5,105.5 l-1.4,1 M130.5,105.5 l1.4,1"/>
  </g>
  <circle cx="96" cy="103" r="6.4" fill="none" stroke="#1d0f06" stroke-width="1.3" opacity=".9"/>
  <circle cx="126" cy="103" r="6.4" fill="none" stroke="#1d0f06" stroke-width="1.3" opacity=".9"/>
  <circle cx="96" cy="103" r="3" fill="#0d0705"/><circle cx="126" cy="103" r="3" fill="#0d0705"/>
  <circle cx="93.4" cy="99.4" r="2.6" fill="#fff" opacity=".55" filter="url(#{u}pb-tiny)"/>
  <circle cx="123.4" cy="99.4" r="2.6" fill="#fff" opacity=".55" filter="url(#{u}pb-tiny)"/>
  <circle cx="97.6" cy="105.2" r="1.1" fill="#fff"/>
  <circle cx="127.6" cy="105.2" r="1.1" fill="#fff"/>
  <path d="M87,109 q8,4 16,-1" stroke="#ffd9c4" stroke-opacity=".6" stroke-width="1.6" fill="none" stroke-linecap="round"/>
  <path d="M117,108 q9,4 17,-2" stroke="#ffd9c4" stroke-opacity=".6" stroke-width="1.6" fill="none" stroke-linecap="round"/>
  <path d="M85,95 q10,-8 20,-2" stroke="#2a160d" stroke-width="3.2" fill="none" stroke-linecap="round"/>
  <path d="M115,93 q10,-6 20,2" stroke="#2a160d" stroke-width="3.2" fill="none" stroke-linecap="round"/>
  <path d="M104,94 l5,-3 M113,92.5 l5,-2.5" stroke="#2a160d" stroke-width="1.6" fill="none" stroke-linecap="round"/>
  <path d="M86,84 q9,-6 19,-2" stroke="#8f3a17" stroke-opacity=".55" stroke-width="4.5" fill="none" stroke-linecap="round" filter="url(#{u}pb-tiny)"/>
  <path d="M116,82 q10,-4 19,2" stroke="#8f3a17" stroke-opacity=".55" stroke-width="4.5" fill="none" stroke-linecap="round" filter="url(#{u}pb-tiny)"/>
  <path d="M86,83 q9,-6 19,-2" stroke="#a33d16" stroke-width="2.4" fill="none" stroke-linecap="round"/>
  <path d="M116,81 q10,-4 19,2" stroke="#a33d16" stroke-width="2.4" fill="none" stroke-linecap="round"/>
  <!-- nose: tip specular, nostril occlusion -->
  <ellipse cx="110" cy="111" rx="5" ry="3.6" fill="#fff" opacity=".34" filter="url(#{u}pb-tiny)"/>
  <ellipse cx="105.6" cy="116.4" rx="2.1" ry="1.5" fill="#9c4f30" opacity=".6" filter="url(#{u}pb-tiny)"/>
  <ellipse cx="114.4" cy="116.4" rx="2.1" ry="1.5" fill="#7d3a22" opacity=".6" filter="url(#{u}pb-tiny)"/>
  <path d="M106,114q5,5 10,1" stroke="#c98a62" stroke-width="3" fill="none" stroke-linecap="round"/>
  <!-- mouth: shaded lips, philtrum, gloss, chin shadow -->
  <path d="M98,126 q13,15 27,-1 q-13,7 -27,1z" fill="#8f2f2b"/>
  <path d="M101,129 q10,9 20,-1 q-10,4 -20,1z" fill="url(#{u}pb-lip)"/>
  <rect x="104" y="125" width="7" height="4" rx="1.6" fill="#fff" opacity=".9"/>
  <rect x="112" y="131.5" width="5" height="2.2" rx="1.1" fill="#fff" opacity=".75"/>
  <path d="M97,126 q-1.5,2 0,4 M126,125 q1.5,2 0,4" stroke="#7d3a22" stroke-opacity=".5" stroke-width="1.8" fill="none" stroke-linecap="round"/>
  <path d="M102,138 q9,5 18,-1" stroke="#7d3a22" stroke-opacity=".3" stroke-width="5" fill="none" stroke-linecap="round" filter="url(#{u}pb-tiny)"/>
</svg>"""


def _bambam_svg(uid: str) -> str:
    u = uid
    return f"""<svg class="persona-art bambam" viewBox="0 0 240 300" role="img"
       aria-label="Bamm-Bamm, the gentle executor">
  <defs>
    <!-- photoreal pass: same rig as Pebbles — warm key upper-left, cool
         terminator right, joint AO, two-light eye speculars, wood grain and
         cloth folds. Static filters only; geometry/palette unchanged. -->
    <linearGradient id="{u}bb-skin" x1="60" y1="34" x2="210" y2="290" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#fff3e4"/><stop offset=".34" stop-color="#fbdaba"/>
      <stop offset=".7" stop-color="#f0bf97"/><stop offset="1" stop-color="#ca845b"/>
    </linearGradient>
    <linearGradient id="{u}bb-term" x1="78" y1="64" x2="196" y2="256" gradientUnits="userSpaceOnUse">
      <stop offset=".42" stop-color="#98502f" stop-opacity="0"/>
      <stop offset=".86" stop-color="#98502f" stop-opacity=".26"/>
      <stop offset="1" stop-color="#7a3a20" stop-opacity=".34"/>
    </linearGradient>
    <linearGradient id="{u}bb-hair" x1="84" y1="30" x2="164" y2="112" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#ffffff"/><stop offset=".6" stop-color="#f3efe6"/><stop offset="1" stop-color="#c9c2ad"/>
    </linearGradient>
    <pattern id="{u}bb-leo" width="34" height="34" patternUnits="userSpaceOnUse" patternTransform="rotate(6)">
      <rect width="34" height="34" fill="#e5a052"/>
      <path d="M11,12c-4,-4 -12,-2 -12,3c0,5 6,7 10,4" fill="none" stroke="#221609" stroke-width="4.6" stroke-linecap="round"/>
      <path d="M27,27c-4,-4 -12,-2 -12,3c0,5 6,7 10,4" fill="none" stroke="#221609" stroke-width="4.6" stroke-linecap="round"/>
      <circle cx="26" cy="9" r="3.4" fill="#221609"/><circle cx="8" cy="28" r="3" fill="#221609"/>
    </pattern>
    <linearGradient id="{u}bb-wood" x1="182" y1="50" x2="226" y2="180" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#c08555"/><stop offset="1" stop-color="#6f4520"/>
    </linearGradient>
    <radialGradient id="{u}bb-blush"><stop offset="0" stop-color="#ef7f6d" stop-opacity=".5"/><stop offset="1" stop-color="#ef7f6d" stop-opacity="0"/></radialGradient>
    <radialGradient id="{u}bb-iris" cx=".42" cy=".36" r=".75">
      <stop offset="0" stop-color="#b4854d"/><stop offset=".45" stop-color="#84552a"/>
      <stop offset=".82" stop-color="#5a3417"/><stop offset="1" stop-color="#2a1608"/>
    </radialGradient>
    <linearGradient id="{u}bb-sclera" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#cdc4c8"/><stop offset=".42" stop-color="#f6f1f0"/>
      <stop offset="1" stop-color="#fffdf9"/>
    </linearGradient>
    <linearGradient id="{u}bb-lip" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#c9584f"/><stop offset="1" stop-color="#e0817a"/>
    </linearGradient>
    <linearGradient id="{u}bb-bone" x1="0" y1="0" x2="0" y2="12" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#fffdf4"/><stop offset=".55" stop-color="#f1e9d4"/><stop offset="1" stop-color="#d6c9ab"/>
    </linearGradient>
    <filter id="{u}bb-soft" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="4"/></filter>
    <filter id="{u}bb-mid" x="-70%" y="-70%" width="240%" height="240%"><feGaussianBlur stdDeviation="2.4"/></filter>
    <filter id="{u}bb-tiny" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="1.1"/></filter>
    <filter id="{u}bb-wide" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="8"/></filter>
  </defs>
  <!-- contact shadow -->
  <ellipse cx="120" cy="289" rx="64" ry="12" fill="#0a0605" opacity=".26" filter="url(#{u}bb-wide)"/>
  <ellipse cx="120" cy="287" rx="46" ry="7" fill="#000" opacity=".34" filter="url(#{u}bb-soft)"/>
  <!-- club: wood grain, highlight, head shading -->
  <path d="M196,170 L186,104 c-2,-16 9,-30 25,-30 c16,0 27,14 25,30 l-10,66 c-1,8 -8,13 -15,13 h-4 c-7,0 -13,-6 -11,-13 z" fill="url(#{u}bb-wood)"/>
  <path d="M198,166 L191,106 c-1,-13 7,-24 21,-25" stroke="#e0ac72" stroke-opacity=".6" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path d="M216,60 c8,6 11,17 9,30 l-7,50" stroke="#4c2c12" stroke-opacity=".45" stroke-width="6" fill="none" stroke-linecap="round" filter="url(#{u}bb-mid)"/>
  <path d="M199,132 q10,-3 20,-1 M197,146 q11,-3 21,-1 M195,160 q12,-3 21,-1" stroke="#6f4520" stroke-opacity=".5" stroke-width="2" fill="none" stroke-linecap="round"/>
  <ellipse cx="216" cy="68" rx="14" ry="10" fill="#a9743f"/>
  <ellipse cx="212" cy="64" rx="7" ry="4.6" fill="#c89055" opacity=".7"/>
  <ellipse cx="212" cy="63" rx="4" ry="2.4" fill="#e6c193" opacity=".8"/>
  <!-- legs: form, medial shadow, knee sheen -->
  <path d="M104,206 L102,266" stroke="url(#{u}bb-skin)" stroke-width="30" stroke-linecap="round" fill="none"/>
  <path d="M97,210 L95,262" stroke="#fff" stroke-opacity=".24" stroke-width="6" stroke-linecap="round" fill="none" filter="url(#{u}bb-tiny)"/>
  <path d="M113,212 L111,262" stroke="#7a3a20" stroke-opacity=".3" stroke-width="7" stroke-linecap="round" fill="none" filter="url(#{u}bb-mid)"/>
  <path d="M138,206 L140,266" stroke="url(#{u}bb-skin)" stroke-width="30" stroke-linecap="round" fill="none"/>
  <path d="M133,210 L136,262" stroke="#fff" stroke-opacity=".22" stroke-width="6" stroke-linecap="round" fill="none" filter="url(#{u}bb-tiny)"/>
  <path d="M147,212 L149,262" stroke="#7a3a20" stroke-opacity=".3" stroke-width="7" stroke-linecap="round" fill="none" filter="url(#{u}bb-mid)"/>
  <ellipse cx="98" cy="274" rx="24" ry="11" fill="url(#{u}bb-skin)"/>
  <path d="M83,277 q15,7 30,0" stroke="#98502f" stroke-opacity=".3" stroke-width="5" fill="none" filter="url(#{u}bb-mid)"/>
  <ellipse cx="146" cy="274" rx="24" ry="11" fill="url(#{u}bb-skin)"/>
  <path d="M131,277 q15,7 30,0" stroke="#7a3a20" stroke-opacity=".32" stroke-width="5" fill="none" filter="url(#{u}bb-mid)"/>
  <!-- arms with rim + AO -->
  <path d="M86,158 C76,180 72,200 70,218" stroke="url(#{u}bb-skin)" stroke-width="26" stroke-linecap="round" fill="none"/>
  <path d="M80,162 C71,182 67,200 65,216" stroke="#fff" stroke-opacity=".3" stroke-width="5" stroke-linecap="round" fill="none" filter="url(#{u}bb-tiny)"/>
  <path d="M93,164 C84,184 80,202 78,218" stroke="#7a3a20" stroke-opacity=".26" stroke-width="6" stroke-linecap="round" fill="none" filter="url(#{u}bb-mid)"/>
  <circle cx="69" cy="226" r="14" fill="url(#{u}bb-skin)"/>
  <path d="M62,221 q6,7 4,14 M67,219 q6,8 4,16" stroke="#98502f" stroke-opacity=".35" stroke-width="1.6" fill="none" stroke-linecap="round"/>
  <path d="M164,152 C178,156 190,166 196,176" stroke="url(#{u}bb-skin)" stroke-width="27" stroke-linecap="round" fill="none"/>
  <path d="M166,147 C179,151 191,161 197,171" stroke="#fff" stroke-opacity=".26" stroke-width="5" stroke-linecap="round" fill="none" filter="url(#{u}bb-tiny)"/>
  <!-- torso: terminator, pec/line shading, rim -->
  <path d="M100,138c-18,6 -28,26 -28,54c0,32 11,56 26,62h24c15,-6 26,-30 26,-62c0,-28 -10,-48 -28,-54z" fill="url(#{u}bb-skin)"/>
  <path d="M100,138c-18,6 -28,26 -28,54c0,32 11,56 26,62h24c15,-6 26,-30 26,-62c0,-28 -10,-48 -28,-54z" fill="url(#{u}bb-term)"/>
  <path d="M84,154 q-6,46 5,88" stroke="#fff" stroke-opacity=".2" stroke-width="7" fill="none" stroke-linecap="round" filter="url(#{u}bb-mid)"/>
  <path d="M96,142 q14,8 27,0" stroke="#7a3a20" stroke-opacity=".4" stroke-width="8" fill="none" stroke-linecap="round" filter="url(#{u}bb-mid)"/>
  <path d="M112,166 q10,26 8,54" stroke="#7a3a20" stroke-opacity=".22" stroke-width="4" fill="none" stroke-linecap="round" filter="url(#{u}bb-tiny)"/>
  <!-- chest strap with AO + bone -->
  <path d="M92,150 L158,216" stroke="#5f3a17" stroke-opacity=".4" stroke-width="15" stroke-linecap="round" filter="url(#{u}bb-tiny)"/>
  <path d="M92,150 L158,216" stroke="#7a4a22" stroke-width="12" stroke-linecap="round"/>
  <path d="M91,147 L157,213" stroke="#b57c44" stroke-width="4" stroke-linecap="round" opacity=".6"/>
  <g transform="translate(106,170) rotate(45)">
    <ellipse cx="19" cy="14" rx="17" ry="5.5" fill="#000" opacity=".22" filter="url(#{u}bb-tiny)"/>
    <rect x="6" y="3" width="26" height="6" rx="3" fill="url(#{u}bb-bone)"/>
    <circle cx="6" cy="3" r="5.4" fill="url(#{u}bb-bone)"/><circle cx="6" cy="9" r="5.4" fill="url(#{u}bb-bone)"/>
    <circle cx="32" cy="3" r="5.4" fill="url(#{u}bb-bone)"/><circle cx="32" cy="9" r="5.4" fill="url(#{u}bb-bone)"/>
    <path d="M11,4 q9,-2 16,1" stroke="#fff" stroke-opacity=".85" stroke-width="1.5" fill="none" stroke-linecap="round"/>
    <path d="M13,11 q7,3 13,0" stroke="#c4b48f" stroke-width="1.2" opacity=".75" fill="none" stroke-linecap="round"/>
  </g>
  <!-- loincloth: pattern, folds, hem AO, sheen -->
  <path d="M80,196 L164,196 C166,224 162,250 156,268 L140,254 L126,272 L112,254 L98,270 L86,252 C80,234 78,216 80,196 Z" fill="url(#{u}bb-leo)"/>
  <path d="M80,202 L164,202" stroke="#000" stroke-opacity=".2" stroke-width="8" stroke-linecap="round"/>
  <path d="M94,204 C90,224 91,246 96,262" stroke="#000" stroke-opacity=".16" stroke-width="9" fill="none" stroke-linecap="round" filter="url(#{u}bb-mid)"/>
  <path d="M124,206 C127,228 126,248 122,266" stroke="#000" stroke-opacity=".12" stroke-width="8" fill="none" stroke-linecap="round" filter="url(#{u}bb-mid)"/>
  <path d="M150,210 C156,232 154,250 150,262" fill="none" stroke="#000" stroke-opacity=".12" stroke-width="7" stroke-linecap="round"/>
  <path d="M157,204 C161,226 159,246 155,260" stroke="#fff" stroke-opacity=".22" stroke-width="6" fill="none" stroke-linecap="round" filter="url(#{u}bb-tiny)"/>
  <!-- neck + jaw AO -->
  <path d="M106,118h26v22c0,10 -26,10 -26,0z" fill="url(#{u}bb-skin)"/>
  <path d="M106,124c7,9 19,9 26,0v7c-7,9 -19,9 -26,0z" fill="#000" opacity=".16"/>
  <path d="M107,121 c7,7 18,7 25,0" stroke="#7a3a20" stroke-opacity=".38" stroke-width="6" fill="none" filter="url(#{u}bb-tiny)"/>
  <!-- ears -->
  <ellipse cx="71" cy="98" rx="9" ry="12" fill="url(#{u}bb-skin)"/>
  <path d="M72,93 q-4,5 0,11" stroke="#98502f" stroke-opacity=".5" stroke-width="3" fill="none" stroke-linecap="round" filter="url(#{u}bb-tiny)"/>
  <ellipse cx="169" cy="98" rx="9" ry="12" fill="url(#{u}bb-skin)"/>
  <path d="M168,93 q4,5 0,11" stroke="#7a3a20" stroke-opacity=".55" stroke-width="3" fill="none" stroke-linecap="round" filter="url(#{u}bb-tiny)"/>
  <!-- head: base, terminator, key highlight -->
  <path d="M120,46c31,0 50,22 50,50c0,29 -22,50 -50,50c-28,0 -50,-21 -50,-50c0,-28 19,-50 50,-50z" fill="url(#{u}bb-skin)"/>
  <path d="M120,46c31,0 50,22 50,50c0,29 -22,50 -50,50c-28,0 -50,-21 -50,-50c0,-28 19,-50 50,-50z" fill="url(#{u}bb-term)"/>
  <ellipse cx="100" cy="78" rx="23" ry="18" fill="#fff" opacity=".18" filter="url(#{u}bb-soft)"/>
  <ellipse cx="94" cy="110" rx="16" ry="11" fill="url(#{u}bb-blush)"/>
  <ellipse cx="146" cy="110" rx="16" ry="11" fill="url(#{u}bb-blush)"/>
  <path d="M74,78c8,-19 26,-31 46,-31" stroke="#fff" stroke-opacity=".24" stroke-width="7" fill="none" stroke-linecap="round"/>
  <!-- white hair: mass, gray lowlights, specular, scalp AO -->
  <path d="M70,106 C64,58 88,34 120,34 C152,34 176,58 170,106
           C166,90 160,80 154,74 L148,88 L141,70 L133,86 L126,66 L118,84
           L110,68 L102,86 L96,70 L90,88 L84,74 C78,82 72,94 70,106 Z" fill="url(#{u}bb-hair)"/>
  <path d="M78,96 C84,66 100,48 126,44" stroke="#b7ae95" stroke-opacity=".6" stroke-width="2.6" fill="none" stroke-linecap="round"/>
  <path d="M86,100 C92,72 106,56 130,50" stroke="#b7ae95" stroke-opacity=".45" stroke-width="2.2" fill="none" stroke-linecap="round"/>
  <path d="M74,98 C80,66 98,46 124,40" stroke="#ffffff" stroke-opacity=".9" stroke-width="3" fill="none" stroke-linecap="round"/>
  <path d="M72,102 C82,106 98,110 112,107" stroke="#a79d82" stroke-opacity=".45" stroke-width="6" fill="none" stroke-linecap="round" filter="url(#{u}bb-tiny)"/>
  <!-- eyes: lidded sclera, radial iris, limbal ring, lid shadow, double
       catchlight, waterline, lashes, pale brows -->
  <ellipse cx="104" cy="104" rx="9.5" ry="11" fill="url(#{u}bb-sclera)"/>
  <ellipse cx="136" cy="104" rx="9.5" ry="11" fill="url(#{u}bb-sclera)"/>
  <ellipse cx="104" cy="97.5" rx="9" ry="5.5" fill="#5a4650" opacity=".3" filter="url(#{u}bb-tiny)"/>
  <ellipse cx="136" cy="97.5" rx="9" ry="5.5" fill="#5a4650" opacity=".3" filter="url(#{u}bb-tiny)"/>
  <circle cx="105" cy="105" r="6.4" fill="url(#{u}bb-iris)"/>
  <circle cx="137" cy="105" r="6.4" fill="url(#{u}bb-iris)"/>
  <g stroke="#e8c48d" stroke-opacity=".3" stroke-width=".9" stroke-linecap="round">
    <path d="M105,99.4 v-0.01 M100.5,107.5 l-1.4,1 M109.5,107.5 l1.4,1"/>
    <path d="M137,99.4 v-0.01 M132.5,107.5 l-1.4,1 M141.5,107.5 l1.4,1"/>
  </g>
  <circle cx="105" cy="105" r="6.4" fill="none" stroke="#1d0f06" stroke-width="1.3" opacity=".9"/>
  <circle cx="137" cy="105" r="6.4" fill="none" stroke="#1d0f06" stroke-width="1.3" opacity=".9"/>
  <circle cx="105" cy="105" r="3" fill="#0d0705"/><circle cx="137" cy="105" r="3" fill="#0d0705"/>
  <circle cx="102.4" cy="101.4" r="2.6" fill="#fff" opacity=".55" filter="url(#{u}bb-tiny)"/>
  <circle cx="134.4" cy="101.4" r="2.6" fill="#fff" opacity=".55" filter="url(#{u}bb-tiny)"/>
  <circle cx="106.6" cy="107.2" r="1.1" fill="#fff"/>
  <circle cx="138.6" cy="107.2" r="1.1" fill="#fff"/>
  <path d="M96,111 q8,4 16,-1" stroke="#ffd9c4" stroke-opacity=".6" stroke-width="1.6" fill="none" stroke-linecap="round"/>
  <path d="M128,110 q9,4 17,-2" stroke="#ffd9c4" stroke-opacity=".6" stroke-width="1.6" fill="none" stroke-linecap="round"/>
  <path d="M95,97 q10,-7 21,-3" stroke="#2a160d" stroke-width="3.2" fill="none" stroke-linecap="round"/>
  <path d="M127,94 q11,-4 21,4" stroke="#2a160d" stroke-width="3.2" fill="none" stroke-linecap="round"/>
  <path d="M115,95.5 l5,-2.5 M124,93.5 l5,-2" stroke="#2a160d" stroke-width="1.6" fill="none" stroke-linecap="round"/>
  <path d="M94,88q10,-7 21,-3" stroke="#efe9db" stroke-width="4.5" fill="none" stroke-linecap="round" filter="url(#{u}bb-tiny)"/>
  <path d="M127,85q11,-4 21,4" stroke="#efe9db" stroke-width="4.5" fill="none" stroke-linecap="round" filter="url(#{u}bb-tiny)"/>
  <path d="M94,88q10,-7 21,-3" stroke="#b7ae95" stroke-opacity=".8" stroke-width="1.8" fill="none" stroke-linecap="round"/>
  <path d="M127,85q11,-4 21,4" stroke="#b7ae95" stroke-opacity=".8" stroke-width="1.8" fill="none" stroke-linecap="round"/>
  <!-- nose -->
  <ellipse cx="120" cy="113" rx="5" ry="3.6" fill="#fff" opacity=".34" filter="url(#{u}bb-tiny)"/>
  <ellipse cx="115.6" cy="118.4" rx="2.1" ry="1.5" fill="#98502f" opacity=".6" filter="url(#{u}bb-tiny)"/>
  <ellipse cx="124.4" cy="118.4" rx="2.1" ry="1.5" fill="#7a3a20" opacity=".6" filter="url(#{u}bb-tiny)"/>
  <path d="M115,117q6,6 12,1" stroke="#c98a62" stroke-width="3" fill="none" stroke-linecap="round"/>
  <!-- mouth -->
  <path d="M104,130 q18,18 36,-2 q-18,8 -36,2z" fill="#8f2f2b"/>
  <path d="M108,133 q14,11 28,-2 q-14,6 -28,2z" fill="url(#{u}bb-lip)"/>
  <rect x="112" y="128" width="8" height="4.5" rx="1.8" fill="#fff" opacity=".9"/>
  <rect x="124" y="130" width="7" height="4" rx="1.7" fill="#fff" opacity=".85"/>
  <path d="M103,130 q-2,2 0,4 M141,128 q2,2 0,4" stroke="#7a3a20" stroke-opacity=".5" stroke-width="1.8" fill="none" stroke-linecap="round"/>
  <path d="M110,142 q11,5 22,-2" stroke="#7a3a20" stroke-opacity=".3" stroke-width="5" fill="none" stroke-linecap="round" filter="url(#{u}bb-tiny)"/>
  <!-- gripping hand over the club -->
  <circle cx="186" cy="176" r="15" fill="url(#{u}bb-skin)"/>
  <path d="M177,169 c5,-5 14,-5 18,-1" stroke="#7a3a20" stroke-opacity=".35" stroke-width="3.4" fill="none" stroke-linecap="round"/>
  <path d="M179,176 q6,6 5,13 M185,174 q6,7 4,14 M191,174 q5,6 3,13" stroke="#7a3a20" stroke-opacity=".32" stroke-width="1.7" fill="none" stroke-linecap="round"/>
  <ellipse cx="182" cy="170" rx="6" ry="4" fill="#fff" opacity=".2" filter="url(#{u}bb-tiny)"/>
</svg>"""


def _personas_html(personas: dict) -> str:
    """Dispatch section: both figures with their spec captions + router rule."""
    router = html.escape(personas.get("router", "").replace("=>", "→"))
    cards = []
    for key, art, cls, rng in (
        ("pebbles", _pebbles_svg("c"), "pebbles-card", "entry 4% cover 24%"),
        ("bambam", _bambam_svg("c"), "bambam-card", "entry 8% cover 28%"),
    ):
        p = personas.get(key)
        if not p:
            continue
        cards.append(f"""
        <article class="persona glass reveal {cls}" style="animation-range: {rng}">
          <div class="persona-figure">{art}</div>
          <div class="persona-copy">
            <h3 class="persona-name">{html.escape(p["name"])}</h3>
            <span class="persona-tag">{html.escape(p["epithet"])}</span>
            <p class="persona-desc">{html.escape(p["body"])}</p>
          </div>
        </article>""")
    out = f'      <div class="personas">' + "\n".join(cards) + "\n      </div>"
    if router:
        out += (f'\n      <p class="separation reveal">Router rule: <b>{router}</b></p>')
    return out


def _emoji(key: str, size: int = 22) -> str:
    char, css_class, animation = EMOJI[key]
    return (f'<span class="em {css_class}" style="font-size:{size}px;'
            f'animation-name:{animation}">{char}</span>')


def _powers_html(members: list[dict]) -> str:
    cards = []
    for i, (key, label, verb, scope, emo, fallback) in enumerate(POWERS):
        desc, scope_txt = fallback, scope
        if i < len(members):
            desc = members[i]["desc"] or fallback
            if members[i]["scope"]:
                scope_txt = members[i]["scope"]
        cards.append(f"""
        <article class="power {key} reveal" style="animation-range: entry {5 + i * 7}% cover {30 + i * 7}%">
          <div class="power-top"><span class="power-glyph">{_emoji(emo, 26)}</span>
            <span class="power-verb">{verb}</span></div>
          <h3 class="power-name">{html.escape(label)}</h3>
          <p class="power-desc">{html.escape(desc)}</p>
          <span class="power-scope">{html.escape(scope_txt)}</span>
        </article>""")
    return "\n".join(cards)


def _covenant_html(covenant: list[dict]) -> str:
    rows = []
    for i, art in enumerate(covenant):
        roman = ROMAN[i] if i < len(ROMAN) else str(art["n"])
        emo = ARTICLE_EMOJI[i % len(ARTICLE_EMOJI)]
        rows.append(f"""
          <li class="article reveal" style="animation-range: entry {4 + i * 8}% cover {28 + i * 8}%">
            <span class="article-n">{roman}</span>
            <span class="article-emoji">{_emoji(emo, 20)}</span>
            <p class="article-body">{html.escape(art["body"])}</p>
          </li>""")
    return "\n".join(rows)


def _edge_chip(cx: int, cy: int, text: str) -> str:
    """Label plate centred on (cx, cy), sized from the text it carries.

    The backing rect is opaque (the per-theme --chip colour) so the marching
    edge never runs through the words: hand-placed labels used to sit right
    on top of the dashes.
    """
    w = int(len(text) * (13 * 0.64 + 13 * 0.14) + 26)
    return (f'<g class="elabel"><rect class="chip" x="{cx - w // 2}" y="{cy - 13}" '
            f'width="{w}" height="26" rx="13"/>'
            f'<text x="{cx}" y="{cy + 5}">{text}</text></g>')


def _flow_html() -> str:
    """Three flow charts: the power loop, the crossing pipeline, the gates."""
    return f"""
      <div class="flows">
        <!-- 1. Power loop: builds -> runs -> verifies, each closing on the ledger -->
        <figure class="flow reveal glass" style="animation-range: entry 6% cover 32%">
          <figcaption><span class="flow-n">A</span>Separation of powers
            <em>· one role each, closing on the ledger</em></figcaption>
          <svg viewBox="0 0 960 470" role="img" aria-label="Forge builds, mesh runs, audit verifies, all meeting at the ledger">
            <defs>
              <marker id="arw-forge" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path class="mk mk-forge" d="M0,0 L10,5 L0,10 z"/>
              </marker>
              <marker id="arw-mesh" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path class="mk mk-mesh" d="M0,0 L10,5 L0,10 z"/>
              </marker>
              <marker id="arw-audit" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path class="mk mk-audit" d="M0,0 L10,5 L0,10 z"/>
              </marker>
              <marker id="arw-gold" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path class="mk mk-gold" d="M0,0 L10,5 L0,10 z"/>
              </marker>
            </defs>
            <g class="flow-edges" fill="none">
              <path class="edge e1" d="M266,130 L694,130" marker-end="url(#arw-forge)"/>
              <path class="edge e2" d="M710,173 L530,325" marker-end="url(#arw-mesh)"/>
              <path class="edge e3" d="M430,325 L250,173" marker-end="url(#arw-audit)"/>
              <path class="edge spoke" d="M260,157 L379,210" marker-end="url(#arw-gold)"/>
              <path class="edge spoke" d="M700,157 L581,210" marker-end="url(#arw-gold)"/>
              <path class="edge spoke" d="M480,302 L480,258" marker-end="url(#arw-gold)"/>
            </g>
            <g class="flow-nodes">
              <g class="node forge"><circle cx="200" cy="130" r="66"/><text x="200" y="124">FORGE</text><text class="sub" x="200" y="148">builds</text></g>
              <g class="node mesh"><circle cx="760" cy="130" r="66"/><text x="760" y="124">MESH</text><text class="sub" x="760" y="148">runs</text></g>
              <g class="node audit"><circle cx="480" cy="368" r="66"/><text x="480" y="362">AUDIT</text><text class="sub" x="480" y="386">verifies</text></g>
              <g class="node ledger"><rect x="385" y="176" width="190" height="76" rx="16"/><text x="480" y="208">LEDGER</text><text class="sub" x="480" y="232">single truth</text></g>
            </g>
            {_edge_chip(480, 130, "models, by gate")}
            {_edge_chip(652, 287, "runs, by endpoint")}
            {_edge_chip(308, 287, "fitness, by ledger row")}
          </svg>
        </figure>

        <!-- 2. Pipeline: genome -> gate -> run -> rows -> ledger -->
        <figure class="flow reveal glass" style="animation-range: entry 10% cover 36%">
          <figcaption><span class="flow-n">B</span>The crossing
            <em>· drivers by endpoint, fitness by ledger row, nothing shared mutable</em></figcaption>
          <svg viewBox="0 0 1160 250" role="img" aria-label="Genome to SVI gate to mesh run to fitness rows to ledger">
            <g class="flow-edges" fill="none">
              <path class="edge pipe" d="M204,108 L244,108" marker-end="url(#arw-forge)"/>
              <path class="edge pipe" d="M434,108 L484,108" marker-end="url(#arw-forge)"/>
              <path class="edge pipe" d="M674,108 L724,108" marker-end="url(#arw-forge)"/>
              <path class="edge pipe" d="M914,108 L964,108" marker-end="url(#arw-forge)"/>
              <path class="edge back" d="M1100,176 L60,176" marker-end="url(#arw-audit)"/>
            </g>
            <g class="flow-nodes small">
              <g class="node forge"><rect x="30" y="64" width="170" height="88" rx="16"/><text x="115" y="100">GENOMES</text><text class="sub" x="115" y="126">forge</text></g>
              <g class="node audit"><rect x="250" y="64" width="180" height="88" rx="16"/><text x="340" y="100">SVI GATE</text><text class="sub" x="340" y="126">audit admits</text></g>
              <g class="node mesh"><rect x="490" y="64" width="180" height="88" rx="16"/><text x="580" y="100">MESH RUN</text><text class="sub" x="580" y="126">endpoint only</text></g>
              <g class="node mesh"><rect x="730" y="64" width="180" height="88" rx="16"/><text x="820" y="100">FITNESS</text><text class="sub" x="820" y="126">rows, not state</text></g>
              <g class="node audit"><rect x="970" y="64" width="160" height="88" rx="16"/><text x="1050" y="100">LEDGER</text><text class="sub" x="1050" y="126">single truth</text></g>
            </g>
            {_edge_chip(580, 212, "fitness enters the set only with ground-truth provenance")}
          </svg>
        </figure>

        <!-- 3. Gates admit in both directions -->
        <figure class="flow reveal glass" style="animation-range: entry 14% cover 40%">
          <figcaption><span class="flow-n">C</span>Two-way gates
            <em>· admission is symmetric; containment is the default</em></figcaption>
          <svg viewBox="0 0 900 290" role="img" aria-label="Models and tasks pass through gates in both directions">
            <g class="flow-edges" fill="none">
              <path class="edge g" d="M324,80 L576,80" marker-end="url(#arw-mesh)"/>
              <path class="edge g" d="M576,120 L324,120" marker-end="url(#arw-mesh)"/>
              <path class="edge g" d="M324,188 L576,188" marker-end="url(#arw-mesh)"/>
              <path class="edge g" d="M576,228 L324,228" marker-end="url(#arw-mesh)"/>
            </g>
            <g class="flow-nodes small">
              <g class="node forge"><rect x="110" y="52" width="210" height="56" rx="14"/><text x="215" y="88">champion models</text></g>
              <g class="node mesh"><rect x="110" y="160" width="210" height="56" rx="14"/><text x="215" y="196">mesh tasks</text></g>
              <g class="gate"><rect x="580" y="52" width="210" height="56" rx="14"/><text x="685" y="88">SVI gate</text></g>
              <g class="gate"><rect x="580" y="160" width="210" height="56" rx="14"/><text x="685" y="196">provenance gate</text></g>
            </g>
            {_edge_chip(450, 80, "admit")}
            {_edge_chip(450, 120, "reject")}
            {_edge_chip(450, 258, "localhost by default — beyond it, separately authorized")}
          </svg>
        </figure>
      </div>
"""


def _ledger_html() -> str:
    rows = [
        ("Article I", "Separation of powers — one role per member.", "handshake"),
        ("Article II", "Drivers cross by endpoint; fitness by ledger row.", "sparkles"),
        ("Article III", "Gates admit in both directions.", "clap"),
        ("Article IV", "Localhost containment by default.", "muscle"),
        ("Article V", "The ledger is the single shared truth.", "pray"),
        ("Disputes", "Resolve by measurement — N≥50, temp 0, seed logged.", "curious"),
    ]
    cells = "\n".join(
        f'<div><dt>{_emoji(e, 14)} {html.escape(k)}</dt><dd>{html.escape(v)}</dd></div>'
        for k, v, e in rows)
    return f'<dl class="ledger reveal">{cells}</dl>'


# --------------------------------------------------------------------------- #
# Render
# --------------------------------------------------------------------------- #

CSS_TEMPLATE = """
  :root {
    --ink: #05080e; --fg: {fg}; --muted: {muted}; --faint: {faint};
    --gold: {gold}; --accent: {accent};
    --forge: {forge}; --mesh: {mesh}; --audit: {audit};
    --panel-bg: {panel_bg}; --panel-edge: {panel_edge};
    --panel-blur: {panel_blur}; --panel-radius: {panel_radius};
    --chip: {chip};
    --cain-t: 0;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { background: {bg}; }
  body {
    font-family: {ui};
    color: var(--fg);
    background: {bg};
    background-attachment: fixed;
    overflow-x: hidden;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
  }

  /* ---------- layers ---------- */
  .aurora { position: fixed; inset: -20%; z-index: 0; pointer-events: none; }
  .blob { position: absolute; border-radius: 50%; opacity: {blob_op};
          filter: blur({blob_blur}); animation: drift 74s ease-in-out infinite; }
  .blob.a { width: 42vw; height: 42vw; left: 3vw;  top: 4vh;  background: var(--forge); }
  .blob.b { width: 40vw; height: 40vw; right: 1vw; top: 30vh; background: var(--mesh);
            animation-duration: 92s; animation-delay: -26s; }
  .blob.c { width: 38vw; height: 38vw; left: 28vw; bottom: 0;  background: var(--audit);
            animation-duration: 108s; animation-delay: -58s; }
  @keyframes drift {
    0%   { transform: translate3d(0,0,0) scale(1); }
    50%  { transform: translate3d(3vw,-4vh,0) scale(1.16); }
    100% { transform: translate3d(0,0,0) scale(1); }
  }
  .grid { position: fixed; inset: 0; z-index: 1; pointer-events: none; opacity: .30;
          background-image: linear-gradient({grid} 1px, transparent 1px),
                            linear-gradient(90deg, {grid} 1px, transparent 1px);
          background-size: {grid_size} {grid_size}; }
  .vignette { position: fixed; inset: 0; z-index: 2; pointer-events: none;
              background: radial-gradient(120% 80% at 50% 30%, transparent 42%, rgba(2,4,8,.86) 100%); }
  {scanlines}

  /* ---------- progress ---------- */
  .progress { position: fixed; top: 0; left: 0; height: 2px; width: 100%; z-index: 40;
              background: linear-gradient(90deg, var(--forge), var(--mesh), var(--accent));
              transform-origin: 0 50%; transform: scaleX(0);
              animation: fill linear both; animation-timeline: scroll(root); }
  @keyframes fill { from { transform: scaleX(0); } to { transform: scaleX(1); } }

  /* ---------- reveal (scroll-driven -> deterministic capture) ---------- */
  .reveal { animation: rise linear both; animation-timeline: view();
            animation-range: entry 8% cover 34%; }
  @keyframes rise {
    from { opacity: 0; transform: translate3d(0,32px,0); filter: blur(7px); }
    to   { opacity: 1; transform: translate3d(0,0,0); filter: blur(0); }
  }
  html.no-sda .reveal { animation: none; opacity: 1; transform: none; filter: none; }

  /* ---------- emotional emoji (names from emoji_maker.py) ---------- */
  .em { display: inline-block; line-height: 1; animation-duration: 2.6s;
        animation-iteration-count: infinite; animation-timing-function: ease-in-out; }
{emoji_keyframes}

  /* ---------- shell ---------- */
  .page { position: relative; z-index: 3; max-width: 1320px; margin: 0 auto;
          padding: 0 clamp(28px, 6vw, 96px); }
  .eyebrow { font-size: 13px; letter-spacing: .42em; text-transform: uppercase;
             color: var(--gold); }
  .glass { background: var(--panel-bg); border: 1px solid var(--panel-edge);
           border-radius: var(--panel-radius);
           backdrop-filter: blur(var(--panel-blur)) saturate(150%);
           -webkit-backdrop-filter: blur(var(--panel-blur)) saturate(150%);
           box-shadow: 0 24px 64px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.07); }

  /* ---------- hero ---------- */
  .hero { min-height: 100vh; display: flex; flex-direction: column; align-items: center;
          justify-content: center; text-align: center; gap: 28px; padding: 16vh 0 12vh; }
  .seal { width: clamp(170px, 19vw, 250px); height: clamp(170px, 19vw, 250px);
          animation: spin 240s linear infinite; }
  .seal .ring { fill: none; stroke-width: 1.4; }
  .seal .r1 { stroke: var(--forge); } .seal .r2 { stroke: var(--mesh); } .seal .r3 { stroke: var(--audit); }
  .seal .mono { fill: var(--accent); font-family: {display}; font-size: 42px; letter-spacing: 2px; }
  .seal-count { animation: gentlePulse 9s ease-in-out infinite; }
  .title { font-family: {display}; font-weight: 400; line-height: .95;
           font-size: clamp(54px, 9vw, 148px); letter-spacing: -.015em;
           background: {title_grad}; -webkit-background-clip: text; background-clip: text;
           color: transparent; }
  .named { display: flex; align-items: center; gap: 20px; width: 100%; max-width: 780px; }
  .named .rule { flex: 1; height: 1px;
                 background: linear-gradient(90deg, transparent, var(--gold), transparent); }
  .named span { font-size: 13px; letter-spacing: .3em; text-transform: uppercase;
                color: var(--gold); white-space: nowrap; }
  .tagline { font-family: {display}; font-size: clamp(20px, 2.4vw, 33px); line-height: 1.5;
             color: var(--muted); max-width: 24ch; }
  .cue { margin-top: 3vh; display: flex; flex-direction: column; align-items: center; gap: 10px;
         font-size: 11px; letter-spacing: .34em; text-transform: uppercase; color: var(--faint); }
  .cue i { display: block; width: 1px; height: 52px;
           background: linear-gradient(180deg, var(--gold), transparent);
           animation: cue 3.4s ease-in-out infinite; }
  @keyframes cue { 0%,100% { transform: scaleY(.4); opacity: .3; } 50% { transform: scaleY(1); opacity: .9; } }

  /* ---------- sections ---------- */
  section { padding: calc(12vh * {gap_scale}) 0; }
  .sec-head { display: flex; align-items: baseline; gap: 22px; margin-bottom: 5.5vh; }
  .sec-head .num { font-family: {display}; font-size: 15px; color: var(--gold); letter-spacing: .2em; }
  .sec-head h2 { font-family: {display}; font-weight: 400;
                 font-size: clamp(32px, 4.4vw, 66px); letter-spacing: -.01em; }
  .sec-head .line { flex: 1; height: 1px;
                    background: linear-gradient(90deg, var(--gold), transparent); opacity: .55; }

  /* ---------- powers ---------- */
  .powers { display: grid; grid-template-columns: repeat(3, 1fr); gap: 26px; }
  @media (max-width: 1000px) { .powers { grid-template-columns: 1fr; } }
  .power { position: relative; padding: 34px 30px 30px; overflow: hidden;
           background: var(--panel-bg); border: 1px solid var(--panel-edge);
           border-radius: var(--panel-radius);
           backdrop-filter: blur(var(--panel-blur)) saturate(150%);
           -webkit-backdrop-filter: blur(var(--panel-blur)) saturate(150%);
           box-shadow: 0 24px 64px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.07); }
  .power::before { content: ""; position: absolute; inset: 0 0 auto 0; height: 2px; }
  .power.forge::before { background: linear-gradient(90deg, transparent, var(--forge), transparent); }
  .power.mesh::before  { background: linear-gradient(90deg, transparent, var(--mesh), transparent); }
  .power.audit::before { background: linear-gradient(90deg, transparent, var(--audit), transparent); }
  .power-top { display: flex; align-items: center; justify-content: space-between; }
  .power.forge .em { color: var(--forge); } .power.mesh .em { color: var(--mesh); }
  .power.audit .em { color: var(--audit); }
  .power-verb { font-size: 12px; letter-spacing: .38em; text-transform: uppercase; color: var(--faint); }
  .power-name { font-family: {display}; font-weight: 400; font-size: 26px; margin: 20px 0 14px; }
  .power-desc { font-size: 15.5px; line-height: 1.72; color: var(--muted); min-height: 6.4em; }
  .power-scope { display: inline-block; margin-top: 20px; padding: 5px 12px; border-radius: 999px;
                 font-size: 11.5px; letter-spacing: .16em; text-transform: uppercase;
                 color: var(--faint); border: 1px solid var(--panel-edge); }

  .separation { margin-top: 40px; padding: 30px 34px; font-family: {display};
                font-size: clamp(18px, 2vw, 26px); line-height: 1.5; color: var(--muted);
                background: var(--panel-bg); border: 1px solid var(--panel-edge);
                border-radius: var(--panel-radius); }
  .separation b { color: var(--accent); font-weight: 400; }

  /* ---------- flow charts — CAIN node language: glowing nodes, role-coloured
     arrowheads, opaque label plates. Every animation here is time-based, so
     CAINClock.seek() pins it and frame N stays deterministic. ---------- */
  .flows { display: flex; flex-direction: column; gap: 34px; }
  .flow { padding: 30px 32px 20px; }
  .flow figcaption { font-family: {display}; font-size: 19px; color: var(--muted);
                     display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
  .flow-n { display: inline-grid; place-items: center; width: 26px; height: 26px; border-radius: 50%;
            border: 1px solid var(--gold); color: var(--gold); font-size: 13px; }
  .flow figcaption em { color: var(--faint); font-size: 15px; }
  .flow svg { width: 100%; height: auto; display: block; color: var(--muted); }
  .flow text { fill: {fg}; font-family: {display}; font-size: 22px; text-anchor: middle; }
  .flow text.sub { font-size: 16px; fill: var(--faint); letter-spacing: .06em; }

  /* nodes carry the role colour and pulse with CAIN's nodeGlow */
  .flow .node { animation: nodeGlow 3s infinite; color: var(--gold); }
  .flow .node.forge { color: var(--forge); }
  .flow .node.mesh { color: var(--mesh); }
  .flow .node.audit { color: var(--audit); }
  .flow .node.ledger { color: var(--gold); }
  .flow .node circle, .flow .node rect { fill: var(--panel-bg); stroke: currentColor; stroke-width: 2.4; }
  .flow .gate { animation: nodeGlow 3s infinite; color: var(--gold); }
  .flow .gate rect { fill: var(--panel-bg); stroke: currentColor; stroke-width: 2.4; stroke-dasharray: 7 6; }

  /* label plates ride on the edges — no line/text collisions at any width */
  .flow .chip { fill: var(--chip); stroke: var(--panel-edge); stroke-width: 1; }
  .flow .elabel text { font-family: {ui}; font-size: 13px; fill: var(--faint);
                       letter-spacing: .14em; text-transform: uppercase; text-anchor: middle; }

  /* one marker per role: a marker resolves currentColor from its own <defs>,
     not from the path referencing it, which is why the old single shared
     currentColor marker rendered every arrowhead muted cream */
  .flow .mk-forge { fill: var(--forge); }
  .flow .mk-mesh { fill: var(--mesh); }
  .flow .mk-audit { fill: var(--audit); }
  .flow .mk-gold { fill: var(--gold); }

  .flow .edge { stroke-width: 2.6; stroke-dasharray: 11 8; animation: march 3.6s linear infinite; }
  .flow .edge.e1, .flow .edge.pipe { stroke: var(--forge); }
  .flow .edge.e2, .flow .edge.g { stroke: var(--mesh); }
  .flow .edge.spoke { stroke: var(--gold); stroke-dasharray: 5 7; animation-duration: 5.2s; }
  .flow .edge.e3, .flow .edge.back { stroke: var(--audit); }
  .flow .edge.back { animation-direction: reverse; }
  @keyframes march { from { stroke-dashoffset: 64; } to { stroke-dashoffset: 0; } }
  @keyframes nodeGlow {
    0%, 100% { filter: drop-shadow(0 0 2px currentColor); }
    50% { filter: drop-shadow(0 0 11px currentColor); }
  }

  /* ---------- covenant ---------- */
  .covenant { list-style: none; }
  .article { display: grid; grid-template-columns: 92px 40px 1fr; gap: 20px; align-items: start;
             padding: 32px 0; border-top: 1px solid var(--panel-edge); }
  .article:last-child { border-bottom: 1px solid var(--panel-edge); }
  .article-n { font-family: {display}; font-size: 28px; color: var(--gold); letter-spacing: .08em; }
  .article-body { font-size: 17.5px; line-height: 1.78; color: var(--muted); }

  /* ---------- ledger ---------- */
  .ledger { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; margin-top: 38px;
            border: 1px solid var(--panel-edge); border-radius: var(--panel-radius); overflow: hidden;
            background: var(--panel-edge); }
  .ledger div { background: var(--panel-bg); padding: 20px 22px;
                backdrop-filter: blur(var(--panel-blur)); }
  .ledger dt { font-size: 11px; letter-spacing: .26em; text-transform: uppercase; color: var(--gold); }
  .ledger dd { margin-top: 9px; font-size: 15px; line-height: 1.6; color: var(--muted); }

  /* ---------- non-goals + footer ---------- */
  .non-goals { text-align: center; padding: 13vh 0 15vh; }
  .non-goals blockquote { font-family: {display}; font-style: italic;
                          font-size: clamp(26px, 3.5vw, 52px); line-height: 1.36;
                          max-width: 24ch; margin: 24px auto 0; }
  .non-goals blockquote em { color: var(--accent); }
  footer { padding: 0 0 12vh; text-align: center; }
  .mono-mark { width: 72px; height: 72px; margin: 0 auto 20px; border-radius: 50%;
               border: 1px solid var(--gold); display: grid; place-items: center;
               font-family: {display}; font-size: 23px; color: var(--accent); }
  .footer-line { font-size: 12px; letter-spacing: .28em; text-transform: uppercase; color: var(--faint); }

  /* ---------- persona figures (Pebbles & Bam-Bam) ---------- */
  .hero-crowd { display: flex; align-items: flex-end; justify-content: center;
                gap: clamp(14px, 3.4vw, 64px); width: 100%; }
  .hero-crowd .persona-art { width: clamp(92px, 11vw, 172px); height: auto; }
  .persona-art { display: block; height: auto;
                 filter: drop-shadow(0 16px 24px rgba(0,0,0,.45)); }
  .persona-art.pebbles { animation: floaty 4.4s ease-in-out infinite; }
  .persona-art.bambam { animation: sway 5.6s ease-in-out infinite;
                        transform-origin: 50% 100%; }
  @keyframes floaty { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-7px); } }
  @keyframes sway { 0%,100% { transform: rotate(-2deg); } 50% { transform: rotate(2deg); } }
  .personas { display: grid; grid-template-columns: repeat(2, 1fr); gap: 26px; }
  @media (max-width: 1000px) { .personas { grid-template-columns: 1fr; } }
  .persona { display: grid; grid-template-columns: minmax(150px, 32%) 1fr; gap: 26px;
             align-items: center; padding: 30px 30px 28px; }
  @media (max-width: 640px) { .persona { grid-template-columns: 1fr; } }
  .persona-figure { display: flex; justify-content: center; }
  .persona-figure .persona-art { width: min(100%, 250px); }
  .persona-name { font-family: {display}; font-weight: 400; font-size: 30px; letter-spacing: .03em; }
  .persona.pebbles-card .persona-name { color: var(--accent); }
  .persona.bambam-card .persona-name { color: var(--forge); }
  .persona-tag { display: inline-block; margin-top: 10px; padding: 5px 12px; border-radius: 999px;
                 font-size: 11.5px; letter-spacing: .16em; text-transform: uppercase;
                 color: var(--faint); border: 1px solid var(--panel-edge); }
  .persona-desc { margin-top: 14px; font-size: 15.5px; line-height: 1.72; color: var(--muted); }

  {extra}
"""


SCANLINES_CSS = (
    ".scan{position:fixed;inset:0;z-index:2;pointer-events:none;opacity:.5;"
    "background:repeating-linear-gradient(180deg,rgba(0,0,0,.28) 0 1px,transparent 1px 3px);}"
)


def _css(theme: dict) -> str:
    """Fill CSS_TEMPLATE's `{token}` placeholders.

    Deliberately NOT `str.format`: the template is CSS, and CSS braces would be
    read as format fields. A plain token replace leaves every literal brace
    alone, and the assertion below makes a typo'd placeholder loud instead of
    silently shipping `{panel_blur}` into the page.
    """
    values = dict(theme)
    values["emoji_keyframes"] = _keyframes_css()
    values["scanlines"] = SCANLINES_CSS if theme["scanlines"] else ""
    css = CSS_TEMPLATE
    for key, value in values.items():
        css = css.replace("{" + key + "}", str(value))
    leftovers = [k for k in values if ("{" + k + "}") in css]
    if leftovers:
        raise ValueError(f"unfilled CSS placeholder(s): {leftovers}")
    return css


def render(data: dict, theme: dict, personas: dict) -> str:
    title = html.escape(data["title"])
    named = html.escape(data["named"])
    tagline = html.escape(data["tagline"])
    non_goals = html.escape(data["non_goals"])
    count = len(data["covenant"])

    css = _css(theme)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="theme" content="{theme["label"]}">
<title>{title} — {theme["label"]}</title>
<style>{css}</style>
</head>
<body>
  <div class="aurora" aria-hidden="true"><div class="blob a"></div><div class="blob b"></div><div class="blob c"></div></div>
  <div class="grid" aria-hidden="true"></div>
  {'<div class="scan" aria-hidden="true"></div>' if theme["scanlines"] else ''}
  <div class="vignette" aria-hidden="true"></div>
  <div class="progress" aria-hidden="true"></div>

  <main class="page">
    <header class="hero">
      <div class="eyebrow">Union Covenant · {html.escape(theme["label"])}</div>
      <div class="hero-crowd">
        {_pebbles_svg("h")}
        <svg class="seal" viewBox="0 0 200 200" aria-hidden="true">
          <circle class="ring r1" cx="100" cy="68" r="46"/>
          <circle class="ring r2" cx="66" cy="126" r="46"/>
          <circle class="ring r3" cx="134" cy="126" r="46"/>
          <text class="mono seal-count" x="100" y="108" text-anchor="middle">III</text>
        </svg>
        {_bambam_svg("h")}
      </div>
      <h1 class="title">{title}</h1>
      <div class="named"><span class="rule"></span><span>Named {named}</span><span class="rule"></span></div>
      <p class="tagline">{tagline}</p>
      <div class="cue"><i></i><span>Scroll</span></div>
    </header>

    <section>
      <div class="sec-head reveal"><span class="num">01</span><h2>Members</h2><span class="line"></span></div>
      <div class="powers">{_powers_html(data["members"])}
      </div>
      <p class="separation reveal">Separation of powers: <b>forge builds, mesh executes, audit verifies.</b>
        No member absorbs another's role.</p>
    </section>

    <section>
      <div class="sec-head reveal"><span class="num">02</span><h2>Dispatch</h2><span class="line"></span></div>
      {_personas_html(personas)}
    </section>

    <section>
      <div class="sec-head reveal"><span class="num">03</span><h2>How it flows</h2><span class="line"></span></div>
      {_flow_html()}
    </section>

    <section>
      <div class="sec-head reveal"><span class="num">04</span><h2>The Covenant</h2><span class="line"></span></div>
      <ol class="covenant">{_covenant_html(data["covenant"])}
      </ol>
      {_ledger_html()}
    </section>

    <section class="non-goals">
      <div class="eyebrow">Non-goals</div>
      <blockquote class="reveal">{non_goals}</blockquote>
    </section>

    <footer>
      <div class="mono-mark">III</div>
      <div class="footer-line">The ledger is the single shared truth · {count} articles · {named}</div>
    </footer>
  </main>

  <script>
  (function () {{
    if (!window.CSS || !CSS.supports || !CSS.supports('animation-timeline', 'view()')) {{
      document.documentElement.classList.add('no-sda');
    }}
  }})();
  {SCENE_CLOCK_JS}
  </script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--compact", default=str(DEFAULT_COMPACT))
    ap.add_argument("--theme", choices=THEME_ORDER, help="render one theme")
    ap.add_argument("--all", action="store_true", help="render every theme")
    ap.add_argument("--list", action="store_true", help="list themes and exit")
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    args = ap.parse_args()

    if args.list:
        for k in THEME_ORDER:
            print(f"  {k:10} {THEMES[k]['label']:18} {THEMES[k]['blurb']}")
        return 0

    src = Path(args.compact)
    if not src.exists():
        print(f"compact not found: {src}")
        return 1
    data = parse_compact(src.read_text(encoding="utf-8"))
    if not data["covenant"]:
        print("parsed 0 covenant articles — refusing to render a partial covenant")
        return 1

    if not DEFAULT_PERSONAS.exists():
        print(f"persona spec not found: {DEFAULT_PERSONAS}")
        return 1
    personas = parse_personas(DEFAULT_PERSONAS.read_text(encoding="utf-8"))
    if "pebbles" not in personas or "bambam" not in personas:
        print("parsed 0 personas from PEBBLES_BAMBAM.md — refusing to render without them")
        return 1

    themes = THEME_ORDER if (args.all or not args.theme) else [args.theme]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"{data['title']} ({data['named']}) — {len(data['members'])} members, "
          f"{len(data['covenant'])} articles")
    for key in themes:
        path = out_dir / f"oxford_compact__{key}.html"
        path.write_text(render(data, THEMES[key], personas), encoding="utf-8")
        print(f"  {key:10} -> {path.name}  ({len(path.read_text(encoding='utf-8')) // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
