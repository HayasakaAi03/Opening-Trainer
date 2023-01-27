from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import * 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 

from functools import partial
import threading, chess
sq_size = 60
x_offset = 5
y_offset = 22


files = ["A", "B", "C", "D", "E", "F", "G", "H"]
chess_pieces = ["b", "k", "n", "p", "q", "r", "B", "K", "N", "P", "Q", "R"]
pieces = ["bB", "bK", "bN", "bP", "bQ", "bR", "wB", "wK", "wN", "wP", "wQ", "wR"]

class EngineLabel(QScrollArea):
 
    def __init__(self, window ):
        QScrollArea.__init__(self,window)
        
        self.setWidgetResizable(True)
 
        content = QWidget(self)
        self.setWidget(content)
 
        lay = QVBoxLayout(content)
 
        self.label = QLabel(content)
 
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
 
        self.label.setWordWrap(True)
        font = QtGui.QFont("Comic Sans MS")
        font.setPointSize(9)
        self.label.setFont(font)
        lay.addWidget(self.label)
        self.setVerticalScrollBar(QtWidgets.QScrollBar(window))

    def setText(self, text):
        self.label.setText(text)
class ScrollLabel(QScrollArea):
 
    def __init__(self , parent_widget, window):
        QScrollArea.__init__(self, parent_widget)
 
        self.setWidgetResizable(True)
 
        content = QWidget(self)
        self.setWidget(content)
 
        lay = QVBoxLayout(content)
 
        self.label = QLabel(content)
 
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
 
        self.label.setWordWrap(True)
        font = QtGui.QFont("Comic Sans MS")
        font.setPointSize(9)
        self.label.setFont(font)
        lay.addWidget(self.label)
        self.setVerticalScrollBar(window.scrollbar)

    def setText(self, text):
        self.label.setText(text)

class Piece(QtWidgets.QPushButton):
    def __init__(self, i , j,piece, window):
        QPushButton.__init__(self, window, objectName = str((i,j)))
        self.piece = piece
        self.x = i
        self.y = j
        self.size = 60
        self.setStyleSheet( 
            "background-color: transparent;"
            "border: none;"
            f"background-image: url({piece});"
            )
        self.setGeometry(i* sq_size+ x_offset, j* sq_size+ y_offset, self.size, self.size)
        self.show()
        
        def clickme():
            print(i,j)
        self.clicked.connect(clickme)
    def mousePressEvent(self, event) :
        super().mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.mousePos = event.pos()
            
        elif event.button() == QtCore.Qt.RightButton:
            print(self.x, self.y)
    def update(self):
        self.setGeometry(self.x* sq_size+ x_offset, self.y* sq_size+ y_offset, self.size, self.size)
    
    def mouseReleaseEvent(self,event):
            opacity_effect = QGraphicsOpacityEffect()
            opacity_effect.setOpacity(1)
            self.setGraphicsEffect(opacity_effect)
            

    def mouseMoveEvent(self, event) :
        if event.buttons() == Qt.LeftButton:
            self.setStyleSheet( 
            "background-color: transparent;"
            "border: none;"
            f"background-image: url({self.piece});"
            )
            opacity_effect = QGraphicsOpacityEffect()
            opacity_effect.setOpacity(0.3)
            self.setGraphicsEffect(opacity_effect)
            mimeData = QtCore.QMimeData()
            byteArray = QtCore.QByteArray()
            stream = QtCore.QDataStream(byteArray, QtCore.QIODevice.WriteOnly)
            
            stream.writeQString(self.objectName())
            stream.writeQVariant(self.mousePos)
           
            mimeData.setData('myApp/QtWidget', byteArray)
            drag = QtGui.QDrag(self)
            drag.setPixmap(self.grab())
            drag.setMimeData(mimeData)
            drag.setHotSpot(self.mousePos - self.rect().topLeft())
            drag.exec_()
        
