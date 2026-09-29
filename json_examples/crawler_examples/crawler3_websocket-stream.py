"""WebSocket 订阅：实时数据流消费模式。"""
import json

# 同步演示：真实连接替换 ws.connect(...) 的目标地址
SAMPLE_MSGS = [
    {"channel": "trades", "data": {"price": 64500.1, "side": "buy"}},
    {"channel": "trades", "data": {"price": 64501.5, "side": "sell"}},
]
print("订阅 trades 频道 → 消费 2 条演示消息")
for msg in SAMPLE_MSGS:
    print(json.dumps(msg, ensure_ascii=False))
# 真实写法:
# from websocket import create_app  # pip install websocket-client
# ws = create_app("wss://stream.example.com/ws")
# ws.send(json.dumps({"op": "subscribe", "channel": "trades"}))
# while True: handle(json.loads(ws.recv()))
