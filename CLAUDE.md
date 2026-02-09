# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GitHub Codespaces starter project with three independent tracks:
- **Data analysis/visualization**: Jupyter notebooks using pandas and matplotlib (`notebooks/`)
- **Machine learning**: CIFAR-10 image classification with PyTorch (`notebooks/image-classifier.ipynb`)
- **Desktop GUI app**: Tic Tac Toe with unbeatable AI using PySide6 (`tictactoe/`)

## Commands

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Run the Tic Tac Toe GUI app
python tictactoe/main.py

# Run Jupyter notebooks
jupyter notebook notebooks/
```

No test framework, linter, or build system is configured.

## Architecture

The three tracks are fully independent with no shared code between them. Each is self-contained:

- `data/atlantis.csv` — sample population dataset used by `notebooks/population.ipynb`
- `notebooks/` — Jupyter notebooks (population analysis, matplotlib examples, PyTorch image classifier)
- `tictactoe/` — PySide6 desktop app
  - `main.py` — game logic (pure functions: `check_winner`, `find_best_move`, `minimax`) is separated from the UI (`TicTacToeWindow` class)
  - `styles.qss` — QSS stylesheet loaded at runtime via `Path(__file__).parent` for dark theme styling

**Tic Tac Toe AI**: Uses minimax with alpha-beta pruning and depth-based scoring (prefers quick wins via `10 - depth`). AI moves are delayed 250ms for UX. The app detects headless environments and falls back to `QT_QPA_PLATFORM=offscreen`.

**QSS note**: Qt Style Sheets are a limited subset of CSS. They do NOT support `transform`, `box-shadow`, CSS class selectors (`.foo`), or most modern CSS features. Stick to Qt-supported properties only.

## Environment

- Dev container: `mcr.microsoft.com/devcontainers/universal:2` (min 4 CPUs)
- Key dependencies: PySide6, torch 2.8.0, torchvision, pandas, matplotlib
- `.gitignore` excludes `notebooks/data/`, checkpoints, `__pycache__/`, and all `*.pth` model files
