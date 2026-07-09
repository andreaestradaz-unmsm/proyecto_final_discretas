from flask import Flask, send_file, jsonify, request
import time
import random

app = Flask(__name__, static_folder='.', static_url_path='')

# =====================================================================
# CONCEPTO [Conteo]:
# AQUÍ SE ESTÁ VIENDO ESTO: Se aplica el "Principio de Multiplicación". 
# Tenemos 7 tipos de piezas distintas y cada una puede tener hasta 
# 4 orientaciones (rotaciones). Multiplicando 7 x 4 = 28, obtenemos 
# todo el espacio finito de figuras posibles con las que interactúa el usuario.
# =====================================================================
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
        
        # =====================================================================
        # CONCEPTO [Sistemas de numeración y Álgebra de Boole]:
        # Mejora 1: Tablero Optimizado con Sistemas de Numeración (Bitboards)
        # AQUÍ SE ESTÁ VIENDO ESTO: En lugar de usar una matriz bidimensional,
        # el tablero se representa como un arreglo unidimensional de 20 enteros.
        # Dado que el tablero tiene 10 columnas, cada fila es un número binario
        # de 10 bits.
        # =====================================================================
        self.board = [0 for _ in range(self.rows)]
        
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        
        self.current_piece = self.get_random_piece()
        self.next_piece = self.get_random_piece()
        self.last_drop = time.time()
        
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
        # =====================================================================
        # CONCEPTO [Álgebra de Boole / Operadores Bit a Bit]:
        # AQUÍ SE ESTÁ VIENDO ESTO: Para asentar una pieza, en lugar de 
        # modificar un array o hacer uniones complejas, usamos la operación 
        # OR lógico (|) bit a bit. Fusionamos los bits de la pieza directamente 
        # con el entero de la fila.
        # =====================================================================
        p = self.current_piece
        for y, row in enumerate(p['matrix']):
            for x, val in enumerate(row):
                if val != 0 and p['y'] + y >= 0:
                    self.board[p['y'] + y] |= (1 << (p['x'] + x))

    def rotate_matrix(self, matrix):
        # =====================================================================
        # CONCEPTO [Funciones]:
        # AQUÍ SE ESTÁ VIENDO ESTO: La rotación se define como una función 
        # matemática biyectiva que toma una matriz bidimensional M y la transforma 
        # en M'. El mapeo transponga coordenadas: f((x,y)) -> (-y,x).
        # =====================================================================
        return [list(r) for r in zip(*matrix[::-1])]

    def do_rotate(self):
        # =====================================================================
        # CONCEPTO [Aritmética modular]:
        # AQUÍ SE ESTÁ VIENDO ESTO: Las piezas rotan dentro de un grupo cíclico.
        # Al llegar a la 4ta rotación, vuelve a la inicial. El estado 
        # se rige mediante aritmética modular módulo 4: estado_siguiente = (estado + 1) % 4.
        # =====================================================================
        original = [row[:] for row in self.current_piece['matrix']]
        self.current_piece['matrix'] = self.rotate_matrix(self.current_piece['matrix'])
        if self.collide(self.current_piece):
            self.current_piece['x'] += 1
            if self.collide(self.current_piece):
                self.current_piece['x'] -= 2
                if self.collide(self.current_piece):
                    self.current_piece['x'] += 1
                    self.current_piece['matrix'] = original

    def sweep(self):
        # =====================================================================
        # CONCEPTO [Eficiencia / Notación O y Sistemas de Numeración]:
        # AQUÍ SE ESTÁ VIENDO ESTO: Evaluar si una línea está completa ya no 
        # requiere iterar 10 celdas; simplemente se verifica si el entero de la fila 
        # es exactamente igual a 1023 (2^10 - 1 en decimal, o sea, 10 unos en binario).
        # Mejora radicalmente la eficiencia a O(1) por fila.
        # =====================================================================
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
            # =====================================================================
            # CONCEPTO [Sucesiones / funciones por partes]:
            # AQUÍ SE ESTÁ VIENDO ESTO: La fórmula de puntaje es una "Función por 
            # partes" discreta. f(x) = { 40 si x=1, 100 si x=2, 300 si x=3, 1200 si x=4 } 
            # Además, la velocidad de caída obedece a una progresión (sucesión) geométrica.
            # =====================================================================
            pts = [0, 40, 100, 300, 1200]
            self.score += pts[lines_cleared] * self.level
            self.lines += lines_cleared
            self.level = (self.lines // 10) + 1
            return 'clear'
        return None

    def update_gravity(self):
        if self.game_over:
            return
        
        now = time.time()
        # Sucesión geométrica decreciente para la gravedad
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
    
    # Transformar el arreglo unidimensional (Bitboard) a matriz 2D para el frontend
    board_2d = []
    for row_int in game.board:
        board_2d.append(['X' if (row_int & (1 << x)) else 0 for x in range(game.cols)])
        
    return jsonify({
        "board": board_2d,
        "current_piece": game.current_piece,
        "next_piece": game.next_piece,
        "score": game.score,
        "level": game.level,
        "lines": game.lines,
        "game_over": game.game_over
    })

@app.route('/action', methods=['POST'])
def action():
    data = request.json
    act = data.get('action')
    event = game.do_action(act)
    return jsonify({"status": "ok", "event": event})

if __name__ == '__main__':
    print("=============================================================")
    print("¡TETRIS EDUCATIVO INICIADO EN PYTHON FLASK!")
    print("Abre tu navegador y entra a: http://127.0.0.1:5000")
    print("=============================================================")
    app.run(debug=True, port=5000, use_reloader=False)
