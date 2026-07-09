from flask import Flask, send_file, jsonify, request
import time
import random

app = Flask(__name__, static_folder='.', static_url_path='')

# =====================================================================
# MATEMÁTICA DISCRETA - CONCEPTO 1: Teoría de Conjuntos y Combinatoria
# =====================================================================
# El conjunto de Tetrominós 'T' está formado por 7 figuras distintas.
# T = {I, J, L, O, S, T, Z}.
# Aplicando el "Principio de Multiplicación", si tenemos 7 figuras y
# cada una puede tener hasta 4 estados de rotación posibles, el tamaño 
# máximo del espacio muestral de piezas orientadas es 7 x 4 = 28.
# Esto define el espacio finito de objetos manipulables en el juego.
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
        # MATEMÁTICA DISCRETA - CONCEPTO 2: Álgebra de Boole y Sistemas de Numeración
        # =====================================================================
        # En lugar de usar una matriz tradicional 2D para representar la grilla,
        # utilizamos un "Bitboard". El tablero es un arreglo 1D de 20 elementos.
        # Dado que el tablero tiene 10 columnas, cada fila se representa como un 
        # número entero que, en su forma binaria de 10 bits, mapea el estado de 
        # las celdas (0 = Vacío, 1 = Ocupado). 
        # Esto reduce drásticamente el uso de memoria y permite aplicar 
        # compuertas lógicas matemáticas para colisiones.
        # =====================================================================
        self.board = [0 for _ in range(self.rows)]
        
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.last_cleared_rows = []
        self.clear_time = 0
        self.game_paused_until = 0
        self.pending_clear = []
        
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
        # =====================================================================
        # MATEMÁTICA DISCRETA - CONCEPTO 3: Operaciones Lógicas (AND) y Traslación
        # =====================================================================
        # Para detectar una colisión evaluamos la conjunción (AND lógico).
        # Para cada bloque de la pieza, calculamos su coordenada global (nx, ny)
        # mediante una Transformación de Traslación (suma de vectores).
        # Luego evaluamos la condición Booleana:
        # colision = (fuera_de_limites) OR ( (tablero[ny] AND (2^nx)) != 0 )
        # Si un bit de la pieza y un bit del tablero coinciden en 1, el AND 
        # lógico da un resultado > 0, demostrando intersección de conjuntos.
        # =====================================================================
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
        # MATEMÁTICA DISCRETA - CONCEPTO 4: Teoría de Conjuntos (Unión) y Operador OR
        # =====================================================================
        # Al asentar la pieza en el tablero, realizamos la unión de dos 
        # conjuntos. Matemáticamente, esto equivale al OR lógico bit a bit (|).
        # tablero_final = tablero_inicial OR mascara_pieza
        # Modifica directamente la representación entera del bitboard.
        # =====================================================================
        p = self.current_piece
        for y, row in enumerate(p['matrix']):
            for x, val in enumerate(row):
                if val != 0 and p['y'] + y >= 0:
                    self.board[p['y'] + y] |= (1 << (p['x'] + x))

    def rotate_matrix(self, matrix):
        # =====================================================================
        # MATEMÁTICA DISCRETA - CONCEPTO 5: Matrices y Transformaciones Geométricas
        # =====================================================================
        # La rotación de una pieza corresponde a una rotación de 90° en álgebra
        # lineal. Si tratamos la pieza como una matriz cuadrada M, rotarla
        # 90 grados a la derecha equivale a transponer la matriz (M^T) y luego
        # revertir el orden de sus columnas.
        # Función f(x, y) = (-y, x).
        # =====================================================================
        return [list(r) for r in zip(*matrix[::-1])]

    def do_rotate(self):
        # =====================================================================
        # MATEMÁTICA DISCRETA - CONCEPTO 6: Aritmética Modular (Anillos y Grupos)
        # =====================================================================
        # Las piezas rotan dentro de un grupo cíclico de orden 4.
        # Al rotar la pieza 4 veces (360°), esta retorna exactamente a su 
        # estado inicial, definiendo una relación de congruencia módulo 4.
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
        # MATEMÁTICA DISCRETA - CONCEPTO 7: Complejidad Algorítmica (Notación Big O)
        # =====================================================================
        # Para verificar si una fila (10 columnas) está llena, normalmente
        # requeriría un tiempo O(n) iterando cada columna.
        # Gracias a nuestra representación binaria (Bitboard), una fila llena 
        # equivale al número binario 1111111111_2, que es exactamente 
        # 2^10 - 1 = 1023. La comparación es matemática y se ejecuta en O(1) constante.
        # =====================================================================
        lines_cleared_indices = []
        y = self.rows - 1
        while y >= 0:
            if self.board[y] == 1023:
                lines_cleared_indices.append(y)
            y -= 1
                
        lines_cleared = len(lines_cleared_indices)
        if lines_cleared > 0:
            self.pending_clear = lines_cleared_indices
            self.last_cleared_rows = lines_cleared_indices
            self.clear_time = time.time()
            self.game_paused_until = time.time() + 0.6  # Pausa dramática para el láser
            return 'clear'
        return None

    def update_gravity(self):
        now = time.time()
        
        # Ejecutar la limpieza pendiente después de la pausa
        if self.pending_clear and now >= self.game_paused_until:
            lines_cleared = len(self.pending_clear)
            for y in sorted(self.pending_clear): # del bottom to top? wait, indices are absolute.
                # Actually, deleting by value or index must be careful.
                # pending_clear has the original Y coords. We just reconstruct the board without them.
                pass
            
            # Reconstruir el tablero sin las filas completas
            new_board = [row for i, row in enumerate(self.board) if i not in self.pending_clear]
            added_rows = self.rows - len(new_board)
            self.board = [0] * added_rows + new_board
            
            # Actualizar puntaje
            pts = [0, 40, 100, 300, 1200]
            self.score += pts[lines_cleared] * self.level
            self.lines += lines_cleared
            self.level = (self.lines // 10) + 1
            
            self.pending_clear = []
            
        if self.game_over or now < self.game_paused_until:
            return
        
        # Sucesión geométrica decreciente para la gravedad
        # Concepto: Progresión Geométrica donde la razón r = 0.85
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
        if self.game_over or time.time() < self.game_paused_until:
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
    cleared_rows = []
    is_clearing = False
    if time.time() - game.clear_time < 0.6:
        cleared_rows = game.last_cleared_rows
        is_clearing = True
        
    return jsonify({
        "board": board_2d,
        "current_piece": game.current_piece,
        "next_piece": game.next_piece,
        "score": game.score,
        "level": game.level,
        "lines": game.lines,
        "game_over": game.game_over,
        "cleared_rows": cleared_rows,
        "is_clearing": is_clearing
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
