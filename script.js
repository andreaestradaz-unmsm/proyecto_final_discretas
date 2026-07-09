const canvas = document.getElementById('tetris');
const ctx = canvas.getContext('2d');
const nextCanvas = document.getElementById('next-piece');
const nextCtx = nextCanvas.getContext('2d');
nextCanvas.width = 120; nextCanvas.height = 120;

const BLOCK_SIZE = 30;

const COLORS = {
    'I': '#00f2fe', 'J': '#4facfe', 'L': '#ffb347', 'O': '#f9d423',
    'S': '#43e97b', 'T': '#f093fb', 'Z': '#f5576c',
    'X': '#a2a2d0'
};

const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playSound(type) {
    if (!type) return;
    if (audioCtx.state === 'suspended') audioCtx.resume();
    
    const osc = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    osc.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    
    if (type === 'move') {
        osc.type = 'sine'; osc.frequency.setValueAtTime(300, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(100, audioCtx.currentTime + 0.1);
        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime); gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.1);
        osc.start(); osc.stop(audioCtx.currentTime + 0.1);
    } else if (type === 'rotate') {
        osc.type = 'triangle'; osc.frequency.setValueAtTime(400, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(600, audioCtx.currentTime + 0.1);
        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime); gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.1);
        osc.start(); osc.stop(audioCtx.currentTime + 0.1);
    } else if (type === 'clear') {
        osc.type = 'square'; osc.frequency.setValueAtTime(400, audioCtx.currentTime);
        osc.frequency.setValueAtTime(600, audioCtx.currentTime + 0.1);
        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime); gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.2);
        osc.start(); osc.stop(audioCtx.currentTime + 0.2);
    } else if (type === 'drop') {
        osc.type = 'sawtooth'; osc.frequency.setValueAtTime(150, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(50, audioCtx.currentTime + 0.1);
        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime); gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.1);
        osc.start(); osc.stop(audioCtx.currentTime + 0.1);
    } else if (type === 'gameover') {
        osc.type = 'sawtooth'; osc.frequency.setValueAtTime(200, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(50, audioCtx.currentTime + 1);
        gainNode.gain.setValueAtTime(0.2, audioCtx.currentTime); gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 1);
        osc.start(); osc.stop(audioCtx.currentTime + 1);
    }
}

function drawBlock(context, color, x, y, scale = 1) {
    const dx = x * BLOCK_SIZE * scale;
    const dy = y * BLOCK_SIZE * scale;
    const size = BLOCK_SIZE * scale;
    
    context.fillStyle = color;
    context.fillRect(dx, dy, size, size);
    context.strokeStyle = 'rgba(0,0,0,0.3)';
    context.lineWidth = 1;
    context.strokeRect(dx, dy, size, size);
    
    context.fillStyle = 'rgba(255, 255, 255, 0.3)';
    context.fillRect(dx, dy, size, size * 0.2);
    context.fillStyle = 'rgba(0, 0, 0, 0.2)';
    context.fillRect(dx, dy + size * 0.8, size, size * 0.2);
    context.fillStyle = 'rgba(0, 0, 0, 0.1)';
    context.fillRect(dx + size * 0.8, dy, size * 0.2, size);
}

function drawGhostBlock(context, color, x, y) {
    const dx = x * BLOCK_SIZE;
    const dy = y * BLOCK_SIZE;
    const size = BLOCK_SIZE;
    
    context.strokeStyle = color;
    context.lineWidth = 2;
    context.strokeRect(dx + 2, dy + 2, size - 4, size - 4);
    context.fillStyle = color + "22";
    context.fillRect(dx + 2, dy + 2, size - 4, size - 4);
}

let gameOverFlag = false;

function render(state) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    state.board.forEach((row, y) => {
        row.forEach((val, x) => {
            if (val !== 0) drawBlock(ctx, COLORS[val], x, y);
        });
    });

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

    if (state.current_piece) {
        const cp = state.current_piece;
        cp.matrix.forEach((row, y) => {
            row.forEach((val, x) => {
                if (val !== 0) drawBlock(ctx, COLORS[cp.type], cp.x + x, cp.y + y);
            });
        });
    }

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
    
    document.getElementById('score').innerText = state.score;
    document.getElementById('level').innerText = state.level;
    document.getElementById('lines').innerText = state.lines;
    
    // RENDERIZAR PROGRESO (Puntuación actual / Requerido para acabar el nivel)
    document.getElementById('level-progress').innerText = `${state.score} / ${state.target_score}`;

    if (state.game_over && !gameOverFlag) {
        document.getElementById('game-over').style.display = 'flex'; // Usamos flex para centrar botón
        playSound('gameover');
        gameOverFlag = true;
    }
}

function loopFetch() {
    fetch('/state')
        .then(res => res.json())
        .then(state => {
            render(state);
            setTimeout(loopFetch, 50);
        })
        .catch(err => {
            setTimeout(loopFetch, 1000);
        });
}

async function sendAction(action) {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    try {
        const response = await fetch('/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        const data = await response.json();
        if (data.event && data.event !== 'gameover') {
            playSound(data.event);
        }
    } catch(e) {}
}

// DETECTOR DE CLICK EN EL BOTÓN REINTENTAR
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

document.addEventListener('keydown', event => {
    if (gameOverFlag) return;
    if (event.keyCode === 37) sendAction('left');
    else if (event.keyCode === 39) sendAction('right');
    else if (event.keyCode === 40) sendAction('down');
    else if (event.keyCode === 38) sendAction('rotate');
});
document.addEventListener('click', () => { if(audioCtx.state === 'suspended') audioCtx.resume(); });

loopFetch();
