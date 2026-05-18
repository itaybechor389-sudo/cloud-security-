#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║               AWS-SENTINEL  v1.0                                 ║
║         AWS Cloud Security Auditor                               ║
║  Course : RTX2026 | Cloud Security (NX216 - Module 12)          ║
║  Author : Itay Bechor | Cyberium Academy                         ║
╚══════════════════════════════════════════════════════════════════╝

Install:
    pip install customtkinter boto3 --break-system-packages
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
import datetime
import time
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_OK = True
except ImportError:
    BOTO3_OK = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

TOOL_VERSION = "1.0"

# ═══════════════════════════════════════════════════════════════════
# THEME
# ═══════════════════════════════════════════════════════════════════
C = {
    "bg0":    "#04070f",
    "bg1":    "#080e1c",
    "bg2":    "#0d1528",
    "bg3":    "#131f38",
    "side":   "#060c1a",
    "border": "#1a2640",
    "orange": "#ff9900",   # AWS orange
    "orange2":"#cc7a00",
    "green":  "#00ff88",
    "cyan":   "#22d3ee",
    "red":    "#f43f5e",
    "yellow": "#fbbf24",
    "blue":   "#3b82f6",
    "purple": "#a855f7",
    "txt":    "#e2e8f0",
    "txt2":   "#64748b",
    "txt3":   "#1e3050",
    "nav":    "#1a0f00",
}

def ts():       return datetime.datetime.now().strftime("%H:%M:%S")
def now_full(): return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ═══════════════════════════════════════════════════════════════════
# SHARED WIDGETS
# ═══════════════════════════════════════════════════════════════════

class LogBox(ctk.CTkTextbox):
    _COLS = {"info": "#22d3ee", "ok": "#00ff88",
             "err": "#f43f5e", "warn": "#ff9900", "hdr": "#a855f7"}
    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self.configure(fg_color="#04070f", text_color="#22d3ee",
                       font=ctk.CTkFont("Consolas", 11),
                       border_width=1, border_color="#1a2640", corner_radius=0)
        for tag, col in self._COLS.items():
            self.tag_config(tag, foreground=col)
    def log(self, msg, level="info"):
        self.configure(state="normal")
        px = {"info":"[*]","ok":"[+]","err":"[-]","warn":"[!]","hdr":"[#]"}
        self.insert("end", f"[{ts()}] {px.get(level,'[*]')} {msg}\n", level)
        self.see("end"); self.configure(state="disabled")
    def clear(self):
        self.configure(state="normal"); self.delete("1.0","end")
        self.configure(state="disabled")


