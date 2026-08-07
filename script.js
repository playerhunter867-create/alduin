const target = document.getElementById('target');
const port = document.getElementById('port');
const threads = document.getElementById('threads');
const duration = document.getElementById('duration');
const payload = document.getElementById('payload');
const ssl = document.getElementById('ssl');
const method = document.getElementById('method');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const presetBtn = document.getElementById('presetBtn');
const sentSpan = document.getElementById('sent');
const failedSpan = document.getElementById('failed');
const bytesSpan = document.getElementById('bytes');
const timeSpan = document.getElementById('time');
const progressFill = document.getElementById('progressFill');
const statusBadge = document.getElementById('statusBadge');
const logDiv = document.getElementById('log');

let ws = null;
let statsInterval = null;
let chartInterval = null;
let startTime = 0;
let totalDuration = 30;
let chartData = [];

// Canvas для графика
const canvas = document.getElementById('chartCanvas');
const ctx = canvas.getContext('2d');

function log(msg, type = 'info') {
    const line = document.createElement('div');
    line.className = type;
    line.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
    logDiv.appendChild(line);
    logDiv.scrollTop = logDiv.scrollHeight;
}

function updateStatus(text, color = '#88aaff') {
    statusBadge.textContent = text;
    statusBadge.style.color = color;
    statusBadge.style.borderColor = color;
}

