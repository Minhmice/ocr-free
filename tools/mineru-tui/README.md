# mineru-tui

Textual TUI: scan an input folder, run **`mineru`** as subprocesses, persist queue state under **`<output>/.mineru-tui/queue.json`** (migrates legacy `<output>/queue_state.json` once).

```bash
pip install -e ./tools/mineru-tui
mineru-tui --help
```

Dependencies: **textual**, **psutil**, **pypdf** (for PDF page hints and `-e` calculation).

See the **repository root `README.md`** for Windows install notes, Docker, and one-liner launch scripts (`scripts/run-mineru-tui.ps1` / `.sh`).
