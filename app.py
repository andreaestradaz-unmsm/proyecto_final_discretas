from flask import Flask, send_file, jsonify, request
import time
import random
from enum import Enum

app = Flask(__name__, static_folder='.', static_url_path='')

# =====================================================================
# CONCEPTO 18: Gramáticas y Autómatas (AFD)
# =====================================================================
# Se refactorizó el control del juego usando un Autómata Finito 
# Determinista (AFD). Los estados son los nodos y las transiciones 
# evitan lógicamente estados inválidos (ej. pausar estando en GAME_OVER).
# =====================================================================
# =====================================================================
# MEJORA 2: Máquina de Estados Finita / Autómatas
# =====================================================================
# Se programa el flujo del menú, la pausa y el fin de juego mediante
# un autómata finito para controlar de forma estricta las transiciones
# válidas entre estados y evitar movimientos inválidos del juego.
# =====================================================================
class GameState(Enum):
    START_SCREEN = "start_screen"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    RESUMING = "resuming"

# =====================================================================
# CONCEPTO 5: Conteo y Combinatoria (Principio de Multiplicación)
# =====================================================================
# Hay 7 piezas distintas. Si cada una tiene 4 rotaciones posibles, 
# el total de estados pieza-rotación en el espacio muestral es 7 x 4 = 28.
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
        self._state = GameState.START_SCREEN
        self._state_enter_time = time.time()
        self.reset_state()
        
    def reset_state(self):
        # =====================================================================
        # MEJORA 1: Sistemas de Numeración (Bitboards)
        # =====================================================================
        # En lugar de usar una matriz bidimensional (Array de Arrays), el 
        # tablero se representa como un arreglo unidimensional de 20 enteros. 
        # Cada fila es un número binario de 10 bits.
        # =====================================================================
        self.board = [0 for _ in range(self.rows)]
        
        self.score = 0
        self.lines = 0
        self.level = 1
        self.last_cleared_rows = []
        self.clear_time = 0
        self.game_paused_until = 0
        self.pending_clear = []
        
        self.current_piece = self.get_random_piece()
        self.next_piece = self.get_random_piece()
        self.last_drop = time.time()
    
    def get_state(self):
        return self._state
    
    def transition_to(self, new_state):
        valid_transitions = {
            GameState.START_SCREEN: [GameState.PLAYING],
            GameState.PLAYING: [GameState.PAUSED, GameState.GAME_OVER],
            GameState.PAUSED: [GameState.RESUMING, GameState.START_SCREEN],
            GameState.RESUMING: [GameState.PLAYING],
            GameState.GAME_OVER: [GameState.START_SCREEN]
        }
        if new_state in valid_transitions.get(self._state, []):
            self._state = new_state
            self._state_enter_time = time.time()
            return True
        return False
    
    def start_game(self): return self.transition_to(GameState.PLAYING)
    def pause_game(self): return self.transition_to(GameState.PAUSED)
    def resume_game(self):
        if self.transition_to(GameState.RESUMING):
            self.transition_to(GameState.PLAYING)
            self.last_drop = time.time()
            return True
        return False
    def end_game(self): return self.transition_to(GameState.GAME_OVER)
    def reset_to_start(self):
        if self._state in [GameState.GAME_OVER, GameState.PAUSED]:
            if self.transition_to(GameState.START_SCREEN):
                self.reset_state()
                return True
        return False
    def reset(self): self.reset_to_start()
        
    def get_target_score(self):
        return self.level * 1000

    def get_ghost_y(self):
        if not self.current_piece: return 0
        
        # =====================================================================
        # MEJORA 3: "Ghost Piece" usando Caminos y Búsqueda (Grafos)
        # =====================================================================
        # Se modela la caída como el cálculo del camino más largo en un grafo 
        # dirigido hacia abajo, iterando hasta encontrar una intersección 
        # de conjuntos (colisión) con los bloques ya fijados.
        # =====================================================================
        ghost_y = self.current_piece['y']
        while not self.collide(self.current_piece, offset_y=(ghost_y - self.current_piece['y'] + 1)):
            ghost_y += 1
        return ghost_y

    def get_random_piece(self):
        # =====================================================================
        # CONCEPTO 11: Conteo / Combinatoria (Pieza I)
        # =====================================================================
        # Si la pieza 'I' se coloca horizontalmente (tamaño 4) en este 
        # tablero de 10 columnas, cabe en exactamente 7 posiciones.
        # Fórmula: (Columnas_Totales - Tamaño_Pieza) + 1 -> 10 - 4 + 1 = 7.
        # =====================================================================
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
        # CONCEPTO 2: Conjuntos (Operación de Unión)
        # =====================================================================
        # Cuando una pieza se fija, ocurre una Unión de conjuntos entre la 
        # zona ya ocupada y las coordenadas de la nueva pieza (usando OR a nivel de bits).
        # =====================================================================
        p = self.current_piece
        for y, row in enumerate(p['matrix']):
            for x, val in enumerate(row):
                if val != 0 and p['y'] + y >= 0:
                    self.board[p['y'] + y] |= (1 << (p['x'] + x))

    def rotate_matrix(self, matrix):
        # =====================================================================
        # CONCEPTO 3 y 14: Funciones (Rotación Biyectiva)
        # =====================================================================
        # La rotación transforma la orientación. Se modela como una función 
        # biyectiva (permutación de coordenadas matriciales), garantizando que 
        # cada estado tiene un único estado siguiente (sin pérdida de datos).
        # =====================================================================
        return [list(r) for r in zip(*matrix[::-1])]

    def do_rotate(self):
        # =====================================================================
        # CONCEPTO 4: Aritmética Modular
        # =====================================================================
        # Las orientaciones rotan en ciclo módulo 4: (orientacion + 1) % 4.
        # Después de la orientación 3, sigue la orientación 0.
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
        # CONCEPTO 1, 8 y 9: Lógica, Eficiencia O(1) y Sistemas de Numeración
        # =====================================================================
        # Lógica proposicional: "Línea completa" es verdadera cuando la 
        # conjunción (C0 AND C1 AND ... AND C9) es verdadera. 
        # Sist. de Numeración: Esto equivale al número decimal 1023 (2^10 - 1).
        # Eficiencia O: Revisar una fila cuesta O(1) en lugar de iterar O(n).
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
            self.game_paused_until = time.time() + 0.6
            return 'clear'
        return None

    def update_gravity(self):
        if self._state != GameState.PLAYING: return
        now = time.time()
        
        if self.pending_clear and now >= self.game_paused_until:
            lines_cleared = len(self.pending_clear)
            # =================================================================
            # CONCEPTO 10: Conjuntos (Descenso de filas)
            # =================================================================
            # Cuando se elimina una línea, se hace una "Diferencia Relativa" 
            # retirando las filas completas del conjunto, y las coordenadas Y
            # de las filas superiores se trasladan (suman offset).
            # =================================================================
            new_board = [row for i, row in enumerate(self.board) if i not in self.pending_clear]
            added_rows = self.rows - len(new_board)
            self.board = [0] * added_rows + new_board
            
            # =================================================================
            # CONCEPTO 7: Sucesiones por Partes
            # =================================================================
            # El puntaje es una función por partes del número de líneas limpiadas:
            # f(1) = 40, f(2) = 100, f(3) = 300, f(4) = 1200.
            # =================================================================
            pts = [0, 40, 100, 300, 1200]
            self.score += pts[lines_cleared] * self.level
            self.lines += lines_cleared
            self.level = (self.lines // 10) + 1
            self.pending_clear = []
        
        if now < self.game_paused_until: return
        
        # =====================================================================
        # CONCEPTO 12: Sucesiones
        # =====================================================================
        # La velocidad de caída se multiplica por un factor fijo (r = 0.85). 
        # Modela una Sucesión Geométrica decreciente: a_n = 1.0 * (0.85)^(n-1)
        # =====================================================================
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
            
            # =================================================================
            # CONCEPTO 6: Lógica Proposicional (Game Over)
            # =================================================================
            # Condición simbólica: (Posicion_Y == 0) AND (Colisión_Inmediata).
            # Si ambas proposiciones son verdaderas, el juego termina.
            # =================================================================
            if self.collide(self.current_piece):
                self.end_game()
            return 'gameover' if self._state == GameState.GAME_OVER else event or 'drop'
        else:
            self.current_piece['y'] += 1
            if is_manual:
                self.last_drop = time.time()
            return 'move'
            
    def do_action(self, action):
        if self._state != GameState.PLAYING: return None
        if time.time() < self.game_paused_until: return None
            
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
    
    def do_pause(self):
        if self._state == GameState.PLAYING: return self.pause_game()
        elif self._state == GameState.PAUSED: return self.resume_game()
        return False

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
    cleared_rows = []
    is_clearing = False
    if time.time() - game.clear_time < 0.6:
        cleared_rows = game.last_cleared_rows
        is_clearing = True
        
    return jsonify({
        "board": board_2d,
        "current_piece": game.current_piece,
        "next_piece": game.next_piece,
        "ghost_y": game.get_ghost_y(),
        "score": game.score,
        "level": game.level,
        "lines": game.lines,
        "game_state": game.get_state().value,
        "target_score": game.get_target_score(),
        "cleared_rows": cleared_rows,
        "is_clearing": is_clearing
    })

@app.route('/action', methods=['POST'])
def action():
    data = request.json
    act = data.get('action')
    event = game.do_action(act)
    return jsonify({"status": "ok", "event": event})

@app.route('/start', methods=['POST'])
def start():
    success = game.start_game()
    return jsonify({"status": "ok" if success else "invalid", "success": success})

@app.route('/pause', methods=['POST'])
def pause():
    success = game.do_pause()
    return jsonify({"status": "ok" if success else "invalid", "success": success, "game_state": game.get_state().value})

@app.route('/reset', methods=['POST'])
def reset():
    game.reset()
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    print("=============================================================")
    print("¡TETRIS EDUCATIVO INICIADO EN PYTHON FLASK!")
    print("Abre tu navegador y entra a: http://127.0.0.1:5000")
    print("=============================================================")
    app.run(debug=True, port=5000, use_reloader=False)