function drawChart() {
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    if (chartData.length < 2) return;
    ctx.strokeStyle = '#00ff88';
    ctx.lineWidth = 2;
    ctx.beginPath();
    const max = Math.max(...chartData, 1);
    for (let i = 0; i < chartData.length; i++) {
        const x = (i / chartData.length) * w;
        const y = h - (chartData[i] / max) * h * 0.85 - 5;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.fillStyle = '#00ff8822';
    ctx.fill();
}

async function startAttack(configOverride = null) {
    const config = configOverride || {
        target: target.value.trim(),
        port: parseInt(port.value) || 80,
        threads: parseInt(threads.value) || 50,
        duration: parseInt(duration.value) || 30,
        payload_size: parseInt(payload.value) || 1024,
        use_ssl: ssl.value === 'true',
        method: method.value,
        proxy_list: []
    };

    if (!config.target) {
        log('❌ Введите цель!', 'error');
        return;
    }

    try {
        startBtn.disabled = true;
        stopBtn.disabled = false;
        presetBtn.disabled = true;
        logDiv.innerHTML = '';
        chartData = [];
        totalDuration = config.duration;
        updateStatus('⏳ АТАКА ИДЁТ...', '#ffaa44');
        log(`🚀 Запуск атаки на ${config.target}:${config.port} (${config.method})`, 'info');
        log(`🧵 Потоков: ${config.threads}, ⏱️ ${config.duration}с`, 'info');

        const res = await fetch('/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        const data = await res.json();
        if (data.status === 'started') {
            log(`✅ ${data.message}`, 'success');
            startTime = Date.now();
            statsInterval = setInterval(fetchStats, 400);
            chartInterval = setInterval(updateChart, 600);
        } else {
            log(`❌ ${data.message}`, 'error');
            resetUI();
        }
    } catch (e) {
        log(`❌ Ошибка: ${e.message}`, 'error');
        resetUI();
    }
}

async function stopAttack() {
    try {
        const res = await fetch('/stop', { method: 'POST' });
        const data = await res.json();
        log(`⏹️ ${data.message}`, 'info');
        updateStatus('⏹️ ОСТАНОВЛЕНА', '#ff5577');
        clearIntervals();
        resetUI();
    } catch (e) {
        log(`❌ Ошибка остановки: ${e.message}`, 'error');
    }
}

function clearIntervals() {
    if (statsInterval) clearInterval(statsInterval);
    if (chartInterval) clearInterval(chartInterval);
    statsInterval = null;
    chartInterval = null;
}

function resetUI() {
    startBtn.disabled = false;
    stopBtn.disabled = true;
    presetBtn.disabled = false;
    if (!document.querySelector('#log .error')) {
        // если не было ошибки, ставим статус готов
        updateStatus('⚡ ГОТОВ', '#88aaff');
    }
}

async function fetchStats() {
    try {
        const res = await fetch('/stats');
        const data = await res.json();
        sentSpan.textContent = data.sent;
        failedSpan.textContent = data.failed;
        bytesSpan.textContent = data.bytes;
        const elapsed = ((Date.now() - startTime) / 1000);
        timeSpan.textContent = elapsed.toFixed(1);
        const progress = Math.min((elapsed / totalDuration) * 100, 100);
        progressFill.style.width = progress + '%';

        if (!data.active && sentSpan.textContent > 0) {
            clearIntervals();
            resetUI();
            updateStatus('✅ ЗАВЕРШЕНА', '#00ff88');
            log('🏁 Атака завершена автоматически', 'info');
        }
    } catch (e) { /* ignore */ }
}

function updateChart() {
    const sent = parseInt(sentSpan.textContent) || 0;
    chartData.push(sent);
    if (chartData.length > 60) chartData.shift();
    drawChart();
}

function connectWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${location.host}/ws`;
    ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'finished') {
                log(`🏁 Завершено: ${data.stats.sent} отправлено, ${data.stats.failed} ошибок`, 'info');
                updateStatus('✅ ЗАВЕРШЕНА', '#00ff88');
                clearIntervals();
                resetUI();
            }
        } catch (e) {}
    };
    ws.onclose = () => setTimeout(connectWebSocket, 3000);
}

// === ПРЕСЕТЫ ===
function presetLight() {
    target.value = '127.0.0.1';
    port.value = 80;
    threads.value = 10;
    duration.value = 15;
    payload.value = 512;
    ssl.value = 'false';
    method.value = 'http';
    log('🌱 Установлен лёгкий режим (10 потоков, 15с)', 'info');
}
function presetMedium() {
    target.value = '127.0.0.1';
    port.value = 80;
    threads.value = 50;
    duration.value = 30;
    payload.value = 1024;
    ssl.value = 'false';
    method.value = 'udp';
    log('🌿 Установлен средний режим (50 потоков, 30с)', 'info');
}
function presetHeavy() {
    target.value = '127.0.0.1';
    port.value = 80;
    threads.value = 150;
    duration.value = 45;
    payload.value = 2048;
    ssl.value = 'false';
    method.value = 'tcp';
    log('🌳 Установлен тяжёлый режим (150 потоков, 45с)', 'info');
}
function presetUltimate() {
    target.value = '127.0.0.1';
    port.value = 80;
    threads.value = 300;
    duration.value = 60;
    payload.value = 4096;
    ssl.value = 'false';
    method.value = 'hybrid';
    log('💀 Установлен ультимативный режим (300 потоков, 60с, гибрид)', 'info');
}

// === КНОПКИ ===
startBtn.addEventListener('click', startAttack);
stopBtn.addEventListener('click', stopAttack);
presetBtn.addEventListener('click', () => {
    if (confirm('Запустить быстрый тест на 127.0.0.1:80 (30 потоков, 20с, HTTP)?')) {
        startAttack({
            target: '127.0.0.1',
            port: 80,
            threads: 30,
            duration: 20,
            payload_size: 1024,
            use_ssl: false,
            method: 'http',
            proxy_list: []
        });
    }
});

window.onload = function() {
    connectWebSocket();
    log('🛠️ Готов к работе. Настройте параметры и запустите.', 'info');
    updateStatus('⚡ ГОТОВ', '#88aaff');
    drawChart();
};

// Доступ к пресетам из HTML
window.presetLight = presetLight;
window.presetMedium = presetMedium;
window.presetHeavy = presetHeavy;
window.presetUltimate = presetUltimate;