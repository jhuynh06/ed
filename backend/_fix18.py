import pathlib
p = pathlib.Path(r"C:\Users\jason\Desktop\ed\firmware\AudioBridge.py")
content = p.read_text(encoding="utf-8")
content = content.replace(
    'async with websockets.connect(BACKEND_WS_URL) as ws:',
    'async with websockets.connect(BACKEND_WS_URL, ping_interval=None, ping_timeout=None, max_size=None) as ws:',
    1
)
p.write_text(content, encoding="utf-8")
print("OK")
