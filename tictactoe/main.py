#!/usr/bin/env python3
"""Tic Tac Toe — a polished PySide6 desktop game with an unbeatable AI."""
from __future__ import annotations

import logging
import math
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
APP_TITLE = "Tic Tac Toe — PySide6"
BOARD_SIZE = 3
NUM_CELLS = BOARD_SIZE * BOARD_SIZE

WINNING_LINES: tuple[tuple[int, int, int], ...] = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
)

PLAYER_X = "X"
PLAYER_O = "O"
EMPTY = ""

MIN_WINDOW_W = 560
MIN_WINDOW_H = 640
GRID_SPACING = 12
GRID_MARGIN = 12
LAYOUT_MARGIN = 20
AI_DELAY_MS = 250
ANIMATION_DURATION_MS = 140
ANIMATION_SHRINK_PX = 6

WINNER_INLINE_STYLE = "font-weight: 900; color: #ffd35c; background: #1a3a2a;"


# ---------------------------------------------------------------------------
# Game logic (pure functions — no UI coupling)
# ---------------------------------------------------------------------------
def check_winner(board: Sequence[str]) -> str | None:
    """Return the winning player token, or *None* if no winner yet."""
    for a, b, c in WINNING_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


def find_winning_cells(board: Sequence[str]) -> set[int]:
    """Return the set of cell indices that form the winning line(s)."""
    cells: set[int] = set()
    for a, b, c in WINNING_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            cells.update((a, b, c))
    return cells


def is_draw(board: Sequence[str]) -> bool:
    return all(board) and check_winner(board) is None


def minimax(
    board: list[str],
    depth: int,
    is_maximizing: bool,
    alpha: float = -math.inf,
    beta: float = math.inf,
) -> int:
    """Minimax with alpha-beta pruning.  Maximiser is O, minimiser is X."""
    winner = check_winner(board)
    if winner == PLAYER_O:
        return 10 - depth
    if winner == PLAYER_X:
        return depth - 10
    if all(board):
        return 0

    if is_maximizing:
        best = -math.inf
        for i in range(NUM_CELLS):
            if not board[i]:
                board[i] = PLAYER_O
                val = minimax(board, depth + 1, False, alpha, beta)
                board[i] = EMPTY
                best = max(best, val)
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
        return int(best)
    else:
        best = math.inf
        for i in range(NUM_CELLS):
            if not board[i]:
                board[i] = PLAYER_X
                val = minimax(board, depth + 1, True, alpha, beta)
                board[i] = EMPTY
                best = min(best, val)
                beta = min(beta, val)
                if beta <= alpha:
                    break
        return int(best)


