from fileinput import filename
from operator import xor
from PyQt5.QtWidgets import QMainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import * 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
from PyQt5.QtWidgets import QMessageBox

from json import JSONEncoder
import pickle

from functools import partial
import chess, chess.engine
from playsound import playsound
import threading
import json
from ui_elements import Piece, ScrollLabel, EngineLabel, CSquare, EngineThread, promotionUI, PrefWindow
from book_class import Trie
sq_size = 60
x_offset = 5
y_offset = 22

board_files = ['blue', 'blue2', 'canvas', 'green', 'grey','horsey', 'leather','maple', 'maple2', 'marble', 'marble2', 'metal','newspaper', 'olive', 'pink','purple','wood','wood2', 'wood3', 'wood4']
piece_files = ['alpha','california','cardinal','chess7','chessnut','companion','dubrovny','fantasy','fresca' ,'gioco','governor','horsey','icpieces','kosal' ,'leipzig','libra','maestro','merida','pirouetti','pixel','reillycraig','riohacha','spatial','staunty','tatiana']

files = ["A", "B", "C", "D", "E", "F", "G", "H"]
chess_pieces = ["b", "k", "n", "p", "q", "r", "B", "K", "N", "P", "Q", "R"]
pieces = ["bB", "bK", "bN", "bP", "bQ", "bR", "wB", "wK", "wN", "wP", "wQ", "wR"]

IMAGES = {}

