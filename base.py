import chess
import chess.svg
import chess.pgn
from PIL import Image, ImageTk
import tkinter as tk
import math
import random
import json
import glob
field_size = 100

def field_coordinates_to_index(x, y, white_to_move):
    file = x
    rank   = 7-y

    if not white_to_move:
        file = 7-file
        rank   = 7-rank

    return file+8*rank

def load_piece_images(field_size):
    ret         = dict()
    king        = r"resources/whiteking.png"
    ret["K"]    = ImageTk.PhotoImage(Image.open(king).resize((field_size, field_size)))
    pawn        = r"resources/whitepawn.png"
    ret["P"]    = ImageTk.PhotoImage(Image.open(pawn).resize((field_size, field_size)))
    knight      = r"resources/whiteknight.png"
    ret["N"]    = ImageTk.PhotoImage(Image.open(knight).resize((field_size, field_size)))
    bishop      = r"resources/whitebishop.png"
    ret["B"]    = ImageTk.PhotoImage(Image.open(bishop).resize((field_size, field_size)))
    rook        = r"resources/whiterook.png"
    ret["R"]    = ImageTk.PhotoImage(Image.open(rook).resize((field_size, field_size)))
    queen       = r"resources/whitequeen.png"
    ret["Q"]    = ImageTk.PhotoImage(Image.open(queen).resize((field_size, field_size)))

    king        = r"resources/blackking.png"
    ret["k"]    = ImageTk.PhotoImage(Image.open(king).resize((field_size, field_size)))
    pawn        = r"resources/blackpawn.png"
    ret["p"]    = ImageTk.PhotoImage(Image.open(pawn).resize((field_size, field_size)))
    knight      = r"resources/blackknight.png"
    ret["n"]    = ImageTk.PhotoImage(Image.open(knight).resize((field_size, field_size)))
    bishop      = r"resources/blackbishop.png"
    ret["b"]    = ImageTk.PhotoImage(Image.open(bishop).resize((field_size, field_size)))
    rook        = r"resources/blackrook.png"
    ret["r"]    = ImageTk.PhotoImage(Image.open(rook).resize((field_size, field_size)))
    queen       = r"resources/blackqueen.png"
    ret["q"]    = ImageTk.PhotoImage(Image.open(queen).resize((field_size, field_size)))
    return ret

class ChessCanvas(tk.Canvas):
    def __init__(self, base, field_size, board):
        super().__init__(base, height=8*field_size, width=8*field_size)

        self.ims = dict()

        self.ims = load_piece_images(field_size)

        self.field_size = field_size
        self.event_listeners = []

        self.set_new_board(board)

    def push_move(self, move):
        self.board.push_san(move)
        self.draw()

    def set_new_board(self, board):
        self.board = board
        self.clicked_index = -1
        if board is not None:
            self.white_bottom = board.turn
        else:
            self.white_bottom = False
        self.draw()

    def draw(self, idx = None):
        if idx is None:
            self.delete("all")

        for horz_idx in range(8):
            for vert_idx in range(8):
                color = "gray"
                if ((horz_idx+vert_idx) % 2) == 0:
                    color = "white"
                field_index = field_coordinates_to_index(horz_idx, vert_idx, self.white_bottom)

                if idx is not None and idx != field_index:
                    continue
                if  self.clicked_index == field_index:
                    color = "green"

                cir = self.create_rectangle(horz_idx*field_size, vert_idx*field_size, (horz_idx+1)*field_size, (vert_idx+1)*field_size, outline=color)
                self.itemconfig(cir, fill=color)

                if self.board is not None:
                    piece = self.board.piece_at(field_index)
                    if piece is not None:
                        piece = piece.symbol()

                    if piece in self.ims:
                        self.create_image(field_size*horz_idx, field_size*vert_idx, image=self.ims[piece], anchor="nw")
    

            

    def click_callback(self, event):
        x = math.floor(event.x/self.field_size)
        y = math.floor(event.y/self.field_size)

        index = field_coordinates_to_index(x, y, self.white_bottom)

        if self.clicked_index != index and self.clicked_index > -1:
            prev_index = self.clicked_index
            self.clicked_index = -1
            for listener in self.event_listeners:
                listener.handle(prev_index, index)
            self.draw(prev_index)
        else:
            if index == self.clicked_index:
                self.clicked_index = -1
            else:
                self.clicked_index = index

            self.draw(index)

    def register_listener(self, listener):
        self.event_listeners.append(listener)

