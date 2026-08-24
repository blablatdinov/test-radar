# One view per file in gui/views/

Each Django view class lives in its own file under `gui/views/` rather than being grouped in a single `views.py`. This decision was made because the project has 11 views, and a single file would exceed 500 lines. One-view-per-file keeps each file focused, simplifies navigation, and makes code review diffs smaller and more targeted. The `__init__.py` re-exports all views so URL configuration imports remain unchanged.