class Grid(ctk.CTkFrame):
    def __init__(self, parent, cols, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        sty = ttk.Style(); sty.theme_use("clam")
        sty.configure("AW.Treeview",
            background="#0d1528", foreground="#e2e8f0",
            fieldbackground="#0d1528", borderwidth=0,
            rowheight=28, font=("Consolas", 10))
        sty.configure("AW.Treeview.Heading",
            background="#04070f", foreground="#ff9900",
            font=("Consolas", 10, "bold"), relief="flat")
        sty.map("AW.Treeview",
            background=[("selected","#cc7a00")],
            foreground=[("selected","white")])
        vsb = ttk.Scrollbar(self, orient="vertical")
        hsb = ttk.Scrollbar(self, orient="horizontal")
        self.tv = ttk.Treeview(self, columns=cols, show="headings",
                                style="AW.Treeview",
                                yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.configure(command=self.tv.yview)
        hsb.configure(command=self.tv.xview)
        for c in cols:
            self.tv.heading(c, text=c.upper())
            self.tv.column(c, anchor="w", minwidth=60)
        self.tv.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        self.tv.tag_configure("alt",      background="#131f38")
        self.tv.tag_configure("critical", foreground="#f43f5e")
        self.tv.tag_configure("high",     foreground="#ff9900")
        self.tv.tag_configure("medium",   foreground="#fbbf24")
        self.tv.tag_configure("low",      foreground="#00ff88")
        self.tv.tag_configure("info",     foreground="#64748b")
        self.tv.tag_configure("warn",     foreground="#ff9900")
    def clear(self):
        for i in self.tv.get_children(): self.tv.delete(i)
    def add(self, vals, tags=()):
        n = len(self.tv.get_children())
        row = ("alt",) if n % 2 else ()
        self.tv.insert("", "end", values=vals, tags=row + tuple(tags))


class MetricCard(ctk.CTkFrame):
    def __init__(self, parent, title, value="--", unit="",
                 color=None, icon="*", **kw):
        super().__init__(parent, **kw)
        color = color or "#ff9900"
        self.configure(fg_color="#0d1528", corner_radius=0,
                       border_width=1, border_color="#1a2640")
        ctk.CTkFrame(self, fg_color=color, height=2, corner_radius=0).pack(fill="x")
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(padx=14, pady=10, fill="both", expand=True)
        ctk.CTkLabel(body, text=f"{icon}  {title}",
                     font=ctk.CTkFont("Consolas", 10),
                     text_color="#64748b").pack(anchor="w")
        row = ctk.CTkFrame(body, fg_color="transparent"); row.pack(anchor="w")
        self._val = ctk.CTkLabel(row, text=str(value),
                                  font=ctk.CTkFont("Consolas", 28, "bold"),
                                  text_color=color)
        self._val.pack(side="left")
        if unit:
            ctk.CTkLabel(row, text=f" {unit}",
                         font=ctk.CTkFont("Consolas", 10),
                         text_color="#64748b").pack(side="left", pady=(8,0))
    def set(self, v): self._val.configure(text=str(v))


def mk_panel(parent):
    return ctk.CTkFrame(parent, fg_color="#0d1528", corner_radius=0,
                        border_width=1, border_color="#1a2640")

def pk_title(parent, text, color=None):
    color = color or "#ff9900"
    hdr = ctk.CTkFrame(parent, fg_color="#04070f", corner_radius=0, height=36)
    hdr.pack(fill="x"); hdr.pack_propagate(False)
    ctk.CTkLabel(hdr, text=text, font=ctk.CTkFont("Consolas", 12, "bold"),
                 text_color=color).pack(side="left", padx=14, pady=6)
    ctk.CTkFrame(parent, fg_color=color, height=1, corner_radius=0).pack(fill="x")

def act_btn(parent, text, cmd, color=None, **kw):
    color = color or "#ff9900"
    return ctk.CTkButton(parent, text=text, command=cmd,
                         font=ctk.CTkFont("Consolas", 11, "bold"),
                         fg_color=color, hover_color="#cc7a00",
                         text_color="#000000", corner_radius=0,
                         height=32, **kw)

def fld(parent, default="", hide=False, **kw):
    e = ctk.CTkEntry(parent, fg_color="#04070f", border_color="#1a2640",
                      font=ctk.CTkFont("Consolas", 11), corner_radius=0,
                      height=32, show="*" if hide else "", **kw)
    if default: e.insert(0, default)
    return e

def hdiv(parent):
    ctk.CTkFrame(parent, fg_color="#1a2640", height=1, corner_radius=0).pack(fill="x")


# ═══════════════════════════════════════════════════════════════════
# PAGE 1 — CONNECT
# ═══════════════════════════════════════════════════════════════════
class ConnectPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app; self._build()

    def _build(self):
        cf = ctk.CTkFrame(self, fg_color="transparent")
        cf.place(relx=0.5, rely=0.5, anchor="center")

        # AWS logo style
        ctk.CTkLabel(cf, text="aws",
                     font=ctk.CTkFont("Consolas", 52, "bold"),
                     text_color="#ff9900").pack(pady=(0, 4))
        ctk.CTkLabel(cf, text="AWS-SENTINEL",
                     font=ctk.CTkFont("Consolas", 22, "bold"),
                     text_color="#e2e8f0").pack()
        ctk.CTkLabel(cf, text="AWS Cloud Security Auditor",
                     font=ctk.CTkFont("Consolas", 11),
                     text_color="#64748b").pack(pady=(0, 24))

        card = mk_panel(cf); card.pack(ipadx=10, ipady=10)
        pk_title(card, "  AWS CREDENTIALS", "#ff9900")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=24, pady=20, fill="x")

        self._entries = {}
        fields = [
            ("ACCESS KEY ID",     "key_id",  "", False),
            ("SECRET ACCESS KEY", "secret",  "", True),
            ("REGION",            "region",  "us-east-1", False),
        ]
        for label, key, default, hide in fields:
            ctk.CTkLabel(inner, text=label,
                         font=ctk.CTkFont("Consolas", 9),
                         text_color="#64748b").pack(anchor="w", pady=(8,2))
            e = fld(inner, default=default, hide=hide, width=420)
            e.pack(fill="x")
            self._entries[key] = e

        ctk.CTkFrame(inner, height=14, fg_color="transparent").pack()
        self._status = ctk.CTkLabel(inner, text="",
                                     font=ctk.CTkFont("Consolas", 11),
                                     text_color="#64748b")
        self._status.pack(pady=(0,8))

        self._btn = act_btn(inner, ">> CONNECT TO AWS",
                            self._connect, width=420)
        self._btn.pack(fill="x")

        ctk.CTkFrame(inner, height=10, fg_color="transparent").pack()
        ctk.CTkLabel(inner,
                     text="[*] Read-only IAM permissions  |  boto3  |  RTX2026 NX216",
                     font=ctk.CTkFont("Consolas", 9),
                     text_color="#1e3050").pack()

    def _connect(self):
        if not BOTO3_OK:
            messagebox.showerror("Missing library",
                "boto3 not installed.\n\nRun:\npip install boto3 --break-system-packages")
            return
        key_id = self._entries["key_id"].get().strip()
        secret = self._entries["secret"].get().strip()
        region = self._entries["region"].get().strip() or "us-east-1"

        if not key_id or not secret:
            self._status.configure(text="[!] Fill Access Key and Secret",
                                    text_color="#f43f5e")
            return

        self._btn.configure(state="disabled", text=">> CONNECTING...")
        self._status.configure(text="[*] Authenticating...", text_color="#fbbf24")

        def go():
            try:
                session = boto3.Session(
                    aws_access_key_id=key_id,
                    aws_secret_access_key=secret,
                    region_name=region)
                # Test credentials
                sts = session.client("sts")
                identity = sts.get_caller_identity()
                self.app.session  = session
                self.app.region   = region
                self.app.account  = identity.get("Account", "")
                self.app.arn      = identity.get("Arn", "")
                self.after(0, lambda: self._status.configure(
                    text=f"[+] Connected! Account: {self.app.account}",
                    text_color="#00ff88"))
                self.after(800, lambda: self.app._nav("dashboard"))
            except Exception as e:
                self.after(0, lambda: self._status.configure(
                    text=f"[-] {str(e)[:50]}", text_color="#f43f5e"))
            finally:
                self.after(0, lambda: self._btn.configure(
                    state="normal", text=">> CONNECT TO AWS"))
        threading.Thread(target=go, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════
# PAGE 2 — DASHBOARD
# ═══════════════════════════════════════════════════════════════════
class DashPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app; self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", pady=(0,14))
        ctk.CTkLabel(hdr, text="aws  AWS SECURITY DASHBOARD",
                     font=ctk.CTkFont("Consolas", 20, "bold"),
                     text_color="#ff9900").pack(side="left")

        mf = ctk.CTkFrame(self, fg_color="transparent")
        mf.pack(fill="x", pady=(0,12))
        for i in range(5): mf.grid_columnconfigure(i, weight=1)

        self.m_users   = MetricCard(mf, "IAM USERS",   icon="[u]", color="#22d3ee")
        self.m_buckets = MetricCard(mf, "S3 BUCKETS",  icon="[s]", color="#ff9900")
        self.m_groups  = MetricCard(mf, "IAM GROUPS",  icon="[g]", color="#a855f7")
        self.m_finds   = MetricCard(mf, "FINDINGS",    icon="[!]", color="#f43f5e")
        self.m_risk    = MetricCard(mf, "RISK SCORE",  icon="[r]",
                                     color="#f43f5e", unit="/100")
        for i, w in enumerate([self.m_users, self.m_buckets, self.m_groups,
                                self.m_finds, self.m_risk]):
            w.grid(row=0, column=i, padx=4, sticky="ew")

        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(fill="both", expand=True)
        mid.grid_columnconfigure(0, weight=3); mid.grid_columnconfigure(1, weight=2)
        mid.grid_rowconfigure(0, weight=1)

        ov = mk_panel(mid); ov.grid(row=0, column=0, padx=(0,6), sticky="nsew")
        pk_title(ov, "aws  AWS THREAT OVERVIEW", "#ff9900")
        threats = [
            ("Root account has no MFA",            "T1078",     "#f43f5e"),
            ("IAM users without MFA",              "T1078.004", "#f43f5e"),
            ("Access keys older than 90 days",     "T1552.001", "#ff9900"),
            ("S3 bucket publicly accessible",      "T1530",     "#f43f5e"),
            ("Security Group open to 0.0.0.0/0",  "T1190",     "#ff9900"),
            ("CloudTrail logging disabled",        "T1562.008", "#f43f5e"),
            ("Weak IAM password policy",           "T1110",     "#ff9900"),
            ("Admin users with full access",       "T1078",     "#f43f5e"),
        ]
        for name, tid, col in threats:
            r = ctk.CTkFrame(ov, fg_color="transparent"); r.pack(fill="x", padx=14, pady=5)
            ctk.CTkLabel(r, text=">>", text_color=col,
                         font=ctk.CTkFont("Consolas", 10)).pack(side="left")
            ctk.CTkLabel(r, text=f"  {name}",
                         font=ctk.CTkFont("Consolas", 11),
                         text_color="#e2e8f0").pack(side="left")
            ctk.CTkLabel(r, text=tid, font=ctk.CTkFont("Consolas", 10),
                         text_color=col).pack(side="right")

        stc = mk_panel(mid); stc.grid(row=0, column=1, padx=(6,0), sticky="nsew")
        pk_title(stc, "[o] SCAN STATUS", "#ff9900")
        self._dots = {}
        for name in ["IAM Users", "S3 Buckets", "Security Groups",
                     "Security Audit", "CloudTrail"]:
            r = ctk.CTkFrame(stc, fg_color="transparent"); r.pack(fill="x", padx=14, pady=8)
            ctk.CTkLabel(r, text=name, width=140, anchor="w",
                         font=ctk.CTkFont("Consolas", 11),
                         text_color="#64748b").pack(side="left")
            d = ctk.CTkLabel(r, text=">> IDLE",
                              font=ctk.CTkFont("Consolas", 10), text_color="#1e3050")
            d.pack(side="right"); self._dots[name] = d

        hdiv(stc)
        ctk.CTkFrame(stc, height=8, fg_color="transparent").pack()
        act_btn(stc, ">> RUN FULL AUDIT", self._run_all).pack(padx=14, fill="x")

        # Account info
        self._acct_lbl = ctk.CTkLabel(stc, text="Account: --",
                                       font=ctk.CTkFont("Consolas", 10),
                                       text_color="#64748b")
        self._acct_lbl.pack(padx=14, pady=8, anchor="w")

    def set_dot(self, name, status):
        col = {"idle":"#1e3050","running":"#fbbf24",
               "done":"#00ff88","error":"#f43f5e"}.get(status,"#1e3050")
        txt = {"idle":">> IDLE","running":">> RUNNING",
               "done":">> DONE","error":">> ERROR"}.get(status,">> IDLE")
        self._dots[name].configure(text=txt, text_color=col)

    def refresh_account(self):
        if self.app.account:
            self._acct_lbl.configure(
                text=f"Account: {self.app.account}  |  {self.app.region}")

    def _run_all(self):
        self.refresh_account()
        def go():
            for name, page_key in [
                ("IAM Users",      "iam"),
                ("S3 Buckets",     "s3"),
                ("Security Groups","sg"),
                ("Security Audit", "audit"),
                ("CloudTrail",     "audit"),
            ]:
                self.after(0, lambda n=name: self.set_dot(n, "running"))
                try:
                    page = self.app._pages.get(page_key)
                    if page and hasattr(page, "_run"):
                        page._run(silent=True)
                except Exception:
                    self.after(0, lambda n=name: self.set_dot(n, "error"))
                    continue
                self.after(0, lambda n=name: self.set_dot(n, "done"))
                time.sleep(0.3)
            self.after(0, lambda: messagebox.showinfo(
                "Done", "AWS Security Audit complete!\nCheck each tab for results."))
        threading.Thread(target=go, daemon=True).start()

    def update(self, users=None, buckets=None, groups=None,
               finds=None, risk=None):
        if users   is not None: self.m_users.set(users)
        if buckets is not None: self.m_buckets.set(buckets)
        if groups  is not None: self.m_groups.set(groups)
        if finds   is not None: self.m_finds.set(finds)
        if risk    is not None: self.m_risk.set(risk)


# ═══════════════════════════════════════════════════════════════════
# PAGE 3 — IAM USERS
# ═══════════════════════════════════════════════════════════════════
class IAMPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app; self._build()

    def _build(self):
        ctk.CTkLabel(self, text="[u] IAM USER AUDIT",
                     font=ctk.CTkFont("Consolas", 20, "bold"),
                     text_color="#ff9900").pack(anchor="w", pady=(0,12))

        cc = mk_panel(self); cc.pack(fill="x", pady=(0,10))
        pk_title(cc, "OPTIONS", "#22d3ee")
        inn = ctk.CTkFrame(cc, fg_color="transparent")
        inn.pack(padx=14, pady=10, fill="x")
        self._btn = act_btn(inn, ">> ENUMERATE IAM USERS",
                            self._start, color="#22d3ee")
        self._btn.pack(side="right")

        self._prog = ctk.CTkProgressBar(self, fg_color="#0d1528",
                                         progress_color="#22d3ee",
                                         height=2, corner_radius=0)
        self._prog.set(0); self._prog.pack(fill="x", pady=(0,8))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=3); body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        tp = mk_panel(body); tp.grid(row=0, column=0, padx=(0,6), sticky="nsew")
        pk_title(tp, "[u] IAM USERS", "#22d3ee")
        self._tbl = Grid(tp, ["Username", "MFA", "Console Access",
                               "Key Age (days)", "Groups", "Last Activity"])
        self._tbl.tv.column("Username",       width=160)
        self._tbl.tv.column("MFA",            width=70)
        self._tbl.tv.column("Console Access", width=100)
        self._tbl.tv.column("Key Age (days)", width=100)
        self._tbl.tv.column("Groups",         width=120)
        self._tbl.tv.column("Last Activity",  width=120)
        self._tbl.pack(fill="both", expand=True, padx=10, pady=10)

        lp = mk_panel(body); lp.grid(row=0, column=1, padx=(6,0), sticky="nsew")
        pk_title(lp, "[o] LOG", "#22d3ee")
        self._log = LogBox(lp, height=300)
        self._log.pack(fill="both", expand=True, padx=8, pady=8)

    def _start(self):
        if not self.app.session:
            messagebox.showerror("Error", "Connect to AWS first!"); return
        self._tbl.clear(); self._log.clear()
        self._prog.configure(mode="indeterminate"); self._prog.start()
        self._btn.configure(state="disabled", text=">> LOADING...")
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self, silent=False):
        if not self.app.session: return
        self.after(0, lambda: self._log.log("Fetching IAM users...", "hdr"))
        try:
            iam = self.app.session.client("iam")

            # Get all users
            users = []
            paginator = iam.get_paginator("list_users")
            for page in paginator.paginate():
                users.extend(page["Users"])

            self.after(0, lambda: self._log.log(f"Found {len(users)} IAM users", "ok"))

            for u in users:
                username = u["UserName"]
                created  = u.get("CreateDate", "")

                # MFA check
                try:
                    mfa_devices = iam.list_mfa_devices(UserName=username)
                    mfa = "YES" if mfa_devices["MFADevices"] else "NO"
                except: mfa = "?"

                # Console access
                try:
                    iam.get_login_profile(UserName=username)
                    console = "YES"
                except ClientError as e:
                    console = "NO" if "NoSuchEntity" in str(e) else "?"

                # Access keys age
                try:
                    keys = iam.list_access_keys(UserName=username)["AccessKeyMetadata"]
                    if keys:
                        oldest = min(k["CreateDate"] for k in keys)
                        age = (datetime.datetime.now(datetime.timezone.utc) - oldest).days
                        key_age = str(age)
                    else:
                        key_age = "No keys"
                except: key_age = "?"

                # Groups
                try:
                    grps = iam.list_groups_for_user(UserName=username)["Groups"]
                    groups_str = ",".join(g["GroupName"] for g in grps[:3]) or "None"
                except: groups_str = "?"

                # Last activity
                try:
                    info = iam.get_user(UserName=username)["User"]
                    last = str(info.get("PasswordLastUsed", "Never"))[:10]
                except: last = "--"

                # Risk tag
                tag = ()
                if mfa == "NO" and console == "YES":
                    tag = ("critical",)
                    self.after(0, lambda n=username:
                        self._log.log(f"CRITICAL: {n} has console access WITHOUT MFA!", "err"))
                elif key_age != "No keys" and key_age != "?" and int(key_age) > 90:
                    tag = ("high",)
                    self.after(0, lambda n=username, a=key_age:
                        self._log.log(f"HIGH: {n} access key is {a} days old", "warn"))
                elif mfa == "NO":
                    tag = ("medium",)

                self.after(0, lambda u=username, m=mfa, c=console,
                           k=key_age, g=groups_str, l=last, t=tag:
                           self._tbl.add([u, m, c, k, g, l], t))

            self.after(0, lambda: self.app.dash.update(users=len(users)))
            self.after(0, lambda: self.app.dash.set_dot("IAM Users", "done"))
            self.after(0, lambda: self._log.log("IAM audit complete", "ok"))

        except Exception as e:
            self.after(0, lambda: self._log.log(str(e), "err"))
        finally:
            self.after(0, self._done)

    def _done(self):
        self._btn.configure(state="normal", text=">> ENUMERATE IAM USERS")
        self._prog.stop(); self._prog.configure(mode="determinate"); self._prog.set(1)


