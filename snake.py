#!/usr/bin/env python3
"""Terminal Snake — classic snake game for the terminal, stdlib only.

Controls:
    Arrow keys / WASD .... change direction
    p or Space ........... pause
    q .................... quit
    r .................... restart (after game over)

Run:  python3 snake.py
"""

import curses
import json
import os
import random
import time

# --- Configuration ----------------------------------------------------------

GAME_TITLE = "TERMINAL SNAKE"

BOARD_MIN_W = 40
BOARD_MIN_H = 20
MAX_SPEED = 2          # fastest tick interval (seconds per move)
START_SPEED = 0.13
SPEED_STEP = 0.006     # speed-up per food eaten

HIGHSCORE_FILE = os.path.join(
    os.path.expanduser("~"), ".config", "terminal_snake", "highscore.json"
)

# Cell rendering
SNAKE_HEAD = "@"
SNAKE_BODY = "o"
FOOD = "*"
WALL = "#"

# Direction vectors
UP, DOWN, LEFT, RIGHT = (0, -1), (0, 1), (-1, 0), (1, 0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}


def load_highscore():
    try:
        with open(HIGHSCORE_FILE) as f:
            return json.load(f).get("highscore", 0)
    except (OSError, ValueError):
        return 0


def save_highscore(score):
    if score <= load_highscore():
        return
    os.makedirs(os.path.dirname(HIGHSCORE_FILE), exist_ok=True)
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump({"highscore": score}, f)
    except OSError:
        pass