class CSquare(QtWidgets.QGraphicsView):
    def __init__(self, i , j, window):
        QGraphicsView.__init__(self, window)
        self.size = 60
        self.i = i
        self.j = j
        self.border = None
        self.color = None
        self.highlighted = False
        self.window = window
        # 

        if (i + j) % 2:
                self.color = window.sq_dark_color 
        else:
                self.color = window.sq_light_color
        self.setGeometry(i* sq_size+ x_offset, j* sq_size+ y_offset, self.size, self.size)

        self.setStyleSheet(   f"background-color: {self.color};"
                                        "color: white;"
                                        "border-style: none;"
                            )
    def highlight(self,con):
        if con:
            if (self.i + self.j) % 2:
                self.color = self.window.move_sq_dark_color  # Dark square
            else:
                self.color = self.window.move_sq_light_color
            self.setStyleSheet(   f"background-color: {self.color};"
                                            "color: white;"
                                            "border-style: none;")
        else:
            if (self.i + self.j) % 2:
                self.color = self.window.sq_dark_color  # Dark square
            else:
                    self.color = self.window.sq_light_color
            self.setStyleSheet(   f"background-color: {self.color};"
                                            "color: white;"
                                            "border-style: none;")
class EngineThread(threading.Thread):
    def __init__(self, window):
        threading.Thread.__init__(self, daemon = True )
        self.kill = threading.Event()
        self.window = window
        
    def run(self):
        self.analyze(self.window)
    def analyze(self, window):
        engine = window.engine
        board = chess.Board(self.window.board.fen())
        analysis =  engine.analyse(board, chess.engine.Limit(depth=15))
            
        move_list = analysis.get("pv")
        
        line = ''
        
        for move in move_list:
            san = board.san(move)
            board.push(move)
            line += san + " "

        eval = float(str(analysis.get("score").white()))
        eval /= 100
        
        window.eval_label.setText(str(eval))
        window.depth_label.setText(f'Depth: {analysis.get("depth")}')
        window.engine_out.label.setText(line)
    
        bar_pos = int(eval*40)
        if bar_pos < -230: bar_pos = -230
        if bar_pos > 230: bar_pos = 230
        
        window.bar_black.setGeometry(480 + 5 , 22, 10, 240-bar_pos+22 )
        window.bar_white.setGeometry(480 + 5 , 22+ 240 - bar_pos, 10, 480+22 - (22+ 240 - bar_pos))
        window.bar_grey.setGeometry(480+5,240+22 - 1,10, 1 )
                    
        if self.kill.is_set():
                window.eval_label.setText("")
                window.depth_label.setText("")
                window.engine_out.label.setText("")

class promotionUI():
    def __init__(self, window, file, color, move):
        self.board_cover = QPushButton(window)
        self.board_cover.setGeometry(x_offset,y_offset,sq_size*8 ,sq_size*8)
        self.board_cover.setStyleSheet("background-color: black")
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.3)
        self.board_cover.setGraphicsEffect(opacity_effect)
        self.board_cover.show()
        self.x = 0
        self.y = 0

        pieces = ['Q','R','B','N']
        buttons = []
        turn = window.board.turn
    
        if turn:
            for piece in pieces:
                b_image = f'UI/pieces/{window.piece_pref}/{"w"}{piece}.png'
                button = QPushButton(window)
                if color:
                    button.setGeometry(x_offset+ (file)*sq_size,y_offset+pieces.index(piece)*sq_size, sq_size, sq_size)
                else:
                    button.setGeometry(x_offset+ (7-file)*sq_size,y_offset+(7-pieces.index(piece))*sq_size, sq_size, sq_size)
                
                button.setStyleSheet( 
                                "background-color: transparent;"
                                "border: none;"
                                f"background-image: url({b_image});"
                                )
                button.show()
                buttons.append(button)

            def delete():
                self.board_cover.deleteLater()
                for button in buttons:
                    try:
                        button.deleteLater()
                    except:
                        pass
            self.board_cover.clicked.connect(delete)
            for button in buttons:
                def clicked(promUI, window, index):
                        p = pieces[index].lower()
                        m = chess.Move.from_uci(move + p) 

                        str_san = window.board.san(m)
                        
                        for button in buttons:
                            button.deleteLater()
                            
                        if not window.training:
                            window.play_san(str_san)
                        else:
                            window.play_training(str_san)
                    
                p_clicked = partial(clicked, self, window,buttons.index(button))
                button.clicked.connect(p_clicked)
        else:
            for piece in pieces:
                b_image = f'UI/pieces/{window.piece_pref}/{"b"}{piece}.png'
                button = QPushButton(window)
                if not color:
                    button.setGeometry(x_offset+ (7-file)*sq_size,y_offset+pieces.index(piece)*sq_size, sq_size, sq_size)
                else:
                    button.setGeometry(x_offset+ (file)*sq_size,y_offset+(7-pieces.index(piece))*sq_size, sq_size, sq_size)
                
                button.setStyleSheet( 
                                "background-color: transparent;"
                                "border: none;"
                                f"background-image: url({b_image});"
                                )
                button.show()
                buttons.append(button)

            def delete():
                self.board_cover.deleteLater()
                for button in buttons:
                    button.deleteLater()
            self.board_cover.clicked.connect(delete)
            for button in buttons:
                def clicked(promUI, window, index):
                        p = pieces[index].lower()
                        m = chess.Move.from_uci(move + p) 

                        str_san = window.board.san(m)
                        promUI.board_cover.deleteLater()
                        
                        for button in buttons:
                            button.deleteLater()
                        if not window.training:
                            window.play_san(str_san)
                        else:
                            window.play_training(str_san)
                    
                p_clicked = partial(clicked, self, window,buttons.index(button))
                button.clicked.connect(p_clicked)