# ═══════════════════════════════════════════════════════════════════
# PAGE 4 — S3 BUCKETS
# ═══════════════════════════════════════════════════════════════════
class S3Page(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app; self._build()

    def _build(self):
        ctk.CTkLabel(self, text="[s] S3 BUCKET SCANNER",
                     font=ctk.CTkFont("Consolas", 20, "bold"),
                     text_color="#ff9900").pack(anchor="w", pady=(0,12))

        cc = mk_panel(self); cc.pack(fill="x", pady=(0,10))
        pk_title(cc, "OPTIONS", "#ff9900")
        inn = ctk.CTkFrame(cc, fg_color="transparent")
        inn.pack(padx=14, pady=10, fill="x")
        self._btn = act_btn(inn, ">> SCAN S3 BUCKETS", self._start)
        self._btn.pack(side="right")

        self._prog = ctk.CTkProgressBar(self, fg_color="#0d1528",
                                         progress_color="#ff9900",
                                         height=2, corner_radius=0)
        self._prog.set(0); self._prog.pack(fill="x", pady=(0,8))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=3); body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        tp = mk_panel(body); tp.grid(row=0, column=0, padx=(0,6), sticky="nsew")
        pk_title(tp, "[s] S3 BUCKETS", "#ff9900")
        self._tbl = Grid(tp, ["Bucket Name", "Region", "Public Access",
                               "Versioning", "Encryption", "Risk"])
        self._tbl.tv.column("Bucket Name",  width=200)
        self._tbl.tv.column("Region",       width=120)
        self._tbl.tv.column("Public Access",width=100)
        self._tbl.tv.column("Versioning",   width=90)
        self._tbl.tv.column("Encryption",   width=90)
        self._tbl.tv.column("Risk",         width=80)
        self._tbl.pack(fill="both", expand=True, padx=10, pady=10)

        lp = mk_panel(body); lp.grid(row=0, column=1, padx=(6,0), sticky="nsew")
        pk_title(lp, "[o] LOG", "#ff9900")
        self._log = LogBox(lp, height=300)
        self._log.pack(fill="both", expand=True, padx=8, pady=8)

    def _start(self):
        if not self.app.session:
            messagebox.showerror("Error", "Connect to AWS first!"); return
        self._tbl.clear(); self._log.clear()
        self._prog.configure(mode="indeterminate"); self._prog.start()
        self._btn.configure(state="disabled", text=">> SCANNING...")
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self, silent=False):
        if not self.app.session: return
        self.after(0, lambda: self._log.log("Listing S3 buckets...", "hdr"))
        try:
            s3 = self.app.session.client("s3")
            response = s3.list_buckets()
            buckets  = response.get("Buckets", [])
            self.after(0, lambda: self._log.log(f"Found {len(buckets)} buckets", "ok"))

            for b in buckets:
                name = b["Name"]
                self.after(0, lambda n=name: self._log.log(f"Checking: {n}", "info"))

                # Region
                try:
                    loc = s3.get_bucket_location(Bucket=name)
                    region = loc["LocationConstraint"] or "us-east-1"
                except: region = "?"

                # Public access block
                try:
                    pub = s3.get_public_access_block(Bucket=name)
                    cfg = pub["PublicAccessBlockConfiguration"]
                    is_public = not all([
                        cfg.get("BlockPublicAcls", False),
                        cfg.get("BlockPublicPolicy", False),
                        cfg.get("IgnorePublicAcls", False),
                        cfg.get("RestrictPublicBuckets", False),
                    ])
                    public_str = "PUBLIC!" if is_public else "Blocked"
                except: public_str = "Unknown"; is_public = False

                # Versioning
                try:
                    ver = s3.get_bucket_versioning(Bucket=name)
                    versioning = ver.get("Status", "Disabled") or "Disabled"
                except: versioning = "?"

                # Encryption
                try:
                    s3.get_bucket_encryption(Bucket=name)
                    encryption = "Enabled"
                except ClientError as e:
                    encryption = "NONE" if "ServerSideEncryptionConfigurationNotFoundError" in str(e) else "?"

                # Risk
                risk = "LOW"
                tag  = ("low",)
                if is_public:
                    risk = "CRITICAL"; tag = ("critical",)
                    self.after(0, lambda n=name:
                        self._log.log(f"CRITICAL: {n} is PUBLICLY accessible!", "err"))
                elif encryption == "NONE":
                    risk = "HIGH"; tag = ("high",)
                elif versioning == "Disabled":
                    risk = "MEDIUM"; tag = ("medium",)

                self.after(0, lambda n=name, r=region, p=public_str,
                           v=versioning, e=encryption, rk=risk, t=tag:
                           self._tbl.add([n, r, p, v, e, rk], t))

            self.after(0, lambda: self.app.dash.update(buckets=len(buckets)))
            self.after(0, lambda: self.app.dash.set_dot("S3 Buckets", "done"))
            self.after(0, lambda: self._log.log("S3 scan complete", "ok"))

        except Exception as e:
            self.after(0, lambda: self._log.log(str(e), "err"))
        finally:
            self.after(0, self._done)

    def _done(self):
        self._btn.configure(state="normal", text=">> SCAN S3 BUCKETS")
        self._prog.stop(); self._prog.configure(mode="determinate"); self._prog.set(1)


