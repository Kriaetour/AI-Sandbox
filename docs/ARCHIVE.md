# Archive & Legacy Notes

This file records removed or deprecated components that previously existed in the AI Sandbox repository. It serves as a lightweight historical reference so future contributors understand why certain files disappeared and what replaced them.

## Removed Files

### `main_old.py` (Removed)
- **Status:** Deleted (superseded by `main.py`).
- **Reason:** Legacy standalone entry point retained outdated control flow and an obsolete dialogue invocation pattern that could cause runtime errors if accidentally executed.
- **Replacement:** Unified CLI + interactive menu in `main.py` (subcommands: `core`, `territory`, `social`, `tribal`, `combined`, `menu`). Running `python main.py` with no arguments now launches the interactive menu by default.
- **Key Improvements in Replacement:**
  - Single authoritative entry surface (reduces drift & duplication).
  - Consistent `--ticks` flag usage across modes (positional removed for core).
  - Integrated logging level selection and future-proof command expansion.

## Deprecation Notices (Active)
- Direct execution of `core_sim.py` prints a deprecation notice instructing use of `python main.py core --ticks <n>`.

## Future Archival Guidance
When removing additional legacy modules, append a concise section here including:
- File/module name
- Date & reason for removal
- Replacement path (if any)
- Any migration notes (API changes, flags, behavior differences)

Keeping this file brief avoids it becoming a secondary changelog; focus on intent and replacement clarity.

---
_Last updated: 2025-09-14_