def load_images():
    pieces = ["bB", "bK", "bN", "bP", "bQ", "bR", "wB", "wK", "wN", "wP", "wQ", "wR"]
    IMAGES['pieces'] = {}
    for name in piece_files:
        IMAGES['pieces'][name] = {}
        for piece in pieces:
            IMAGES['pieces'][name][piece] = f'UI/pieces/{name}/{piece}.png' 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.title = "Untitled.pkl"
        self.path = ""
        self.setWindowTitle("Project C - " + self.title)
        self.setGeometry(0, 0, 1230, 630)
        
        # self.setWindowIcon(QIcon("UI/icon.ico"))
        load_images()
        self.setAcceptDrops(True)
        self.init_menubar()
        self.translate_menubar()
        

        self.is_user_white = True
        self.colors_default()

    
        self.board_colors(self.board_pref)
        self.pgn = ""
        self.board = chess.Board()
        self.squares = {}
        self.clicked = False
        self.clicked_square = None
        self.highlighted_squares = []
        self.pieces = []
        self.trie = Trie()  

        self.training = False
        self.i = 0
        self.reps = 3
        self.accuracy = 0
        self.played_moves = 0
        self.mistakes = 0 

        self.to_train = []
        self.correct_move = ''
        self.starting_pos = []
        
        self.engine_running = False
        self.engine_thread = None
        self.engine = chess.engine.SimpleEngine.popen_uci("engines/stockfish_15_x64_avx2.exe")

        self.ui_components()
    
    

    def closeEvent(self, event):

        msgBox = QMessageBox()
        reply = msgBox.question(
            None,
            "Window Close",
            "Save Changes?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setDefaultButton(QMessageBox.Cancel)
        
        if reply == QMessageBox.No:
            self.engine.quit()
            event.accept
        elif reply == QMessageBox.Yes:
            self.engine.quit()
            if self.title == "Untitled.pkl":
                options = QFileDialog.Options()
                options |= QFileDialog.DontUseNativeDialog
                fileName, _ = QFileDialog.getSaveFileName(None,"Save As","","Pickle File (*.pkl)", options=options)
                if fileName:
                    if fileName.endswith(".pkl"):
                        fileName = self.path
                    else:
                        fileName += '.pkl'
                    self.path = fileName
                    self.title = fileName.split("/")[len(fileName.split("/"))-1]
                    self.setWindowTitle("Project C - " + self.title)
                    with open(fileName, 'wb') as f:
                        pickle.dump(self.trie.root, f)
            event.accept()
        else:
            event.ignore()
    
    def dragEnterEvent(self, event):
        stream = QtCore.QDataStream(event.mimeData().data('myApp/QtWidget'))
        objectName = stream.readQString()
        widget = self.findChild(QtWidgets.QWidget, objectName)
        if not widget:
            return

        if event.mimeData().hasFormat('myApp/QtWidget'):
                    
            if event.pos().x() > x_offset and event.pos().x() < 480 and event.pos().y() > y_offset and event.pos().y() < 480+ y_offset:
                event.accept()
            else:
                opacity_effect = QGraphicsOpacityEffect()
                opacity_effect.setOpacity(1)
                widget.setGraphicsEffect(opacity_effect)
    
    def dropEvent(self, event):
        files = ["a", "b", "c", "d", "e", "f", "g", "h"]
        stream = QtCore.QDataStream(event.mimeData().data('myApp/QtWidget'))
        objectName = stream.readQString()
        widget = self.findChild(QtWidgets.QWidget, objectName)
        if not widget:
            return
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(1)
        widget.setGraphicsEffect(opacity_effect)
        i_x = widget.x
        i_y = widget.y
        
        x = int((event.pos().x() - x_offset )/60)
        y = int((event.pos().y() - y_offset)/60)
        
        if x not in range(0,8) or y not in range(0,8):
            return
        if not self.is_user_white:
            x = 7-x
            y = 7-y
            i_x = 7 - i_x
            i_y = 7 - i_y
        piece = widget.piece[:-4]
        piece = piece[len(piece)-2:len(piece):]
        
        i_coords = files[i_x] + str(7- i_y+ 1)
        f_coords = files[x] + str(7- y + 1)
        
        move = i_coords + f_coords
        if piece == 'wP' and i_y == 1 and y == 0:
            m = move + 'q'
            if chess.Move.from_uci(m) in self.board.legal_moves:
                p_UI = promotionUI(self,x,self.is_user_white, move)
        
        if piece == 'bP' and i_y == 6 and y == 7:
            m = move + 'q'
            if chess.Move.from_uci(m) in self.board.legal_moves:
                # print("black_promotes")
                p_UI = promotionUI(self,x,self.is_user_white, move)
        try:
            if chess.Move.from_uci(move) in self.board.legal_moves:

                move_ob = chess.Move.from_uci(move)
                san = self.board.san(move_ob)
                if not self.training:
                    self.play_san(san)
                    widget.move(QPoint(x*sq_size + x_offset,y*sq_size + y_offset))
                else:
                    # print(san, self.correct_move)
                    self.play_training(san)
        except ValueError:
            pass
    def play_training(self, san):
        if san == self.correct_move:
            self.played_moves += 1
            self.play_san(san)
            self.i += 1
            # print("to_train pgn: ", self.to_train[0].pgn)

            if self.i == len(self.to_train[0].pgn):
                
                args = 'sounds/check_sound.wav'
                threading.Thread(target=playsound, args=(args,), daemon=True).start()
                
                self.to_train[0].reps += 1
                if self.to_train[0].reps == 1:
                    self.to_train[0].trained = True
                    self.to_train.pop(0)
                self.pgn = self.starting_pos
                self.pgn = (" ").join(self.pgn) + " "
                # print(self.pgn)
                if self.to_train == []:
                    # print("All variations are completed")
                    self.pgn = self.starting_pos
                    self.pgn = (" ").join(self.pgn) + " "
                    self.board = chess.Board()
                    for move in self.starting_pos:
                            self.board.push_san(move)
                    self.training = False
                    self.redraw_board()
                    self.update_pgn()
                    
                    self.update_candidates()
                    msgBox = QMessageBox()
                    if self.played_moves != 0:
                        accuracy = int((self.played_moves - self.mistakes)* 100/self.played_moves)
                    else:
                        accuracy = 0
                    reply = msgBox.question(
                        None,
                        "Training Completed",
                        f"Completed all variations in this line. \n\nPlayed Moves: {self.played_moves}\nAccuracy: {accuracy}",
                        QMessageBox.Ok
                    )
                    msgBox.setIcon(QMessageBox.Information)
                    msgBox.setDefaultButton(QMessageBox.Ok)
                else:
                    self.board = chess.Board()
                    for move in self.starting_pos:
                        self.board.push_san(move)
                    self.i  = len(self.starting_pos)
                    if not xor(self.board.turn , not self.is_user_white):
                        self.play_san(self.to_train[0].pgn[self.i])
                        self.i +=1
                    self.redraw_board()
                    self.correct_move = self.to_train[0].pgn[self.i]
                    # print("waiting for:" , self.to_train[0].pgn[self.i])
                    self.update_candidates()
            else:
                # print("play:" ,self.to_train[0].pgn[self.i])
                self.play_san(self.to_train[0].pgn[self.i])
                self.i += 1
                if self.i == len(self.to_train[0].pgn):
                    args = 'sounds/check_sound.wav'
                    threading.Thread(target=playsound, args=(args,), daemon=True).start()

                    self.to_train[0].reps += 1
                    if self.to_train[0].reps == 1:
                        self.to_train[0].trained = True
                        self.to_train.pop(0)
                    self.pgn = self.starting_pos
                    self.pgn = (" ").join(self.pgn) + " "
                    if self.to_train == []:
                        # print("All variations are completed")
                        self.pgn = self.starting_pos
                        self.pgn = (" ").join(self.pgn) + " "
                        self.board = chess.Board()
                        for move in self.starting_pos:
                            self.board.push_san(move)
                        self.training = False
                        self.redraw_board()
                        self.update_pgn()
                        self.update_candidates()
                        msgBox = QMessageBox()
                        if self.played_moves != 0:
                            accuracy = int((self.played_moves - self.mistakes)* 100/self.played_moves)
                        else:
                            accuracy = 0
                        reply = msgBox.question(
                            None,
                            "Training Completed",
                            f"Completed all variations in this line. \nPlayed Moves: {self.played_moves}\nAccuracy: {accuracy}",
                            QMessageBox.Ok
                        )
                        msgBox.setIcon(QMessageBox.Information)
                        msgBox.setDefaultButton(QMessageBox.Ok)
                    else:
                        self.board = chess.Board()
                        for move in self.starting_pos:
                            self.board.push_san(move)
                        self.i  = len(self.starting_pos)
                        if not xor(self.board.turn , not self.is_user_white):
                            self.play_san(self.to_train[0].pgn[self.i])
                            self.i +=1
                        self.redraw_board()
                        self.correct_move = self.to_train[0].pgn[self.i]
                        # print("waiting for:" , self.to_train[0].pgn[self.i])
                        self.update_candidates()
                else:
                    self.correct_move = self.to_train[0].pgn[self.i]
        else:
            self.to_train[0].reps = 1-self.reps
            self.mistakes += 1
            args = 'sounds/err.wav'
            threading.Thread(target=playsound, args=(args,), daemon=True).start()

    def colors_default(self):
        self.modeselect_color = "#161428" 
        self.background_color = '#060519'
        
        self.board_pref = "Blue"
        self.piece_pref = "cardinal"

        self.sq_light_color = '#F0D9B5'
        self.sq_dark_color = '#B58863'

        self.move_sq_light_color = '#E8E18E'
        self.move_sq_dark_color = '#B8AF4E'

        self.comment_color = '#b9d6e8'
        self.comment_text_color = 'black'

        self.move_list_color = '#4790c0'
        self.move_list_text_color = 'white'

        self.candidates_color = '#4790c0'
        

    def init_menubar(self):
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuCommands = QtWidgets.QMenu(self.menubar)
        self.menuCommands.setObjectName("menuCommands")
        self.menuPGN = QtWidgets.QMenu(self.menubar)
        self.menuPGN.setObjectName("menuPGN")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        self.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)
        self.Open = QtWidgets.QAction(self)
        self.Open.setObjectName("Open")
        self.New = QtWidgets.QAction(self)
        self.New.setObjectName("New")
        self.Program_Preferences = QtWidgets.QAction(self)
        self.Program_Preferences.setObjectName("Program_Preferences")
        self.Flip_Board = QtWidgets.QAction(self)
        self.Flip_Board.setObjectName("Flip_Board")
        self.Training = QtWidgets.QAction(self)
        self.Training.setObjectName("Training")
        self.Stop_Training = QtWidgets.QAction(self)
        self.Stop_Training.setObjectName("Stop_Training")
        self.Reset_Training = QtWidgets.QAction(self)
        self.Reset_Training.setObjectName("Reset_Training")
        self.Import_PGN = QtWidgets.QAction(self)
        self.Import_PGN.setObjectName("Import_PGN")
        self.Save = QtWidgets.QAction(self)
        self.Save.setObjectName("Save")
        self.SaveAs = QtWidgets.QAction(self)
        self.SaveAs.setObjectName("Save")

        self.menuFile.addAction(self.New)
        self.menuFile.addAction(self.Open)
        self.menuFile.addAction(self.Save)
        self.menuFile.addAction(self.SaveAs)

        self.menuEdit.addAction(self.Program_Preferences)
        self.menuCommands.addAction(self.Flip_Board)
        self.menuCommands.addSeparator()
        self.menuCommands.addAction(self.Training)
        self.menuCommands.addAction(self.Stop_Training)
        self.menuCommands.addAction(self.Reset_Training)
        self.menuPGN.addAction(self.Import_PGN)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuCommands.menuAction())
        self.menubar.addAction(self.menuPGN.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        self.menubar.setStyleSheet("background: white")

    def translate_menubar(self):
        _translate = QtCore.QCoreApplication.translate
        
        self.menuFile.setTitle(_translate(self.title, "File"))
        self.menuEdit.setTitle(_translate(self.title, "Edit"))
        self.menuCommands.setTitle(_translate(self.title, "Commands"))
        self.menuPGN.setTitle(_translate(self.title, "PGN"))
        self.menuHelp.setTitle(_translate(self.title, "Help"))
        self.Open.setText(_translate(self.title, "Open"))
        self.Open.setShortcut(_translate(self.title, "Ctrl+O"))
        self.New.setText(_translate(self.title, "New"))
        self.New.setShortcut(_translate(self.title, "Ctrl+N"))
        self.Program_Preferences.setText(_translate(self.title, "Program Preferences"))
        self.Program_Preferences.setShortcut(_translate(self.title, "Ctrl+I"))
        self.Flip_Board.setText(_translate(self.title, "Flip Board"))
        self.Flip_Board.setShortcut(_translate(self.title, "Ctrl+F"))
        self.Training.setText(_translate(self.title, "Training"))
        self.Training.setShortcut(_translate(self.title, "Ctrl+T"))
        self.Stop_Training.setText(_translate(self.title, "Stop Training"))
        self.Stop_Training.setShortcut(_translate(self.title, "Shift+S"))
        self.Reset_Training.setText(_translate(self.title, "Reset Training"))

        self.Reset_Training.setShortcut(_translate(self.title, "Ctrl+R"))
        self.Import_PGN.setText(_translate(self.title, "Import PGN"))
        self.Import_PGN.setShortcut(_translate(self.title, "Ctrl+P"))
        self.Save.setText(_translate(self.title, "Save"))
        self.Save.setShortcut(_translate(self.title, "Ctrl+S"))
        self.SaveAs.setText(_translate(self.title, "Save As"))
        self.SaveAs.setShortcut(_translate(self.title, "Ctrl+Shift+S"))

        def Flip(self):
            self.is_user_white = not self.is_user_white
            self.redraw_board()
        self.Flip_Board.triggered.connect(lambda: Flip(self) )
        def Train(self):
            self.accuracy = 0
            self.played_moves = 0
            self.mistakes = 0 
            # print(self.pgn)
            arr = self.pgn.split(" ")
            while "" in arr:
                arr.pop(arr.index(""))
            stack = self.trie.get_lines(arr)
            to_train = []
            for node in stack:
                if node.trained == False:
                    to_train.append(node)
            if to_train == []:
                # print("All variations are completed in this line")
                msgBox = QMessageBox()
                self.training = False
                if self.played_moves != 0:
                        accuracy = int((self.played_moves - self.mistakes)* 100/self.played_moves)
                else:
                    accuracy = 0
                reply = msgBox.question(
                    None,
                    "Training Completed",
                    f"Completed all variations in this line. \nPlayed Moves: {self.played_moves}\nAccuracy: {accuracy}",
                    QMessageBox.Ok
                )
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setDefaultButton(QMessageBox.Ok)
                
                return

            self.training = True
            try:
                self.engine_thread.kill.set()
            except AttributeError:
                pass
            self.engine_running = False
            self.starting_pos = arr
            self.to_train = to_train
            self.i = len(arr)
            node = to_train[0]
            line = node.pgn
            if len(line) == 0:
                self.training = False
                # print("Nothing to train")
                msgBox = QMessageBox()
                reply = msgBox.question(
                    None,
                    "Training",
                    "Nothing to train.",
                    QMessageBox.Ok
                )
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setDefaultButton(QMessageBox.Ok)
            else:
                board = chess.Board()
                for move in arr:
                    board.push_san(move)
                self.i  = len(arr)
                self.board = board
                if not xor(board.turn , not self.is_user_white):
                    self.play_san(line[self.i])
                    self.i +=1
                self.correct_move = line[self.i]
                # print("waiting for:" , line[self.i])
                self.update_candidates()
        self.Training.triggered.connect(lambda: Train(self))

        def Train_Stop(self):
            self.training = False
            self.update_candidates()    
        self.Stop_Training.triggered.connect(lambda: Train_Stop(self))

        def Train_Reset(self):
            if not self.training:
                stack = self.trie.get_lines([])
                for node in stack:
                    node.trained = False
                    node.reps = 0
                msgBox = QMessageBox()
                reply = msgBox.question(
                    None,
                    "Reset Training",
                    "Training Reset for this file",
                    QMessageBox.Ok
                )
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setDefaultButton(QMessageBox.Ok)
            else:
                msgBox = QMessageBox()
                reply = msgBox.question(
                    None,
                    "Reset Training",
                    "Can't Reset While Training",
                    QMessageBox.Ok
                )
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setDefaultButton(QMessageBox.Ok)
        self.Reset_Training.triggered.connect(lambda: Train_Reset(self))
        
        def edit_pref(self):
            self.edit = PrefWindow(self)
        self.Program_Preferences.triggered.connect(lambda: edit_pref(self))

        def new_pkl(self):
            self.pgn = ''
            board= chess.Board()
            self.board = board
            self.redraw_board()
            self.update_candidates()
            self.update_pgn()

            msgBox = QMessageBox()
            reply = msgBox.question(
                None,
                "Window Close",
                "Save Changes?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setDefaultButton(QMessageBox.Cancel)
            
            if reply == QMessageBox.No:
                self.trie = Trie()
                self.title = "Untitled.pkl"
                self.setWindowTitle(self.title)
            elif reply == QMessageBox.Yes:
                if self.title == "Untitled.pkl":
                    options = QFileDialog.Options()
                    options |= QFileDialog.DontUseNativeDialog
                    fileName, _ = QFileDialog.getSaveFileName(None,"Save As","","Pickle File (*.pkl)", options=options)
                    if fileName:
                        if fileName.endswith(".pkl"):
                            fileName = self.path
                        else:
                            fileName += '.pkl'
                        self.path = fileName
                        self.title = fileName.split("/")[len(fileName.split("/"))-1]
                        self.setWindowTitle("Project C - " + self.title)
                else:
                    fileName = self.path
                    
                with open(fileName, 'wb') as f:
                    pickle.dump(self.trie.root, f)
                self.trie = Trie()
                self.title = "Untitled.pkl"
                self.setWindowTitle(self.title)
            self.update_candidates()
        self.New.triggered.connect(lambda: new_pkl(self))

        def open_pkl(self):
            self.pgn = ''
            board= chess.Board()
            self.board = board
            self.redraw_board()
            self.update_candidates()
            self.update_pgn()

            msgBox = QMessageBox()
            reply = msgBox.question(
                None,
                "Window Close",
                "Save Changes?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setDefaultButton(QMessageBox.Cancel)
            
            if reply == QMessageBox.No:
                pass
            elif reply == QMessageBox.Yes:
                if self.title == "Untitled.pkl":
                    options = QFileDialog.Options()
                    options |= QFileDialog.DontUseNativeDialog
                    fileName, _ = QFileDialog.getSaveFileName(None,"Save As","","Pickle File (*.pkl)", options=options)
                    if fileName:
                        if fileName.endswith(".pkl"):
                            fileName = self.path
                        else:
                            fileName += '.pkl'
                        self.path = fileName
                        self.title = fileName.split("/")[len(fileName.split("/"))-1]
                        self.setWindowTitle("Project C - " + self.title)
                else:
                    fileName = self.path
                    
                with open(fileName, 'wb') as f:
                    pickle.dump(self.trie.root, f)
                self.trie = Trie()
                self.path = ""
                self.title = "Untitled.pkl"
                self.setWindowTitle(self.title)
            if reply == QMessageBox.Cancel:
                pass
            else:
                options = QFileDialog.Options()
                options |= QFileDialog.DontUseNativeDialog
                fileName, _ = QFileDialog.getOpenFileName(None,"Open", "","Pickle Files (*.pkl)", options=options)
                if fileName:
                    # print(fileName)
                    with open(fileName, 'rb') as f:
                        self.trie = Trie()
                        self.trie.root = pickle.load(f)
                    self.update_candidates()
                    self.path = fileName
                    self.title = fileName.split("/")[len(fileName.split("/"))-1]
                    self.setWindowTitle("Project C - " + self.title)
                    self.update_candidates()
            
        self.Open.triggered.connect(lambda: open_pkl(self))

        def save_pkl(self):
            if self.title == "Untitled.pkl":
                    options = QFileDialog.Options()
                    options |= QFileDialog.DontUseNativeDialog
                    fileName, _ = QFileDialog.getSaveFileName(None,"Save As","","Pickle File (*.pkl)", options=options)
                    if fileName:
                        if fileName.endswith(".pkl"):
                            fileName = self.path
                        else:
                            fileName += '.pkl'
                        self.path = fileName
                        self.title = fileName.split("/")[len(fileName.split("/"))-1]
                        self.setWindowTitle("Project C - " + self.title)
            else:
                    fileName = self.path      
            if not fileName == '':
                with open(fileName, 'wb') as f:
                    pickle.dump(self.trie.root, f)
        self.Save.triggered.connect(lambda: save_pkl(self))
        
        def save_as_pkl(self):
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getSaveFileName(None,"Save As","","Pickle File (*.pkl)", options=options)
            if fileName:
                if fileName.endswith(".pkl"):
                    pass
                else:
                    fileName += '.pkl'
                self.path = fileName
                self.title = fileName.split("/")[len(fileName.split("/"))-1]
                self.setWindowTitle("Project C - " + self.title)
                if not fileName == '':
                    with open(fileName, 'wb') as f:
                        pickle.dump(self.trie.root, f)
        self.SaveAs.triggered.connect(lambda: save_as_pkl(self))

        def d_import_pgn(self):
            file , check = QFileDialog.getOpenFileName(None, "Import PGN",
                                                    "", "PGN Files (*.pgn)")
            if check:
                # print(file)
                self.trie.import_pgn(file)
                self.update_candidates()
        self.Import_PGN.triggered.connect(lambda: d_import_pgn(self))

    def update_candidates(self):
        self.listWidget.clear()
        if self.training == False:
            try:
                while True:
                    self.listWidget.itemClicked.disconnect()
                    self.listWidget.itemDoubleClicked.disconnect()
            except TypeError:
                pass     
            
            pgn = str(self.pgn).split(" ")
            
            while "" in pgn:
                pgn.pop(pgn.index(""))
            
            candidates = self.trie.list_child(pgn)
            
            def candidate_clicked(window, item):
                    window.play_san(item.text())
                    window.update_candidates()
            
            if not candidates == []:
                for key_string in candidates:
                    new = QListWidgetItem(key_string, self.listWidget)
                    

                par_candidate = partial(candidate_clicked,self)
                self.listWidget.itemClicked.connect(par_candidate)
                def delete(window, item):
                    pgn = str(window.pgn).split(" ")
                    while "" in pgn:
                        pgn.pop(pgn.index(""))
                    window.trie.delete(pgn, item.text())

                    window.update_candidates()
                p= partial(delete, self)
                self.listWidget.itemDoubleClicked.connect(p)

        if self.engine_running == True:
            self.engine_thread.kill.set()
            if not self.training:
                self.engine_thread = EngineThread(self)
                self.engine_thread.start()
                self.engine_running = True
        

    def board_colors(self, board_pref):
        if board_pref == 'Gray':
                self.sq_light_color = '#D8D8D8'
                self.sq_dark_color = '#808080'
                self.move_sq_light_color = '#e0e0ad'
                self.move_sq_dark_color = '#999966'

        if board_pref == 'Green':
            self.sq_light_color = '#daf1e3'
            self.sq_dark_color = '#3a7859'
            self.move_sq_light_color = '#bae58f'
            self.move_sq_dark_color = '#6fbc55'

        if board_pref == 'Blue':
            self.sq_light_color = '#b9d6e8'
            self.sq_dark_color = '#4790c0'
            self.move_sq_light_color = '#d2e4ba'
            self.move_sq_dark_color = '#91bc9c'
           
        if board_pref == 'Brown':
            self.sq_light_color = '#F0D9B5'
            self.sq_dark_color = '#B58863'
            self.move_sq_light_color = '#E8E18E'
            self.move_sq_dark_color = '#B8AF4E'
    def create_board(self):
        board = self.board
        for i in range(0, 8, 1):
            for j in range(0, 8, 1):

                coords = files[i] + str(7-j+1)
                
                square = CSquare(i,j,self) 
                self.squares[(i,j)] = square
        for i in range(0, 8, 1):
            for j in range(0, 8, 1):
                
                coords = files[i] + str(7-j+1)
               
                if piece := board.piece_at(chess.__getattribute__(coords)):
                    index = chess_pieces.index(str(piece))
                    if not self.is_user_white:
                        j = 7-j
                        i= 7- i 
                    piece_image = IMAGES['pieces'][self.piece_pref][pieces[index]]
                    piece_view = Piece(i,j,piece_image, self)
                    self.pieces.append(piece_view)

    def redraw_board(self):
        for sq in self.highlighted_squares:
                sq.highlight(False)
        for piece in self.pieces:
            piece.deleteLater()
        self.pieces = []
        
        for i in range(0, 8, 1):
            for j in range(0, 8, 1):
                coords = files[i] + str(7-j+1)
                if piece := self.board.piece_at(chess.__getattribute__(coords)):
                    index = chess_pieces.index(str(piece))
                    if not self.is_user_white:
                        j = 7-j
                        i = 7-i
                    
                    piece_image = IMAGES['pieces'][self.piece_pref][pieces[index]]
                    piece_view = Piece(i,j,piece_image, self)
                    self.pieces.append(piece_view)

                    if not self.is_user_white: #revert i and j to the original values so that they don't ruin the loop
                        j = 7-j
                        i = 7-i 
                    
    def update_pgn(self):
        pgn = self.pgn.split(" ")
        while "" in pgn:
                pgn.pop(pgn.index(""))
        white = True
        white_moves = ''
        black_moves = ''
        counter = 1
        for move in pgn:
            move = move.replace("N", "♞")
            move = move.replace("B", "♝" )
            move = move.replace("R", "♜" )
            move = move.replace("Q", "♛")
            move = move.replace("K", "♚")
            if white:
                white = False
                white_moves += f"{counter}. {move}\n"
                counter +=1
            else:
                white = True
                black_moves += move + "\n"
        
        self.wheel_white.setText(white_moves)
        self.wheel_black.setText(black_moves)
        self.scrollbar.setSliderPosition(12000000)

    def play_san(self, san: str):
            arr = str(self.pgn).split(" ")
            while "" in arr:
                arr.pop(arr.index(""))
            if not self.training:
                comment = self.comment.toPlainText()
                self.trie.save_comment(arr,comment)

            move = self.board.push_san(san)
            if "O" in san:
                    args = 'sounds/castles_sound.wav'

            elif "+" in san or "#" in san:
                args = 'sounds/check_sound.wav'
                
            elif "x" in san:
                args = 'sounds/capture_sound.wav'
                
            else:
                args = 'sounds/move1_sound.wav'
            
            threading.Thread(target=playsound, args=(args,), daemon=True).start()
            self.redraw_board()
            self.pgn += san + " "
            self.update_pgn()
            arr = str(self.pgn).split(" ")
            while "" in arr:
                arr.pop(arr.index(""))
            if not self.training:
                self.trie.insert(arr)
            
            if not self.training:
                comment = self.trie.load_comment(arr)
                self.comment.setMarkdown(comment)
            else:
                self.comment.setMarkdown("")

            uci = move.uci()
            alpha = 'abcdefgh'
            i_x = alpha.index(uci[0])
            i_y = 7 - (int(uci[1]) -1)

            x = alpha.index(uci[2])
            y = 7 - (int(uci[3]) -1)
            # print(i_x , i_y)
            # print(x,y)

            if not self.is_user_white:
                    x = 7-x
                    y = 7-y
                    i_x = 7 - i_x
                    i_y = 7 - i_y
            
            square1 = self.squares[(i_x,i_y)]
            square1.highlight(True)
            square2 = self.squares[(x,y)]
            square2.highlight(True)
            self.highlighted_squares = [square1, square2]
            self.update_candidates()
            
            

            

    def ui_components(self):
        self.setStyleSheet(f"background-color: {self.background_color};")
        self.create_board()

        self.ModeSelect = QtWidgets.QTabWidget(self)
        self.ModeSelect.setGeometry(QtCore.QRect(510, 30, 700, 590))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ModeSelect.sizePolicy().hasHeightForWidth())
        self.ModeSelect.setSizePolicy(sizePolicy)
        self.ModeSelect.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.ModeSelect.setStyleSheet(f"background-color: {self.modeselect_color}")
        self.ModeSelect.setTabPosition(QtWidgets.QTabWidget.North)
        self.ModeSelect.setElideMode(QtCore.Qt.ElideLeft)
        self.ModeSelect.setDocumentMode(False)
        self.ModeSelect.setMovable(False)
        self.ModeSelect.setTabBarAutoHide(True)
        self.ModeSelect.setObjectName("ModeSelect")
        
        self.Viewer = QtWidgets.QWidget()
        self.Viewer.setAutoFillBackground(True)
        self.Viewer.setObjectName("Viewer")
        self.comment = QtWidgets.QTextEdit(self.Viewer)
        self.comment.setGeometry(QtCore.QRect(10, 350, 680, 210))
        self.comment.viewport().setProperty("cursor", QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self.comment.setObjectName("Comment")
        self.comment.setMarkdown("")
        self.comment.setStyleSheet(f"color: {self.comment_text_color};"
                                   f"background-color: {self.comment_color}"
                        )
        font = QtGui.QFont("Calibri")
        font.setPointSize(15)
        self.comment.setFont(font)

        self.scrollbar = QScrollBar(self.Viewer)
        self.scrollbar.setGeometry((QtCore.QRect(210, 10, 10, 330)))

        self.wheel_white = ScrollLabel(self.Viewer , self)
        self.wheel_white.setText('')
        self.wheel_white.setStyleSheet(f"color: {self.move_list_text_color};"
                            f"background-color: {self.move_list_color}"
                        )
        self.wheel_white.setGeometry(QtCore.QRect(10, 10, 100, 330))
        self.wheel_white.setObjectName("whitepgnwheel")
        
        
        self.wheel_black = ScrollLabel(self.Viewer,self)
        self.wheel_black.setText('')
        self.wheel_black.setStyleSheet(f"color: {self.move_list_text_color};"
                            f"background-color: {self.move_list_color}"
                        )
        self.wheel_black.setGeometry(QtCore.QRect(110, 10, 100, 330))
        self.wheel_black.setObjectName("blackpgnwheel")

        self.listWidget = QListWidget(self.Viewer)
        self.listWidget.setGeometry(QtCore.QRect(215, 10, 420, 330))
        self.listWidget.setObjectName("candidates")
        self.listWidget.setStyleSheet("color: white;"
                            f"background-color: {self.candidates_color}")

        font = QtGui.QFont("Comic Sans MS")
        font.setPointSize(16)
        self.listWidget.setFont(font)
        
        self.ModeSelect.addTab(self.Viewer, "")
        
        self.Engine = QtWidgets.QWidget()
        self.Engine.setObjectName("Engine")
        # self.label = QtWidgets.QLabel(self.Engine)
        # self.label.setGeometry(QtCore.QRect(20, 10, 331, 31))
        # font = QtGui.QFont()
        # font.setPointSize(16)
        # self.label.setFont(font)
        # self.label.setObjectName("label")
        # self.line1 = QtWidgets.QLabel(self.Engine)
        # self.line1.setGeometry(QtCore.QRect(40, 50, 291, 16))
        # self.line1.setObjectName("line1")
        # self.line2 = QtWidgets.QLabel(self.Engine)
        # self.line2.setGeometry(QtCore.QRect(40, 70, 291, 16))
        # self.line2.setObjectName("line2")
        # self.line2_2 = QtWidgets.QLabel(self.Engine)
        # self.line2_2.setGeometry(QtCore.QRect(40, 90, 291, 16))
        # self.line2_2.setObjectName("line2_2")
        # self.textBrowser = QtWidgets.QTextBrowser(self.Engine)
        # self.textBrowser.setGeometry(QtCore.QRect(20, 120, 331, 201))
        # self.textBrowser.setObjectName("textBrowser")
        # self.ModeSelect.addTab(self.Engine, "")
        self.Database = QtWidgets.QWidget()
        self.Database.setObjectName("Database")
        self.ModeSelect.addTab(self.Database, "")

        _translate = QtCore.QCoreApplication.translate

        self.ModeSelect.setTabText(self.ModeSelect.indexOf(self.Viewer), _translate("MainWindow", "Openings Viewer"))
        # self.label.setText(_translate("MainWindow", "Engine"))
        # self.line1.setText(_translate("MainWindow", "Line 1"))
        # self.line2.setText(_translate("MainWindow", "Line 2"))
        # self.line2_2.setText(_translate("MainWindow", "Line 3"))
        # self.ModeSelect.setTabText(self.ModeSelect.indexOf(self.Engine), _translate("MainWindow", "Engine"))
        # self.ModeSelect.setTabText(self.ModeSelect.indexOf(self.Database), _translate("MainWindow", "Database"))

        # eval bar
        eval = 0
        bar_pos = int(eval*40)
        if bar_pos < -230: bar_pos = -230
        if bar_pos > 230: bar_pos = 230
        self.bar_black = QGraphicsView( self)
        self.bar_black.setGeometry(480 + 5 , 22, 10, 240-bar_pos+22 )
        self.bar_black.setStyleSheet( "background-color: black;")
                                
        self.bar_white = QGraphicsView(self)
        self.bar_white.setGeometry(480 + 5 , 22+ 240 - bar_pos, 10, 480+22 - (22+ 240 - bar_pos))
        self.bar_white.setStyleSheet("background-color: white;")

        self.bar_grey = QGraphicsView(self)
        self.bar_grey.setGeometry(480+5,240+22 - 1,10, 1 )

        self.update_candidates()

        #buttons
        def backward(window):
            if not window.training:
                arr = str(self.pgn).split(" ")
                while "" in arr:
                    arr.pop(arr.index(""))
                comment = self.comment.toPlainText()
                self.trie.save_comment(arr,comment)

                pgn = window.pgn.split(" ")
                while "" in pgn:
                    pgn.pop(pgn.index(""))
                if pgn:
                    args = 'sounds/move1_sound.wav'
                    threading.Thread(target=playsound, args=(args,), daemon=True).start()
                    pgn.pop()
                    board = chess.Board()
                    for move in pgn:
                        board.push_san(move)
                    window.board = board
                    window.redraw_board()
                    pgn = (" ").join(pgn)
                    pgn += " "
                    window.pgn = pgn
                    window.update_candidates()
                    window.update_pgn()

                    arr = str(self.pgn).split(" ")
                    while "" in arr:
                        arr.pop(arr.index(""))
                    comment = self.trie.load_comment(arr)
                    self.comment.setMarkdown(comment)
                
                else: 
                    args = 'sounds/err.wav'
                    threading.Thread(target=playsound, args=(args,), daemon=True).start()
            

                
        def f_backward(window):
            if not window.training:
                arr = str(self.pgn).split(" ")
                while "" in arr:
                    arr.pop(arr.index(""))
                comment = self.comment.toPlainText()
                self.trie.save_comment(arr,comment)
                
                window.pgn = ''
                board= chess.Board()
                window.board = board
                window.redraw_board()
                window.update_candidates()
                window.update_pgn()
                arr = str(self.pgn).split(" ")

                while "" in arr:
                    arr.pop(arr.index(""))
                comment = self.trie.load_comment(arr)
                self.comment.setMarkdown(comment)

        b = partial(backward, self)
        f_b = partial(f_backward, self)
        arrows = ['UI/arrows/reset.png', 'UI/arrows/fast-backward.png' ,'UI/arrows/backward.png','UI/arrows/forward.png','UI/arrows/fast-forward.png']
        button1 = QPushButton("", self)
        button1.setGeometry(5, 510, 91, 32)
        button1.setStyleSheet(   f"background-color: {self.sq_light_color};"
                                "color: red;"
                                f"background-image: url({arrows[0]});"
                                "background-repeat: no-repeat;"
                                "background-position: center;"
                                )
        button1.clicked.connect(f_b)
        
        
        button2 = QPushButton("", self)
        button2.setGeometry(101, 510, 91, 32)
        button2.setStyleSheet(   f"background-color:{self.sq_light_color};"
                                "color: white;"
                                f"background-image: url({arrows[1]});"
                                "background-repeat: no-repeat;"
                                "background-position: center;"
                                )
        button2.clicked.connect(f_b)

        button3 = QPushButton("", self)
        button3.setGeometry(197, 510, 91, 32)
        button3.setStyleSheet(   f"background-color: {self.sq_light_color};"
                                "color: white;"
                                f"background-image: url({arrows[2]});"
                                "background-repeat: no-repeat;"
                                "background-position: center;"
                                )
        button3.clicked.connect(b)

        button4 = QPushButton("", self)
        button4.setGeometry(293, 510, 91, 32)
        button4.setStyleSheet(   f"background-color: {self.sq_light_color};"
                                "color: white;"
                                f"background-image: url({arrows[3]});"
                                "background-repeat: no-repeat;"
                                "background-position: center;"
                                )
        button5 = QPushButton("", self)
        button5.setGeometry(389, 510, 91, 32)
        button5.setStyleSheet(   f"background-color:{self.sq_light_color};"
                                "color: white;"
                                f"background-image: url({arrows[4]});"
                                "background-repeat: no-repeat;"
                                "background-position: center;"
                                )
        def toggle_engine(window):
            if not self.training:
                if window.engine_running == False:
                    window.engine_thread = EngineThread(window)
                    window.engine_thread.start()
                    self.engine_running = True
                    window.engine_button.setText("Pause Engine")
                    
                else:
                    window.engine_thread.kill.set()
                    window.engine_running = False
                    window.engine_button.setText("Start Engine")
        
        self.engine_out = EngineLabel(self)
        self.engine_out.setGeometry(5, 550, 300, 75)
        self.engine_out.setObjectName("enginebox")
        self.engine_out.setText("")
        self.engine_out.setStyleSheet("color: black;"
                                            f"background-color: {self.sq_light_color}"
                        )

         

        p_toggle = partial(toggle_engine, self)
       
        self.engine_button =  QPushButton("Start Engine", self)
        
        self.engine_button.clicked.connect(p_toggle)
        self.engine_button.setGeometry(310, 550, 91, 32)
        self.engine_button.setStyleSheet(   f"background-color: {self.sq_light_color};"
                                "color: black;"
                                )
        
        self.eval_label = QtWidgets.QLabel(self)
        self.eval_label.setGeometry(412, 550, 70, 32)
        self.eval_label.setStyleSheet(   f"background-color: none;"
                                f"color: {self.sq_light_color};"
                                )
        self.eval_label.setText("")

        self.depth_label = QtWidgets.QLabel(self)
        self.depth_label.setGeometry(312, 586, 70, 32)
        self.depth_label.setStyleSheet(   f"background-color: none;"
                                f"color:  {self.sq_light_color};"
                                )
        self.depth_label.setText("")
        font = QtGui.QFont("Calibri")
        font.setPointSize(12)
        self.eval_label.setFont(font)
        self.depth_label.setFont(font)
        
