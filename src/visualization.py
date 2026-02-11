"""
Graph Visualization Module for X Knowledge Graph
Provides multiple layout options and interactive visualization using Matplotlib
"""

import sys
import os
from pathlib import Path
from typing import Dict, Optional, List, Any, Tuple
from dataclasses import dataclass
import json

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# For 3D visualization
try:
    from mpl_toolkits.mplot3d import Axes3D
    HAS_3D = True
except ImportError:
    HAS_3D = False


@dataclass
class VisualizationConfig:
    """Configuration for graph visualization"""
    # Layout options
    layout_type: str = "spring"  # spring, circular, shell, spectral, kamada_kawai, random, hierarchical, 3d
    
    # Visual settings
    node_size: int = 200
    edge_width: float = 0.5
    edge_alpha: float = 0.3
    
    # Node colors by type
    node_colors: Dict[str, str] = None
    
    # Action status colors
    action_pending_color: str = "#f44336"  # Red
    action_complete_color: str = "#4CAF50"  # Green
    
    # Thresholds
    similarity_threshold: float = 0.7
    max_nodes_for_3d: int = 500
    
    def __post_init__(self):
        if self.node_colors is None:
            self.node_colors = {
                "tweet": "#2196F3",      # Blue
                "like": "#E91E63",       # Pink
                "retweet": "#9C27B0",    # Purple
                "retweeted_original": "#673AB7",  # Deep Purple
                "grok": "#FF9800",       # Orange
                "topic": "#607D8B",      # Blue Grey
                "action": self.action_pending_color,  # Red (changes based on status)
            }


