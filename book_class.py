
import io
from types import NoneType
import chess.pgn
import chess

def stacking(stack):
    for node in stack:
        if node.children == {}:
            pass
        else:
            stack.pop(stack.index(node))
            for child in node.children:
                stack.append(node.children[child])
                stacking(stack)
    return stack

def get_end_nodes(stack):

    for node in stack:
        # print(node)
        if type(node) is NoneType:
            pass
        elif node.variations == []:
            pass
        
        else:
            stack.pop(stack.index(node))
            for child in node.variations:
                stack.append(child)
                get_end_nodes(stack)
    return stack

class TrieNode:
    def __init__(self):
       self.children = {}
       self.pgn = []
       self.trained= False
       self.reps = 0
       self.comment = ""
       

class Trie:
    def __init__(self):
        self.root = TrieNode()
    def insert(self,pgn :list) -> None:
        cur = self.root
        line = []
        for move in pgn:
            line.append(move)
            if move not in cur.children:
                cur.children[move] = TrieNode()
                cur.children[move].pgn = line
            cur = cur.children[move]
    def save_comment(self, pgn:list, comment: str):
        cur = self.root
        for move in pgn:
            if move not in cur.children:
                print("Error, line not found")
            
            cur = cur.children[move]
        cur.comment = comment
    def load_comment(self,pgn: list) -> str:
        cur = self.root
        for move in pgn:
            if move not in cur.children:
                return ""
            cur = cur.children[move]
        return cur.comment
    def has_pgn(self, pgn: list) -> bool:
        cur = self.root

        for move in pgn:
            if move not in cur.children:
                return False
            cur = cur.children[move]
        return True
    
    def list_child(self, pgn: list) -> list:
        cur = self.root
        for move in pgn:
            if move not in cur.children:
                return []
            cur = cur.children[move]
        return cur.children
    def delete(self, pgn: list, move: str):
        cur = self.root
        for m in pgn:
            if m not in cur.children:
                return []
            cur = cur.children[m]
        
        if move in cur.children:
            cur.children.pop(move)
    
    def import_p(self, stack):
        parents = []
        
        for node in stack:
            comments = []
            pgn = str(node.move)

            while not node.parent is None:
                comments.append(node.comment)
                node = node.parent
                pgn += f" {str(node.move)}"
            comments.append(node.comment)
            arr = pgn.split(" ")
            while "" in arr:
                arr.pop(arr.index(""))
            
            arr = arr[::-1]
            comments = comments[::-1]
            
            arr.pop(0)
            pgn = arr
            # print(pgn)
            # print(comments)
            board = chess.Board()
            cur = self.root
            line = []
            if comments[0] in cur.comment:
                pass
            else:
                cur.comment += "\n" + comments[0]
            for move in pgn:
                from_uci =  chess.Move.from_uci(move)
                san = board.san(from_uci)
                board.push_san(san)
                line.append(san)
                if san not in cur.children:
                    cur.children[san] = TrieNode()
                    cur.children[san].pgn = line
                cur = cur.children[san]
                if comments[pgn.index(move)+1] in cur.comment:
                    pass
                else:
                    cur.comment += "\n" + comments[pgn.index(move)+1]
                
                

    def import_pgn(self, f):
        file = open(f)
        pgn = file.read()

        pgn = pgn.replace('[Result "*"]', '[Result ""]' )
        # print(pgn)
        pgn = pgn.split("*")

        for game in pgn:
            game_pgn = io.StringIO(game)
            first_game = chess.pgn.read_game(game_pgn)
            nodes = get_end_nodes([first_game])
            # print(nodes)
            if nodes == [None]:
                pass
            else:
                self.import_p(nodes)

    def get_lines(self, pgn: list) :
        cur = self.root
        for move in pgn:
            if move not in cur.children:
                return []
            cur = cur.children[move]
        
        stack = [cur]

        stack = stacking(stack)
        return stack
