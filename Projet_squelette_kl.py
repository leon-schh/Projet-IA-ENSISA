import tkinter as tk
from tkinter import ttk
import numpy as np
import random as rnd
from threading import Thread
from queue import Queue
import multiprocessing as mp
from functools import partial


disk_color = ['white', 'red', 'orange']
disks = list()

game = None
window = None
canvas1 = None
information = None
combobox_player1 = None
combobox_player2 = None
row_width = 100

player_type = ['human']
for i in range(20):
    player_type.append('AI: alpha-beta level '+str(i+1))

def max_value(board, depth, alpha, beta, player):
    if depth == 0 or board.check_victory() != 0:
        return board.eval(player)
    possible_moves = board.get_possible_moves()
    if not possible_moves:
        return 0
    v = -float('inf')
    for move in possible_moves:
        new_board = board.copy()
        new_board.add_disk(move, player, update_display=False)
        v = max(v, min_value(new_board, depth - 1, alpha, beta, 3 - player))
        if v >= beta:
            return v
        alpha = max(alpha, v)
    return v

def min_value(board, depth, alpha, beta, player):
    if depth == 0 or board.check_victory() != 0:
        return board.eval(player)
    possible_moves = board.get_possible_moves()
    if not possible_moves:
        return 0
    v = float('inf')
    for move in possible_moves:
        new_board = board.copy()
        new_board.add_disk(move, player, update_display=False)
        v = min(v, max_value(new_board, depth - 1, alpha, beta, 3 - player))
        if v <= alpha:
            return v
        beta = min(beta, v)
    return v

def alpha_beta_decision(board, turn, ai_level, queue, max_player):
    """algorithme alpha-beta"""
    possible_moves = board.get_possible_moves()
    if not possible_moves:
        queue.put(None)
        return
    
    num_processes = min(len(possible_moves), mp.cpu_count())
    
    args_list = []
    for move in possible_moves:
        new_board = board.copy()
        new_board.add_disk(move, max_player, update_display=False)
        args_list.append((new_board.grid.copy(), ai_level - 1, max_player, move))
    
    with mp.Pool(processes=num_processes) as pool:
        results = pool.map(evaluate_move_parallel, args_list)
    
    best_move = None
    best_value = -float('inf')
    for move, value in results:
        if value > best_value:
            best_value = value
            best_move = move
    
    queue.put(best_move)


def evaluate_move_parallel(args):
    """Fonction worker pour évaluer un coup en parallèle"""
    grid, depth, max_player, move = args
    board = Board()
    board.grid = grid
    value = min_value(board, depth, -float('inf'), float('inf'), 3 - max_player)
    return (move, value)