class GraphVisualizer:
    """Handles all graph visualization operations"""
    
    def __init__(self, graph: nx.Graph, config: Optional[VisualizationConfig] = None):
        self.graph = graph
        self.config = config or VisualizationConfig()
        
        # Create figure and axes
        self.figure = Figure(figsize=(10, 8), dpi=100)
        self.ax = self.figure.add_subplot(111)
        
        # 3D figure (created on demand)
        self.figure_3d = None
        self.ax_3d = None
        
        # Current positions
        self.positions = None
        self.layout_type = self.config.layout_type
        
        # Color mapping cache
        self._node_color_cache = {}
    
    def compute_layout(self, layout_type: Optional[str] = None) -> Dict:
        """Compute node positions based on layout type"""
        if layout_type:
            self.layout_type = layout_type
        
        if self.graph is None or self.graph.number_of_nodes() == 0:
            return {}
        
        n_nodes = self.graph.number_of_nodes()
        
        # For large graphs, use faster layouts
        if n_nodes > 1000:
            if self.layout_type in ["3d", "kamada_kawai"]:
                self.layout_type = "spring"
        
        # Compute layout based on type
        layouts = {
            "spring": self._spring_layout,
            "circular": self._circular_layout,
            "shell": self._shell_layout,
            "spectral": self._spectral_layout,
            "random": self._random_layout,
            "hierarchical": self._hierarchical_layout,
            "kamada_kawai": self._kamada_kawai_layout,
            "3d": self._spring_layout_3d,
        }
        
        layout_func = layouts.get(self.layout_type, self._spring_layout)
        self.positions = layout_func()
        
        return self.positions
    
    def _spring_layout(self) -> Dict:
        """Force-directed (spring) layout"""
        return nx.spring_layout(
            self.graph,
            k=2/np.sqrt(self.graph.number_of_nodes()),
            iterations=50,
            seed=42
        )
    
    def _circular_layout(self) -> Dict:
        """Circular layout - nodes on a circle"""
        return nx.circular_layout(self.graph)
    
    def _shell_layout(self) -> Dict:
        """Shell (radial) layout - concentric circles"""
        # Group nodes by type for shell assignment
        types = {}
        for node, data in self.graph.nodes(data=True):
            node_type = data.get("type", "other")
            if node_type not in types:
                types[node_type] = []
            types[node_type].append(node)
        
        # Create shells (most important = inner)
        shells = []
        priority = ["topic", "tweet", "like", "retweet", "retweeted_original", "grok", "action"]
        for p in priority:
            if p in types:
                shells.append(types[p])
        # Add any remaining nodes
        for t in types:
            if t not in priority:
                shells.append(types[t])
        
        return nx.shell_layout(self.graph, nlist=shells)
    
    def _spectral_layout(self) -> Dict:
        """Spectral layout using Laplacian"""
        return nx.spectral_layout(self.graph)
    
    def _random_layout(self) -> Dict:
        """Random layout"""
        return nx.random_layout(self.graph, seed=42)
    
    def _hierarchical_layout(self) -> Dict:
        """Hierarchical layout (top-down)"""
        if not nx.is_directed_acyclic_graph(self.graph):
            # Fallback to spring for non-DAGs
            return self._spring_layout()
        
        # Assign levels based on longest path from roots
        levels = {}
        
        # Find roots (nodes with no predecessors)
        for node in self.graph.nodes():
            preds = list(self.graph.predecessors(node))
            if not preds:
                levels[node] = 0
        
        # BFS to assign levels
        visited = set(levels.keys())
        queue = list(levels.keys())
        
        while queue:
            current = queue.pop(0)
            for successor in self.graph.successors(current):
                if successor not in visited:
                    level = levels[current] + 1
                    levels[successor] = level
                    visited.add(successor)
                    queue.append(successor)
        
        # Assign positions
        positions = {}
        level_groups = {}
        for node, level in levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(node)
        
        max_level = max(levels.values()) if levels else 0
        
        for level, nodes in level_groups.items():
            n_nodes = len(nodes)
            for i, node in enumerate(nodes):
                x = (i - n_nodes/2) / max(1, n_nodes)
                y = -level / max(1, max_level)
                positions[node] = (x, y)
        
        return positions
    
    def _kamada_kawai_layout(self) -> Dict:
        """Kamada-Kawai force-directed layout"""
        return nx.kamada_kawai_layout(self.graph)
    
    def _spring_layout_3d(self) -> Dict:
        """3D spring layout"""
        # Use 2D spring and add random z
        pos_2d = self._spring_layout()
        return {
            node: (x, y, np.random.random() * 2 - 1)
            for node, (x, y) in pos_2d.items()
        }
    
    def get_node_colors(self) -> List[str]:
        """Generate list of colors for each node"""
        colors = []
        
        for node, data in self.graph.nodes(data=True):
            node_type = data.get("type", "other")
            
            # Check for cached color
            if node in self._node_color_cache:
                colors.append(self._node_color_cache[node])
                continue
            
            # Determine color based on type and status
            if node_type == "action":
                status = data.get("status", "pending")
                color = self.config.action_complete_color if status == "complete" else self.config.action_pending_color
            else:
                color = self.config.node_colors.get(node_type, "#999999")
            
            self._node_color_cache[node] = color
            colors.append(color)
        
        return colors
    
    def get_node_sizes(self) -> List[float]:
        """Generate list of sizes for each node"""
        sizes = []
        
        for node, data in self.graph.nodes(data=True):
            node_type = data.get("type", "other")
            
            if node_type == "topic":
                size = self.config.node_size * 3
            elif node_type == "action":
                size = self.config.node_size * 1.5
            elif node_type in ["tweet", "like", "retweet"]:
                size = self.config.node_size
            else:
                size = self.config.node_size * 0.8
            
            sizes.append(size)
        
        return sizes
    
    def get_node_labels(self, max_length: int = 30) -> Dict[str, str]:
        """Generate labels for nodes"""
        labels = {}
        
        for node, data in self.graph.nodes(data=True):
            text = data.get("text", "")
            node_type = data.get("type", "")
            
            if node_type == "topic":
                name = data.get("name", "")
                keywords = data.get("keywords", [])[:3]
                labels[node] = f"📁 {name}\n({', '.join(keywords[:2])})" if name else str(node)
            elif node_type == "action":
                priority = data.get("priority", "").upper()
                text_short = text[:max_length] + "..." if len(text) > max_length else text
                labels[node] = f"⚡ {text_short}\n[{priority}]" if priority else f"⚡ {text_short}"
            else:
                text_short = text[:max_length] + "..." if len(text) > max_length else text
                labels[node] = text_short if text_short else str(node)
        
        return labels
    
    def draw(self, ax: Optional[plt.Axes] = None, show_labels: bool = True,
             highlight_actions: bool = True) -> Tuple[plt.Figure, plt.Axes]:
        """Draw the graph"""
        if ax is None:
            ax = self.ax
        
        if self.positions is None:
            self.compute_layout()
        
        if self.graph is None or self.graph.number_of_nodes() == 0:
            ax.text(0.5, 0.5, "No graph data to display", 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=14, color="#666")
            return self.figure, ax
        
        # Get visual properties
        colors = self.get_node_colors()
        sizes = self.get_node_sizes()
        labels = self.get_node_labels() if show_labels else {}
        
        # Draw edges
        edge_colors = []
        edge_widths = []
        
        for u, v, data in self.graph.edges(data=True):
            relation = data.get("relation", "default")
            
            if relation == "reply":
                edge_colors.append("#4CAF50")  # Green for replies
                edge_widths.append(0.8)
            elif relation == "contains_action":
                edge_colors.append("#FF9800")  # Orange for actions
                edge_widths.append(1.0)
            elif relation == "similar":
                edge_colors.append("#FFC107")  # Amber for similar
                edge_widths.append(0.3)
            elif relation == "belongs_to":
                edge_colors.append("#607D8B")  # Grey for topics
                edge_widths.append(0.5)
            else:
                edge_colors.append("#CCCCCC")
                edge_widths.append(self.config.edge_width)
        
        # Draw the graph
        nx.draw_networkx_edges(
            self.graph, self.positions,
            ax=ax,
            edge_color=edge_colors,
            width=edge_widths,
            alpha=self.config.edge_alpha,
            arrows=True,
            arrowsize=10,
            arrowstyle="->",
            connectionstyle="arc3,rad=0.1"
        )
        
        nx.draw_networkx_nodes(
            self.graph, self.positions,
            ax=ax,
            node_color=colors,
            node_size=sizes,
            alpha=0.9
        )
        
        if show_labels:
            nx.draw_networkx_labels(
                self.graph, self.positions,
                labels=labels,
                ax=ax,
                font_size=6,
                font_color="black"
            )
        
        # Add legend
        self._add_legend(ax)
        
        # Style the axes
        ax.set_facecolor("#FAFAFA")
        ax.set_xticks([])
        ax.set_yticks([])
        
        return self.figure, ax
    
    def _add_legend(self, ax: plt.Axes):
        """Add a legend to the plot"""
        from matplotlib.patches import Patch
        
        legend_elements = [
            Patch(facecolor="#2196F3", label="Tweet"),
            Patch(facecolor="#E91E63", label="Like"),
            Patch(facecolor="#FF9800", label="Grok"),
            Patch(facecolor="#607D8B", label="Topic"),
            Patch(facecolor="#f44336", label="Action (Pending)"),
            Patch(facecolor="#4CAF50", label="Action (Complete)"),
        ]
        
        ax.legend(handles=legend_elements, loc='upper left', 
                 fontsize=8, framealpha=0.9)
    
    def draw_3d(self) -> Tuple[plt.Figure, plt.Axes]:
        """Draw 3D visualization"""
        if not HAS_3D:
            raise ImportError("3D visualization requires mpl_toolkits.mplot3d")
        
        if self.figure_3d is None:
            self.figure_3d = plt.figure(figsize=(12, 10), dpi=100)
            self.ax_3d = self.figure_3d.add_subplot(111, projection='3d')
        
        self.ax_3d.clear()
        
        if self.graph is None or self.graph.number_of_nodes() == 0:
            self.ax_3d.text(0.5, 0.5, 0.5, "No graph data", 
                           ha='center', va='center', transform=self.ax_3d.transAxes)
            return self.figure_3d, self.ax_3d
        
        if self.positions is None:
            self.compute_layout("3d")
        
        # Extract 3D positions
        xs, ys, zs = [], [], []
        colors = []
        
        for node in self.graph.nodes():
            pos = self.positions.get(node, (0, 0, 0))
            xs.append(pos[0])
            ys.append(pos[1])
            zs.append(pos[2])
            
            data = self.graph.nodes[node]
            node_type = data.get("type", "other")
            
            if node_type == "action":
                status = data.get("status", "pending")
                color = self.config.action_complete_color if status == "complete" else self.config.action_pending_color
            else:
                color = self.config.node_colors.get(node_type, "#999999")
            
            colors.append(color)
        
        # Draw nodes
        sizes = [s / 10 for s in self.get_node_sizes()]
        self.ax_3d.scatter(xs, ys, zs, c=colors, s=sizes, alpha=0.8)
        
        # Draw edges
        for u, v in self.graph.edges():
            if u in self.positions and v in self.positions:
                pu = self.positions[u]
                pv = self.positions[v]
                self.ax_3d.plot([pu[0], pv[0]], [pu[1], pv[1]], [pu[2], pv[2]], 
                               'gray', alpha=0.3, linewidth=0.5)
        
        # Labels for actions
        labels = self.get_node_labels()
        for node, label in labels.items():
            if node in self.positions:
                pos = self.positions[node]
                self.ax_3d.text(pos[0], pos[1], pos[2], label, fontsize=5, alpha=0.7)
        
        self.ax_3d.set_xlabel('X')
        self.ax_3d.set_ylabel('Y')
        self.ax_3d.set_zlabel('Z')
        
        return self.figure_3d, self.ax_3d
    
    def get_statistics(self) -> Dict:
        """Get graph visualization statistics"""
        if self.graph is None:
            return {"nodes": 0, "edges": 0}
        
        stats = {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "layout": self.layout_type,
            "node_types": {},
            "action_stats": {"pending": 0, "complete": 0}
        }
        
        for _, data in self.graph.nodes(data=True):
            node_type = data.get("type", "unknown")
            stats["node_types"][node_type] = stats["node_types"].get(node_type, 0) + 1
            
            if node_type == "action":
                status = data.get("status", "pending")
                stats["action_stats"][status] = stats["action_stats"].get(status, 0) + 1
        
        return stats


