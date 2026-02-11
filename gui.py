#!/usr/bin/env python3
"""
X Knowledge Graph - Windows GUI Application
A desktop app to build knowledge graphs from X exports and Grok chats.
"""

import sys
import os
from pathlib import Path
from tkinter import *
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
from datetime import datetime

# Add core to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.xkg_core import KnowledgeGraph, ActionItem


class XKGApp:
    def __init__(self, root):
        self.root = root
        self.kg = None
        self.setup_ui()
    
    def setup_ui(self):
        self.root.title("X Knowledge Graph")
        self.root.geometry("900x600")
        self.root.configure(bg="#1a1a2e")
        
        # Colors
        self.colors = {
            "bg": "#1a1a2e",
            "panel": "#16213e", 
            "text": "#ffffff",
            "accent": "#0f3460",
            "success": "#4CAF50",
            "warning": "#FF9800"
        }
        
        # Header
        header = Frame(self.root, bg=self.colors["bg"], pady=10)
        header.pack(fill=X)
        Label(header, text="X Knowledge Graph", font=("Arial", 18, "bold"), 
              bg=self.colors["bg"], fg=self.colors["text"]).pack()
        Label(header, text="Extract actions from your X and Grok exports", 
              font=("Arial", 9), bg=self.colors["bg"], fg="#888").pack()
        
        # Main content
        content = Frame(self.root, padx=20, pady=10)
        content.pack(fill=BOTH, expand=True)
        
        # Left panel - Controls
        left = Frame(content, width=250)
        left.pack(side=LEFT, fill=Y, padx=(0, 15))
        
        # Export type selector
        self.export_type = StringVar(value="grok")
        Label(left, text="Export Type:", bg=self.colors["bg"], fg=self.colors["text"]).pack(anchor=W, pady=(0, 5))
        Radiobutton(left, text="Grok", variable=self.export_type, value="grok", 
                   bg=self.colors["bg"], fg=self.colors["text"], selectcolor=self.colors["panel"]).pack(anchor=W)
        Radiobutton(left, text="X (Twitter)", variable=self.export_type, value="x",
                   bg=self.colors["bg"], fg=self.colors["text"], selectcolor=self.colors["panel"]).pack(anchor=W)
        
        # Select folder button
        Button(left, text="📁 Select Export Folder", command=self.select_folder,
               bg=self.colors["accent"], fg="white", font=("Arial", 10, "bold")).pack(fill=X, pady=15)
        
        # Selected path
        self.path_label = Label(left, text="No folder selected", wraplength=230,
                                bg=self.colors["bg"], fg="#888", font=("Arial", 8))
        self.path_label.pack(anchor=W)
        
        # Build button
        Button(left, text="🔨 Build Knowledge Graph", command=self.build_graph,
               bg="#4CAF50", fg="white", font=("Arial", 11, "bold")).pack(fill=X, pady=10)
        
        # Export buttons
        Button(left, text="📤 Export Actions (JSON)", command=self.export_actions,
               bg=self.colors["accent"], fg="white").pack(fill=X, pady=5)
        Button(left, text="📊 Export Stats (JSON)", command=self.export_stats,
               bg=self.colors["accent"], fg="white").pack(fill=X, pady=5)
        
        # Right panel - Output
        right = Frame(content)
        right.pack(side=RIGHT, fill=BOTH, expand=True)
        
        Label(right, text="Output:", bg=self.colors["bg"], fg=self.colors["text"]).pack(anchor=W)
        
        self.output = scrolledtext.ScrolledText(right, bg="#0d0d1a", fg=self.colors["text"],
                                                font=("Consolas", 10), wrap=WORD)
        self.output.pack(fill=BOTH, expand=True, pady=(5, 0))
        
        # Footer
        footer = Frame(self.root, bg=self.colors["panel"], pady=8)
        footer.pack(fill=X)
        self.status = Label(footer, text="Ready", bg=self.colors["panel"], fg="#888")
        self.status.pack()
    
    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.output.insert(END, f"[{timestamp}] {msg}\n")
        self.output.see(END)
    
    def select_folder(self):
        folder = filedialog.askdirectory(title="Select export folder")
        if folder:
            self.export_path = folder
            self.path_label.config(text=folder[:50] + "..." if len(folder) > 50 else folder)
            self.log(f"Selected: {folder}")
    
    def build_graph(self):
        if not hasattr(self, 'export_path'):
            messagebox.showerror("Error", "Please select an export folder first")
            return
        
        self.log("Building knowledge graph...")
        self.status.config(text="Building...")
        self.root.update()
        
        try:
            self.kg = KnowledgeGraph()
            result = self.kg.build_from_export(self.export_path, self.export_type.get())
            
            self.log(f"✅ Done!")
            self.log(f"  Tweets/Posts: {result['stats']['total_tweets']}")
            self.log(f"  Actions: {result['stats']['total_actions']}")
            self.log(f"  Topics: {result['stats']['topics_count']}")
            
            if result['actions']:
                self.log(f"\n📋 Actions extracted:")
                for i, action in enumerate(result['actions'][:10], 1):
                    self.log(f"  {i}. {action.text[:60]}...")
                    if action.amazon_link:
                        self.log(f"     🛒 {action.amazon_link}")
            
            self.status.config(text=f"Built: {result['stats']['total_actions']} actions")
            
        except Exception as e:
            self.log(f"❌ Error: {e}")
            messagebox.showerror("Error", str(e))
            self.status.config(text="Error")
    
    def export_actions(self):
        if not self.kg:
            messagebox.showwarning("Warning", "Build a graph first")
            return
        
        actions = [a.to_dict() for a in self.kg.actions]
        filepath = filedialog.asksaveasfilename(defaultextension=".json",
                                               filetypes=[("JSON", "*.json")])
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(actions, f, indent=2)
            self.log(f"📤 Exported {len(actions)} actions to {filepath}")
            messagebox.showinfo("Exported", f"{len(actions)} actions exported")
    
    def export_stats(self):
        if not self.kg:
            messagebox.showwarning("Warning", "Build a graph first")
            return
        
        filepath = filedialog.asksaveasfilename(defaultextension=".json",
                                               filetypes=[("JSON", "*.json")])
        if filepath:
            stats = {
                'stats': {
                    'total_tweets': len(kg.tweets) if hasattr(kg, 'tweets') else 0,
                    'total_actions': len(kg.actions),
                    'topics_count': len(kg.topics)
                }
            }
            with open(filepath, 'w') as f:
                json.dump(stats, f, indent=2)
            self.log(f"📊 Stats exported to {filepath}")


def main():
    root = Tk()
    app = XKGApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