def find_best_move(board: list[str]) -> int | None:
    """Return the index of the best move for O, or *None* if board is full."""
    best_score = -math.inf
    best_move: int | None = None
    for i in range(NUM_CELLS):
        if not board[i]:
            board[i] = PLAYER_O
            score = minimax(board, 0, False)
            board[i] = EMPTY
            if score > best_score:
                best_score = score
                best_move = i
    return best_move


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
class TicTacToeWindow(QtWidgets.QMainWindow):
    """Main window for the Tic Tac Toe application."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(MIN_WINDOW_W, MIN_WINDOW_H)

        # -- central widget & board frame --
        self.central = QtWidgets.QWidget()
        self.setCentralWidget(self.central)

        self.board_frame = QtWidgets.QFrame(objectName="boardFrame")
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(GRID_SPACING)
        self.grid.setContentsMargins(*(GRID_MARGIN,) * 4)
        self.board_frame.setLayout(self.grid)

        # -- cell buttons --
        self.cells: list[QtWidgets.QPushButton] = []
        for i in range(NUM_CELLS):
            btn = QtWidgets.QPushButton(objectName="cell")
            btn.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
            btn.clicked.connect(lambda _checked=False, idx=i: self._on_cell_clicked(idx))
            self.cells.append(btn)
            self.grid.addWidget(btn, i // BOARD_SIZE, i % BOARD_SIZE)

        # -- controls --
        self.status_label = QtWidgets.QLabel(objectName="status")
        self.new_btn = QtWidgets.QPushButton("New Game", objectName="control")
        self.new_btn.clicked.connect(self._restart_game)

        self.mode_btn = QtWidgets.QPushButton(objectName="control")
        self.mode_btn.setCheckable(True)
        self.mode_btn.setChecked(True)
        self.mode_btn.clicked.connect(self._toggle_mode)

        controls = QtWidgets.QHBoxLayout()
        controls.addWidget(self.status_label)
        controls.addStretch()
        controls.addWidget(self.mode_btn)
        controls.addWidget(self.new_btn)

        layout = QtWidgets.QVBoxLayout(self.central)
        layout.addStretch()
        layout.addWidget(self.board_frame, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        layout.addLayout(controls)
        layout.setContentsMargins(*(LAYOUT_MARGIN,) * 4)

        # -- game state --
        self.board: list[str] = [EMPTY] * NUM_CELLS
        self.current = PLAYER_X
        self.vs_ai = True
        self.game_over = False

        # -- stylesheet --
        self._load_stylesheet()

        self._sync_ui()

    # -- Stylesheet --------------------------------------------------------

    def _load_stylesheet(self) -> None:
        qss_path = Path(__file__).resolve().parent / "styles.qss"
        try:
            self.setStyleSheet(qss_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            logger.warning("Stylesheet not found at %s — using defaults", qss_path)
        except OSError:
            logger.exception("Failed to load stylesheet from %s", qss_path)

    # -- Mode toggle -------------------------------------------------------

    def _toggle_mode(self) -> None:
        self.vs_ai = self.mode_btn.isChecked()
        self._restart_game()

    # -- Cell interaction --------------------------------------------------

    def _on_cell_clicked(self, idx: int) -> None:
        if self.game_over or self.board[idx]:
            return
        if self.vs_ai and self.current == PLAYER_O:
            return  # ignore clicks while AI is "thinking"

        self._place_move(idx, self.current)

        winner = check_winner(self.board)
        if winner or is_draw(self.board):
            self._finish(winner)
            return

        self._advance_turn()

        if self.vs_ai and self.current == PLAYER_O:
            QtCore.QTimer.singleShot(AI_DELAY_MS, self._ai_move)

    def _place_move(self, idx: int, player: str) -> None:
        self.board[idx] = player
        btn = self.cells[idx]
        btn.setText(player)
        self._animate_reveal(btn)

    def _animate_reveal(self, btn: QtWidgets.QPushButton) -> None:
        rect = btn.geometry()
        anim = QtCore.QPropertyAnimation(btn, b"geometry", btn)
        anim.setStartValue(
            rect.adjusted(
                ANIMATION_SHRINK_PX, ANIMATION_SHRINK_PX,
                -ANIMATION_SHRINK_PX, -ANIMATION_SHRINK_PX,
            )
        )
        anim.setEndValue(rect)
        anim.setDuration(ANIMATION_DURATION_MS)
        anim.start(QtCore.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    # -- Turn / status -----------------------------------------------------

    def _advance_turn(self) -> None:
        self.current = PLAYER_O if self.current == PLAYER_X else PLAYER_X
        self._sync_ui()

    def _sync_ui(self) -> None:
        for i, token in enumerate(self.board):
            btn = self.cells[i]
            btn.setText(token)
            btn.setEnabled(not token and not self.game_over)

        if not self.game_over:
            if self.vs_ai:
                label = "Your move" if self.current == PLAYER_X else "AI is thinking..."
            else:
                label = f"Player {self.current}'s turn"
            self.status_label.setText(label)

        self.mode_btn.setText("Mode: Vs AI" if self.vs_ai else "Mode: PvP")

    # -- Game end ----------------------------------------------------------

    def _finish(self, winner: str | None) -> None:
        self.game_over = True

        if winner:
            self.status_label.setText(
                f"You {'win' if winner == PLAYER_X and self.vs_ai else 'lose'}"
                if self.vs_ai
                else f"Player {winner} wins!"
            )
            for i in find_winning_cells(self.board):
                self.cells[i].setStyleSheet(WINNER_INLINE_STYLE)
        else:
            self.status_label.setText("Draw!")

        for btn in self.cells:
            btn.setEnabled(False)

    # -- Restart -----------------------------------------------------------

    def _restart_game(self) -> None:
        self.board = [EMPTY] * NUM_CELLS
        self.current = PLAYER_X
        self.game_over = False
        for btn in self.cells:
            btn.setText(EMPTY)
            btn.setEnabled(True)
            btn.setStyleSheet("")
        self._sync_ui()

    # -- AI ----------------------------------------------------------------

    def _ai_move(self) -> None:
        if self.game_over:
            return
        move = find_best_move(self.board)
        if move is None:
            return

        self._place_move(move, PLAYER_O)

        winner = check_winner(self.board)
        if winner or is_draw(self.board):
            self._finish(winner)
            return

        self.current = PLAYER_X
        self._sync_ui()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    if not any(os.environ.get(v) for v in ("DISPLAY", "WAYLAND_DISPLAY", "MIR_SOCKET")):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    app = QtWidgets.QApplication(sys.argv)
    win = TicTacToeWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