class PrefWindow(QWidget):
    def __init__(self, parent_window):
        super(PrefWindow, self).__init__()
        self.parent_window = parent_window
        self.resize(900, 500)
        self.setWindowTitle("Edit Program Preferences")
        self.show()
        self.bg = QGraphicsView(self)
        self.bg.setGeometry(0, 0, 600, 310)
        self.bg.setStyleSheet(f"background-color: {parent_window.background_color}")
        self.bg.show()

        self.draw_board(parent_window)
        self.ui_elements(parent_window)

        
    def ui_elements(self, parent_window):
        self.modeselect = QGraphicsView(self)
        self.modeselect.setGeometry(250, 5, 350, 295)
        self.modeselect.setStyleSheet(f"background-color: {parent_window.modeselect_color}")
        self.modeselect.show()

        self.wheel_white = QGraphicsView(self.modeselect)
        self.wheel_white.setGeometry(QtCore.QRect(5, 5, 50, 165))
        self.wheel_white.setStyleSheet(f"background-color: {self.parent_window.move_list_color}" )
        self.wheel_white.show()

        self.wheel_black = QGraphicsView(self.modeselect)
        self.wheel_black.setGeometry(QtCore.QRect(55, 5, 50, 165))
        self.wheel_black.setStyleSheet(f"background-color: {self.parent_window.move_list_color}" )
        self.wheel_black.show()

        self.list_widget = QGraphicsView(self.modeselect)
        self.list_widget.setGeometry(QtCore.QRect(107, 5, 210, 165))
        self.list_widget.setStyleSheet("color: white;"
                            f"background-color: {self.parent_window.candidates_color}")
        self.list_widget.show()

        self.comment = QGraphicsView(self.modeselect)
        self.comment.setGeometry(QtCore.QRect(5, 175, 340, 105))
        self.comment.setStyleSheet(f"color: {self.parent_window.comment_text_color};"
                                   f"background-color: {self.parent_window.comment_color}"
                        )
        self.comment.show()
    def draw_board(self, parent_window):
        board = chess.Board()
        for i in range(0, 8, 1):
            for j in range(0, 8, 1):
                sq_size = 30
                x_offset = 5
                y_offset = 5
                coords = files[i] + str(7-j+1)
                square = QGraphicsView(self) 
                if (i + j) % 2:
                        color = parent_window.sq_dark_color 
                else:
                        color = parent_window.sq_light_color
                square.setGeometry(i* sq_size+ x_offset, j* sq_size+ y_offset, sq_size, sq_size)

                square.setStyleSheet(  f"background-color: {color};"
                                                "color: white;"
                                                "border-style: none;")
                square.show()
        for i in range(0, 8, 1):
            for j in range(0, 8, 1):
                
                coords = files[i] + str(7-j+1)
               
                if piece := board.piece_at(chess.__getattribute__(coords)):
                    index = chess_pieces.index(str(piece))
                    piece_image = f'UI/pieces/{parent_window.piece_pref}/{pieces[index]}.png'
                    piece_object = QGraphicsView(self) 
                    piece_object.setGeometry(i* sq_size+ x_offset, j* sq_size+ y_offset, sq_size, sq_size)
                    piece_object.setStyleSheet( 
                        f"border-image: url({piece_image});"
                        "background-color: transparent;"
                        "border: none;"
                            
                        )
                    piece_object.show()
                    