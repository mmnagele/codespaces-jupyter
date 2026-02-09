# Code Review: A Masterclass in How Not To Write Software

**Reviewer:** Someone who cares about code quality
**Date:** 2026-02-09
**Verdict:** This code compiles. That is the nicest thing I can say about it.

---

## Executive Summary

What we have here is a GitHub Codespaces "starter project" that appears to have been started... and then abandoned mid-thought. Repeatedly. Across multiple files. The author demonstrates a consistent ability to almost do the right thing, and then veer off into a ditch at the last possible moment.

Let's walk through the wreckage.

---

## 1. `tictactoe/main.py` — The Main Attraction

### 1.1 The Copy-Paste Hall of Fame (Lines 14-18 vs 142-146)

```python
# In check_winner():
wins = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6)
]

# In finish(), because apparently Ctrl+C Ctrl+V is easier than a constant:
wins = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6)
]
```

The winning combinations are defined **twice**. Identically. In the same file. If you ever need to change the rules of Tic Tac Toe (say, moving to a 4x4 board), you get to update it in two places and pray you don't miss one. DRY isn't just a weather condition.

**Severity:** High | **Category:** DRY violation

---

### 1.2 The Mode Toggle Bug (Lines 80, 60-61, 92-95)

This one is *chef's kiss*. Let's trace the logic:

```python
# Init:
self.vs_ai = True                          # AI mode is ON
self.mode_btn = QPushButton("Mode: Vs AI") # Text says AI
self.mode_btn.setCheckable(True)           # Checkable, but NOT checked

# On click:
def toggle_mode(self):
    self.vs_ai = self.mode_btn.isChecked()  # First click -> checked -> True
    self.mode_btn.setText("Mode: Vs AI" if self.vs_ai else "Mode: PvP")
```

Initial state: `vs_ai = True`, button is **unchecked**. User clicks once: button becomes **checked**, `isChecked()` returns `True`, so `vs_ai` stays `True`. Text stays "Mode: Vs AI". **The first click does absolutely nothing.** You need to click TWICE to toggle. This is a genuine, shipped bug caused by the button's checked state being out of sync with `vs_ai` from the start.

But it gets better! The button text shows the **current** mode, not what clicking will do. So the user sees "Mode: Vs AI" and clicks it thinking "I want to switch to AI mode"... but they're ALREADY in AI mode. UX designed by someone who thinks users enjoy puzzles.

**Severity:** Critical | **Category:** Logic bug + UX failure

---

### 1.3 The Stylesheet That Can't Be Found (Lines 84-88)

```python
try:
    with open(QtCore.QDir.currentPath() + "/tictactoe/styles.qss", "r") as f:
        self.setStyleSheet(f.read())
except Exception:
    pass
```

Two crimes in one block:

1. **`QDir.currentPath()`** returns the *current working directory*, not the directory containing the script. Run `python tictactoe/main.py` from anywhere other than the project root and the stylesheet silently vanishes. The correct approach is `pathlib.Path(__file__).parent / "styles.qss"`.

2. **`except Exception: pass`** — The crown jewel of "I don't want to know what went wrong." File not found? Permission denied? Disk on fire? Who cares! Swallow everything, show the user an ugly unstyled window, and let them figure it out. This is the programming equivalent of turning off your check engine light with electrical tape.

**Severity:** High | **Category:** Fragile path + Silent failure

---

### 1.4 The "I Know CSS" Stylesheet (styles.qss)

```css
QPushButton#cell:hover {
  transform: scale(1.02);   /* Does absolutely nothing */
}

.winner {
  box-shadow: 0 0 18px rgba(255,215,0,0.12);   /* Also does nothing */
}
```

Qt Style Sheets are **not CSS**. They are a subset that looks like CSS to lure web developers into a false sense of security. Qt does not support `transform`, `box-shadow`, CSS class selectors (`.winner`), or most other modern CSS features.

The author wrote a hover animation and a winner glow effect that **literally do nothing**. Zero. The comments say "Subtle glow for winner highlight" — yes, so subtle it's invisible, because the code doesn't execute.

