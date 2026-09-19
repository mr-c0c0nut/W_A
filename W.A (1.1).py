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
from tkinter import messagebox
from datetime import datetime

# ============================================================
# W.A 1.4 ELITE — Windows Security & Analysis Suite
# ============================================================

APP_NAME = "W.A"
APP_VERSION = "1.4 Elite"
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
        self.spoofed_ip = None  # Giả lập đổi IP online qua môi trường ứng dụng

        self.root.title(f"{APP_NAME} — {APP_TITLE}")
        self.root.configure(bg=BG)
        self.root.attributes("-fullscreen", True, "-topmost", True)

        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False) if self.root.attributes("-fullscreen") else self.exit_app())
        self.root.bind("<F11>", lambda e: self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen")))

        self.build_gui()
        self.print_banner()
        self.root.after(200, self.startup_sequence)

    def build_gui(self):
        # Header Matrix Style
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(header, text="╔═W.A═MATRIX═╗", font=("Consolas", 18, "bold"), fg=GREEN, bg=BG).pack(side="left")
        tk.Label(header, text=f"  [{APP_VERSION}]", font=("Consolas", 11, "bold"), fg=CYAN, bg=BG).pack(side="left", pady=(5, 0))
        
        self.status_label = tk.Label(header, text="● OFFLINE", font=("Consolas", 11, "bold"), fg=RED, bg=BG)
        self.status_label.pack(side="right", pady=(5, 0))

        tk.Frame(self.root, bg=DARK_GREEN, height=1).pack(fill="x", padx=20)

        # Terminal Area
        term_frame = tk.Frame(self.root, bg=BG)
        term_frame.pack(fill="both", expand=True, padx=20, pady=8)

        self.terminal = tk.Text(term_frame, bg=BG, fg=GREEN, insertbackground=GREEN, selectbackground=DARK_GREEN, selectforeground=WHITE, font=FONT, wrap="word", borderwidth=0, highlightthickness=0, padx=5, pady=5)
        self.terminal.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(term_frame, command=self.terminal.yview)
        scrollbar.pack(side="right", fill="y")
        self.terminal.configure(yscrollcommand=scrollbar.set, state="disabled")

        # Input Area (Streamlined)
        input_frame = tk.Frame(self.root, bg=BG)
        input_frame.pack(fill="x", padx=20, pady=(0, 15))

        tk.Label(input_frame, text="W.A@Matrix:~>", font=("Consolas", 12, "bold"), fg=GREEN, bg=BG).pack(side="left")

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

    def write(self, text="", color=GREEN, animate=False, speed=0.005):
        def _write():
            self.terminal.configure(state="normal")
            tag = f"tag_{color}_{time.time()}"
            self.terminal.tag_configure(tag, foreground=color)
            
            if animate and text:
                self.terminal.insert("end", "\n", tag)
                self.terminal.see("end")
                self.terminal.configure(state="disabled")
                
                def type_char(i=0):
                    if i < len(text):
                        self.terminal.configure(state="normal")
                        self.terminal.insert("end", text[i], tag)
                        self.terminal.see("end")
                        self.terminal.configure(state="disabled")
                        self.root.after(int(speed * 1000), lambda: type_char(i + 1))
                type_char()
            else:
                self.terminal.insert("end", text + "\n", tag)
                self.terminal.see("end")
                self.terminal.configure(state="disabled")

        self.root.after(0, _write)

    def delete_last_line(self):
        """Xóa dòng cuối cùng trong terminal (phục vụ hiệu ứng loading)"""
        self.terminal.configure(state="normal")
        self.terminal.delete("end-2c linestart", "end-1c")
        self.terminal.configure(state="disabled")

    # ========================================================
    # BANNER & STARTUP
    # ========================================================

    def print_banner(self):
        banner = """
    ██╗  ██╗       █████╗ 
    ██║  ██║      ██╔══██╗
    ██║  ██║  ██╗ ███████║
    ██║  ██║  ██╗ ██╔══██║
    ╚█████╔╝  ██║ ██║  ██║
     ╚════╝   ╚═╝ ╚═╝  ╚═╝
"""
        self.write(banner, GREEN, animate=True, speed=0.001)
        self.write(" >>> W.A 1.4 ELITE — SECURE WINDOWS MATRIX ENVIRONMENT <<<", CYAN)
        self.write("────────────────────────────────────────────────────────────", DARK_GREEN)

    def startup_sequence(self):
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
            self.write("[i] Gõ 'help' để xem danh sách toàn bộ lệnh mở rộng phiên bản 1.4.", CYAN)
            self.write("", GREEN)
            self.command_entry.focus_set()
            return

        self.write(f"[+] {steps[idx]}", GREEN)
        self.root.after(50, lambda: self._run_startup_step(steps, idx + 1))

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
        self.write(f"[{timestamp}] W.A@Matrix:~> {cmd}", CYAN)
        self.execute_command(cmd)
        return "break"

    def execute_command(self, cmd):
        parts = cmd.split()
        if not parts: return
        base = parts[0]
        base_lower = base.lower()

        # --- SYSTEM COMMANDS ---
        if base_lower in ("exit", "quit"):
            self.exit_app()
        elif base_lower == "help":
            self.help_general() if len(parts) == 1 else self.help_topic(parts[1].lower())
        elif base_lower == "version":
            self.write(f"{APP_NAME} {APP_VERSION} - Matrix Edition", GREEN)
        elif base_lower == "status":
            self.status()
        elif base_lower in ("clear", "cls"):
            self.clear_terminal()
        elif base_lower == "history":
            for i, c in enumerate(self.history, 1):
                self.write(f"{i:03d}  {c}", GREEN)

        # --- NEW NETWORK COMMANDS ---
        elif base_lower == "ipconfig":
            self.run_background(["ipconfig", "/all"], "Lấy toàn bộ thông tin IP & Adapters", 30)
        elif base_lower == "ipv4":
            self.cmd_ipv4()
        elif base_lower == "ipv6":
            self.cmd_ipv6()
        elif base_lower == "ip_on":
            self.cmd_ip_on()
        elif base.startswith("$$$_"):
            url = base[4:]
            self.cmd_full_web_scan(url)
        elif base.startswith("#show#_"):
            url = base[7:]
            self.cmd_show_server_ip(url)
        elif base == "SECTO3_ME":
            self.cmd_secto3_me()
        elif base.startswith("PP_"):
            new_ip = base[3:]
            self.cmd_pp(new_ip)
        elif base == "PK":
            self.cmd_pk()

        # --- NMAP MODULE ---
        elif base_lower.startswith("nmap_"):
            self.handle_nmap_command(base_lower)
        elif base_lower == "nmap":
            self.help_nmap_streamlined()

        # --- TSHARK / WIRESHARK MODULE ---
        elif base_lower.startswith("wireshark_") or base_lower.startswith("tshark_"):
            self.handle_tshark_command(base_lower)
        elif base_lower in ("wireshark", "tshark"):
            self.help_wireshark_streamlined()

        # --- NPCAP MODULE ---
        elif base_lower.startswith("npcap_"):
            self.handle_npcap_command(base_lower)
        elif base_lower == "npcap":
            self.help_npcap_streamlined()

        # --- REQUEST MODULE ---
        elif base_lower.startswith("request_"):
            self.handle_request_command(base_lower)
        elif base_lower == "request":
            self.help_request_streamlined()

        # --- NEW TOOLS MODULE ---
        elif base_lower.startswith("tool_") or base_lower in ("dns", "portscan", "procs"):
            self.handle_new_tools(base_lower, parts)

        else:
            self.write(f"[!] Lệnh không xác định: {cmd}", YELLOW)
            self.write("[i] Gõ 'help' để xem danh sách lệnh hỗ trợ.", CYAN)

    # ========================================================
    # CUSTOM NETWORK COMMAND IMPLEMENTATIONS
    # ========================================================

    def cmd_ipv4(self):
        """Lấy IPv4 địa phương"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            self.write(f"[+] IPv4 (Local): {ip}", GREEN)
        except Exception as e:
            self.write(f"[!] Lỗi khi lấy IPv4: {e}", RED)

    def cmd_ipv6(self):
        """Lấy IPv6 địa phương"""
        try:
            found = False
            for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET6):
                ipv6 = info[4][0]
                if ipv6 and not ipv6.startswith("fe80"):
                    self.write(f"[+] IPv6 (Global): {ipv6}", GREEN)
                    found = True
                    break
            if not found:
                # Nếu không tìm thấy Global IPv6, hiển thị địa chỉ Link-local nếu có
                for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET6):
                    self.write(f"[+] IPv6 (Link-local): {info[4][0]}", GREEN)
                    found = True
                    break
            if not found:
                self.write("[!] Không tìm thấy cấu hình IPv6.", YELLOW)
        except Exception as e:
            self.write(f"[!] Lỗi khi lấy IPv6: {e}", RED)

    def cmd_ip_on(self):
        """Lấy Public IP từ Internet"""
        if self.spoofed_ip:
            self.write(f"[+] Public IP (Spoofed): {self.spoofed_ip}", CYAN)
            return

        self.command_running = True
        self.status_label.config(text="● FETCHING", fg=YELLOW)
        self.write("[*] Đang tra cứu IP Online (Public IP)...", CYAN)

        def worker():
            ip = "Không lấy được IP"
            if requests:
                try:
                    ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
                except:
                    try:
                        ip = requests.get("https://ifconfig.me/ip", timeout=5).text.strip()
                    except:
                        pass
            def finish():
                self.command_running = False
                self.status_label.config(text="● SECURE", fg=GREEN)
                self.write(f"[+] Public IP: {ip}", GREEN)
            self.root.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    def cmd_full_web_scan(self, url):
        """$$$_(url): Tìm cổng mở, IP mở, IP máy chủ và liên kết tên miền"""
        clean_url = url.replace("https://", "").replace("http://", "").split("/")[0].strip()
        if not clean_url:
            self.write("[!] Vui lòng nhập URL hợp lệ. Ví dụ: $$$_example.com", YELLOW)
            return

        self.command_running = True
        self.status_label.config(text="● SCANNING", fg=YELLOW)
        self.write(f"[*] Đang phân tích chuyên sâu URL: {clean_url}...", CYAN)

        def worker():
            lines = [f"\n=== PHÂN TÍCH CHUYÊN SÂU WEB: {clean_url} ==="]
            
            # 1. Server IP & Linked IPs
            try:
                ips = list(set([item[4][0] for item in socket.getaddrinfo(clean_url, None)]))
                lines.append(f"[+] Server IP(s): {', '.join(ips)}")
            except Exception as e:
                lines.append(f"[!] Không thể phân tích IP máy chủ: {e}")
                ips = []

            # 2. Quét cổng mở phổ biến
            lines.append("\n[*] Đang quét các cổng mở...")
            common_ports = [21, 22, 80, 443, 8080, 8443, 3306, 5432]
            open_ports = []
            if ips:
                target_ip = ips[0]
                for port in common_ports:
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.settimeout(0.6)
                        if s.connect_ex((target_ip, port)) == 0:
                            open_ports.append(str(port))
                        s.close()
                    except:
                        pass
            if open_ports:
                lines.append(f"[+] Các cổng đang mở: {', '.join(open_ports)}")
            else:
                lines.append("[-] Không tìm thấy cổng mở phổ biến nào.")

            # 3. Phân tích tên miền liên kết / Reverse DNS
            lines.append("\n[*] Tra cứu thông tin liên kết DNS...")
            if ips:
                try:
                    host = socket.gethostbyaddr(ips[0])
                    lines.append(f"[+] Reverse DNS Hostname: {host[0]}")
                    if host[1]: lines.append(f"[+] Alias Domains: {', '.join(host[1])}")
                except:
                    lines.append("[-] Không tìm thấy tên miền liên kết khác qua PTR Record.")

            lines.append("===============================================\n")
            out_str = "\n".join(lines)

            def finish():
                self.command_running = False
                self.status_label.config(text="● SECURE", fg=GREEN)
                self.write(out_str, GREEN)

            self.root.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    def cmd_show_server_ip(self, url):
        """#show#_(url): Chỉ tìm IP của máy chủ"""
        clean_url = url.replace("https://", "").replace("http://", "").split("/")[0].strip()
        if not clean_url:
            self.write("[!] Vui lòng nhập URL hợp lệ. Ví dụ: #show#_example.com", YELLOW)
            return

        try:
            ip = socket.gethostbyname(clean_url)
            self.write(f"[+] Host: {clean_url} -> IP: {ip}", GREEN)
        except Exception as e:
            self.write(f"[!] Không thể lấy IP cho {clean_url}: {e}", RED)

    def cmd_secto3_me(self):
        """SECTO3_ME: Quét danh sách các máy cùng mạng LAN"""
        self.command_running = True
        self.status_label.config(text="● SCANNING", fg=YELLOW)
        self.write("[*] Đang quét các thiết bị cùng mạng LAN (ARP Table Scan)...", CYAN)

        def worker():
            code, out = run_process(["arp", "-a"])
            def finish():
                self.command_running = False
                self.status_label.config(text="● SECURE", fg=GREEN)
                if code == 0:
                    self.write("\n=== DANH SÁCH THIẾT BỊ Ở GẦN (MẠNG NỘI BỘ) ===", GREEN)
                    self.write(out, GREEN)
                else:
                    self.write("[!] Lỗi khi quét ARP table.", RED)
            self.root.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    def cmd_pp(self, new_ip):
        """PP_(ip): Đổi IP online giả lập trong môi trường ứng dụng"""
        if not new_ip:
            self.write("[!] Cú pháp: PP_<IP_mong_muốn>", YELLOW)
            return
        self.spoofed_ip = new_ip
        self.write(f"[+] Đã thay đổi IP Online (Giả lập) thành: {self.spoofed_ip}", GREEN)

    def cmd_pk(self):
        """PK: Trở về IP online gốc"""
        self.spoofed_ip = None
        self.write("[+] Đã khôi phục IP Online về địa chỉ thực tế.", GREEN)

    # ========================================================
    # HELP MENUS
    # ========================================================

    def help_general(self):
        text = """
W.A 1.4 ELITE — COMMAND MATRIX
────────────────────────────────────────
System Commands:
  help                     - Menu tổng quan
  help <module>            - Hướng dẫn module (nmap|wireshark|npcap|request|tools)
  status / clear / history - Quản lý hệ thống & bộ nhớ lệnh
  exit                     - Thoát ứng dụng

Lệnh Kiểm Tra Mạng & IP:
  ipconfig                 - Toàn bộ thông tin cấu hình IP mạng
  ipv4                     - Xem IPv4 nội bộ
  ipv6                     - Xem IPv6 nội bộ
  ip_on                    - Xem Public IP Online thực tế
  $$$_<url>                - Phân tích web (Cổng mở, IP máy chủ, tên miền liên kết)
  #show#_<url>             - Chỉ tìm IP máy chủ của website
  SECTO3_ME                - Quét danh sách các máy cùng mạng nội bộ (LAN)
  PP_<ip>                  - Đổi IP Online sang IP mong muốn (Giả lập)
  PK                       - Khôi phục về IP Online gốc

Streamlined Tools & Modules:
  • Nmap     : nmap_host_<ip>, nmap_all_<ip>, nmap_services_<ip>, nmap_os_<ip>
  • Wireshark: wireshark_interfaces, wireshark_capture, wireshark_filter
  • Npcap    : npcap_status, npcap_adapters, npcap_restart
  • Request  : request_get, request_post
  • NEW TOOLS (v1.4):
    - tool_dns <domain>    - Phân tích DNS Lookup (A, CNAME, MX, NS)
    - tool_portscan <ip>   - Quét nhanh các cổng phổ biến trên máy chủ
    - tool_procs           - Liệt kê các tiến trình Python/Node đang chạy
────────────────────────────────────────
"""
        self.write(text, GREEN, animate=True, speed=0.001)

    def help_topic(self, topic):
        if "nmap" in topic: self.help_nmap_streamlined()
        elif "wireshark" in topic or "tshark" in topic: self.help_wireshark_streamlined()
        elif "npcap" in topic: self.help_npcap_streamlined()
        elif "request" in topic: self.help_request_streamlined()
        elif "tool" in topic: self.help_tools_streamlined()
        else: self.write(f"[!] Không tìm thấy chủ đề trợ giúp: {topic}", YELLOW)

    def help_nmap_streamlined(self):
        self.write("[NMAP] nmap_host_<ip> | nmap_all_<ip> | nmap_services_<ip> | nmap_os_<ip>", CYAN)

    def help_wireshark_streamlined(self):
        self.write("[WIRESHARK] wireshark_interfaces | wireshark_capture | wireshark_filter | wireshark_stats", CYAN)

    def help_npcap_streamlined(self):
        self.write("[NPCAP] npcap_status | npcap_adapters | npcap_restart", CYAN)

    def help_request_streamlined(self):
        self.write("[HTTP] request_get | request_post (Chỉ chấp nhận Localhost)", CYAN)

    def help_tools_streamlined(self):
        self.write("""
NEW TOOLS GUIDE (V1.4)
────────────────────────────────────────
  • tool_dns <domain>    - Tra cứu thông tin bản ghi DNS.
  • tool_portscan <ip>   - Kiểm tra trạng thái cổng nhanh (TCP Connect Scan).
  • tool_procs           - Kiểm tra các tiến trình đang chạy trên hệ thống.
""", CYAN)

    # ========================================================
    # STATUS & SYSTEM
    # ========================================================

    def status(self):
        nmap = shutil.which("nmap")
        tshark = shutil.which("tshark")
        npcap_check, _ = run_process(["sc", "query", "npcap"])
        npcap_ok = (npcap_check == 0)

        self.write("W.A 1.4 SYSTEM MATRIX STATUS", GREEN)
        self.write("────────────────────────────────────────", DARK_GREEN)
        self.write(f"Python Runtime : {sys.version.split()[0]}", WHITE)
        self.write(f"Requests Lib   : {'READY' if requests else 'MISSING'}", GREEN if requests else RED)
        self.write(f"Nmap Engine    : {'DETECTED' if nmap else 'NOT FOUND'}", GREEN if nmap else YELLOW)
        self.write(f"TShark Toolkit : {'DETECTED' if tshark else 'NOT FOUND'}", GREEN if tshark else YELLOW)
        self.write(f"Npcap Driver   : {'ACTIVE' if npcap_ok else 'INACTIVE'}", GREEN if npcap_ok else YELLOW)
        self.write("Security Mode  : MATRIX RESTRICTED", CYAN)

    def clear_terminal(self):
        self.terminal.configure(state="normal")
        self.terminal.delete("1.0", "end")
        self.terminal.configure(state="disabled")
        self.print_banner()

    # ========================================================
    # NMAP HANDLER & ANIMATED DOTS SCANNER
    # ========================================================

    def handle_nmap_command(self, base):
        nmap_path = shutil.which("nmap")
        if not nmap_path:
            self.write("[!] Không tìm thấy Nmap trong hệ thống.", RED)
            return

        parts = base.split("_")
        mode = parts[1] if len(parts) > 1 else "host"
        target = parts[2] if len(parts) > 2 else LOCALHOST

        commands = {
            "host": [nmap_path, "-sn", target],
            "all": [nmap_path, "-p-", "--open", target],
            "services": [nmap_path, "-sV", target],
            "os": [nmap_path, "-O", target]
        }

        if mode not in commands:
            self.write(f"[!] Lệnh Nmap không hợp lệ: {base}", YELLOW)
            return

        self.run_nmap_with_dots(commands[mode], f"Nmap [{mode}] on {target}", 180)

    def run_nmap_with_dots(self, cmd, desc, timeout):
        """Thực thi Nmap với hiệu ứng dấu chấm động (...)"""
        if self.command_running:
            self.write("[!] Đang có tiến trình chạy ngầm.", YELLOW)
            return

        self.command_running = True
        self.status_label.config(text="● SCANNING", fg=YELLOW)
        self.write(f"[*] {desc}", CYAN)

        dots_stop_event = threading.Event()

        def animate_dots():
            dot_count = 1
            self.write("[*] Scanning .", YELLOW)
            while not dots_stop_event.is_set():
                time.sleep(0.5)
                if dots_stop_event.is_set():
                    break
                dot_count = (dot_count % 3) + 1
                dots_str = "." * dot_count
                
                def update_dots(d=dots_str):
                    self.delete_last_line()
                    self.write(f"[*] Scanning {d}", YELLOW)
                
                self.root.after(0, update_dots)

        def worker():
            code, out = run_process(cmd, timeout)
            dots_stop_event.set()

            def finish():
                self.delete_last_line()
                self.command_running = False
                self.status_label.config(text="● SECURE", fg=GREEN)
                if out: self.write(out, GREEN if code == 0 else YELLOW)
                if code == 0: self.write("[+] Scan completed successfully.", GREEN)
                elif code == -2: self.write("[!] Timeout quá thời gian.", YELLOW)
                elif code == -1: self.write("[!] Không tìm thấy chương trình.", RED)
                else: self.write(f"[!] Kết thúc với mã lỗi {code}.", YELLOW)

            self.root.after(0, finish)

        threading.Thread(target=animate_dots, daemon=True).start()
        threading.Thread(target=worker, daemon=True).start()

    # ========================================================
    # TSHARK HANDLER
    # ========================================================

    def handle_tshark_command(self, base):
        tshark = shutil.which("tshark")
        if not tshark:
            self.write("[!] Không tìm thấy TShark trong hệ thống.", RED)
            return

        if "interfaces" in base:
            self.run_background([tshark, "-D"], "TShark: List Interfaces", 30)
        elif "capture" in base:
            self.capture_dialog(tshark)
        elif "filter" in base:
            self.filter_dialog(tshark)
        elif "stats" in base:
            self.statistics_dialog(tshark)
        else:
            self.write("[!] Lệnh Wireshark không xác định.", YELLOW)

    def capture_dialog(self, tshark):
        dlg = tk.Toplevel(self.root)
        dlg.title("W.A — Live Capture")
        dlg.configure(bg=BG)
        dlg.geometry("450x240")
        dlg.transient(self.root)

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
            except ValueError: dur = 10
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

    # ========================================================
    # NPCAP HANDLER
    # ========================================================

    def handle_npcap_command(self, base):
        if "status" in base:
            self.run_background(["sc", "query", "npcap"], "Npcap Status Check", 15)
        elif "adapters" in base:
            tshark = shutil.which("tshark")
            if tshark: self.run_background([tshark, "-D"], "Npcap Adapters Check", 15)
            else: self.run_background(["getmac"], "Adapters Overview", 15)
        elif "restart" in base:
            self.run_background(["net", "stop", "npcap"], "Stopping Npcap", 15)
            self.run_background(["net", "start", "npcap"], "Starting Npcap", 15)

    # ========================================================
    # HTTP REQUEST HANDLER
    # ========================================================

    def handle_request_command(self, base):
        if requests is None:
            self.write("[!] Thiếu thư viện 'requests'.", RED)
            return
        method = "POST" if "post" in base else "GET"
        self.request_dialog(method)

    def request_dialog(self, default_method):
        dlg = tk.Toplevel(self.root)
        dlg.title(f"W.A — HTTP {default_method}")
        dlg.configure(bg=BG)
        dlg.geometry("450x260")

        tk.Label(dlg, text=f"HTTP {default_method} TEST", font=("Consolas", 14, "bold"), fg=GREEN, bg=BG).pack(pady=10)
        tk.Label(dlg, text="URL (Localhost only)", fg=WHITE, bg=BG, font=FONT_SMALL).pack()
        url_entry = tk.Entry(dlg, bg="#050505", fg=GREEN, insertbackground=GREEN, font=FONT_SMALL)
        url_entry.insert(0, f"http://{LOCALHOST}/")
        url_entry.pack(padx=30, pady=5, fill="x")

        tk.Label(dlg, text="Body (Tùy chọn)", fg=WHITE, bg=BG, font=FONT_SMALL).pack()
        body_entry = tk.Entry(dlg, bg="#050505", fg=GREEN, insertbackground=GREEN, font=FONT_SMALL)
        body_entry.pack(padx=30, pady=5, fill="x")

        def send():
            url, body = url_entry.get().strip(), body_entry.get()
            if not (url.startswith("http://localhost") or url.startswith("http://127.0.0.1")):
                messagebox.showerror("W.A", "Chỉ cho phép gọi localhost!")
                return
            dlg.destroy()
            self.run_http_request(default_method, url, body)

        tk.Button(dlg, text="SEND", command=send, bg="#001a00", fg=GREEN).pack(pady=10)

    def run_http_request(self, method, url, body):
        self.command_running = True
        self.status_label.config(text="● REQ", fg=YELLOW)
        self.write(f"[*] Gửi {method} tới {url}...", CYAN)

        def worker():
            try:
                res = requests.request(method, url, data=body if body else None, timeout=10)
                out = f"\n[HTTP {res.status_code}]\n{res.text[:1500]}"
                code = 0
            except Exception as e:
                out, code = f"[!] Lỗi: {e}", 1

            def finish():
                self.command_running = False
                self.status_label.config(text="● SECURE", fg=GREEN)
                self.write(out, GREEN if code == 0 else RED)
            self.root.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    # ========================================================
    # NEW TOOLS MODULE
    # ========================================================

    def handle_new_tools(self, base, parts):
        if "dns" in base:
            domain = parts[1] if len(parts) > 1 else "localhost"
            self.run_background(["nslookup", domain], f"DNS Lookup: {domain}", 20)
        elif "portscan" in base:
            target = parts[1] if len(parts) > 1 else LOCALHOST
            self.run_custom_portscan(target)
        elif "procs" in base or base == "procs":
            self.run_background(["tasklist"], "System Processes Scan", 20)
        else:
            self.write("[!] Tool không hợp lệ. Gõ 'help tools'.", YELLOW)

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
                    res = s.connect_ex((target, p))
                    if res == 0:
                        results.append(f"  [OPEN] Port {p}")
                    s.close()
                except:
                    pass
            out = "\n".join(results) if results else "  Không tìm thấy cổng mở phổ biến nào."
            
            def finish():
                self.command_running = False
                self.status_label.config(text="● SECURE", fg=GREEN)
                self.write(f"\n--- Port Scan Results [{target}] ---\n{out}\n----------------------------------", GREEN)
            self.root.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    # ========================================================
    # BACKGROUND THREAD RUNNER
    # ========================================================

    def run_background(self, cmd, desc, timeout):
        if self.command_running:
            self.write("[!] Đang có tiến trình chạy ngầm.", YELLOW)
            return

        self.command_running = True
        self.status_label.config(text="● RUN", fg=YELLOW)
        self.write(f"[*] {desc}", CYAN, animate=True, speed=0.005)

        def worker():
            code, out = run_process(cmd, timeout)
            def finish():
                self.command_running = False
                self.status_label.config(text="● SECURE", fg=GREEN)
                if out: self.write(out, GREEN if code == 0 else YELLOW)
                if code == 0: self.write("[+] Hoàn tất.", GREEN)
                elif code == -2: self.write("[!] Timeout quá thời gian.", YELLOW)
                elif code == -1: self.write("[!] Không tìm thấy chương trình.", RED)
                else: self.write(f"[!] Kết thúc với mã lỗi {code}.", YELLOW)
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
