# -*- coding: utf-8 -*-
import os
import sys
import time
import shutil
import socket
import subprocess
import threading
import importlib.util
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime

# ============================================================
# W.A 1.6.1 ELITE — Windows Security & Analysis Suite (Advanced)
# ============================================================

APP_NAME = "W.A"
APP_VERSION = "1.6.1 Elite Advanced"
APP_TITLE = "Windows Security & Analysis Matrix"
LOCALHOST = "127.0.0.1"

BG = "#000000"
GREEN = "#00ff41"
DARK_GREEN = "#008f11"
CYAN = "#00ffff"
YELLOW = "#ffff00"
RED = "#ff3030"
WHITE = "#d0ffd0"

FONT = ("Consolas", 13)
FONT_SMALL = ("Consolas", 10)


# ============================================================
# DEPENDENCY CHECKER
# ============================================================

def package_exists(name):
    return importlib.util.find_spec(name) is not None

def install_requests():
    if package_exists("requests"):
        return True
    try:
        py = sys.executable
        if os.name == "nt" and py.lower().endswith("pythonw.exe"):
            cand = os.path.join(os.path.dirname(py), "python.exe")
            if os.path.exists(cand): py = cand
        subprocess.run([py, "-m", "pip", "install", "requests"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        return package_exists("requests")
    except Exception:
        return False

REQUESTS_OK = install_requests()
requests = __import__("requests") if REQUESTS_OK else None


# ============================================================
# SAFE PROCESS RUNNER
# ============================================================

def run_process(cmd, timeout=120):
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return res.returncode, res.stdout
    except FileNotFoundError:
        return -1, "Program not found."
    except subprocess.TimeoutExpired:
        return -2, "Operation timed out."
    except Exception as e:
        return -3, str(e)


# ============================================================
# MAIN APPLICATION
# ============================================================

class WAApp:
    def __init__(self, root):
        self.root = root
        self.history = []
        self.history_index = 0
        self.command_running = False
        self.spoofed_ip = None
        
        # Trạng thái God Mode và Background
        self.god_mode_active = False
        self.bg_image_path = None
        self.matrix_rain_active = True

        self.original_ipv4 = self.get_local_ipv4()

        self.root.title(f"{APP_NAME} — {APP_TITLE}")
        self.root.configure(bg=BG)
        self.root.attributes("-fullscreen", True, "-topmost", True)

        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False) if self.root.attributes("-fullscreen") else self.exit_app())
        self.root.bind("<F11>", lambda e: self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen")))

        self.build_gui()
        self.print_banner_and_startup()

    def get_local_ipv4(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "192.168.1.100"

    def build_gui(self):
        # Header Matrix Style
        self.header = tk.Frame(self.root, bg=BG)
        self.header.pack(fill="x", padx=20, pady=(15, 5))

        self.lbl_title_matrix = tk.Label(self.header, text="╔═W.A═MATRIX═╗", font=("Consolas", 18, "bold"), fg=GREEN, bg=BG)
        self.lbl_title_matrix.pack(side="left")
        
        self.lbl_ver = tk.Label(self.header, text=f"  [{APP_VERSION}]", font=("Consolas", 11, "bold"), fg=CYAN, bg=BG)
        self.lbl_ver.pack(side="left", pady=(5, 0))
        
        self.status_label = tk.Label(self.header, text="● OFFLINE", font=("Consolas", 11, "bold"), fg=RED, bg=BG)
        self.status_label.pack(side="right", pady=(5, 0))

        tk.Frame(self.root, bg=DARK_GREEN, height=1).pack(fill="x", padx=20)

        # Terminal Area
        self.term_frame = tk.Frame(self.root, bg=BG)
        self.term_frame.pack(fill="both", expand=True, padx=20, pady=8)

        self.terminal = tk.Text(self.term_frame, bg=BG, fg=GREEN, insertbackground=GREEN, selectbackground=DARK_GREEN, selectforeground=WHITE, font=FONT, wrap="word", borderwidth=0, highlightthickness=0, padx=5, pady=5)
        self.terminal.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(self.term_frame, command=self.terminal.yview)
        scrollbar.pack(side="right", fill="y")
        self.terminal.configure(yscrollcommand=scrollbar.set, state="disabled")

        # Input Area
        input_frame = tk.Frame(self.root, bg=BG)
        input_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.prompt_label = tk.Label(input_frame, text="W.A@Matrix:~>", font=("Consolas", 12, "bold"), fg=GREEN, bg=BG)
        self.prompt_label.pack(side="left")

        self.command_entry = tk.Entry(input_frame, bg="#050505", fg=GREEN, insertbackground=GREEN, font=FONT, borderwidth=0, highlightthickness=1, highlightbackground=DARK_GREEN, highlightcolor=GREEN)
        self.command_entry.pack(side="left", fill="x", expand=True, padx=(10, 10), ipady=6)
        self.command_entry.bind("<Return>", self.submit_command)
        self.command_entry.bind("<Up>", self.history_up)
        self.command_entry.bind("<Down>", self.history_down)

        tk.Button(input_frame, text="RUN", command=self.submit_command, bg="#001a00", fg=GREEN, activebackground="#003300", font=("Consolas", 10, "bold"), relief="solid", padx=12, pady=5).pack(side="right")
        tk.Button(input_frame, text="EXIT", command=self.exit_app, bg="#1a0000", fg=RED, activebackground="#330000", font=("Consolas", 10, "bold"), relief="solid", padx=12, pady=5).pack(side="right", padx=(0, 6))

    # ========================================================
    # TYPING ANIMATION & OUTPUT WRITER
    # ========================================================

    def write(self, text="", color=GREEN):
        """In chuỗi trực tiếp ra terminal an toàn"""
        def _write():
            self.terminal.configure(state="normal")
            tag = f"tag_{color}_{time.time()}"
            self.terminal.tag_configure(tag, foreground=color)
            self.terminal.insert("end", text + "\n", tag)
            self.terminal.see("end")
            self.terminal.configure(state="disabled")
        self.root.after(0, _write)

    def write_hacker_typing(self, text_block, color=GREEN, delay=0.008):
        """Hiệu ứng đánh chữ kiểu hacker mượt mà từng ký tự"""
        def worker():
            for line in text_block.splitlines():
                self.terminal.configure(state="normal")
                tag = f"tag_{color}_{time.time()}"
                self.terminal.tag_configure(tag, foreground=color)
                
                # Chèn dòng trống trước để gõ dần
                self.terminal.insert("end", "\n", tag)
                self.terminal.see("end")
                self.terminal.configure(state="disabled")
                
                for char in line:
                    def _append_char(c=char, t=tag):
                        self.terminal.configure(state="normal")
                        self.terminal.insert("end", c, t)
                        self.terminal.see("end")
                        self.terminal.configure(state="disabled")
                    self.root.after(0, _append_char)
                    time.sleep(delay)
        threading.Thread(target=worker, daemon=True).start()

    # ========================================================
    # BANNER & STARTUP SEQUENCE
    # ========================================================

    def print_banner_and_startup(self):
        banner = """
    ██╗  ██╗       █████╗ 
    ██║  ██║      ██╔══██╗
    ██║  ██║  ██╗ ███████║
    ██║  ██║  ██╗ ██╔══██║
    ╚█████╔╝  ██║ ██║  ██║
     ╚════╝   ╚═╝ ╚═╝  ╚═╝
"""
        self.write(banner, GREEN)
        self.write(" >>> W.A 1.6.1 ELITE — ADVANCED WINDOWS MATRIX ENVIRONMENT <<<", CYAN)
        self.write("────────────────────────────────────────────────────────────", DARK_GREEN)
        
        steps = [
            "Bypassing kernel security layers...",
            "Loading Nmap & TShark automation hooks...",
            "Initializing Npcap packet capture driver...",
            "Binding new security tools & Network inspection engine...",
            "Matrix interface operational."
        ]
        self._run_startup_step(steps, 0)

    def _run_startup_step(self, steps, idx):
        if idx >= len(steps):
            self.status_label.config(text="● SECURE", fg=GREEN)
            self.write("\n[+] System initialized successfully.", GREEN)
            self.write("[i] Gõ 'help' để xem hướng dẫn chi tiết hoặc 'god_mode' để kích hoạt quyền tối cao.", CYAN)
            self.write("", GREEN)
            self.command_entry.focus_set()
            return

        self.write(f"[+] {steps[idx]}", GREEN)
        self.root.after(250, lambda: self._run_startup_step(steps, idx + 1))

    # ========================================================
    # HISTORY
    # ========================================================

    def history_up(self, event=None):
        if not self.history: return "break"
        if self.history_index > 0: self.history_index -= 1
        self.command_entry.delete(0, "end")
        self.command_entry.insert(0, self.history[self.history_index])
        return "break"

    def history_down(self, event=None):
        if not self.history: return "break"
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            val = self.history[self.history_index]
        else:
            self.history_index = len(self.history)
            val = ""
        self.command_entry.delete(0, "end")
        self.command_entry.insert(0, val)
        return "break"

    # ========================================================
    # COMMAND PARSER & EXECUTION
    # ========================================================

    def submit_command(self, event=None):
        if self.command_running:
            self.write("[!] Tiến trình khác đang thực thi...", YELLOW)
            return "break"

        cmd = self.command_entry.get().strip()
        if not cmd: return "break"

        self.command_entry.delete(0, "end")
        self.history.append(cmd)
        self.history_index = len(self.history)

        timestamp = datetime.now().strftime("%H:%M:%S")
        prompt_str = "W.A@GodMode:~>" if self.god_mode_active else "W.A@Matrix:~>"
        self.write(f"[{timestamp}] {prompt_str} {cmd}", CYAN)
        
        if self.god_mode_active:
            self.execute_god_mode_command(cmd)
        else:
            self.execute_command(cmd)
        return "break"

    def execute_god_mode_command(self, cmd):
        cmd_lower = cmd.lower()
        
        if cmd_lower == "exit_god":
            self.god_mode_active = False
            self.prompt_label.config(text="W.A@Matrix:~>", fg=GREEN)
            self.status_label.config(text="● SECURE", fg=GREEN)
            self.write("[-] Đã thoát khỏi GOD MODE. Trở về trạng thái an toàn.", YELLOW)
            return
        elif cmd_lower == "change_background":
            self.cmd_change_background()
            return
        elif cmd_lower.startswith("matrix_color_"):
            self.cmd_change_matrix_color(cmd.split("_")[-1])
            return
        elif cmd_lower == "matrix_toggle":
            self.cmd_matrix_toggle()
            return

        self.command_running = True
        self.status_label.config(text="● CMD EXEC", fg=RED)
        self.write(f"[*] Đang thực thi trực tiếp qua Windows CMD...", CYAN)

        def worker():
            code, out = run_process(["cmd.exe", "/c", cmd], timeout=180)
            def finish():
                self.command_running = False
                self.status_label.config(text="● GOD MODE", fg=RED)
                if out: 
                    self.write(out, WHITE if code == 0 else YELLOW)
                else:
                    self.write("[+] Lệnh đã thực thi thành công (Không có output trả về).", GREEN)
            self.root.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    def execute_command(self, cmd):
        parts = cmd.split()
        if not parts: return
        base = parts[0]
        base_lower = base.lower()

        # --- GOD MODE TRIGGER ---
        if base_lower == "god_mode":
            self.god_mode_active = True
            self.prompt_label.config(text="W.A@GodMode:~>", fg=RED)
            self.status_label.config(text="● GOD MODE", fg=RED)
            box_text = """
╔══════════════════════════════════════════════════════════╗
║                 ⚠️  ACTIVATED: GOD MODE ⚠️               ║
║ Mọi lệnh bạn gõ sẽ được chuyển thẳng xuống Windows CMD    ║
║ của máy tính. Màn hình Hack GUI chỉ là cổng giao tiếp!   ║
║ Lệnh đặc biệt trong God Mode:                            ║
║  - change_background : Mở hộp thoại chọn ảnh làm nền GUI  ║
║  - matrix_color_<hex>: Đổi màu chữ Matrix (vd: #ff0000)   ║
║  - exit_god          : Thoát chế độ quyền năng tối cao   ║
╚══════════════════════════════════════════════════════════╝
"""
            self.write(box_text, RED)
            return

        # --- SYSTEM COMMANDS ---
        if base_lower in ("exit", "quit"):
            self.exit_app()
        elif base_lower == "help":
            if len(parts) == 1:
                self.help_general()
            else:
                self.help_topic(parts[1].lower())
        elif base_lower == "version":
            self.write(f"{APP_NAME} {APP_VERSION} - Advanced Full Edition", GREEN)
        elif base_lower == "status":
            self.status()
        elif base_lower in ("clear", "cls"):
            self.clear_terminal()
        elif base_lower == "history":
            for i, c in enumerate(self.history, 1):
                self.write(f"{i:03d}  {c}", GREEN)

        # --- GÓI & ĐỔI MẠNG ---
        elif base_lower.startswith("git_"):
            self.cmd_git_download(base[4:])
        elif base_lower.startswith("ch_adr_"):
            self.cmd_change_ipv4(base[7:])
        elif base_lower == "re_adr":
            self.cmd_re_ipv4()
        elif base_lower.startswith("ch_online_"):
            self.cmd_ch_online(base[10:])
        elif base_lower == "re_online":
            self.cmd_re_online()

        # --- NETWORK & WEB COMMANDS ---
        elif base_lower == "ipconfig":
            self.run_background(["ipconfig", "/all"], "Lấy toàn bộ thông tin IP & Adapters", 30)
        elif base_lower == "ipv4":
            self.cmd_ipv4()
        elif base_lower == "ipv6":
            self.cmd_ipv6()
        elif base_lower == "ip_on":
            self.cmd_ip_on()
        elif base.startswith("$$$_"):
            self.cmd_full_web_scan(base[4:])
        elif base.startswith("#show#_"):
            self.cmd_show_server_ip(base[7:])
        elif base == "SECTO3_ME":
            self.cmd_secto3_me()
        elif base.startswith("PP_"):
            self.cmd_pp(base[3:])
        elif base == "PK":
            self.cmd_pk()

        # --- MODULES: NMAP, TSHARK, NPCAP, REQUEST, TOOLS ---
        elif base_lower.startswith("nmap_"):
            self.handle_nmap_command(base_lower)
        elif base_lower == "nmap":
            self.help_nmap_streamlined()
        elif base_lower.startswith("wireshark_") or base_lower.startswith("tshark_"):
            self.handle_tshark_command(base_lower)
        elif base_lower in ("wireshark", "tshark"):
            self.help_wireshark_streamlined()
        elif base_lower.startswith("npcap_"):
            self.handle_npcap_command(base_lower)
        elif base_lower == "npcap":
            self.help_npcap_streamlined()
        elif base_lower.startswith("request_"):
            self.handle_request_command(base_lower)
        elif base_lower == "request":
            self.help_request_streamlined()
        elif base_lower.startswith("tool_") or base_lower in ("dns", "portscan", "procs"):
            self.handle_new_tools(base_lower, parts)

        else:
            self.write(f"[!] Lệnh không xác định: {cmd}", YELLOW)
            self.write("[i] Gõ 'help' để xem danh sách toàn bộ lệnh hỗ trợ.", CYAN)

    # ========================================================
    # CUSTOM FEATURES & GOD MODE ACTIONS
    # ========================================================

    def cmd_change_background(self):
        file_path = filedialog.askopenfilename(
            title="Chọn ảnh nền cho Hack GUI",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if file_path:
            self.bg_image_path = file_path
            self.write(f"[+] Đã ghi nhận đường dẫn ảnh nền: {file_path}", GREEN)

    def cmd_change_matrix_color(self, hex_code):
        if not hex_code.startswith("#"):
            hex_code = "#" + hex_code
        try:
            self.terminal.configure(fg=hex_code, insertbackground=hex_code)
            self.prompt_label.configure(fg=hex_code)
            self.write(f"[+] Đã chuyển đổi màu hệ thống sang: {hex_code}", hex_code)
        except Exception as e:
            self.write(f"[!] Lỗi đổi màu: {e}", YELLOW)

    def cmd_matrix_toggle(self):
        self.matrix_rain_active = not self.matrix_rain_active
        self.write(f"[*] Trạng thái giao diện Matrix: {'BẬT' if self.matrix_rain_active else 'TẮT'}", CYAN)

    def cmd_git_download(self, url):
        if not url:
            self.write("[!] Cú pháp: git_<url>", YELLOW)
            return
        if not requests:
            self.write("[!] Thiếu thư viện requests.", RED)
            return
        self.command_running = True
        self.status_label.config(text="● DOWNLOADING", fg=YELLOW)
        self.write(f"[*] Đang tải gói từ: {url}...", CYAN)

        def worker():
            try:
                folder = "git_package_" + datetime.now().strftime("%H%M%S")
                os.makedirs(folder, exist_ok=True)
                fname = url.split("/")[-1].split("?")[0] or "package.zip"
                fpath = os.path.join(folder, fname)
                r = requests.get(url, stream=True, timeout=30)
                if r.status_code == 200:
                    with open(fpath, 'wb') as f:
                        for chunk in r.iter_content(8192):
                            if chunk: f.write(chunk)
                    msg, code = f"[+] Tải thành công! Thư mục lưu: {os.path.abspath(folder)}", 0
                else:
                    msg, code = f"[!] Lỗi HTTP: {r.status_code}", 1
            except Exception as e:
                msg, code = f"[!] Lỗi tải: {e}", 1

            def finish():
                self.command_running = False
                self.status_label.config(text="● SECURE", fg=GREEN)
                self.write(msg, GREEN if code == 0 else RED)
            self.root.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    def cmd_change_ipv4(self, new_ip):
        self.write(f"[*] Đang đổi IPv4 sang: {new_ip}...", CYAN)
        code, out = run_process(["netsh", "interface", "show", "interface"])
        if code != 0:
            self.write("[!] Không đọc được cấu hình mạng.", RED)
            return
        iface = "Wi-Fi"
        for line in out.splitlines():
            if "Connected" in line or "Đã kết nối" in line:
                parts = line.split()
                if parts:
                    iface = " ".join(parts[3:]) if len(parts) > 3 else parts[-1]
                    break
        c_code, _ = run_process(["netsh", "interface", "ipv4", "set", "address", f"name={iface}", "source=static", f"addr={new_ip}", "mask=255.255.255.0", "gateway=none"])
        if c_code == 0:
            self.write(f"[+] Đổi IPv4 thành công trên card [{iface}] sang {new_ip}", GREEN)
        else:
            self.write("[!] Thất bại! Cần chạy ứng dụng với quyền Administrator.", YELLOW)

    def cmd_re_ipv4(self):
        self.cmd_change_ipv4(self.original_ipv4)

    def cmd_ch_online(self, online_ip):
        self.spoofed_ip = online_ip
        self.write(f"[+] Đã chuyển hướng IP Online giả lập: {self.spoofed_ip}", GREEN)

    def cmd_re_online(self):
        self.spoofed_ip = None
        self.write("[+] Đã khôi phục IP thực tế.", GREEN)

    def cmd_ipv4(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.write(f"[+] IPv4 (Local): {s.getsockname()[0]}", GREEN)
            s.close()
        except Exception as e:
            self.write(f"[!] Lỗi: {e}", RED)

    def cmd_ipv6(self):
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET6):
                ipv6 = info[4][0]
                if ipv6 and not ipv6.startswith("fe80"):
                    self.write(f"[+] IPv6: {ipv6}", GREEN)
                    return
            self.write("[!] Không tìm thấy IPv6 toàn cục.", YELLOW)
        except Exception as e:
            self.write(f"[!] Lỗi: {e}", RED)

    def cmd_ip_on(self):
        if self.spoofed_ip:
            self.write(f"[+] Public IP (Spoofed): {self.spoofed_ip}", CYAN)
            return
        self.command_running = True
        self.status_label.config(text="● FETCHING", fg=YELLOW)
        def worker():
            ip = "Không lấy được"
            if requests:
                try: ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
                except: pass
            def finish():
                self.command_running = False
                self.status_label.config(text="● SECURE", fg=GREEN)
                self.write(f"[+] Public IP: {ip}", GREEN)
            self.root.after(0, finish)
        threading.Thread(target=worker, daemon=True).start()

    def cmd_full_web_scan(self, url):
        clean = url.replace("https://", "").replace("http://", "").split("/")[0].strip()
        self.command_running = True
        self.status_label.config(text="● SCANNING", fg=YELLOW)
        def worker():
            lines = [f"\n=== WEB SCAN: {clean} ==="]
            try:
                ips = list(set([item[4][0] for item in socket.getaddrinfo(clean, None)]))
                lines.append(f"[+] Server IP(s): {', '.join(ips)}")
            except Exception as e:
                lines.append(f"[!] Lỗi phân giải IP: {e}")
            out = "\n".join(lines)
            def finish():
                self.command_running = False
                self.status_label.config(text="● SECURE", fg=GREEN)
                self.write(out, GREEN)
            self.root.after(0, finish)
        threading.Thread(target=worker, daemon=True).start()

    def cmd_show_server_ip(self, url):
        clean = url.replace("https://", "").replace("http://", "").split("/")[0].strip()
        try:
            self.write(f"[+] Host: {clean} -> IP: {socket.gethostbyname(clean)}", GREEN)
        except Exception as e:
            self.write(f"[!] Lỗi: {e}", RED)

    def cmd_secto3_me(self):
        self.run_background(["arp", "-a"], "Quét thiết bị mạng LAN (ARP Scan)", 20)

    def cmd_pp(self, ip):
        self.spoofed_ip = ip
        self.write(f"[+] Giả lập IP Online: {ip}", GREEN)

    def cmd_pk(self):
        self.spoofed_ip = None
        self.write("[+] Đã hủy giả lập IP Online.", GREEN)

    # ========================================================
    # ADVANCED TYPING HELP SYSTEM
    # ========================================================

    def help_general(self):
        text = """
============================================================
           W.A 1.6.1 ELITE — ADVANCED HELP MENU            
============================================================
[1] HỆ THỐNG & ĐIỀU HƯỚNG:
  help                     - Hiển thị menu tổng quan này
  help <module>            - Xem chi tiết lệnh (nmap|wireshark|npcap|request|tools)
  status                   - Kiểm tra trạng thái hệ thống, thư viện và tiến trình
  clear / cls              - Xóa màn hình terminal và nạp lại Banner
  history                  - Xem lịch sử các lệnh đã gõ trong phiên làm việc
  version                  - Kiểm tra phiên bản hiện tại
  exit / quit              - Thoát khỏi ứng dụng

[2] CHẾ ĐỘ TỐI CAO (GOD MODE & GUI CUSTOMIZATION):
  god_mode                 - Kích hoạt God Mode (Điều khiển trực tiếp Windows CMD)
  change_background        - Mở cửa sổ hệ thống chọn hình nền cho Hack GUI
  matrix_color_<hex>       - Đổi màu toàn bộ chữ ma trận (vd: matrix_color_ff0000)
  matrix_toggle            - Bật/tắt trạng thái giao diện ma trận
  exit_god                 - Thoát khỏi God Mode, trở về trạng thái an toàn

[3] QUẢN LÝ MẠNG & TẢI GÓI:
  git_<url>                - Tải trực tiếp gói/file từ URL vào thư mục gom gọn
  ch_adr_<ip_v4>           - Cấu hình đổi IPv4 nội bộ sang địa chỉ tĩnh mới
  re_adr                   - Khôi phục lại IPv4 gốc ban đầu của máy
  ch_online_<ip>           - Đổi IP online giả lập (VPN/Proxy mode trong ứng dụng)
  re_online                - Hủy bỏ IP giả lập, khôi phục IP online thực tế

[4] TRA CỨU & KIỂM TRA MẠNG:
  ipconfig                 - Lấy toàn bộ thông tin cấu hình IP & Network Adapters
  ipv4 / ipv6              - Tra cứu địa chỉ IPv4 và IPv6 nội bộ
  ip_on                    - Tra cứu Public IP (IP Internet thực tế)
  $$$_<url>                - Phân tích chuyên sâu web (Server IP, cổng mở, DNS)
  #show#_<url>             - Truy vấn nhanh IP máy chủ của website
  SECTO3_ME                - Quét danh sách các thiết bị trong mạng LAN nội bộ
  PP_<ip> / PK             - Giả lập nhanh / Khôi phục IP Online

[5] CÔNG CỤ BỔ TRỢ MỚI (TOOLS):
  tool_dns <domain>        - Tra cứu DNS chi tiết (A, AAAA, MX, NS)
  tool_portscan <ip>       - Quét nhanh các cổng phổ biến trên mục tiêu
  tool_procs               - Liệt kê toàn bộ tiến trình hệ thống đang chạy
  tool_netstat             - Hiển thị bảng kết nối mạng và port đang mở
  tool_ping <target>       - Kiểm tra độ trễ kết nối mạng tới IP/Domain
  tool_sysinfo             - Trích xuất toàn bộ thông tin hệ thống Windows
  tool_wifi                - Liệt kê toàn bộ profile Wi-Fi đã lưu trên máy
============================================================
"""
        self.write_hacker_typing(text, GREEN, delay=0.002)

    def help_topic(self, topic):
        if "nmap" in topic: self.help_nmap_streamlined()
        elif "wireshark" in topic or "tshark" in topic: self.help_wireshark_streamlined()
        elif "npcap" in topic: self.help_npcap_streamlined()
        elif "request" in topic: self.help_request_streamlined()
        elif "tool" in topic: self.help_tools_streamlined()
        else: self.write(f"[!] Không tìm thấy chủ đề trợ giúp: {topic}", YELLOW)

    def help_nmap_streamlined(self):
        self.write("""
--- NMAP MODULE GUIDE ---
  • nmap_host_<ip>     - Ping quét máy chủ trực tuyến (-sn)
  • nmap_all_<ip>      - Quét toàn bộ 65535 cổng mở (-p-)
  • nmap_services_<ip> - Quét phát hiện dịch vụ và phiên bản (-sV)
  • nmap_os_<ip>       - Nhận diện hệ điều hành mục tiêu (-O)
""", CYAN)

    def help_wireshark_streamlined(self):
        self.write("""
--- WIRESHARK / TSHARK MODULE GUIDE ---
  • wireshark_interfaces - Liệt kê các card mạng có thể bắt gói tin (-D)
  • wireshark_capture    - Mở giao diện cấu hình bắt gói tin trực tiếp (.pcapng)
  • wireshark_filter     - Lọc dữ liệu tệp pcap theo bộ lọc hiển thị (-Y)
  • wireshark_stats      - Thống kê giao thức mạng từ tệp lưu trữ
""", CYAN)

    def help_npcap_streamlined(self):
        self.write("""
--- NPCAP MODULE GUIDE ---
  • npcap_status   - Kiểm tra trạng thái service Npcap trên Windows
  • npcap_adapters - Kiểm tra danh sách card mạng hỗ trợ Npcap
  • npcap_restart  - Khởi động lại dịch vụ driver Npcap
""", CYAN)

    def help_request_streamlined(self):
        self.write("""
--- HTTP REQUEST MODULE GUIDE ---
  • request_get  - Gửi yêu cầu HTTP GET tới Localhost / Web app
  • request_post - Gửi yêu cầu HTTP POST kèm dữ liệu body
""", CYAN)

    def help_tools_streamlined(self):
        self.write("""
--- TOOLS MODULE GUIDE ---
  • tool_dns <domain>    - Tra cứu chi tiết các bản ghi DNS của tên miền
  • tool_portscan <ip>   - Kiểm tra nhanh các cổng phổ biến (TCP Connect Scan)
  • tool_procs           - Liệt kê toàn bộ tiến trình đang chạy trên hệ thống
  • tool_netstat         - Xem các kết nối TCP/UDP đang hoạt động
  • tool_ping <target>   - Gói ICMP Ping kiểm tra đường truyền
  • tool_sysinfo         - Lấy thông tin chi tiết cấu hình máy tính
  • tool_wifi            - Xem danh sách tên các mạng Wi-Fi đã lưu
""", CYAN)

    # ========================================================
    # STATUS & SYSTEM MANAGEMENT
    # ========================================================

    def status(self):
        nmap = shutil.which("nmap")
        tshark = shutil.which("tshark")
        npcap_check, _ = run_process(["sc", "query", "npcap"])
        npcap_ok = (npcap_check == 0)

        self.write("W.A 1.6.1 SYSTEM MATRIX STATUS", GREEN)
        self.write("────────────────────────────────────────", DARK_GREEN)
        self.write(f"Python Runtime : {sys.version.split()[0]}", WHITE)
        self.write(f"Requests Lib   : {'READY' if requests else 'MISSING'}", GREEN if requests else RED)
        self.write(f"Nmap Engine    : {'DETECTED' if nmap else 'NOT FOUND'}", GREEN if nmap else YELLOW)
        self.write(f"TShark Toolkit : {'DETECTED' if tshark else 'NOT FOUND'}", GREEN if tshark else YELLOW)
        self.write(f"Npcap Driver   : {'ACTIVE' if npcap_ok else 'INACTIVE'}", GREEN if npcap_ok else YELLOW)
        self.write(f"God Mode Status: {'ACTIVE' if self.god_mode_active else 'OFF'}", CYAN)

    def clear_terminal(self):
        self.terminal.configure(state="normal")
        self.terminal.delete("1.0", "end")
        self.terminal.configure(state="disabled")
        self.print_banner_and_startup()

    # ========================================================
    # NMAP, TSHARK, NPCAP, REQUEST & TOOLS HANDLERS
    # ========================================================

    def handle_nmap_command(self, base):
        nmap_path = shutil.which("nmap")
        if not nmap_path:
            self.write("[!] Không tìm thấy Nmap trong hệ thống.", RED)
            return
        parts = base.split("_")
        mode = parts[1] if len(parts) > 1 else "host"
        target = parts[2] if len(parts) > 2 else LOCALHOST

        cmds = {
            "host": [nmap_path, "-sn", target],
            "all": [nmap_path, "-p-", "--open", target],
            "services": [nmap_path, "-sV", target],
            "os": [nmap_path, "-O", target]
        }
        if mode not in cmds: return
        self.run_background(cmds[mode], f"Nmap [{mode}] on {target}", 180)

    def handle_tshark_command(self, base):
        tshark = shutil.which("tshark")
        if not tshark:
            self.write("[!] Không tìm thấy TShark.", RED)
            return
        if "interfaces" in base:
            self.run_background([tshark, "-D"], "TShark Interfaces", 30)
        elif "capture" in base:
            self.capture_dialog(tshark)
        elif "filter" in base:
            self.filter_dialog(tshark)
        elif "stats" in base:
            self.statistics_dialog(tshark)

    def capture_dialog(self, tshark):
        dlg = tk.Toplevel(self.root)
        dlg.title("W.A — Live Capture")
        dlg.configure(bg=BG)
        dlg.geometry("450x240")
        tk.Label(dlg, text="PACKET CAPTURE", font=("Consolas", 14, "bold"), fg=GREEN, bg=BG).pack(pady=10)
        tk.Label(dlg, text="Interface ID/Name", fg=WHITE, bg=BG, font=FONT_SMALL).pack()
        iface_entry = tk.Entry(dlg, bg="#050505", fg=GREEN, insertbackground=GREEN, font=FONT_SMALL)
        iface_entry.pack(padx=30, pady=5, fill="x")
        tk.Label(dlg, text="Duration (seconds)", fg=WHITE, bg=BG, font=FONT_SMALL).pack()
        dur_entry = tk.Entry(dlg, bg="#050505", fg=GREEN, insertbackground=GREEN, font=FONT_SMALL)
        dur_entry.insert(0, "10")
        dur_entry.pack(padx=30, pady=5, fill="x")

        def start():
            iface = iface_entry.get().strip()
            try: dur = int(dur_entry.get())
            except: dur = 10
            fname = f"wa_capture_{datetime.now().strftime('%H%M%S')}.pcapng"
            dlg.destroy()
            self.run_background([tshark, "-i", iface, "-a", f"duration:{dur}", "-w", fname], f"Capturing to {fname}", dur + 15)

        tk.Button(dlg, text="START", command=start, bg="#001a00", fg=GREEN, font=("Consolas", 10, "bold")).pack(pady=10)

    def filter_dialog(self, tshark):
        dlg = tk.Toplevel(self.root)
        dlg.title("W.A — Filter")
        dlg.configure(bg=BG)
        dlg.geometry("450x220")
        tk.Label(dlg, text="DISPLAY FILTER", font=("Consolas", 14, "bold"), fg=GREEN, bg=BG).pack(pady=10)
        tk.Label(dlg, text="Đường dẫn file .pcapng", fg=WHITE, bg=BG, font=FONT_SMALL).pack()
        f_entry = tk.Entry(dlg, bg="#050505", fg=GREEN, insertbackground=GREEN, font=FONT_SMALL)
        f_entry.pack(padx=30, pady=5, fill="x")
        tk.Label(dlg, text="Bộ lọc (vd: tcp.port == 80)", fg=WHITE, bg=BG, font=FONT_SMALL).pack()
        filt_entry = tk.Entry(dlg, bg="#050505", fg=GREEN, insertbackground=GREEN, font=FONT_SMALL)
        filt_entry.pack(padx=30, pady=5, fill="x")

        def run_f():
            path, flt = f_entry.get().strip(), filt_entry.get().strip()
            dlg.destroy()
            self.run_background([tshark, "-r", path, "-Y", flt], "Filtering PCAP", 40)

        tk.Button(dlg, text="APPLY", command=run_f, bg="#001a00", fg=GREEN).pack(pady=10)

    def statistics_dialog(self, tshark):
        dlg = tk.Toplevel(self.root)
        dlg.title("W.A — Stats")
        dlg.configure(bg=BG)
        dlg.geometry("400x180")
        tk.Label(dlg, text="PROTOCOL STATS", font=("Consolas", 14, "bold"), fg=GREEN, bg=BG).pack(pady=10)
        tk.Label(dlg, text="Đường dẫn file .pcapng", fg=WHITE, bg=BG, font=FONT_SMALL).pack()
        f_entry = tk.Entry(dlg, bg="#050505", fg=GREEN, insertbackground=GREEN, font=FONT_SMALL)
        f_entry.pack(padx=30, pady=5, fill="x")

        def run_s():
            path = f_entry.get().strip()
            dlg.destroy()
            self.run_background([tshark, "-r", path, "-q", "-z", "io,phs"], "Protocol Stats", 40)

        tk.Button(dlg, text="ANALYZE", command=run_s, bg="#001a00", fg=GREEN).pack(pady=10)

    def handle_npcap_command(self, base):
        if "status" in base:
            self.run_background(["sc", "query", "npcap"], "Npcap Status", 15)
        elif "adapters" in base:
            tshark = shutil.which("tshark")
            if tshark: self.run_background([tshark, "-D"], "Adapters Check", 15)
            else: self.run_background(["getmac"], "Adapters Overview", 15)
        elif "restart" in base:
            self.run_background(["net", "stop", "npcap"], "Stopping Npcap", 15)
            self.run_background(["net", "start", "npcap"], "Starting Npcap", 15)

    def handle_request_command(self, base):
        if requests is None:
            self.write("[!] Thiếu thư viện requests.", RED)
            return
        self.request_dialog("POST" if "post" in base else "GET")

    def request_dialog(self, method):
        dlg = tk.Toplevel(self.root)
        dlg.title(f"W.A — HTTP {method}")
        dlg.configure(bg=BG)
        dlg.geometry("450x240")
        tk.Label(dlg, text=f"HTTP {method} TEST", font=("Consolas", 14, "bold"), fg=GREEN, bg=BG).pack(pady=10)
        tk.Label(dlg, text="URL (Localhost only)", fg=WHITE, bg=BG, font=FONT_SMALL).pack()
        url_entry = tk.Entry(dlg, bg="#050505", fg=GREEN, insertbackground=GREEN, font=FONT_SMALL)
        url_entry.insert(0, f"http://{LOCALHOST}/")
        url_entry.pack(padx=30, pady=5, fill="x")

        def send():
            url = url_entry.get().strip()
            if not ("localhost" in url or "127.0.0.1" in url):
                messagebox.showerror("W.A", "Chỉ cho phép gọi localhost!")
                return
            dlg.destroy()
            self.command_running = True
            self.status_label.config(text="● REQ", fg=YELLOW)
            def worker():
                try:
                    res = requests.request(method, url, timeout=10)
                    out, code = f"\n[HTTP {res.status_code}]\n{res.text[:1000]}", 0
                except Exception as e:
                    out, code = f"[!] Lỗi: {e}", 1
                def finish():
                    self.command_running = False
                    self.status_label.config(text="● SECURE", fg=GREEN)
                    self.write(out, GREEN if code == 0 else RED)
                self.root.after(0, finish)
            threading.Thread(target=worker, daemon=True).start()

        tk.Button(dlg, text="SEND", command=send, bg="#001a00", fg=GREEN).pack(pady=10)

    def handle_new_tools(self, base, parts):
        if "dns" in base:
            self.run_background(["nslookup", parts[1] if len(parts) > 1 else "localhost"], "DNS Lookup", 20)
        elif "portscan" in base:
            self.run_custom_portscan(parts[1] if len(parts) > 1 else LOCALHOST)
        elif "procs" in base or base == "procs":
            self.run_background(["tasklist"], "System Processes Scan", 20)
        elif "netstat" in base:
            self.run_background(["netstat", "-ano"], "Active Network Connections", 20)
        elif "ping" in base:
            target = parts[1] if len(parts) > 1 else "8.8.8.8"
            self.run_background(["ping", "-n", "4", target], f"ICMP Ping Test to {target}", 20)
        elif "sysinfo" in base:
            self.run_background(["systeminfo"], "Windows System Information", 30)
        elif "wifi" in base:
            self.run_background(["netsh", "wlan", "show", "profiles"], "Saved Wi-Fi Profiles", 15)

    def run_custom_portscan(self, target):
        self.command_running = True
        self.status_label.config(text="● SCAN", fg=YELLOW)
        self.write(f"[*] Đang quét các cổng phổ biến trên {target}...", CYAN)
        def worker():
            ports = [21, 22, 23, 80, 443, 3306, 5000, 8080, 8443]
            results = []
            for p in ports:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.5)
                    if s.connect_ex((target, p)) == 0:
                        results.append(f"  [OPEN] Port {p}")
                    s.close()
                except: pass
            out = "\n".join(results) if results else "  Không tìm thấy cổng mở phổ biến nào."
            def finish():
                self.command_running = False
                self.status_label.config(text="● SECURE", fg=GREEN)
                self.write(f"\n--- Port Scan Results [{target}] ---\n{out}\n----------------------------------", GREEN)
            self.root.after(0, finish)
        threading.Thread(target=worker, daemon=True).start()

    def run_background(self, cmd, desc, timeout):
        if self.command_running: return
        self.command_running = True
        self.status_label.config(text="● RUN", fg=YELLOW)
        self.write(f"[*] {desc}", CYAN)

        def worker():
            code, out = run_process(cmd, timeout)
            def finish():
                self.command_running = False
                self.status_label.config(text="● SECURE", fg=GREEN)
                if out: self.write(out, GREEN if code == 0 else YELLOW)
                if code == 0: self.write("[+] Hoàn tất.", GREEN)
            self.root.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    def exit_app(self):
        try: self.root.destroy()
        except: pass


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    root = tk.Tk()
    WAApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
