# -*- coding: utf-8 -*-
"""手机试玩：在电脑上开一个小服务器，手机和电脑连同一个 Wi-Fi，手机浏览器打开屏幕上印出来的网址就能玩。

    python tools/serve_phone.py            # 端口 8000，被占了就往后找
    python tools/serve_phone.py 9000       # 指定端口
（或者直接双击游戏目录里的「手机试玩.bat」）

为什么不能直接把 index.html 发到手机上双击打开：浏览器对 file:// 管得很严（画面、声音、开场视频都会出问题），
要用 http:// 打开；而且 iPhone 的 Safari 放视频 / 音频必须服务器支持“分段请求（Range）”，Python 自带的 http.server 不支持，这里补上了。

只在局域网里给同一个 Wi-Fi 的设备用；关掉这个窗口就停。Windows 第一次会弹“防火墙是否允许 Python 访问网络”，点“允许”（专用网络）。
想在手机上看按键长什么样但不想连 Wi-Fi：电脑浏览器打开 http://localhost:8000/?touch=1 也能看到（强制显示屏幕按键）。
"""
import http.server
import os
import re
import socket
import socketserver
import sys

GAME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Limited:
    """只读前 n 个字节的文件包装（给 206 分段响应用）。"""

    def __init__(self, f, n):
        self.f, self.n = f, n

    def read(self, k=-1):
        if self.n <= 0:
            return b""
        k = self.n if k is None or k < 0 else min(k, self.n)
        b = self.f.read(k)
        self.n -= len(b)
        return b

    def close(self):
        self.f.close()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=GAME, **kw)

    def log_message(self, fmt, *args):      # 不刷屏，只打印出错的请求
        if args and str(args[1]).startswith(("4", "5")):
            sys.stderr.write("  %s %s\n" % (self.address_string(), fmt % args))

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-cache")      # 改了代码，手机刷新就是新的
        super().end_headers()

    def send_head(self):
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        m = re.match(r"bytes=(\d*)-(\d*)$", (rng or "").strip())
        if not m or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        a, b = m.group(1), m.group(2)
        if a == "" and b == "":
            return super().send_head()
        if a == "":                               # bytes=-500：最后 500 个字节
            start, end = max(0, size - int(b)), size - 1
        else:
            start, end = int(a), (int(b) if b else size - 1)
        end = min(end, size - 1)
        if start > end or start >= size:
            self.send_error(416, "Requested Range Not Satisfiable")
            return None
        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        return Limited(f, end - start + 1)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def lan_ips():
    """这台电脑在局域网里的地址（192.168.* / 10.* / 172.16-31.*），手机连的是这个。"""
    found = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))          # 不会真的发包，只是让系统选出走哪块网卡
        found.append(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        found += socket.gethostbyname_ex(socket.gethostname())[2]
    except OSError:
        pass
    out = []
    for ip in found:
        p = ip.split(".")
        private = ip.startswith(("192.168.", "10.")) or (ip.startswith("172.") and 16 <= int(p[1]) <= 31)
        if private and ip not in out:
            out.append(ip)
    return out


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    srv = None
    for p in range(port, port + 20):
        try:
            srv = Server(("0.0.0.0", p), Handler)
            port = p
            break
        except OSError:
            continue
    if srv is None:
        print("端口都被占了，换一个：python tools/serve_phone.py 9000")
        return
    print("=" * 60)
    print("《银魂 像素剧场 · 游戏版》手机试玩")
    print("=" * 60)
    ips = lan_ips()
    if ips:
        print("手机和电脑连同一个 Wi-Fi，手机浏览器（Chrome / Safari）打开下面任意一个：")
        for ip in ips:
            print(f"    http://{ip}:{port}/")
        print("（几个地址里，一般 192.168.x.x 开头的那个是对的；打不开就换下一个）")
    else:
        print("没找到局域网地址——电脑连上 Wi-Fi 再来一次。")
    print()
    print(f"电脑上看：http://localhost:{port}/        电脑上强制显示屏幕按键：http://localhost:{port}/?touch=1")
    print("手机打开后：点右上角 ⛶ 全屏（iPhone：Safari 分享 → 添加到主屏幕，再从桌面图标打开）。")
    print("手机打不开：① 手机连的得是同一个 Wi-Fi（不是流量）；② Windows 防火墙弹窗点“允许”了吗；")
    print("            ③ 路由器开了“AP 隔离 / 客户端隔离”时设备之间互相访问不了，要在路由器里关掉。")
    print("关掉这个窗口（或按 Ctrl+C）就停止。")
    print()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
