from flask import Flask, send_file, jsonify, request
import time
import random

app = Flask(__name__, static_folder='.', static_url_path='')

PIECES = ['I', 'J', 'L', 'O', 'S', 'T', 'Z']

SHAPES = {
    'I': [[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]],
    'J': [[1,0,0],[1,1,1],[0,0,0]],
    'L': [[0,0,1],[1,1,1],[0,0,0]],
    'O': [[1,1],[1,1]],
    'T': [[0,1,0],[1,1,1],[0,0,0]],
    'S': [[0,1,1],[1,1,0],[0,0,0]],
    'Z': [[1,1,0],[0,1,1],[0,0,0]]
}

class TetrisGame:
    def __init__(self):
        self.rows = 20
        self.cols = 10
        self.board = [0 for _ in range(self.rows)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        
        self.current_piece = self.get_random_piece()
        self.next_piece = self.get_random_piece()
        self.last_drop = time.time()
        
    def reset(self):
        # =====================================================================
        # CONCEPTO [Teoría de Autómatas / Máquinas de Estado Finitas]:
        # AQUÍ SE ESTÁ VIENDO ESTO: El reinicio del juego representa una 
        # transición de regreso al estado inicial S_0. El autómata limpia las 
        # variables de estado, la memoria del Bitboard y reestablece los parámetros.
        # =====================================================================
        self.board = [0 for _ in range(self.rows)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.current_piece = self.get_random_piece()
        self.next_piece = self.get_random_piece()
        self.last_drop = time.time()

    def get_target_score(self):
        # =====================================================================
        # CONCEPTO [Sucesiones y Progresiones Aritméticas]:
        # AQUÍ SE ESTÁ VIENDO ESTO: La meta de puntos requerida para superar el 
        # nivel actual se modela como una sucesión aritmética estricta donde 
        # f(n) = n * 1000. Esto define la cota superior necesaria para el estado.
        # =====================================================================
        return self.level * 1000

    def get_random_piece(self):
        ptype = random.choice(PIECES)
        matrix = [row[:] for row in SHAPES[ptype]]
        return {
            'type': ptype,
            'matrix': matrix,
            'x': self.cols // 2 - len(matrix[0]) // 2,
            'y': 0
        }

    def collide(self, piece, offset_x=0, offset_y=0):
        for y, row in enumerate(piece['matrix']):
            for x, val in enumerate(row):
                if val != 0:
                    nx = piece['x'] + x + offset_x
                    ny = piece['y'] + y + offset_y
                    if nx < 0 or nx >= self.cols or ny >= self.rows:
                        return True
                    if ny >= 0 and (self.board[ny] & (1 << nx)) != 0:
                        return True
        return False

    def merge(self):
        p = self.current_piece
        for y, row in enumerate(p['matrix']):
            for x, val in enumerate(row):
                if val != 0 and p['y'] + y >= 0:
                    self.board[p['y'] + y] |= (1 << (p['x'] + x))

    def rotate_matrix(self, matrix):
        return [list(r) for r in zip(*matrix[::-1])]

    def do_rotate(self):
        original = [row[:] for row in self.current_piece['matrix']]
        self.current_piece['matrix'] = self.rotate_matrix(self.current_piece['matrix'])
        if self.collide(self.current_piece):
            self.current_piece['x'] += 1
            if self.collide(self.current_piece):
                self.current_piece['x'] -= 2
                if self.collide(self.current_piece):
                    self.current_piece['x'] += 1
                    self.current_piece['matrix'] = original

    def get_ghost_y(self):
        if not self.current_piece:
            return 0
        temp_piece = {
            'matrix': self.current_piece['matrix'],
            'x': self.current_piece['x'],
            'y': self.current_piece['y']
        }
        while not self.collide(temp_piece, offset_y=1):
            temp_piece['y'] += 1
        return temp_piece['y']

    def sweep(self):
        lines_cleared = 0
        y = self.rows - 1
        while y >= 0:
            if self.board[y] == 1023:
                del self.board[y]
                self.board.insert(0, 0)
                lines_cleared += 1
            else:
                y -= 1
                
        if lines_cleared > 0:
            pts = [0, 40, 100, 300, 1200]
            self.score += pts[lines_cleared] * self.level
            self.lines += lines_cleared
            
            # El nivel aumenta si el puntaje supera el umbral de la sucesión aritmética
            while self.score >= self.get_target_score():
                self.level += 1
            return 'clear'
        return None

    def update_gravity(self):
        if self.game_over:
            return
        now = time.time()
        drop_interval = 1.0 * (0.85 ** (self.level - 1))
        if now - self.last_drop > drop_interval:
            self.last_drop = now
            self.do_drop()

    def do_drop(self, is_manual=False):
        if self.collide(self.current_piece, offset_y=1):
            self.merge()
            event = self.sweep()
            self.current_piece = self.next_piece
            self.next_piece = self.get_random_piece()
            if self.collide(self.current_piece):
                self.game_over = True
            return 'gameover' if self.game_over else event or 'drop'
        else:
            self.current_piece['y'] += 1
            if is_manual:
                self.last_drop = time.time()
            return 'move'
            
    def do_action(self, action):
        if self.game_over:
            return None
        event = None
        if action == 'left':
            if not self.collide(self.current_piece, offset_x=-1):
                self.current_piece['x'] -= 1
                event = 'move'
        elif action == 'right':
            if not self.collide(self.current_piece, offset_x=1):
                self.current_piece['x'] += 1
                event = 'move'
        elif action == 'down':
            event = self.do_drop(is_manual=True)
        elif action == 'rotate':
            self.do_rotate()
            event = 'rotate'
        return event

game = TetrisGame()

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/state', methods=['GET'])
def get_state():
    game.update_gravity()
    board_2d = []
    for row_int in game.board:
        board_2d.append(['X' if (row_int & (1 << x)) else 0 for x in range(game.cols)])
        
    return jsonify({
        "board": board_2d,
        "current_piece": game.current_piece,
        "next_piece": game.next_piece,
        "ghost_y": game.get_ghost_y(),
        "score": game.score,
        "level": game.level,
        "lines": game.lines,
        "game_over": game.game_over,
        "target_score": game.get_target_score() # Enviamos la meta de puntos al frontend
    })

@app.route('/action', methods=['POST'])
def action():
    data = request.json
    act = data.get('action')
    event = game.do_action(act)
    return jsonify({"status": "ok", "event": event})

@app.route('/reset', methods=['POST'])
def reset():
    game.reset()
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)
