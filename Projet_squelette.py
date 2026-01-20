import tkinter as tk
from tkinter import ttk
import numpy as np
import random as rnd
from threading import Thread
from queue import Queue


disk_color = ['white', 'red', 'orange']
disks = list()

player_type = ['human']
for i in range(10):
    player_type.append('AI: alpha-beta level '+str(i+1))

def alpha_beta_decision(board, turn, ai_level, queue, max_player):
    """Décision alpha-beta : choisit le meilleur coup pour le joueur max_player."""
    best_move = None
    best_value = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    
    for move in board.get_possible_moves():
        new_board = board.copy()
        new_board.add_disk(move, max_player, update_display=False)
        
        # Si ce coup est gagnant, on le joue immédiatement
        if new_board.check_victory():
            queue.put(move)
            return
        
        # Sinon on évalue avec alpha-beta
        opponent = 3 - max_player
        value = min_value(new_board, ai_level - 1, alpha, beta, max_player, opponent)
        
        if value > best_value:
            best_value = value
            best_move = move
        alpha = max(alpha, best_value)
    
    queue.put(best_move)

def max_value(board, depth, alpha, beta, max_player, current_player):
    """Fonction max de l'algorithme alpha-beta."""
    # Condition d'arrêt
    if board.check_victory():
        return float('-inf')  # L'adversaire vient de gagner
    if depth == 0 or len(board.get_possible_moves()) == 0:
        return board.eval(max_player)
    
    value = float('-inf')
    for move in board.get_possible_moves():
        new_board = board.copy()
        new_board.add_disk(move, current_player, update_display=False)
        
        if new_board.check_victory():
            return float('inf')  # On gagne
        
        opponent = 3 - current_player
        value = max(value, min_value(new_board, depth - 1, alpha, beta, max_player, opponent))
        
        if value >= beta:
            return value  # Élagage beta
        alpha = max(alpha, value)
    
    return value

def min_value(board, depth, alpha, beta, max_player, current_player):
    """Fonction min de l'algorithme alpha-beta."""
    # Condition d'arrêt
    if board.check_victory():
        return float('inf')  # On vient de gagner
    if depth == 0 or len(board.get_possible_moves()) == 0:
        return board.eval(max_player)
    
    value = float('inf')
    for move in board.get_possible_moves():
        new_board = board.copy()
        new_board.add_disk(move, current_player, update_display=False)
        
        if new_board.check_victory():
            return float('-inf')  # L'adversaire gagne
        
        opponent = 3 - current_player
        value = min(value, max_value(new_board, depth - 1, alpha, beta, max_player, opponent))
        
        if value <= alpha:
            return value  # Élagage alpha
        beta = min(beta, value)
    
    return value