# ═══════════════════════════════════════════════════════════════════
# PAGE 5 — SECURITY GROUPS
# ═══════════════════════════════════════════════════════════════════
class SGPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app; self._build()

    def _build(self):
        ctk.CTkLabel(self, text="[n] SECURITY GROUP AUDIT",
                     font=ctk.CTkFont("Consolas", 20, "bold"),
                     text_color="#ff9900").pack(anchor="w", pady=(0,12))

        cc = mk_panel(self); cc.pack(fill="x", pady=(0,10))
        pk_title(cc, "OPTIONS", "#a855f7")
        inn = ctk.CTkFrame(cc, fg_color="transparent")
        inn.pack(padx=14, pady=10, fill="x")
        self._btn = act_btn(inn, ">> SCAN SECURITY GROUPS",
                            self._start, color="#a855f7")
        self._btn.pack(side="right")

        self._prog = ctk.CTkProgressBar(self, fg_color="#0d1528",
                                         progress_color="#a855f7",
                                         height=2, corner_radius=0)
        self._prog.set(0); self._prog.pack(fill="x", pady=(0,8))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=3); body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        tp = mk_panel(body); tp.grid(row=0, column=0, padx=(0,6), sticky="nsew")
        pk_title(tp, "[n] SECURITY GROUPS", "#a855f7")
        self._tbl = Grid(tp, ["SG Name", "SG ID", "Port", "Protocol",
                               "Source", "Risk"])
        self._tbl.tv.column("SG Name",   width=150)
        self._tbl.tv.column("SG ID",     width=130)
        self._tbl.tv.column("Port",      width=80)
        self._tbl.tv.column("Protocol",  width=80)
        self._tbl.tv.column("Source",    width=120)
        self._tbl.tv.column("Risk",      width=80)
        self._tbl.pack(fill="both", expand=True, padx=10, pady=10)

        lp = mk_panel(body); lp.grid(row=0, column=1, padx=(6,0), sticky="nsew")
        pk_title(lp, "[o] LOG", "#a855f7")
        self._log = LogBox(lp, height=300)
        self._log.pack(fill="both", expand=True, padx=8, pady=8)

    def _start(self):
        if not self.app.session:
            messagebox.showerror("Error", "Connect to AWS first!"); return
        self._tbl.clear(); self._log.clear()
        self._prog.configure(mode="indeterminate"); self._prog.start()
        self._btn.configure(state="disabled", text=">> SCANNING...")
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self, silent=False):
        if not self.app.session: return
        self.after(0, lambda: self._log.log("Scanning Security Groups...", "hdr"))
        try:
            ec2 = self.app.session.client("ec2")
            sgs  = ec2.describe_security_groups()["SecurityGroups"]
            self.after(0, lambda: self._log.log(f"Found {len(sgs)} security groups", "ok"))

            DANGEROUS = {22:"SSH", 3389:"RDP", 3306:"MySQL",
                         5432:"PostgreSQL", 27017:"MongoDB",
                         6379:"Redis", 80:"HTTP", 443:"HTTPS"}

            for sg in sgs:
                name  = sg.get("GroupName", "--")
                sg_id = sg.get("GroupId", "--")
                for rule in sg.get("IpPermissions", []):
                    from_port = rule.get("FromPort", 0)
                    to_port   = rule.get("ToPort", 65535)
                    proto     = rule.get("IpProtocol", "?")
                    for ip_range in rule.get("IpRanges", []):
                        cidr = ip_range.get("CidrIp", "")
                        if cidr in ["0.0.0.0/0", "::/0"]:
                            port_str = (str(from_port)
                                        if from_port == to_port
                                        else f"{from_port}-{to_port}")
                            svc  = DANGEROUS.get(from_port, "")
                            risk = "CRITICAL" if from_port in [22,3389,3306,5432,27017,6379] else "HIGH"
                            tag  = ("critical",) if risk == "CRITICAL" else ("high",)
                            self.after(0, lambda n=name, i=sg_id,
                                       p=port_str, pr=proto, c=cidr,
                                       r=risk, t=tag:
                                       self._tbl.add([n, i, p, pr, c, r], t))
                            self.after(0, lambda n=name, p=port_str:
                                self._log.log(f"OPEN to world: {n} port {p}", "err"))

            self.after(0, lambda: self.app.dash.set_dot("Security Groups", "done"))
            self.after(0, lambda: self._log.log("Security Groups scan complete", "ok"))

        except Exception as e:
            self.after(0, lambda: self._log.log(str(e), "err"))
        finally:
            self.after(0, self._done)

    def _done(self):
        self._btn.configure(state="normal", text=">> SCAN SECURITY GROUPS")
        self._prog.stop(); self._prog.configure(mode="determinate"); self._prog.set(1)