The winner highlighting actually falls back to inline `setStyleSheet()` on line 151, which **replaces** the button's entire computed style, potentially breaking the cell's gradient background. Magnificent.

**Severity:** High | **Category:** Fundamental misunderstanding of Qt

---

### 1.5 The Import Identity Crisis (Lines 1-7)

```python
from __future__ import annotations  # "I'm modern!"
import sys
from functools import partial
from typing import List, Optional   # "...but not THAT modern"

import os                            # Why am I separated from my friends?
```

The `from __future__ import annotations` on line 1 makes all annotations lazy strings, which means you can use `list[str]` and `int | None` directly. But then the author imports `List` and `Optional` from `typing` anyway, as if they put on a top hat but forgot to take off their pajama pants.

And `os` is exiled on line 7, separated from the other stdlib imports by a blank line and the third-party imports that... aren't there yet. It's just floating alone. Lonely. Confused. Violating PEP 8 import ordering for no reason.

**Severity:** Low | **Category:** Style inconsistency

---

### 1.6 Magic Numbers: A Comprehensive Tour

```python
self.setMinimumSize(560, 640)      # Why 560x640? Nobody knows
self.grid.setSpacing(12)           # The sacred number 12
best_score = -999                  # Not -inf, not -1000, but -999
best = 999                         # Symmetrically wrong
QTimer.singleShot(250, ...)        # AI delay: arbitrary
anim.setDuration(140)              # Animation: equally arbitrary
rect.adjusted(6, 6, -6, -6)       # Shrink by 6 pixels because... vibes?
```

Not a single constant. Not a single comment explaining *why* these values. The code reads like someone rolling dice for their parameters.

`-999` as a stand-in for negative infinity is particularly delightful. On a 3x3 board the minimax scores range from about -10 to +10, so it works, but it screams "I don't know that `float('-inf')` exists."

**Severity:** Medium | **Category:** Maintainability

---

### 1.7 Dead Code and Useless Operations (Lines 45-46)

```python
btn.setProperty("pos", i)    # Set a property...
btn.setStyleSheet("")         # Set an empty stylesheet...
```

`setProperty("pos", i)` stores the cell position on the button. It is **never read** anywhere in the code. The click handler uses `partial(self.on_cell_clicked, i)` to capture the index. So this property just sits there, wasting memory and confusing readers.

`setStyleSheet("")` sets an empty stylesheet on every button during creation. This is a no-op. It does nothing. It's like writing `x = x`.

**Severity:** Low | **Category:** Dead code

---

### 1.8 The Minimax That Mutates Its Own State (Lines 182-221)

```python
def find_best_move(self):
    for i in range(9):
        if not self.board[i]:
            self.board[i] = "O"                    # Mutate!
            score = self.minimax(self.board, 0, False)
            self.board[i] = ""                     # Pray nothing went wrong
```

The minimax algorithm directly mutates `self.board` during its search, then restores it. This is the board game equivalent of performing surgery on the patient to see what would happen, then stitching them back up.

If **any** exception occurs during `minimax()`, the board is left in a corrupted state with ghost moves. No try/finally, no copy — just raw mutation and hope.

The method also takes `board` as a parameter (creating the illusion of a pure function) but it's always passed `self.board`. You're not fooling anyone.

And no alpha-beta pruning. Yes, the 3x3 search space is small, but the author explores ~255,000 game states when ~1,500 would suffice. The AI "thinks" for 250ms not because of UX design but because it's doing 170x more work than necessary.

**Severity:** Medium | **Category:** Fragile state management + inefficiency

---

### 1.9 The Accessibility Void (Line 43)

```python
btn.setFocusPolicy(QtCore.Qt.NoFocus)
```

Every cell button has keyboard focus explicitly **disabled**. Users who navigate with Tab, use screen readers, or simply prefer keyboard controls cannot play this game at all. The author built a GUI application and then said "mice only, peasants."

**Severity:** Medium | **Category:** Accessibility

---

### 1.10 Status Text Lies in PvP Mode (Line 135)

```python
self.status_label.setText(f"Your move: {self.current}")
```

In Player vs Player mode, both players are humans. But the label says "Your move" as if only one person exists. Player O looks at the screen and reads "Your move: X" and wonders... whose move?