class VisualizationPanel:
    """Tkinter panel for embedding graph visualization"""
    
    def __init__(self, parent, graph: Optional[nx.Graph] = None, 
                 config: Optional[VisualizationConfig] = None):
        self.parent = parent
        self.graph = graph
        self.config = config or VisualizationConfig()
        
        self.visualizer = None
        self.canvas = None
        
        self.layout_var = tk.StringVar(value="Force-Directed")
        self.show_labels_var = tk.BooleanVar(value=True)
        self.highlight_actions_var = tk.BooleanVar(value=True)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the visualization panel UI"""
        # Control frame
        control_frame = ttk.Frame(self.parent)
        control_frame.pack(fill=X, pady=(0, 10))
        
        # Layout selector
        ttk.Label(control_frame, text="Layout:").pack(side=LEFT, padx=(0, 5))
        
        layouts = ["Force-Directed", "Hierarchical", "Circular", "Shell", "Spectral", "3D"]
        if not HAS_3D:
            layouts = [l for l in layouts if l != "3D"]
        
        layout_combo = ttk.Combobox(
            control_frame, 
            textvariable=self.layout_var,
            values=layouts,
            state="readonly",
            width=15
        )
        layout_combo.pack(side=LEFT, padx=(0, 10))
        layout_combo.bind("<<ComboboxSelected>>", self._on_layout_change)
        
        # Checkboxes
        ttk.Checkbutton(
            control_frame, 
            text="Labels",
            variable=self.show_labels_var,
            command=self.redraw
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Checkbutton(
            control_frame, 
            text="Highlight Actions",
            variable=self.highlight_actions_var,
            command=self.redraw
        ).pack(side=LEFT, padx=(0, 10))
        
        # Refresh button
        ttk.Button(control_frame, text="🔄 Refresh", 
                  command=self.redraw).pack(side=LEFT, padx=(0, 10))
        
        # Export button
        ttk.Button(control_frame, text="💾 Save Image", 
                  command=self._save_image).pack(side=RIGHT)
        
        # Figure frame
        self.figure_frame = ttk.Frame(self.parent)
        self.figure_frame.pack(fill=BOTH, expand=True)
        
        # Create initial figure
        self.figure = Figure(figsize=(6, 5), dpi=100)
        self.figure.patch.set_facecolor("#FAFAFA")
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.figure_frame)
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        
        # Status label
        self.status_label = ttk.Label(self.parent, text="No graph loaded", font=("Segoe UI", 9))
        self.status_label.pack(fill=X, pady=(5, 0))
    
    def set_graph(self, graph: nx.Graph):
        """Set the graph to visualize"""
        self.graph = graph
        self.visualizer = GraphVisualizer(graph, self.config)
        self.redraw()
    
    def _on_layout_change(self, event=None):
        """Handle layout change"""
        layout_map = {
            "Force-Directed": "spring",
            "Hierarchical": "hierarchical",
            "Circular": "circular",
            "Shell": "shell",
            "Spectral": "spectral",
            "3D": "3d"
        }
        
        layout = layout_map.get(self.layout_var.get(), "spring")
        
        if self.visualizer:
            self.visualizer.compute_layout(layout)
            self._draw()
    
    def redraw(self):
        """Redraw the visualization"""
        if self.graph is None:
            self.status_label.config(text="No graph loaded")
            return
        
        self.visualizer = GraphVisualizer(self.graph, self.config)
        
        layout_map = {
            "Force-Directed": "spring",
            "Hierarchical": "hierarchical",
            "Circular": "circular",
            "Shell": "shell",
            "Spectral": "spectral",
            "3D": "3d"
        }
        
        layout = layout_map.get(self.layout_var.get(), "spring")
        self.visualizer.compute_layout(layout)
        
        self._draw()
        self._update_status()
    
    def _draw(self):
        """Draw the current graph"""
        if self.layout_var.get() == "3D" and HAS_3D:
            self.visualizer.draw_3d()
        else:
            self.visualizer.draw(
                show_labels=self.show_labels_var.get(),
                highlight_actions=self.highlight_actions_var.get()
            )
        
        self.canvas.draw()
    
    def _update_status(self):
        """Update status label with statistics"""
        if self.visualizer:
            stats = self.visualizer.get_statistics()
            pending = stats.get("action_stats", {}).get("pending", 0)
            complete = stats.get("action_stats", {}).get("complete", 0)
            
            self.status_label.config(
                text=f"Nodes: {stats['nodes']} | Edges: {stats['edges']} | "
                     f"Actions: 🔴{pending} 🟢{complete} | Layout: {stats['layout']}"
            )
    
    def _save_image(self):
        """Save current visualization as image"""
        if self.visualizer is None:
            messagebox.showwarning("Warning", "No graph to save")
            return
        
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("PDF", "*.pdf"), ("SVG", "*.svg")],
            initialfile="knowledge_graph.png"
        )
        
        if path:
            if self.layout_var.get() == "3D" and HAS_3D:
                self.visualizer.figure_3d.savefig(path, dpi=150, bbox_inches='tight')
            else:
                self.figure.savefig(path, dpi=150, bbox_inches='tight')
            
            messagebox.showinfo("Saved", f"Graph saved to: {path}")


def create_visualization_window(parent, graph: nx.Graph, title: str = "Graph Visualization"):
    """Create a popup window with full visualization"""
    window = tk.Toplevel(parent)
    window.title(title)
    window.geometry("900x700")
    
    panel = VisualizationPanel(window, graph)
    panel.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    return window, panel
