#!/usr/bin/env python3
"""
🍳 KITCHEN DISPLAY v3.1 — SmartWaiter
Экран кухни — повар видит заказы
Открыть: http://ROBOT_IP:8081
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json, threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, List


class KitchenState:
    def __init__(self):
        self.orders: Dict[str, Dict] = {}
        self.lock = threading.Lock()

    def add(self, order_id, table_id, items, lang):
        with self.lock:
            self.orders[order_id] = {
                "order_id": order_id,
                "table_id": table_id,
                "items":    items,
                "status":   "new",
                "time":     datetime.now().strftime("%H:%M:%S"),
            }

    def ready(self, order_id):
        with self.lock:
            if order_id in self.orders:
                self.orders[order_id]["status"] = "ready"

    def all(self) -> List[Dict]:
        with self.lock:
            return list(self.orders.values())


STATE  = KitchenState()
ROS_PUB = None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        if self.path == '/':
            self._html()
        elif self.path == '/api/orders':
            data = json.dumps(
                STATE.all(), ensure_ascii=False
            ).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path.startswith('/api/ready/'):
            oid = self.path.split('/')[-1]
            STATE.ready(oid)
            if ROS_PUB:
                msg = String()
                msg.data = json.dumps(
                    {"order_id": oid, "status": "ready"}
                )
                ROS_PUB.publish(msg)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

    def _html(self):
        html = """<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>🍳 Кухня</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial;background:#1a1a2e;color:#eee;padding:10px}
h1{text-align:center;padding:12px;background:#16213e;
   border-radius:10px;margin-bottom:12px}
#orders{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px}
.card{background:#16213e;border-radius:12px;padding:15px;
      border-left:5px solid #e94560}
.card.ready{border-left-color:#4caf50;opacity:0.6}
.card h2{color:#e94560;margin-bottom:8px}
.card.ready h2{color:#4caf50}
.time{font-size:0.8em;color:#aaa;margin-bottom:8px}
.item{background:#0f3460;border-radius:6px;padding:6px;margin:3px 0}
.btn{width:100%;padding:12px;background:#4caf50;color:white;
     border:none;border-radius:8px;font-size:1em;
     font-weight:bold;cursor:pointer;margin-top:8px}
.done{text-align:center;padding:10px;color:#4caf50;font-weight:bold}
.empty{text-align:center;padding:40px;color:#666}
#clock{text-align:center;font-size:2em;color:#e94560;padding:8px}
</style></head>
<body>
<h1>🍳 Кухня — SmartWaiter</h1>
<div id="clock"></div>
<div id="orders"><div class="empty">⏳ Ожидание...</div></div>
<script>
setInterval(()=>{
  document.getElementById('clock').textContent=
  new Date().toLocaleTimeString('ru-RU')
},1000)

async function ready(id){
  await fetch('/api/ready/'+id,{method:'POST'})
  load()
}

async function load(){
  const r=await fetch('/api/orders')
  const orders=await r.json()
  const d=document.getElementById('orders')
  if(!orders.length){
    d.innerHTML='<div class="empty">✅ Нет заказов</div>'
    return
  }
  d.innerHTML=orders.map(o=>`
    <div class="card ${o.status==='ready'?'ready':''}">
      <h2>🍽️ Стол №${o.table_id}</h2>
      <div class="time">⏰ ${o.time}</div>
      ${(o.items||[]).map(i=>
        `<div class="item">• ${i.name||i}</div>`
      ).join('')||'<div class="item">Заказ принят</div>'}
      ${o.status==='ready'
        ?'<div class="done">✅ ГОТОВО</div>'
        :`<button class="btn" onclick="ready('${o.order_id}')">
           ✅ ГОТОВО
         </button>`}
    </div>`).join('')
}
setInterval(load,3000)
load()
</script></body></html>"""
        e = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type','text/html;charset=utf-8')
        self.send_header('Content-Length', len(e))
        self.end_headers()
        self.wfile.write(e)


class KitchenDisplayNode(Node):

    def __init__(self):
        super().__init__('kitchen_display')
        self.get_logger().info("🍳 Kitchen Display v3.1...")

        global ROS_PUB
        self.pub = self.create_publisher(
            String, '/kitchen/order_ready', 10
        )
        ROS_PUB = self.pub

        self.create_subscription(
            String, '/restaurant/log', self._cb_log, 10
        )

        self.declare_parameter('port', 8081)
        port = self.get_parameter('port').value
        self.server = HTTPServer(('0.0.0.0', port), Handler)
        threading.Thread(
            target=self.server.serve_forever, daemon=True
        ).start()
        self.get_logger().info(
            f"✅ Кухня: http://ROBOT_IP:{port}"
        )

    def _cb_log(self, msg: String):
        try:
            d = json.loads(msg.data)
            if d.get("action") == "order_created":
                STATE.add(
                    d.get("order_id",""),
                    d.get("table", 0),
                    d.get("items", []),
                    d.get("lang","ru")
                )
        except Exception:
            pass

    def destroy_node(self):
        self.server.shutdown()
        super().destroy_node()


def main():
    rclpy.init()
    node = KitchenDisplayNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