class Board:
    def __init__(self):
        self.grid = np.array([[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
                              [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]])


    def eval(self, player):
        """
        Évalue la grille pour le joueur donné.
        Score positif = avantage pour player, négatif = avantage adversaire.
        """
        score = 0
        opponent = 3 - player
        
        # Évaluation de toutes les fenêtres de 4 cases
        # Horizontales
        for line in range(6):
            for col in range(4):
                window = [self.grid[col + i][line] for i in range(4)]
                score += self.evaluate_window(window, player, opponent)
        
        # Verticales
        for col in range(7):
            for line in range(3):
                window = [self.grid[col][line + i] for i in range(4)]
                score += self.evaluate_window(window, player, opponent)
        
        # Diagonales montantes
        for col in range(4):
            for line in range(3):
                window = [self.grid[col + i][line + i] for i in range(4)]
                score += self.evaluate_window(window, player, opponent)
        
        # Diagonales descendantes
        for col in range(4):
            for line in range(3, 6):
                window = [self.grid[col + i][line - i] for i in range(4)]
                score += self.evaluate_window(window, player, opponent)
        
        # Bonus pour le contrôle du centre
        center_col = [self.grid[3][i] for i in range(6)]
        score += center_col.count(player) * 3
        score -= center_col.count(opponent) * 3
        
        return score
    
    def evaluate_window(self, window, player, opponent):
        """Évalue une fenêtre de 4 cases."""
        score = 0
        player_count = window.count(player)
        opponent_count = window.count(opponent)
        empty_count = window.count(0)
        
        # Si la fenêtre contient des pions des deux joueurs, elle est bloquée
        if player_count > 0 and opponent_count > 0:
            return 0
        
        # Score pour le joueur
        if player_count == 3 and empty_count == 1:
            score += 50  # Menace de victoire
        elif player_count == 2 and empty_count == 2:
            score += 10
        elif player_count == 1 and empty_count == 3:
            score += 1
        
        # Score pour l'adversaire (négatif)
        if opponent_count == 3 and empty_count == 1:
            score -= 50  # Menace adverse
        elif opponent_count == 2 and empty_count == 2:
            score -= 10
        elif opponent_count == 1 and empty_count == 3:
            score -= 1
        
        return score

    def copy(self):
        new_board = Board()
        new_board.grid = np.copy(self.grid)
        return new_board

    def reinit(self):
        self.grid = np.array([[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
                              [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]])
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
                self.grid[column][j] = player
                if update_display:
                    canvas1.itemconfig(disks[column][j], fill=disk_color[player])
                return True
        return False  # Colonne pleine

    def column_filled(self, column):
        return self.grid[column][5] != 0

    def check_victory(self):
        # Horizontal alignment check
        for line in range(6):
            for horizontal_shift in range(4):
                if self.grid[horizontal_shift][line] == self.grid[horizontal_shift + 1][line] == self.grid[horizontal_shift + 2][line] == self.grid[horizontal_shift + 3][line] != 0:
                    return True
        # Vertical alignment check
        for column in range(7):
            for vertical_shift in range(3):
                if self.grid[column][vertical_shift] == self.grid[column][vertical_shift + 1] == \
                        self.grid[column][vertical_shift + 2] == self.grid[column][vertical_shift + 3] != 0:
                    return True
        # Diagonal alignment check
        for horizontal_shift in range(4):
            for vertical_shift in range(3):
                if self.grid[horizontal_shift][vertical_shift] == self.grid[horizontal_shift + 1][vertical_shift + 1] ==\
                        self.grid[horizontal_shift + 2][vertical_shift + 2] == self.grid[horizontal_shift + 3][vertical_shift + 3] != 0:
                    return True
                elif self.grid[horizontal_shift][5 - vertical_shift] == self.grid[horizontal_shift + 1][4 - vertical_shift] ==\
                        self.grid[horizontal_shift + 2][3 - vertical_shift] == self.grid[horizontal_shift + 3][2 - vertical_shift] != 0:
                    return True
        return False


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
        if not self.board.column_filled(column):
            self.board.add_disk(column, self.current_player())
            self.handle_turn()

    def click(self, event):
        if self.human_turn:
            column = event.x // row_width
            self.move(column)

    def ai_turn(self, ai_level):
        Thread(target=alpha_beta_decision, args=(self.board, self.turn, ai_level, self.ai_move, self.current_player(),)).start()
        self.ai_wait_for_move()

    def ai_wait_for_move(self):
        if not self.ai_move.empty():
            self.move(self.ai_move.get())
        else:
            window.after(100, self.ai_wait_for_move)

    def handle_turn(self):
        self.human_turn = False
        if self.board.check_victory():
            information['fg'] = 'red'
            information['text'] = "Player " + str(self.current_player()) + " wins !"
            return
        elif self.turn >= 42:
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


game = Connect4()

# Graphical settings
width = 700
row_width = width // 7
row_height = row_width
height = row_width * 6
row_margin = row_height // 10

window = tk.Tk()
window.title("Connect 4")
canvas1 = tk.Canvas(window, bg="blue", width=width, height=height)

# Drawing the grid
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

# Mouse handling
canvas1.bind('<Button-1>', game.click)

window.mainloop()
