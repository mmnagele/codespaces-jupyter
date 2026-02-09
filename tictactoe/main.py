#!/usr/bin/env python3
from __future__ import annotations
import sys
from functools import partial
from typing import List, Optional

import os
from PySide6 import QtCore, QtGui, QtWidgets

APP_TITLE = "Tic Tac Toe — PySide6"


def check_winner(board: List[str]) -> Optional[str]:
    wins = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]
    for a, b, c in wins:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


class TicTacToeWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(560, 640)

        self.central = QtWidgets.QWidget()
        self.setCentralWidget(self.central)

        self.board_frame = QtWidgets.QFrame(objectName="boardFrame")
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(12)
        self.grid.setContentsMargins(12, 12, 12, 12)
        self.board_frame.setLayout(self.grid)

        self.cells: List[QtWidgets.QPushButton] = []
        for i in range(9):
            btn = QtWidgets.QPushButton(objectName="cell")
            btn.setFocusPolicy(QtCore.Qt.NoFocus)
            btn.clicked.connect(partial(self.on_cell_clicked, i))
            btn.setProperty("pos", i)
            btn.setStyleSheet("")
            self.cells.append(btn)

        # place in grid
        idx = 0
        for r in range(3):
            for c in range(3):
                self.grid.addWidget(self.cells[idx], r, c)
                idx += 1

        # Controls
        self.status_label = QtWidgets.QLabel("Your move: X", objectName="status")
        self.new_btn = QtWidgets.QPushButton("New Game", objectName="control")
        self.new_btn.clicked.connect(self.restart_game)
        self.mode_btn = QtWidgets.QPushButton("Mode: Vs AI", objectName="control")
        self.mode_btn.setCheckable(True)
        self.mode_btn.clicked.connect(self.toggle_mode)

        controls_h = QtWidgets.QHBoxLayout()
        controls_h.addWidget(self.status_label)
        controls_h.addStretch()
        controls_h.addWidget(self.mode_btn)
        controls_h.addWidget(self.new_btn)

        layout = QtWidgets.QVBoxLayout(self.central)
        layout.addStretch()
        layout.addWidget(self.board_frame, alignment=QtCore.Qt.AlignCenter)
        layout.addStretch()
        layout.addLayout(controls_h)
        layout.setContentsMargins(20, 20, 20, 20)

        # game state
        self.board: List[str] = [""] * 9
        self.current = "X"  # X always starts
        self.vs_ai = True
        self.game_over = False

        # styling
        try:
            with open(QtCore.QDir.currentPath() + "/tictactoe/styles.qss", "r") as f:
                self.setStyleSheet(f.read())
        except Exception:
            pass

        self.update_ui()

    def toggle_mode(self):
        self.vs_ai = self.mode_btn.isChecked()
        self.mode_btn.setText("Mode: Vs AI" if self.vs_ai else "Mode: PvP")
        self.restart_game()

    def on_cell_clicked(self, idx: int):
        if self.game_over:
            return
        if self.board[idx]:
            return
        if self.vs_ai and self.current == "O":
            return
        self.place_move(idx, self.current)
        winner = check_winner(self.board)
        if winner or all(self.board):
            self.finish(winner)
            return
        self.current = "O" if self.current == "X" else "X"
        self.update_ui()
        if self.vs_ai and self.current == "O":
            QtCore.QTimer.singleShot(250, self.ai_move)

    def place_move(self, idx: int, player: str):
        self.board[idx] = player
        btn = self.cells[idx]
        btn.setText(player)
        # subtle reveal animation
        anim = QtCore.QPropertyAnimation(btn, b"geometry")
        rect = btn.geometry()
        anim.setStartValue(rect.adjusted(6, 6, -6, -6))
        anim.setEndValue(rect)
        anim.setDuration(140)
        anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    def update_ui(self):
        for i, b in enumerate(self.board):
            btn = self.cells[i]
            btn.setText(b)
            if b:
                btn.setEnabled(False)
            else:
                btn.setEnabled(not self.game_over)
        if not self.game_over:
            self.status_label.setText(f"Your move: {self.current}")

    def finish(self, winner: Optional[str]):
        self.game_over = True
        if winner:
            self.status_label.setText(f"Winner: {winner}")
            # highlight winning cells
            wins = [
                (0, 1, 2), (3, 4, 5), (6, 7, 8),
                (0, 3, 6), (1, 4, 7), (2, 5, 8),
                (0, 4, 8), (2, 4, 6)
            ]
            for a, b, c in wins:
                if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                    for i in (a, b, c):
                        self.cells[i].setProperty("class", "winner")
                        self.cells[i].setStyleSheet(self.cells[i].styleSheet() + "\nfont-weight:900; color:#ffd35c;")
        else:
            self.status_label.setText("Draw")
        for btn in self.cells:
            btn.setEnabled(False)

    def restart_game(self):
        self.board = [""] * 9
        self.current = "X"
        self.game_over = False
        for btn in self.cells:
            btn.setText("")
            btn.setEnabled(True)
            btn.setProperty("class", "")
            btn.setStyleSheet("")
        self.update_ui()

    # --- AI (minimax) ---
    def ai_move(self):
        if self.game_over:
            return
        move = self.find_best_move()
        if move is not None:
            self.place_move(move, "O")
            winner = check_winner(self.board)
            if winner or all(self.board):
                self.finish(winner)
                return
            self.current = "X"
            self.update_ui()

    def find_best_move(self) -> Optional[int]:
        best_score = -999
        best_move = None
        for i in range(9):
            if not self.board[i]:
                self.board[i] = "O"
                score = self.minimax(self.board, 0, False)
                self.board[i] = ""
                if score > best_score:
                    best_score = score
                    best_move = i
        return best_move

    def minimax(self, board: List[str], depth: int, is_maximizing: bool) -> int:
        winner = check_winner(board)
        if winner == "O":
            return 10 - depth
        elif winner == "X":
            return depth - 10
        elif all(board):
            return 0

        if is_maximizing:
            best = -999
            for i in range(9):
                if not board[i]:
                    board[i] = "O"
                    val = self.minimax(board, depth + 1, False)
                    board[i] = ""
                    best = max(best, val)
            return best
        else:
            best = 999
            for i in range(9):
                if not board[i]:
                    board[i] = "X"
                    val = self.minimax(board, depth + 1, True)
                    board[i] = ""
                    best = min(best, val)
            return best


def main():
    # If no display is available (headless/container), fall back to offscreen
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or os.environ.get("MIR_SOCKET")):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QtWidgets.QApplication(sys.argv)
    win = TicTacToeWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