**Severity:** Low | **Category:** UX

---

### 1.11 Manual Grid Indexing (Lines 50-54)

```python
idx = 0
for r in range(3):
    for c in range(3):
        self.grid.addWidget(self.cells[idx], r, c)
        idx += 1
```

Manual index counter with nested loops. In a language that has `divmod`, `enumerate`, and basic arithmetic (`i // 3, i % 3`). This is the kind of code that survives from a C homework assignment.

**Severity:** Low | **Category:** Non-idiomatic Python

---

## 2. Jupyter Notebooks — The Neglected Siblings

### 2.1 `image-classifier.ipynb` — Deprecated API Calls

```python
images, labels = dataiter.next()    # .next() was deprecated in Python 3.0
```

`.next()` has been deprecated since **Python 3.0** (2008). That's 18 years ago. The correct call is `next(dataiter)`. This appears TWICE in the notebook.

```python
if dataiter == None:    # Identity check with equality operator
```

`== None` instead of `is None`. PEP 8 has been clear about this since 2001. Twenty-five years. A quarter century of ignoring style guides.

```python
torch.load(PATH)       # No weights_only=True
```

Missing `weights_only=True` on `torch.load()`. Since PyTorch 2.6, this triggers a security warning because unpickling arbitrary data can execute arbitrary code. Our author trusts the pickle file they just saved 3 cells ago? Sure. But anyone who downloads this notebook and loads a model from the internet is now vulnerable.

**Severity:** High (security) + Medium (deprecated APIs) | **Category:** Security + Outdated code

---

### 2.2 `population.ipynb` — The Little Things

```python
import pandas
df = pandas.read_csv(...)
```

Every pandas tutorial, every data science textbook, every Stack Overflow answer uses `import pandas as pd`. This isn't just convention — it's practically law. Using the full `pandas` name is like calling your friend by their full legal name including middle initial at a party.

```python
plt.plot(x,y)    # No space after comma
```

PEP 8. Spaces after commas. It's in the first few paragraphs.

**Severity:** Low | **Category:** Convention violations

---

## 3. `requirements.txt` — Pick a Pinning Strategy

```
matplotlib==3.8.4      # Exact pin
pandas==2.2.2          # Exact pin
fonttools>=4.60.0      # Minimum version
PySide6>=6.6.0         # Minimum version
```

Some packages are pinned exactly (`==`), others have minimum versions (`>=`). Pick a strategy. Exact pins for reproducibility, or ranges for flexibility — not both randomly mixed. This is how you get "works on my machine" bugs.

**Severity:** Medium | **Category:** Dependency management

---

## 4. `.gitignore` — The Path That Lies

```
notebooks/cifar_net.pth
```

The image classifier saves its model to `./cifar_net.pth` (relative to CWD). The gitignore entry assumes it's saved to `notebooks/cifar_net.pth`. If you run the notebook from the project root (as Jupyter often does), the `.pth` file lands in the project root and gets committed. If you run from `notebooks/`, it lands in `notebooks/` but is saved as `notebooks/data` would catch it... no, `notebooks/data` is a directory pattern.

The gitignore should be `*.pth` or the notebook should use an absolute path.

**Severity:** Low | **Category:** Build hygiene

---

## Final Score

| Category | Issues Found |
|---|---|
| Logic Bugs | 1 (mode toggle) |
| Security | 1 (torch.load) |
| DRY Violations | 1 (winning combos) |
| Dead/Useless Code | 2 (pos property, empty stylesheet) |
| Silent Failures | 1 (swallowed exception) |
| Broken Features | 2 (QSS transform + box-shadow) |
| Magic Numbers | 7+ |
| Deprecated APIs | 3 (.next(), == None, typing imports) |
| Fragile Patterns | 2 (CWD path, board mutation) |
| Accessibility | 1 (no keyboard support) |
| Style/Convention | 4+ |
| **Total** | **25+** |

The code works. Like a car with three wheels works — it gets you somewhere, eventually, wobbling the whole way, and heaven help you if you hit a bump.

---

*Now let's fix all of this.*
