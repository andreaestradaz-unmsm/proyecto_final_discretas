const canvas = document.getElementById('tetris');
const ctx = canvas.getContext('2d');
const nextCanvas = document.getElementById('next-piece');
const nextCtx = nextCanvas.getContext('2d');
nextCanvas.width = 120; nextCanvas.height = 120;

const BLOCK_SIZE = 30;

const COLORS = {
    'I': '#00ffff', 'J': '#4facfe', 'L': '#ffb347', 'O': '#ffff00',
    'S': '#43e97b', 'T': '#f093fb', 'Z': '#ff0000',
    'X': '#888' // Color asentado
};

// ==========================================
// SONIDOS (Estilo Undertale Text Voice)
// ==========================================
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playSound(type) {
    if (!type) return;
    if (audioCtx.state === 'suspended') audioCtx.resume();
    
    const osc = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    osc.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    
    if (type === 'move' || type === 'rotate') {
        // Sonido corto "blip" estilo texto de Sans
        osc.type = 'square';
        osc.frequency.setValueAtTime(350, audioCtx.currentTime);
        gainNode.gain.setValueAtTime(0.05, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.05);
        osc.start(); osc.stop(audioCtx.currentTime + 0.05);
    } else if (type === 'clear') {
        // Sonido de Gaster Blaster disparando
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(100, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(800, audioCtx.currentTime + 0.5);
        gainNode.gain.setValueAtTime(0.2, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);
        osc.start(); osc.stop(audioCtx.currentTime + 0.5);
    } else if (type === 'drop') {
        osc.type = 'square';
        osc.frequency.setValueAtTime(100, audioCtx.currentTime);
        gainNode.gain.setValueAtTime(0.05, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.1);
        osc.start(); osc.stop(audioCtx.currentTime + 0.1);
    } else if (type === 'gameover') {
        osc.type = 'square';
        osc.frequency.setValueAtTime(150, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(50, audioCtx.currentTime + 1);
        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 1);
        osc.start(); osc.stop(audioCtx.currentTime + 1);
    }
}

// ==========================================
// RENDERIZADO
// ==========================================
function drawBlock(context, color, x, y, scale = 1) {
    const dx = x * BLOCK_SIZE * scale;
    const dy = y * BLOCK_SIZE * scale;
    const size = BLOCK_SIZE * scale;
    
    context.fillStyle = color;
    context.fillRect(dx, dy, size, size);
    
    // Borde blanco estilo pixel
    context.strokeStyle = '#fff';
    context.lineWidth = 2;
    context.strokeRect(dx, dy, size, size);
}

function drawGhostBlock(context, color, x, y) {
    const dx = x * BLOCK_SIZE;
    const dy = y * BLOCK_SIZE;
    const size = BLOCK_SIZE;
    
    context.strokeStyle = color;
    context.lineWidth = 2;
    context.strokeRect(dx + 2, dy + 2, size - 4, size - 4);
    context.fillStyle = color + "22"; // Transparente
    context.fillRect(dx + 2, dy + 2, size - 4, size - 4);
}

let gameOverFlag = false;

function render(state) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Tablero fijado
    state.board.forEach((row, y) => {
        row.forEach((val, x) => {
            if (val !== 0) drawBlock(ctx, COLORS[val], x, y);
        });
    });

    // Pieza fantasma (Ghost piece)
    if (state.current_piece && state.ghost_y !== undefined) {
        const cp = state.current_piece;
        cp.matrix.forEach((row, y) => {
            row.forEach((val, x) => {
                if (val !== 0) {
                    drawGhostBlock(ctx, COLORS[cp.type], cp.x + x, state.ghost_y + y);
                }
            });
        });
    }

    // Pieza cayendo
    if (state.current_piece) {
        const cp = state.current_piece;
        cp.matrix.forEach((row, y) => {
            row.forEach((val, x) => {
                if (val !== 0) drawBlock(ctx, COLORS[cp.type], cp.x + x, cp.y + y);
            });
        });
    }

    // Siguiente pieza
    nextCtx.clearRect(0, 0, nextCanvas.width, nextCanvas.height);
    if (state.next_piece) {
        const np = state.next_piece;
        const boundsX = np.matrix[0].length;
        const boundsY = np.matrix.length;
        const px = (nextCanvas.width / BLOCK_SIZE - boundsX) / 2;
        const py = (nextCanvas.height / BLOCK_SIZE - boundsY) / 2;
        
        np.matrix.forEach((row, y) => {
            row.forEach((val, x) => {
                if (val !== 0) drawBlock(nextCtx, COLORS[np.type], px + x, py + y);
            });
        });
    }
    
    // RAYO LÁSER AZUL (dibujado sobre el canvas exactamente en las filas eliminadas)
    if (state.cleared_rows && state.cleared_rows.length > 0) {
        state.cleared_rows.forEach(rowY => {
            const py = rowY * BLOCK_SIZE;
            // Fila cian brillante
            ctx.shadowBlur = 25;
            ctx.shadowColor = '#00ffff';
            ctx.fillStyle = '#00ffff';
            ctx.fillRect(0, py, canvas.width, BLOCK_SIZE);
            // Centro blanco (núcleo del láser)
            ctx.shadowBlur = 0;
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, py + BLOCK_SIZE * 0.35, canvas.width, BLOCK_SIZE * 0.3);
        });
        ctx.shadowBlur = 0;
    }
    
    // Texto
    document.getElementById('score').innerText = String(state.score).padStart(6, '0');
    document.getElementById('level-progress').innerText = `${state.score} / ${state.target_score}`;
    document.getElementById('level').innerText = state.level;
    document.getElementById('lines').innerText = state.lines;

    if (state.game_over && !gameOverFlag) {
        document.getElementById('game-over').style.display = 'block';
        playSound('gameover');
        gameOverFlag = true;
    }
}

