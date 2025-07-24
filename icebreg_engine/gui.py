import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict

from .config import load_hosts, save_hosts, load_watchlist, save_watchlist
from .fetcher import FetchThread

logging.basicConfig(level=logging.INFO)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IceBreg Engine")
        self.geometry("700x500")
        self.fetch_thread = None
        self.create_widgets()

    def create_widgets(self):
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)

        self.conn_frame = ttk.Frame(self.tabs)
        self.watch_frame = ttk.Frame(self.tabs)
        self.tabs.add(self.conn_frame, text="Connection")
        self.tabs.add(self.watch_frame, text="Watchlist")

        self._build_conn_page()
        self._build_watch_page()

    # ----- Connection Page -----
    def _build_conn_page(self):
        frame = self.conn_frame
        columns = ("url", "apikey", "intervals")
        self.host_table = ttk.Treeview(frame, columns=columns, show="headings")
        for c in columns:
            self.host_table.heading(c, text=c.title())
        self.host_table.pack(fill="both", expand=True, pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Add Host", command=self.add_host).pack(side="left")
        ttk.Button(btn_frame, text="Remove", command=self.remove_host).pack(side="left")
        ttk.Button(btn_frame, text="Save", command=self.save_hosts).pack(side="left")

        self.status_label = ttk.Label(frame, text="Idle")
        self.status_label.pack(pady=5)
        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.pack(fill="x", padx=5)
        ttk.Button(frame, text="Fetch Data", command=self.start_fetch).pack(pady=5)

        self.load_hosts_table()

    def load_hosts_table(self):
        for row in self.host_table.get_children():
            self.host_table.delete(row)
        for h in load_hosts():
            self.host_table.insert("", "end", values=(h.get("url"), h.get("apikey"), ",".join(h.get("intervals", []))))

    def add_host(self):
        self.host_table.insert("", "end", values=("", "", "5s"))

    def remove_host(self):
        sel = self.host_table.selection()
        for item in sel:
            self.host_table.delete(item)

    def save_hosts(self):
        hosts = []
        for item in self.host_table.get_children():
            url, apikey, intervals = self.host_table.item(item, "values")
            hosts.append({"url": url.strip(), "apikey": apikey.strip(), "intervals": [i.strip() for i in intervals.split(',') if i.strip()]})
        save_hosts(hosts)
        messagebox.showinfo("Saved", "Hosts saved")

    # ----- Watchlist Page -----
    def _build_watch_page(self):
        frame = self.watch_frame
        columns = ("symbol", "exchange", "priority")
        self.watch_table = ttk.Treeview(frame, columns=columns, show="headings")
        for c in columns:
            self.watch_table.heading(c, text=c.title())
        self.watch_table.pack(fill="both", expand=True, pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Add", command=self.add_stock).pack(side="left")
        ttk.Button(btn_frame, text="Remove", command=self.remove_stock).pack(side="left")
        ttk.Button(btn_frame, text="Save", command=self.save_watchlist).pack(side="left")

        self.load_watch_table()

    def load_watch_table(self):
        for row in self.watch_table.get_children():
            self.watch_table.delete(row)
        for w in load_watchlist():
            self.watch_table.insert("", "end", values=(w.get("symbol"), w.get("exchange"), w.get("priority", "medium")))

    def add_stock(self):
        self.watch_table.insert("", "end", values=("", "NSE", "medium"))

    def remove_stock(self):
        sel = self.watch_table.selection()
        for item in sel:
            self.watch_table.delete(item)

    def save_watchlist(self):
        watch = []
        for item in self.watch_table.get_children():
            symbol, exch, prio = self.watch_table.item(item, "values")
            watch.append({"symbol": symbol.strip(), "exchange": exch.strip(), "priority": prio.strip()})
        save_watchlist(watch)
        messagebox.showinfo("Saved", "Watchlist saved")

    # ----- Fetching -----
    def start_fetch(self):
        if self.fetch_thread and self.fetch_thread.is_alive():
            return
        self.save_hosts()
        self.save_watchlist()
        self.progress.start()
        self.status_label.config(text="Fetching...")
        self.fetch_thread = FetchThread(update_callback=self.update_status)
        self.fetch_thread.start()

    def update_status(self, text: str):
        self.status_label.config(text=text)
        if text == "Fetch completed":
            self.progress.stop()


def run():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    run()