class ChessExercise():
    def __init__(self, input_dict):
        self.fen = input_dict["fen"]
        self.bestmove = input_dict["bestmove"]

    def check_move(self, move):
        return self.bestmove == move

    def get_fen(self):
        return self.fen

class PgnExercise():
    def __init__(self, path):
        self.path = path
        with open(self.path) as pgn:
            self.game = chess.pgn.read_game(pgn)
        self.index = 0
        self.moves = [str(move) for move in self.game.mainline_moves()]

    def check_move(self, move):
        ret = self.moves[self.index] == move
        if ret:
            self.index =         self.index +2
        return ret
    
    def check_success(self):
        return self.index > len(self.moves)

    def get_fen(self):
        with open(self.path) as pgn:
            self.game = chess.pgn.read_game(pgn)
        board = self.game.board()
        idx = 0
        for move  in self.game.mainline_moves():
            if idx >= self.index:
                break
            idx = idx+1
            board.push(move)
        
        return board.fen()

class ChessExerciseManager():
    def __init__(self, root, exercise_list):
        self.chess_canvas = ChessCanvas(root, field_size, None)
        self.chess_canvas .bind("<Button-1>", self.chess_canvas .click_callback)
        self.chess_canvas .pack()
        self.exercises = exercise_list
        self.chess_canvas .register_listener(self)
        self.index = len(self.exercises)-1
        self.start_new_exercise()
        

    def start_new_exercise(self):
        self.exercise = PgnExercise(random.choice(self.exercises))  #ChessExercise(self.exercises[self.index]) 
        #self.index = self.index-1
        self.chess_canvas.set_new_board(chess.Board(self.exercise.get_fen()))

    def handle(self, source, target):
        source_file = chr(ord('a')+(source % 8))
        source_rank = math.floor(source/8)+ 1

        target_file = chr(ord('a')+(target % 8))
        target_rank = math.floor(target/8) + 1

        move = f"{source_file}{source_rank}{target_file}{target_rank}"

        if self.exercise.check_move(move):
            print("SUCCESS")
            self.chess_canvas.set_new_board(chess.Board(self.exercise.get_fen()))
            #self.chess_canvas.push_move(move)
            if self.exercise.check_success():
                print("FINISHED EXERCISE")
                self.start_new_exercise()
        else:
            print("FAILURE")

root = tk.Tk()

exercise_list = ["pgn/white/four_knights/other/4Bb4_crazy.pgn"] # glob.glob("pgn/**/*.pgn", recursive=True) # #glob.glob("pgn/**/*.pgn", recursive=True) #

manager = ChessExerciseManager(root, exercise_list)

root.mainloop()





"""for horz_idx in range(8):
    for vert_idx in range(8):
        color = "black"
        if ((horz_idx+vert_idx) % 2) == 0:
            color = "white"
        cir = canvas.TKCanvas.create_rectangle(horz_idx*field_size, vert_idx*field_size, (horz_idx+1)*field_size, (vert_idx+1)*field_size+field_size)
        canvas.TKCanvas.itemconfig(cir, fill=color)

king = "/home/vabi/code/chessTrainer/chessTrainer/src/main/kotlin/ChessBoard/whiteking.png"
print("Adding king...")
canvas.TKCanvas.create_image(100, 100, image=ImageTk.PhotoImage(Image.open(king)), anchor="nw")


while True:      
    event, values = window.read()      
    if event == sg.WIN_CLOSED:      
        break
    print("Updating")"""
