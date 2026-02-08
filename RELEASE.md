# Release Proposal: v2.0.3

**Previous release:** 2.0.2
**Proposed release:** 2.0.3 (patch)
**Commits since last tag:** 8

## Release Type Rationale

Patch release — all changes are bug fixes, type hint additions, and packaging
improvements. No new features or breaking API changes.

## What's Changed

### Bug Fixes
- **Improved task name wrapping in reports** — long task names now wrap at word
  boundaries with proper indentation (72-char hard limit with multi-line support)
- **Improved task handling and reliability** — `Task.cancel()` returns empty
  string instead of `None`; `Task.start()` returns `bool`; null-safety added to
  `start_task_handler`

### Packaging & Maintenance
- **Snap: migrated base from core20 to core24** — core20 (Ubuntu 20.04) reached
  end of standard support; core24 (Ubuntu 24.04) is supported until April 2029
  and ships Python 3.12 natively, eliminating several build workarounds
- **Snap: version bumped to 2.0.2** to match PyPI release
- **Type hints added** to `handlers.py` (`Tuple` return types) and `tasks.py`
  (`Optional` return type on `Task.get_running()`)
- Updated `.gitignore` to exclude `build/`, `dist/`, and egg-info directories
- Makefile test target now includes coverage reporting (`--cov=src`)
- Added `pytest-cov` to `requirements.txt`

## Changed Files
- `.gitignore` — added build artifacts
- `Makefile` — coverage flag
- `requirements.txt` — added pytest-cov
- `snap/snapcraft.yaml` — core24 migration, version bump, simplified build
- `src/app.py` — task name wrapping logic
- `src/handlers.py` — type hints, null-safety
- `src/tasks.py` — type hints, return type fixes
- `src/tests/test_base.py` — updated to match new Task API

**Full Changelog**: https://github.com/clobrano/letsdo/compare/2.0.2...2.0.3