// ==========================================
// ANIMACIONES SANS & BLASTER
// ==========================================
// clearedRows: array de indices Y de las filas eliminadas
function triggerBlaster(clearedRows) {
    const sansSprite = document.getElementById('sans-sprite');
    const blaster = document.getElementById('gaster-blaster');
    
    // Calcular posición exacta en pantalla usando el canvas como referencia
    const boardRect = canvas.getBoundingClientRect();
    
    // Posicionar el blaster a la DERECHA del tablero, a la altura de la fila borrada
    if (clearedRows && clearedRows.length > 0) {
        const midRow = clearedRows[Math.floor(clearedRows.length / 2)];
        // Coordenada Y en pantalla del centro de la fila eliminada
        const rowCenterY = boardRect.top + (midRow * BLOCK_SIZE) + (BLOCK_SIZE / 2);
        // Coordenada X: borde derecho del tablero
        const boardRightX = boardRect.right + 4;
        
        blaster.style.left = boardRightX + 'px';
        blaster.style.top  = (rowCenterY - 60) + 'px'; // centrar el blaster de 120px en la fila
    }
    
    // Bad Time Eye
    const sansContainer = document.getElementById('sans-container');
    if (sansContainer) {
        sansContainer.classList.add('bad-time');
    }
    
    // Forzar reinicio de animación CSS
    blaster.classList.remove('fire');
    void blaster.offsetWidth;
    blaster.classList.add('fire');
    playSound('clear');
    
    setTimeout(() => {
        sansContainer.classList.remove('bad-time');
        blaster.classList.remove('fire');
    }, 600);
}

let sansIdleTimer = null;
let sansFrame = 1;

function animateSansController() {
    const sprite = document.getElementById('sans-sprite');
    const container = document.getElementById('sans-container');
    if (!sprite || !container) return;
    
    // Si existe sans_press.png, cambiar imagen
    if (sprite.tagName === 'IMG') {
        sprite.src = 'assets/sans_press.png';
        container.classList.add('sans-press');
        
        clearTimeout(sansIdleTimer);
        sansIdleTimer = setTimeout(() => {
            container.classList.remove('sans-press');
            sprite.src = 'assets/sans_idle.png';
        }, 150);
    }
}

// Animación de respiración idle (arriba y abajo muy suave)
setInterval(() => {
    const container = document.getElementById('sans-container');
    if (container && !container.classList.contains('sans-press')) {
        container.classList.toggle('sans-idle-bob');
    }
}, 800);

// ==========================================
// CHAT FALSO (Twitch Style)
// ==========================================
const chatBox = document.getElementById('chat-box');
const fakeChatNames = ['Papyrus', 'Undyne', 'Mettaton', 'Alphys', 'Frisk', 'Toriel', 'Asgore', 'xXx_Flowey_xXx'];
const fakeChatMsgs = [
    'SANS, VUELVE AL TRABAJO!', 'lol he got dunked on', 'Mettaton: Oh yesss!', 'Anime is real right?', 
    'determinacion', 'hOI!! im temmie', 'NYEH HEH HEH!', 'sans ur so lazy', 'poggers', 'F', 'get good'
];

function spawnChatMessage() {
    if (gameOverFlag) return;
    const name = fakeChatNames[Math.floor(Math.random() * fakeChatNames.length)];
    const msg = fakeChatMsgs[Math.floor(Math.random() * fakeChatMsgs.length)];
    
    const el = document.createElement('div');
    el.className = 'chat-msg';
    el.innerHTML = `<span class="user">${name}:</span><span>${msg}</span>`;
    
    chatBox.appendChild(el);
    if (chatBox.children.length > 8) {
        chatBox.removeChild(chatBox.firstChild);
    }
    
    setTimeout(spawnChatMessage, Math.random() * 2000 + 1000);
}
spawnChatMessage();

// ==========================================
// COMUNICACIÓN CON PYTHON (BACKEND)
// ==========================================
let isClearingState = false;

function loopFetch() {
    fetch('/state')
        .then(res => res.json())
        .then(state => {
            if (state.is_clearing && !isClearingState) {
                triggerBlaster(state.cleared_rows); // pasar coordenadas
                isClearingState = true;
            } else if (!state.is_clearing) {
                isClearingState = false;
            }
            render(state);
            setTimeout(loopFetch, 50);
        })
        .catch(err => setTimeout(loopFetch, 1000));
}

async function sendAction(action) {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    animateSansController();
    
    try {
        const response = await fetch('/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        const data = await response.json();
        
        if (data.event && data.event !== 'gameover' && data.event !== 'clear') {
            playSound(data.event);
        }
    } catch(e) {}
}

document.addEventListener('keydown', event => {
    if (gameOverFlag) return;
    if (event.keyCode === 37) sendAction('left');
    else if (event.keyCode === 39) sendAction('right');
    else if (event.keyCode === 40) sendAction('down');
    else if (event.keyCode === 38) sendAction('rotate');
});
document.addEventListener('click', () => { if(audioCtx.state === 'suspended') audioCtx.resume(); });

document.getElementById('retry-btn').addEventListener('click', () => {
    fetch('/reset', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'ok') {
                document.getElementById('game-over').style.display = 'none';
                gameOverFlag = false;
            }
        });
});

loopFetch();