class Board:
    grid = np.array([[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
                     [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]])


    def eval(self, player):
        winner = self.check_victory()
        if winner == player:
            return 1000
        elif winner != 0:
            return -1000
        else:
            score = 0
            opponent = 3 - player
            for row in range(6):
                for col in range(4):
                    window = [self.grid[col + i][row] for i in range(4)]
                    score += self.evaluate_window(window, player)
            for col in range(7):
                for row in range(3):
                    window = [self.grid[col][row + i] for i in range(4)]
                    score += self.evaluate_window(window, player)
            for col in range(4):
                for row in range(3):
                    window = [self.grid[col + i][row + i] for i in range(4)]
                    score += self.evaluate_window(window, player)
            for col in range(4):
                for row in range(3, 6):
                    window = [self.grid[col + i][row - i] for i in range(4)]
                    score += self.evaluate_window(window, player)
            return score

    def evaluate_window(self, window, player):
        score = 0
        opponent = 3 - player
        player_count = window.count(player)
        empty_count = window.count(0)
        opponent_count = window.count(opponent)
        if player_count == 4:
            score += 100
        elif player_count == 3 and empty_count == 1:
            score += 10
        elif player_count == 2 and empty_count == 2:
            score += 2
        if opponent_count == 3 and empty_count == 1:
            score -= 80
        return score

    def copy(self):
        new_board = Board()
        new_board.grid = np.array(self.grid, copy=True)
        return new_board

    def reinit(self):
        self.grid.fill(0)
        for i in range(7):
            for j in range(6):
                canvas1.itemconfig(disks[i][j], fill=disk_color[0])

    def get_possible_moves(self):
        possible_moves = list()
        if self.grid[3][5] == 0:
            possible_moves.append(3)
        for shift_from_center in range(1, 4):
            if self.grid[3 + shift_from_center][5] == 0:
                possible_moves.append(3 + shift_from_center)
            if self.grid[3 - shift_from_center][5] == 0:
                possible_moves.append(3 - shift_from_center)
        return possible_moves

    def add_disk(self, column, player, update_display=True):
        for j in range(6):
            if self.grid[column][j] == 0:
                break
        self.grid[column][j] = player
        if update_display:
            canvas1.itemconfig(disks[column][j], fill=disk_color[player])

    def column_filled(self, column):
        return self.grid[column][5] != 0

    def check_victory(self):
        for line in range(6):
            for horizontal_shift in range(4):
                cells = [self.grid[horizontal_shift + i][line] for i in range(4)]
                if cells[0] != 0 and all(c == cells[0] for c in cells):
                    return cells[0]
        for column in range(7):
            for vertical_shift in range(3):
                cells = [self.grid[column][vertical_shift + i] for i in range(4)]
                if cells[0] != 0 and all(c == cells[0] for c in cells):
                    return cells[0]
        for horizontal_shift in range(4):
            for vertical_shift in range(3):
                cells = [self.grid[horizontal_shift + i][vertical_shift + i] for i in range(4)]
                if cells[0] != 0 and all(c == cells[0] for c in cells):
                    return cells[0]
        for horizontal_shift in range(4):
            for vertical_shift in range(3):
                cells = [self.grid[horizontal_shift + i][5 - vertical_shift - i] for i in range(4)]
                if cells[0] != 0 and all(c == cells[0] for c in cells):
                    return cells[0]
        return 0


class Connect4:

    def __init__(self):
        self.board = Board()
        self.human_turn = False
        self.turn = 1
        self.players = (0, 0)
        self.ai_move = Queue()

    def current_player(self):
        return 2 - (self.turn % 2)

    def launch(self):
        self.board.reinit()
        self.turn = 0
        information['fg'] = 'black'
        information['text'] = "Turn " + str(self.turn) + " - Player " + str(
            self.current_player()) + " is playing"
        self.human_turn = False
        self.players = (combobox_player1.current(), combobox_player2.current())
        self.handle_turn()

    def move(self, column):
        if column is None:
            return
        if not self.board.column_filled(column):
            self.board.add_disk(column, self.current_player())
            self.handle_turn()

    def click(self, event):
        if self.human_turn:
            column = event.x // row_width
            self.move(column)

    def ai_turn(self, ai_level):
        if not self.board.get_possible_moves():
            return
        Thread(target=alpha_beta_decision, args=(self.board, self.turn, ai_level, self.ai_move, self.current_player(),)).start()
        self.ai_wait_for_move()

    def ai_wait_for_move(self):
        if not self.ai_move.empty():
            self.move(self.ai_move.get())
        else:
            window.after(100, self.ai_wait_for_move)

    def handle_turn(self):
        self.human_turn = False
        winner = self.board.check_victory()
        if winner:
            information['fg'] = 'red'
            information['text'] = "Player " + str(winner) + " wins !"
            return
        if not self.board.get_possible_moves():
            information['fg'] = 'red'
            information['text'] = "This a draw !"
            return
        self.turn = self.turn + 1
        information['text'] = "Turn " + str(self.turn) + " - Player " + str(
            self.current_player()) + " is playing"
        if self.players[self.current_player() - 1] != 0:
            self.human_turn = False
            self.ai_turn(self.players[self.current_player() - 1])
        else:
            self.human_turn = True


def main():
    global game, window, canvas1, disks, information, combobox_player1, combobox_player2, row_width

    game = Connect4()

    width = 700
    row_width = width // 7
    row_height = row_width
    height = row_width * 6
    row_margin = row_height // 10

    window = tk.Tk()
    window.title("Connect 4")
    canvas1 = tk.Canvas(window, bg="blue", width=width, height=height)

    for i in range(7):
        disks.append(list())
        for j in range(5, -1, -1):
            disks[i].append(canvas1.create_oval(row_margin + i * row_width, row_margin + j * row_height, (i + 1) * row_width - row_margin,
                                (j + 1) * row_height - row_margin, fill='white'))


    canvas1.grid(row=0, column=0, columnspan=2)

    information = tk.Label(window, text="")
    information.grid(row=1, column=0, columnspan=2)

    label_player1 = tk.Label(window, text="Player 1: ")
    label_player1.grid(row=2, column=0)
    combobox_player1 = ttk.Combobox(window, state='readonly')
    combobox_player1.grid(row=2, column=1)

    label_player2 = tk.Label(window, text="Player 2: ")
    label_player2.grid(row=3, column=0)
    combobox_player2 = ttk.Combobox(window, state='readonly')
    combobox_player2.grid(row=3, column=1)

    combobox_player1['values'] = player_type
    combobox_player1.current(0)
    combobox_player2['values'] = player_type
    combobox_player2.current(6)

    button2 = tk.Button(window, text='New game', command=game.launch)
    button2.grid(row=4, column=0)

    button = tk.Button(window, text='Quit', command=window.destroy)
    button.grid(row=4, column=1)

    canvas1.bind('<Button-1>', game.click)

    window.mainloop()


if __name__ == "__main__":
    mp.freeze_support()
    main()