class SnakeGame:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.keypad(True)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)   # snake
        curses.init_pair(2, curses.COLOR_RED, -1)     # food
        curses.init_pair(3, curses.COLOR_CYAN, -1)    # walls / frame
        curses.init_pair(4, curses.COLOR_YELLOW, -1)  # score
        curses.init_pair(5, curses.COLOR_MAGENTA, -1) # highlights

        self.highscore = load_highscore()
        self.reset()

    # --- Setup helpers ------------------------------------------------------

    def board_bounds(self):
        """Compute a centered board rect fitting the current terminal."""
        rows, cols = self.stdscr.getmaxyx()
        bh = min(rows - 4, max(BOARD_MIN_H, rows - 10))
        bw = min(cols - 2, max(BOARD_MIN_W, cols - 20))
        bh = max(6, bh)
        bw = max(16, bw)
        top = max(0, (rows - bh) // 2 - 1)
        left = max(0, (cols - bw) // 2)
        return top, left, bw, bh

    def reset(self):
        self.top, self.left, self.bw, self.bh = self.board_bounds()
        self.inner = [(x, y) for y in range(1, self.bh - 1)
                      for x in range(1, self.bw - 1)]

        cy, cx = self.bh // 2, self.bw // 2
        self.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.speed = START_SPEED
        self.score = 0
        self.paused = False
        self.game_over = False
        self.new_high = False
        self.food = self.spawn_food()

    def spawn_food(self):
        occupied = set(self.snake)
        free = [c for c in self.inner if c not in occupied]
        return random.choice(free) if free else None

    # --- Game logic ---------------------------------------------------------

    def step(self):
        """Advance one tick. Returns False when the game ends."""
        if self.next_direction != OPPOSITE[self.direction]:
            self.direction = self.next_direction

        dx, dy = self.direction
        hx, hy = self.snake[0]
        head = (hx + dx, hy + dy)

        # Wall collision
        if not (0 < head[0] < self.bw - 1 and 0 < head[1] < self.bh - 1):
            return self.end_game()
        # Self collision (tail cell is safe — it moves away this tick)
        if head in self.snake[:-1]:
            return self.end_game()

        self.snake.insert(0, head)

        if head == self.food:
            self.score += 10
            self.speed = max(MAX_SPEED, self.speed - SPEED_STEP)
            self.food = self.spawn_food()
            if self.food is None:            # board full — you win!
                self.score += 100
                return self.end_game(won=True)
        else:
            self.snake.pop()
        return True

    def end_game(self, won=False):
        self.game_over = True
        self.won = won
        if self.score > self.highscore:
            self.highscore = self.score
            self.new_high = True
            save_highscore(self.score)
        return False

    # --- Input --------------------------------------------------------------

    KEYMAP = {
        curses.KEY_UP: UP, ord("w"): UP, ord("W"): UP,
        curses.KEY_DOWN: DOWN, ord("s"): DOWN, ord("S"): DOWN,
        curses.KEY_LEFT: LEFT, ord("a"): LEFT, ord("A"): LEFT,
        curses.KEY_RIGHT: RIGHT, ord("d"): RIGHT, ord("D"): RIGHT,
    }

    def handle_input(self):
        key = self.stdscr.getch()
        while key != -1:                     # drain the input buffer
            if key in (ord("q"), ord("Q")):
                return "quit"
            if self.game_over:
                if key in (ord("r"), ord("R")):
                    self.reset()
                    return "restart"
            elif key in (ord("p"), ord("P"), ord(" ")):
                self.paused = not self.paused
            elif key in self.KEYMAP:
                d = self.KEYMAP[key]
                if d != OPPOSITE[self.direction]:
                    self.next_direction = d
            key = self.stdscr.getch()
        return None

    # --- Rendering ----------------------------------------------------------

    def draw_cell(self, x, y, ch, pair):
        try:
            self.stdscr.addstr(self.top + y, self.left + x, ch,
                               curses.color_pair(pair) | curses.A_BOLD)
        except curses.error:
            pass

    def draw_frame(self):
        t, l, w, h = self.top, self.left, self.bw, self.bh
        attr = curses.color_pair(3)
        try:
            self.stdscr.addstr(t, l, WALL * w, attr)
            self.stdscr.addstr(t + h - 1, l, WALL * w, attr)
            for row in range(1, h - 1):
                self.stdscr.addstr(t + row, l, WALL, attr)
                self.stdscr.addstr(t + row, l + w - 1, WALL, attr)
        except curses.error:
            pass

    def draw_status(self):
        rows, cols = self.stdscr.getmaxyx()
        line_y = self.top + self.bh + 1
        score = f" SCORE: {self.score} "
        high = f" HIGH: {self.highscore} "
        speed = f" SPEED: {round((START_SPEED - self.speed) * 100 / 1):3d}% "
        try:
            self.stdscr.addstr(line_y, self.left, score,
                               curses.color_pair(4) | curses.A_BOLD)
            self.stdscr.addstr(line_y, self.left + self.bw // 2 - len(high) // 2,
                               high, curses.color_pair(5))
            self.stdscr.addstr(line_y, self.left + self.bw - len(speed), speed,
                               curses.color_pair(4))
        except curses.error:
            pass

        hint = " Arrows/WASD move · P pause · Q quit "
        if rows > line_y + 2 and cols >= len(hint):
            try:
                self.stdscr.addstr(line_y + 1, max(0, self.left),
                                   hint[:cols - 1], curses.A_DIM)
            except curses.error:
                pass

    def draw_board(self):
        self.stdscr.erase()
        self.draw_frame()

        self.draw_cell(*self.food, FOOD, 2)
        for i, (x, y) in enumerate(self.snake):
            self.draw_cell(x, y, SNAKE_HEAD if i == 0 else SNAKE_BODY, 1)

        self.draw_status()

        if self.paused:
            self.overlay("PAUSED", ["Press P or Space to resume"])
        elif self.game_over:
            lines = []
            if self.won:
                lines.append("PERFECT! YOU FILLED THE BOARD!")
            else:
                lines.append("GAME OVER")
            lines.append(f"Score: {self.score}")
            if self.new_high:
                lines.append("*** NEW HIGHSCORE! ***")
            lines.append("Press R to restart, Q to quit")
            self.overlay("SNAKE", lines)

    def overlay(self, title, lines):
        h, w = len(lines) + 4, max(len(title), *(len(l) for l in lines)) + 6
        rows, cols = self.stdscr.getmaxyx()
        y0, x0 = (rows - h) // 2, (cols - w) // 2
        box = curses.newwin(h, w, y0, x0)
        box.box()
        try:
            box.addstr(0, (w - len(title)) // 2, f" {title} ",
                       curses.color_pair(5) | curses.A_BOLD)
            for i, line in enumerate(lines):
                box.addstr(i + 2, (w - len(line)) // 2, line,
                           curses.A_BOLD if i == 0 else curses.A_NORMAL)
        except curses.error:
            pass
        box.refresh()

    # --- Main loop ----------------------------------------------------------

    def run(self):
        last_tick = time.monotonic()
        while True:
            action = self.handle_input()
            if action == "quit":
                return
            if not self.paused and not self.game_over:
                now = time.monotonic()
                if now - last_tick >= self.speed:
                    last_tick = now
                    self.step()
            self.draw_board()
            time.sleep(0.01)


def main(stdscr):
    while True:
        game = SnakeGame(stdscr)
        game.run()                 # returns only on Q
        if not game.game_over:     # quit mid-game
            return


def wrapper():
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    wrapper()