# ═══════════════════════════════════════════════════════════════════
# PAGE 6 — SECURITY AUDIT
# ═══════════════════════════════════════════════════════════════════
class AuditPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app; self._findings = []; self._build()

    def _build(self):
        ctk.CTkLabel(self, text="[!] SECURITY AUDIT",
                     font=ctk.CTkFont("Consolas", 20, "bold"),
                     text_color="#ff9900").pack(anchor="w", pady=(0,12))

        cc = mk_panel(self); cc.pack(fill="x", pady=(0,10))
        pk_title(cc, "AUDIT MODULES", "#f43f5e")
        inn = ctk.CTkFrame(cc, fg_color="transparent")
        inn.pack(padx=14, pady=10, fill="x")

        self._checks = {}
        row = ctk.CTkFrame(inn, fg_color="transparent"); row.pack(fill="x", pady=(0,8))
        for name in ["Password Policy", "Root MFA", "CloudTrail",
                     "Access Key Age", "IAM Policies"]:
            v = tk.BooleanVar(value=True); self._checks[name] = v
            ctk.CTkCheckBox(row, text=name, variable=v,
                             font=ctk.CTkFont("Consolas", 10),
                             fg_color="#f43f5e", checkmark_color="white",
                             border_color="#1a2640",
                             corner_radius=0).pack(side="left", padx=10)

        self._btn = act_btn(inn, ">> RUN SECURITY AUDIT",
                            self._start, color="#f43f5e")
        self._btn.pack(side="right")

        self._prog = ctk.CTkProgressBar(self, fg_color="#0d1528",
                                         progress_color="#f43f5e",
                                         height=2, corner_radius=0)
        self._prog.set(0); self._prog.pack(fill="x", pady=(0,8))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=3); body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        tp = mk_panel(body); tp.grid(row=0, column=0, padx=(0,6), sticky="nsew")
        pk_title(tp, "[!] FINDINGS", "#f43f5e")
        self._tbl = Grid(tp, ["Risk", "Category", "Finding", "Recommendation"])
        self._tbl.tv.column("Risk",           width=80)
        self._tbl.tv.column("Category",       width=120)
        self._tbl.tv.column("Finding",        width=240)
        self._tbl.tv.column("Recommendation", width=240)
        self._tbl.pack(fill="both", expand=True, padx=10, pady=10)

        rp = mk_panel(body); rp.grid(row=0, column=1, padx=(6,0), sticky="nsew")
        pk_title(rp, "[o] RISK SUMMARY", "#f43f5e")
        self._rlbls = {}
        for risk, col in [("CRITICAL","#f43f5e"),("HIGH","#ff9900"),
                           ("MEDIUM","#fbbf24"),("LOW","#00ff88")]:
            r = ctk.CTkFrame(rp, fg_color="transparent"); r.pack(fill="x", padx=14, pady=8)
            ctk.CTkLabel(r, text=f">> {risk}", width=100, anchor="w",
                         font=ctk.CTkFont("Consolas", 11),
                         text_color=col).pack(side="left")
            lbl = ctk.CTkLabel(r, text="0",
                                font=ctk.CTkFont("Consolas", 20, "bold"),
                                text_color=col)
            lbl.pack(side="right"); self._rlbls[risk] = lbl

        hdiv(rp)
        ctk.CTkLabel(rp, text="RISK SCORE",
                     font=ctk.CTkFont("Consolas", 9),
                     text_color="#64748b").pack(padx=14, anchor="w", pady=(8,0))
        self._score = ctk.CTkLabel(rp, text="--",
                                    font=ctk.CTkFont("Consolas", 40, "bold"),
                                    text_color="#f43f5e")
        self._score.pack(padx=14, anchor="w")
        self._rbar = ctk.CTkProgressBar(rp, fg_color="#04070f",
                                         progress_color="#f43f5e",
                                         height=6, corner_radius=0)
        self._rbar.set(0); self._rbar.pack(padx=14, pady=6, fill="x")
        self._alog = LogBox(rp, height=150)
        self._alog.pack(fill="both", expand=True, padx=8, pady=8)

    def _add(self, risk, cat, finding, rec):
        self._findings.append((risk, cat, finding, rec))
        tag = (risk.lower(),)
        self.after(0, lambda r=risk, c=cat, f=finding, rc=rec, t=tag:
                   self._tbl.add([r, c, f, rc], t))
        cnt = {k:0 for k in self._rlbls}
        for f in self._findings:
            if f[0] in cnt: cnt[f[0]] += 1
        for k, v in cnt.items():
            self.after(0, lambda k=k, v=v: self._rlbls[k].configure(text=str(v)))

    def _calc_score(self):
        W = {"CRITICAL":25,"HIGH":15,"MEDIUM":8,"LOW":3}
        s = min(sum(W.get(f[0],0) for f in self._findings), 100)
        col = "#f43f5e" if s>=70 else "#ff9900" if s>=40 else "#fbbf24" if s>=20 else "#00ff88"
        self.after(0, lambda: self._score.configure(text=str(s), text_color=col))
        self.after(0, lambda: self._rbar.set(s/100))
        self.after(0, lambda: self.app.dash.update(
            finds=len(self._findings), risk=s))

    def _start(self):
        if not self.app.session:
            messagebox.showerror("Error", "Connect to AWS first!"); return
        self._findings.clear(); self._tbl.clear(); self._alog.clear()
        self._score.configure(text="--"); self._rbar.set(0)
        for l in self._rlbls.values(): l.configure(text="0")
        self._prog.configure(mode="indeterminate"); self._prog.start()
        self._btn.configure(state="disabled", text=">> AUDITING...")
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self, silent=False):
        if not self.app.session: return
        self.after(0, lambda: self._alog.log("Starting AWS security audit...", "hdr"))
        iam = self.app.session.client("iam")
        try:
            # 1. Root account MFA
            if self._checks.get("Root MFA", tk.BooleanVar(value=True)).get():
                self.after(0, lambda: self._alog.log("Checking root account MFA...", "info"))
                try:
                    summary = iam.get_account_summary()["SummaryMap"]
                    if summary.get("AccountMFAEnabled", 0) == 0:
                        self._add("CRITICAL", "Root Account",
                                  "Root account has NO MFA enabled",
                                  "Enable MFA on root account immediately")
                        self.after(0, lambda: self._alog.log("CRITICAL: Root MFA disabled!", "err"))
                    else:
                        self.after(0, lambda: self._alog.log("Root MFA: enabled", "ok"))
                except Exception as e:
                    self.after(0, lambda: self._alog.log(f"Root check: {e}", "warn"))

            # 2. Password Policy
            if self._checks.get("Password Policy", tk.BooleanVar(value=True)).get():
                self.after(0, lambda: self._alog.log("Checking password policy...", "info"))
                try:
                    policy = iam.get_account_password_policy()["PasswordPolicy"]
                    if policy.get("MinimumPasswordLength", 0) < 12:
                        self._add("HIGH", "Password Policy",
                                  f"Min password length is {policy.get('MinimumPasswordLength')} (should be 12+)",
                                  "Set minimum password length to 14 characters")
                    if not policy.get("RequireUppercaseCharacters", False):
                        self._add("MEDIUM", "Password Policy",
                                  "Uppercase characters not required",
                                  "Enable uppercase requirement in password policy")
                    if not policy.get("RequireSymbols", False):
                        self._add("MEDIUM", "Password Policy",
                                  "Special characters not required",
                                  "Enable symbol requirement in password policy")
                    if policy.get("MaxPasswordAge", 0) == 0:
                        self._add("MEDIUM", "Password Policy",
                                  "Password expiration not configured",
                                  "Set password expiration to 90 days")
                    self.after(0, lambda: self._alog.log("Password policy checked", "ok"))
                except ClientError as e:
                    if "NoSuchEntity" in str(e):
                        self._add("CRITICAL", "Password Policy",
                                  "No IAM password policy configured",
                                  "Create a strong password policy immediately")
                        self.after(0, lambda: self._alog.log("CRITICAL: No password policy!", "err"))

            # 3. CloudTrail
            if self._checks.get("CloudTrail", tk.BooleanVar(value=True)).get():
                self.after(0, lambda: self._alog.log("Checking CloudTrail...", "info"))
                try:
                    ct = self.app.session.client("cloudtrail")
                    trails = ct.describe_trails()["trailList"]
                    active = [t for t in trails if t.get("IsMultiRegionTrail")]
                    if not trails:
                        self._add("CRITICAL", "CloudTrail",
                                  "CloudTrail is NOT configured",
                                  "Enable CloudTrail in all regions immediately")
                        self.after(0, lambda: self._alog.log("CRITICAL: CloudTrail disabled!", "err"))
                    elif not active:
                        self._add("HIGH", "CloudTrail",
                                  "No multi-region CloudTrail configured",
                                  "Enable multi-region CloudTrail")
                    else:
                        self.after(0, lambda: self._alog.log(f"CloudTrail: {len(trails)} trail(s)", "ok"))
                except Exception as e:
                    self.after(0, lambda: self._alog.log(f"CloudTrail: {e}", "warn"))

            # 4. Users without MFA
            self.after(0, lambda: self._alog.log("Checking users MFA status...", "info"))
            try:
                users = []
                paginator = iam.get_paginator("list_users")
                for page in paginator.paginate():
                    users.extend(page["Users"])
                no_mfa = []
                for u in users:
                    try:
                        mfa_devices = iam.list_mfa_devices(UserName=u["UserName"])
                        if not mfa_devices["MFADevices"]:
                            login = True
                            try: iam.get_login_profile(UserName=u["UserName"])
                            except: login = False
                            if login: no_mfa.append(u["UserName"])
                    except: pass
                if no_mfa:
                    self._add("CRITICAL" if len(no_mfa) > 1 else "HIGH",
                              "MFA",
                              f"{len(no_mfa)} users have console access WITHOUT MFA: {', '.join(no_mfa[:3])}",
                              "Enforce MFA for all IAM users with console access")
                    self.after(0, lambda n=len(no_mfa):
                        self._alog.log(f"{n} users without MFA!", "err"))
            except Exception as e:
                self.after(0, lambda: self._alog.log(f"MFA check: {e}", "warn"))

            # 5. Old Access Keys
            if self._checks.get("Access Key Age", tk.BooleanVar(value=True)).get():
                self.after(0, lambda: self._alog.log("Checking access key ages...", "info"))
                try:
                    old_keys = []
                    for u in users:
                        keys = iam.list_access_keys(UserName=u["UserName"])["AccessKeyMetadata"]
                        for k in keys:
                            age = (datetime.datetime.now(datetime.timezone.utc) -
                                   k["CreateDate"]).days
                            if age > 90:
                                old_keys.append(f"{u['UserName']} ({age}d)")
                    if old_keys:
                        self._add("HIGH", "Access Keys",
                                  f"Old access keys (>90 days): {', '.join(old_keys[:3])}",
                                  "Rotate access keys every 90 days")
                        self.after(0, lambda n=len(old_keys):
                            self._alog.log(f"{n} old access keys found", "warn"))
                except Exception as e:
                    self.after(0, lambda: self._alog.log(f"Key age: {e}", "warn"))

            self._calc_score()
            self.after(0, lambda: self._alog.log(
                f"Audit done -- {len(self._findings)} findings", "ok"))
            self.after(0, lambda: self.app.dash.set_dot("Security Audit", "done"))
            self.after(0, lambda: self.app.dash.set_dot("CloudTrail", "done"))

        except Exception as e:
            self.after(0, lambda: self._alog.log(str(e), "err"))
        finally:
            self.after(0, self._done)

    def _done(self):
        self._btn.configure(state="normal", text=">> RUN SECURITY AUDIT")
        self._prog.stop(); self._prog.configure(mode="determinate"); self._prog.set(1)

    @property
    def findings(self): return self._findings


