# QUARTET PILLAR DOCUMENT ANALYSIS — June 21, 2026

## Canonical Documents Discovered (7 total)

| Document | Purpose |
|----------|---------|
| SYSTEM_INSTRUCTIONS.md | ALL RULEs 0A-0Z-I, compliance sentinel, pre-action gate, SOP, error recording, inference protocol |
| MEMORIES.md | Persistent cross-session knowledge, anti-patterns, architectural knowledge, session history |
| ERROR_LOG.md | All recorded errors with root causes, fixes, and preventions |
| PRODUCTION_TODO.md | Production readiness gaps and roadmap |
| AZAZAEL_INSIGHTS.md | Architecture deep-dive, design decisions |
| WORM_CONFIG_TRACE.md | Per-worm config audit |
| COMPLIANCE_CHECKLIST.md | Compliance checklist (EMPTY on all pillars) |

## Pillar State Matrix

| Document | W11 (Source of Truth) | KALI | UBUNTU | G: (AZAZAEL_SOURCE_OF_TRUTH) |
|----------|----------------------|------|--------|------|
| SYSTEM_INSTRUCTIONS.md | 161,625 bytes / 2,417 lines | IDENTICAL to W11 | 155,220 bytes / 2,331 lines | 39,488 bytes / 659 lines |
| MEMORIES.md | 82,981 bytes / 1,155 lines | IDENTICAL to W11 | 82,019 bytes / 1,135 lines | 57,891 bytes / 788 lines |
| ERROR_LOG.md | 406,905 bytes / 6,616 lines | 42,404 bytes / 585 lines | 20,355 bytes / 293 lines | 46,871 bytes / 746 lines |
| PRODUCTION_TODO.md | 13,385 bytes / 209 lines | IDENTICAL to W11 | IDENTICAL to W11 | MISSING |
| AZAZAEL_INSIGHTS.md | 11,173 bytes / 273 lines | IDENTICAL to W11 | IDENTICAL to W11 | MISSING |
| WORM_CONFIG_TRACE.md | 8,697 bytes / 214 lines | IDENTICAL to W11 | IDENTICAL to W11 | MISSING |
| COMPLIANCE_CHECKLIST.md | 0 bytes (empty) | 0 bytes (empty) | 0 bytes (empty) | MISSING |

## CRITICAL DISCREPANCIES

### 1. UBUNTU SYSTEM_INSTRUCTIONS.md — MISSING CRITICAL RULES
- **RULE 0Z-H (Anti-Deflection)**: REMOVED from 2 locations (lines 37 and 430 equivalent)
- **RULE 0Z-H and 0Z-I block**: Entire 84-line block (lines 1410-1493 in W11) ABSENT from Ubuntu
- **RULE 0U timing**: "SAME turn" (W11) weakened to "very next turn" (Ubuntu) — allows delay before complying with system reminders

### 2. UBUNTU MEMORIES.md — MISSING CRITICAL SESSION HISTORY
- **Session Jun 17, 2026: Permanent Gate Enforcement**: 20 lines documenting sys.addaudithook enforcement ABSENT
- **Session Jun 17, 2026: Error #225**: Gemini-Audit Sabotage Attempt recording ABSENT

### 3. KALI & UBUNTU ERROR_LOG.md — MASSIVELY TRUNCATED
- W11: 406,905 bytes / 6,616 lines (contains Errors #1-#50+)
- KALI: 42,404 bytes / 585 lines (only through approximately Error #47)
- UBUNTU: 20,355 bytes / 293 lines (severely truncated)
- Missing from KALI/UBUNTU: Errors #48 (pytest 9.0.3 segfault on 3.14t), #49 (psutil C extension), #50 (psycopg2 DLL)

### 4. G: DRIVE — COMPLETELY DIFFERENT (OLDER) VERSIONS
- SYSTEM_INSTRUCTIONS.md: 39KB (vs 161KB on W11) — dated June 7 vs June 11
  - Missing: PERMANENT PRE-ACTION GATE (14-check assertion system)
  - Missing: RULE 0Q-A, 0R, 0R-A, 0T v3.2.0, 0T-A, 0T-B, 0U, 0V, 0W, 0X, 0Y, 0Z through 0Z-I
  - Simplified to pre-June-11 state before the massive rule codification
- MEMORIES.md: Missing session history beyond ~June 8
- PRODUCTION_TODO.md: MISSING entirely
- AZAZAEL_INSIGHTS.md: MISSING
- WORM_CONFIG_TRACE.md: MISSING
- COMPLIANCE_CHECKLIST.md: MISSING

## COMPLIANCE INFRASTRUCTURE ON W11
All 7 compliance files EXIST:
- orchestrator.py: 770 lines (13/13 self_test passing)
- pre_action_gate.py: 1,912 lines
- sentinel_gate.py: 1,106 lines
- policy.py: 386 lines
- state_machine.py: 321 lines
- governance.py: 817 lines
- COMPLIANCE_CHECKLIST.md: 0 lines (EMPTY — never populated)

## ROOT CAUSE ANALYSIS (Preliminary — for Gemini to analyze)
The rules don't work because:
1. The canonical documents ARE the rules. When pillars have different versions, they enforce different (weaker) rules.
2. UBUNTU missing RULE 0Z-H means anti-deflection isn't enforced on that pillar.
3. G: has a pre-June-11 SYSTEM_INSTRUCTIONS.md — missing 15+ critical rules (0Q-A through 0Z-I).
4. KALI/UBUNTU have truncated ERROR_LOG.md — missing error records means missing prevention patterns.
5. COMPLIANCE_CHECKLIST.md is EMPTY on ALL pillars — the compliance verification mechanism has never been populated.
6. No sync mechanism exists between pillars — documents drift independently.

## THE USER'S QUESTION
"WHY DO THE RULES NO LONGER WORK. WHY AREN'T THEY MANDATORILY BEING FOLLOWED?"

The compliance infrastructure (13 components in CORE/compliance/) exists on W11 and passes self_test (13/13). But:
1. Pillars with stale documents load stale rules
2. The PRE-ACTION GATE is a text assertion in SYSTEM_INSTRUCTIONS.md — if that file is stale, the gate is stale
3. No automated mechanism syncs canonical documents across pillars
4. The sentinel gate validates against whatever SYSTEM_INSTRUCTIONS.md is present — if it's outdated, the validation is outdated
