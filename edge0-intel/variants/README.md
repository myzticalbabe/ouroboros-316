# The Oxford Compact — scroll-video variants (2026-09-24)

Five renderings of `../COMPACT.md` for comparison, plus two rendered videos.
Everything is generated from the document — no content is transcribed — and the
emoji come from the mesh repo's own emotional-emoji vocabulary
(`azazael/src/CODEX/CORE/emoji_maker.py`), carrying the same `css_class` and
`animation` name, so the page cannot drift from either source.

## The five themes

| theme | name | look | motion |
|-------|------|------|--------|
| `oxford` | Oxford Heritage | ink + gold, editorial serif, restrained frost | slow aurora, gold hairlines |
| `prism` | Prism Glass | **maximal glassmorphism**, vivid gradient mesh, heavy frost | drifting colour field |
| `aurora` | Aurora Telemetry | deep-space neon, hairline instrumentation, telemetry labels | march-dash flow edges |
| `parchment` | Parchment Light | warm paper, dark ink, light-theme frost | print-like, quiet |
| `carbon` | Carbon Terminal | monospace, scanlines, colour only as signal | exact, minimal |

All five carry the same structure: hero + seal **flanked by the two persona
figures**, **3 power cards**, a **Dispatch** band (PEBBLES & BAM-BAM — captions
parsed from `../PEBBLES_BAMBAM.md`, never transcribed), **3 flow charts** (A
separation-of-powers loop closing on the ledger, B the crossing pipeline, C
two-way gates), the 5 covenant articles, a ledger strip, and the non-goals
pull-quote. Each theme emits every animation name it references — 15 names,
all with real `@keyframes`.

The figures are original shaded vector illustrations drawn inside the
generator — red topknot + white bone + leopard-print tunic for PEBBLES;
white tuft, leopard-print loincloth, bone chest strap and club for BAM-BAM —
not WB artwork, and self-contained (no network, no image files). The flow
charts borrow CAIN's node language: `nodeGlow` on every node, one
role-coloured `<marker>` per edge (a marker resolves `currentColor` from its
own `<defs>`, never from the path referencing it — the old single shared
marker rendered every arrowhead muted cream), and opaque label plates so no
caption ever sits on a dash.

## Artifacts

```
variants/oxford_compact__<theme>.html   the 5 pages (self-contained, 57 KB)
variants/sheets/sheet_<theme>.png       2x2 contact sheet, 4 scroll positions
variants/stills/<page>/1..4.png         the individual 1920x1080 stills
video/oxford_compact__oxford.mp4        heritage theme, HEVC 1080p, 44.0 s
video/oxford_compact__prism.mp4         glass theme,    HEVC 1080p, 44.0 s
```

## Commands

```bash
python scripts/make_oxford_compact.py --all          # regenerate the 5 pages
python scripts/make_oxford_compact.py --list         # themes and blurbs
node   scripts/validate_page.js --html variants/oxford_compact__prism.html
node   scripts/scroll_video.js --html variants/oxford_compact__prism.html --stills 4
node   scripts/scroll_video.js --html variants/oxford_compact__prism.html \
       --out video/oxford_compact__prism.mp4 --fps 30 --px-per-sec 140 --codec hevc
```

## The capture contract

`scroll_video.js` does not screen-record. It chooses every frame:
`window.scrollTo(y)` from a schedule, `CAINClock.seek(t)` for the ambience, two
animation frames so the compositor flushes, one screenshot. Speed is fixed in
px/second (260 for stills, 140 for the videos), so duration adapts to the
document and every theme reads at one pace. Four rules make that exact:

1. **Reveals must be scroll-driven.** `animation-timeline: view()` is a pure
   function of scroll offset. An `IntersectionObserver` reveal fires in a task
   that a single-frame scroll jump never waits for, so it captures as blank.
2. **The clock must not touch scroll-driven animations.** `seek()` pauses and
   sets `currentTime`, which is meaningless for a timeline that reads scroll —
   and pins every `.reveal` at its `from` keyframe (opacity 0). `CAINClock`
   therefore classifies each animation (`ScrollTimeline` / `.source`) and seeks
   only the time-based ones. 22 scroll-driven, 52 timed on the prism page.
3. **Viewport-only screenshots, and no clip.** Puppeteer 19 defaults to
   `captureBeyondViewport: true`, which returns the whole document (1920x5847 —
   not a scrolled view, and an odd height libx265 rejects). Setting it `false`
   is required; adding a `clip` on top captures an empty region.
4. **Color tags ride on the frames, not the `-color_*` output options.** A
   measured probe of Chrome's JPEG encoder (known solid colors → raw YUV vs
   matrix predictions) shows **full-range BT.601: zero error, BT.709 off by 119
   levels** (red Y 76 vs 54). So the encode sets frame properties with
   `-vf setparams=range=pc:color_primaries=bt709:color_trc=bt709:colorspace=bt470bg`
   — libx265 reads those, while `-color_primaries`/`-color_trc` are silently
   dropped (context fields the frames override) and ship `unknown/unknown`.
   The matrix stays `bt470bg` deliberately: retagging BT.601 data as BT.709
   would *shift* the color it claims to preserve. Published files probe as
   `pc / bt470bg / bt709 / bt709`. To re-tag an already-encoded file without
   touching a frame:
   `ffmpeg -i in.mp4 -c copy -bsf:v hevc_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=5:video_full_range_flag=1 -movflags +faststart out.mp4`
   (the bsf takes numeric table E-3/E-4/E-5 values, not names like `colorprim=bt709`).

## Two failures that look like success

Both were hit and are now guarded — recorded here because neither announces itself:

- **A blank capture still produces a correct-length video.** Rules 2 and 3
  above each yield frames that are byte-identical, so ffmpeg happily writes a
  44-second, 1080p, 0.3 MB "video" that plays as a still gradient. `scroll_video.js`
  now samples five frames across the run and refuses to encode if they are all
  identical; a healthy run reports `5/5 sampled frames distinct` (≈4.3 MB).
- **A structurally fine page can render invisible content.** `validate_page.js`
  checks counts, overflow and `@keyframes` coverage, then *scrolls to 45%* and
  asserts the reveals in view are actually opaque. Without that last check the
  page passed every structural test while capturing as empty.

## Note on separation

`make_oxford_compact.py` carries its scene clock inline rather than importing
the mesh's. The canonical implementation is
`azazael/src/CODEX/CORE/scene_clock.py`; the Compact's own Article I keeps the
powers separate, so the forge does not import the mesh at render time. The two
share the same API by construction.