# ═══════════════════════════════════════════════════════════════════
# PAGE 7 — REPORTS
# ═══════════════════════════════════════════════════════════════════
class ReportPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app; self._build()

    def _build(self):
        ctk.CTkLabel(self, text="[*] REPORT GENERATOR",
                     font=ctk.CTkFont("Consolas", 20, "bold"),
                     text_color="#ff9900").pack(anchor="w", pady=(0,12))

        oc = mk_panel(self); oc.pack(fill="x", pady=(0,10))
        pk_title(oc, "CONFIGURATION", "#ff9900")
        inn = ctk.CTkFrame(oc, fg_color="transparent")
        inn.pack(padx=14, pady=10, fill="x")
        inn.grid_columnconfigure((0,1,2,3), weight=1)

        ctk.CTkLabel(inn, text="TITLE", font=ctk.CTkFont("Consolas",9),
                     text_color="#64748b").grid(row=0, column=0, sticky="w")
        self._title = fld(inn, "AWS Cloud Security Assessment")
        self._title.grid(row=1, column=0, padx=(0,8), sticky="ew")

        ctk.CTkLabel(inn, text="AUTHOR", font=ctk.CTkFont("Consolas",9),
                     text_color="#64748b").grid(row=0, column=1, sticky="w")
        self._author = fld(inn, "Itay Bechor")
        self._author.grid(row=1, column=1, padx=(0,8), sticky="ew")

        ctk.CTkLabel(inn, text="FORMAT", font=ctk.CTkFont("Consolas",9),
                     text_color="#64748b").grid(row=0, column=2, sticky="w")
        self._fmt = ctk.CTkComboBox(inn, values=["HTML Report","JSON Export"],
                                     fg_color="#04070f", border_color="#1a2640",
                                     font=ctk.CTkFont("Consolas",11),
                                     corner_radius=0, height=32)
        self._fmt.set("HTML Report")
        self._fmt.grid(row=1, column=2, padx=(0,8), sticky="ew")

        act_btn(inn, ">> GENERATE", self._generate).grid(row=1, column=3, sticky="ew")

        pc = mk_panel(self); pc.pack(fill="both", expand=True)
        pk_title(pc, "[*] PREVIEW", "#ff9900")
        self._prev = ctk.CTkTextbox(pc, fg_color="#04070f", text_color="#e2e8f0",
                                     font=ctk.CTkFont("Consolas",11),
                                     border_width=0, corner_radius=0)
        self._prev.pack(fill="both", expand=True, padx=14, pady=14)
        self._refresh()

    def _refresh(self):
        t = f"""
+================================================================+
|            AWS-SENTINEL  REPORT PREVIEW                        |
+================================================================+

  Title   : AWS Cloud Security Assessment
  Author  : Itay Bechor
  Date    : {now_full()}
  Course  : RTX2026 | Cloud Security NX216 - Module 12
  Academy : Cyberium Academy -- John Bryce / ThinkCyber

  API     : AWS boto3 SDK
  Scope   : IAM, S3, EC2 Security Groups, CloudTrail

  CHECKS PERFORMED
  ----------------------------------------------------------------
  [u] IAM Users      -- MFA status, access key age, groups
  [s] S3 Buckets     -- Public access, encryption, versioning
  [n] Security Groups -- Ports open to 0.0.0.0/0
  [!] Security Audit  -- Root MFA, password policy, CloudTrail

  MITRE ATT&CK COVERAGE
  ----------------------------------------------------------------
  T1078      Valid Accounts -- Root account abuse
  T1078.004  Cloud Accounts -- IAM user without MFA
  T1530      Data from Cloud Storage -- Public S3 bucket
  T1190      Exploit Public-Facing App -- Open security group
  T1552.001  Credentials in Files -- Old access keys
  T1562.008  Disable Cloud Logs -- CloudTrail disabled

  >> Run all modules then click GENERATE
+================================================================+
"""
        self._prev.configure(state="normal")
        self._prev.delete("1.0","end"); self._prev.insert("1.0", t)
        self._prev.configure(state="disabled")

    def _generate(self):
        findings = self.app.audit_page.findings if hasattr(self.app,"audit_page") else []
        title    = self._title.get()
        author   = self._author.get()
        if "HTML" in self._fmt.get():
            self._html(title, author, findings)
        else:
            self._json(title, author, findings)

    def _html(self, title, author, findings):
        rows = ""
        for risk, cat, finding, rec in findings:
            col = {"CRITICAL":"#f43f5e","HIGH":"#ff9900",
                   "MEDIUM":"#fbbf24","LOW":"#00ff88","INFO":"#64748b"}.get(risk,"#888")
            rows += f"""<tr>
<td><span style="background:{col}22;color:{col};border:1px solid {col}55;
    padding:2px 8px;font-size:10px">{risk}</span></td>
<td>{cat}</td><td>{finding}</td><td>{rec}</td></tr>"""

        acct = getattr(self.app, "account", "--")
        region = getattr(self.app, "region", "--")
        html = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><title>{title}</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:#04070f;color:#e2e8f0;font-family:Consolas,monospace;
       padding:40px;line-height:1.6}}
  h1{{font-size:20px;color:#ff9900;letter-spacing:4px;
      border-bottom:2px solid #ff9900;padding-bottom:12px;margin-bottom:20px}}
  .meta{{color:#64748b;font-size:11px;margin-bottom:24px}}
  .card{{background:#0d1528;border:1px solid #1a2640;padding:20px;margin-bottom:14px}}
  .ch{{color:#ff9900;font-size:11px;letter-spacing:2px;
       border-bottom:1px solid #1a2640;padding-bottom:8px;margin-bottom:12px}}
  table{{width:100%;border-collapse:collapse;font-size:11px}}
  th{{background:#04070f;color:#ff9900;padding:8px;text-align:left}}
  td{{padding:8px;border-bottom:1px solid #1a2640}}
  tr:hover{{background:#131f38}}
  .mitre{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}}
  .mt{{background:#131f38;padding:10px;font-size:10px;
       border-left:3px solid #ff9900}}
  .mt-id{{color:#ff9900;font-weight:bold;margin-bottom:4px}}
  .footer{{text-align:center;color:#1e3050;font-size:10px;margin-top:28px}}
</style></head><body>
<h1>aws  AWS-SENTINEL -- SECURITY REPORT</h1>
<div class="meta">
  <b>Title:</b> {title} &nbsp;|&nbsp;
  <b>Author:</b> {author} &nbsp;|&nbsp;
  <b>Date:</b> {now_full()}
</div>
<div class="card">
  <div class="ch">[o] ENVIRONMENT</div>
  <table><tr><th>KEY</th><th>VALUE</th></tr>
  <tr><td>AWS Account ID</td><td>{acct}</td></tr>
  <tr><td>Region</td><td>{region}</td></tr>
  <tr><td>Tool</td><td>AWS-Sentinel v{TOOL_VERSION}</td></tr>
  <tr><td>Course</td><td>RTX2026 | Cloud Security NX216 Module 12</td></tr>
  <tr><td>Academy</td><td>Cyberium Academy -- John Bryce / ThinkCyber</td></tr>
  </table>
</div>
<div class="card">
  <div class="ch">[!] SECURITY FINDINGS ({len(findings)} total)</div>
  <table><tr><th>RISK</th><th>CATEGORY</th><th>FINDING</th><th>RECOMMENDATION</th></tr>
  {rows or '<tr><td colspan="4" style="text-align:center;color:#1e3050">No findings -- run Security Audit first</td></tr>'}
  </table>
</div>
<div class="card">
  <div class="ch">[*] MITRE ATT&amp;CK MAPPING</div>
  <div class="mitre">
    <div class="mt"><div class="mt-id">T1078 / T1078.004</div>Valid/Cloud Accounts -- Root & IAM without MFA</div>
    <div class="mt"><div class="mt-id">T1530</div>Data from Cloud Storage -- Public S3 bucket</div>
    <div class="mt"><div class="mt-id">T1190</div>Exploit Public-Facing -- Open Security Group</div>
    <div class="mt"><div class="mt-id">T1552.001</div>Credentials in Files -- Expired access keys</div>
    <div class="mt"><div class="mt-id">T1562.008</div>Disable Cloud Logs -- CloudTrail disabled</div>
    <div class="mt"><div class="mt-id">T1110</div>Brute Force -- Weak password policy</div>
  </div>
</div>
<div class="footer">AWS-Sentinel v{TOOL_VERSION} | Cyberium Academy | RTX2026 Module 12 | {now_full()}</div>
</body></html>"""

        fp = filedialog.asksaveasfilename(
            defaultextension=".html", filetypes=[("HTML","*.html")],
            initialfile=f"aws_sentinel_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        if fp:
            Path(fp).write_text(html, encoding="utf-8")
            messagebox.showinfo("Saved", f"Report saved:\n{fp}")

    def _json(self, title, author, findings):
        d = {"tool": f"AWS-Sentinel v{TOOL_VERSION}",
             "title": title, "author": author,
             "generated": now_full(),
             "account": getattr(self.app, "account", "--"),
             "region":  getattr(self.app, "region", "--"),
             "course": "RTX2026 NX216 Module 12 -- Cloud Security",
             "findings": [{"risk":f[0],"category":f[1],
                           "finding":f[2],"recommendation":f[3]}
                          for f in findings]}
        fp = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON","*.json")],
            initialfile=f"aws_sentinel_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        if fp:
            Path(fp).write_text(json.dumps(d, indent=2), encoding="utf-8")
            messagebox.showinfo("Saved", f"JSON saved:\n{fp}")


# ═══════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"AWS-SENTINEL v{TOOL_VERSION}  |  AWS Cloud Security Auditor")
        self.geometry("1480x900"); self.minsize(1200,750)
        self.configure(fg_color="#080e1c")
        self.session = None; self.region = "us-east-1"
        self.account = ""; self.arn = ""
        self._build()

    def _build(self):
        tb = ctk.CTkFrame(self, fg_color="#060c1a", height=52, corner_radius=0)
        tb.pack(fill="x", side="top"); tb.pack_propagate(False)
        lf = ctk.CTkFrame(tb, fg_color="transparent"); lf.pack(side="left", padx=20)
        ctk.CTkLabel(lf, text="aws",
                     font=ctk.CTkFont("Consolas", 16, "bold"),
                     text_color="#ff9900").pack(side="left", pady=12)
        ctk.CTkLabel(lf, text="  AWS-SENTINEL",
                     font=ctk.CTkFont("Consolas", 16, "bold"),
                     text_color="#e2e8f0").pack(side="left", pady=12)
        ctk.CTkLabel(lf, text=f"  v{TOOL_VERSION}",
                     font=ctk.CTkFont("Consolas", 11),
                     text_color="#1e3050").pack(side="left", pady=12)
        ctk.CTkLabel(tb,
            text="AWS SDK boto3  |  IAM · S3 · EC2 · CloudTrail  |  NX216 Module 12",
            font=ctk.CTkFont("Consolas", 10),
            text_color="#64748b").pack(side="right", padx=20, pady=12)
        ctk.CTkFrame(self, fg_color="#ff9900", height=2, corner_radius=0).pack(fill="x")

        main = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        main.pack(fill="both", expand=True)
        main.grid_columnconfigure(1, weight=1); main.grid_rowconfigure(0, weight=1)

        sb = ctk.CTkFrame(main, fg_color="#060c1a", width=220, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew"); sb.pack_propagate(False)

        logo = ctk.CTkFrame(sb, fg_color="#04070f", height=96, corner_radius=0)
        logo.pack(fill="x"); logo.pack_propagate(False)
        ctk.CTkLabel(logo, text="aws",
                     font=ctk.CTkFont("Consolas", 32, "bold"),
                     text_color="#ff9900").pack(pady=(12,0))
        ctk.CTkLabel(logo, text="AWS-SENTINEL",
                     font=ctk.CTkFont("Consolas", 9, "bold"),
                     text_color="#64748b").pack()
        ctk.CTkFrame(sb, fg_color="#1a2640", height=1, corner_radius=0).pack(fill="x")
        ctk.CTkFrame(sb, height=6, fg_color="transparent").pack()

        content = ctk.CTkFrame(main, fg_color="#080e1c", corner_radius=0)
        content.grid(row=0, column=1, sticky="nsew")

        self.connect_page = ConnectPage(content, self)
        self.dash         = DashPage   (content, self)
        self.iam_page     = IAMPage    (content, self)
        self.s3_page      = S3Page     (content, self)
        self.sg_page      = SGPage     (content, self)
        self.audit_page   = AuditPage  (content, self)
        self.report_page  = ReportPage (content, self)

        self._pages = {
            "connect":   self.connect_page,
            "dashboard": self.dash,
            "iam":       self.iam_page,
            "s3":        self.s3_page,
            "sg":        self.sg_page,
            "audit":     self.audit_page,
            "report":    self.report_page,
        }
        for p in self._pages.values():
            p.place(relx=0, rely=0, relwidth=1, relheight=1)

        nav_items = [
            (">> CONNECT",       "connect"),
            (">> DASHBOARD",     "dashboard"),
            (">> IAM USERS",     "iam"),
            (">> S3 BUCKETS",    "s3"),
            (">> SECURITY GROUPS","sg"),
            (">> SECURITY AUDIT","audit"),
            (">> REPORTS",       "report"),
        ]
        self._nav_btns = {}
        for label, key in nav_items:
            btn = ctk.CTkButton(sb, text=f"  {label}", anchor="w",
                                font=ctk.CTkFont("Consolas", 11),
                                fg_color="transparent", hover_color="#1a0f00",
                                text_color="#64748b", corner_radius=0,
                                height=44, border_width=0,
                                command=lambda k=key: self._nav(k))
            btn.pack(fill="x", pady=1); self._nav_btns[key] = btn

        ctk.CTkFrame(sb, fg_color="transparent").pack(fill="both", expand=True)
        ctk.CTkFrame(sb, fg_color="#1a2640", height=1, corner_radius=0).pack(fill="x")
        ctk.CTkLabel(sb, text="RTX2026 | NX216 Module 12",
                     font=ctk.CTkFont("Consolas", 9),
                     text_color="#1e3050").pack(pady=(4,0))
        ctk.CTkLabel(sb, text="Cyberium Academy",
                     font=ctk.CTkFont("Consolas", 9),
                     text_color="#1e3050").pack(pady=(0,8))

        sbar = ctk.CTkFrame(self, fg_color="#060c1a", height=24, corner_radius=0)
        sbar.pack(fill="x", side="bottom"); sbar.pack_propagate(False)
        ctk.CTkLabel(sbar,
            text=f"  AWS-Sentinel v{TOOL_VERSION}  |  boto3  |  IAM · S3 · EC2 · CloudTrail  |  RTX2026",
            font=ctk.CTkFont("Consolas", 9),
            text_color="#1e3050").pack(side="left", pady=4)
        self._tlbl = ctk.CTkLabel(sbar, text="",
                                   font=ctk.CTkFont("Consolas", 9),
                                   text_color="#1e3050")
        self._tlbl.pack(side="right", padx=14, pady=4)
        self._tick()
        self._nav("connect")

    def _nav(self, key):
        for k, btn in self._nav_btns.items():
            btn.configure(fg_color="transparent", text_color="#64748b")
        self._nav_btns[key].configure(fg_color="#1a0f00", text_color="#ff9900")
        self._pages[key].lift()

    def _tick(self):
        self._tlbl.configure(text=now_full() + "  ")
        self.after(1000, self._tick)

if __name__ == "__main__":
    App().mainloop()
