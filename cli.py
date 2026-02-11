#!/usr/bin/env python3
"""
X Knowledge Graph - Multi-Graph CLI
Supports building and managing separate graphs for tweets, likes, and Grok.
"""

import sys
import os
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any

from src.data_ingestion import load_x_export, load_grok_export
from src.graph_builder import KnowledgeGraph
from src.action_extractor import ActionExtractor
from src.topic_modeler import TopicModeler
from src.task_flow import TaskFlowManager


@dataclass
class GraphBundle:
    """Container for all knowledge graphs"""
    grok: KnowledgeGraph = None
    tweets: KnowledgeGraph = None
    likes: KnowledgeGraph = None
    combined: KnowledgeGraph = None
    
    def get(self, name: str) -> Optional[KnowledgeGraph]:
        return getattr(self, name, None)
    
    def names(self) -> List[str]:
        return ["grok", "tweets", "likes", "combined"]


class MultiGraphManager:
    """Manages multiple knowledge graphs"""
    
    def __init__(self):
        self.graphs = GraphBundle()
        self.flow_managers = {name: TaskFlowManager() for name in self.graphs.names()}
    
    def build_graph(self, graph_type: str, x_path: str = None, grok_path: str = None) -> Dict:
        """Build a specific graph type"""
        kg = KnowledgeGraph()
        action_extractor = ActionExtractor()
        topic_modeler = TopicModeler()
        
        data = {"tweets": [], "likes": [], "retweets": [], "grok": []}
        
        # Load data
        if graph_type in ["tweets", "likes", "combined"]:
            if x_path and os.path.exists(x_path):
                x_data = load_x_export(Path(x_path))
                data["tweets"] = x_data.get("tweets", [])
                data["likes"] = x_data.get("likes", [])
                data["retweets"] = x_data.get("retweets", [])
        
        if graph_type in ["grok", "combined"]:
            if grok_path and os.path.exists(grok_path):
                grok_data = load_grok_export(Path(grok_path))
                if grok_data:
                    data["grok"] = grok_data
                    kg.add_grok_messages(grok_data)
        
        # Build graph
        if graph_type in ["tweets", "combined"]:
            kg.add_tweets(data["tweets"])
            kg.add_retweets(data["retweets"])
        
        if graph_type in ["likes", "combined"]:
            kg.add_likes(data["likes"])
        
        # Extract actions
        all_content = []
        if graph_type in ["tweets", "combined"]:
            all_content.extend(data["tweets"])
        if graph_type in ["likes", "combined"]:
            all_content.extend(data["likes"])
        if graph_type in ["grok", "combined"]:
            all_content.extend(data["grok"])
        
        actions = action_extractor.extract_all_actions(all_content)
        kg.add_actions(actions)
        
        # Topics
        topics = topic_modeler.identify_topics(
            data["tweets"] + data["likes"] + data["grok"]
        )
        kg.add_topics(topics)
        
        # Build flows
        self.flow_managers[graph_type].build_flows(kg)
        
        # Store
        setattr(self.graphs, graph_type, kg)
        
        return {
            "graph_type": graph_type,
            "tweets": len(data["tweets"]),
            "likes": len(data["likes"]),
            "grok": len(data["grok"]),
            "actions": len(actions),
            "topics": len(topics),
            "nodes": kg.get_stats()["total_nodes"],
            "edges": kg.get_stats()["total_edges"]
        }
    
    def build_all(self, x_path: str = None, grok_path: str = None) -> Dict:
        """Build all graphs"""
        results = {}
        for graph_type in self.graphs.names():
            print(f"Building {graph_type}...")
            results[graph_type] = self.build_graph(graph_type, x_path, grok_path)
        return results
    
    def get_next_action(self, graph_type: str = "combined") -> Optional[Dict]:
        """Get next action from a graph"""
        kg = self.graphs.get(graph_type)
        if kg:
            return kg.get_next_action()
        return None
    
    def complete_action(self, graph_type: str, action_text: str) -> Optional[Dict]:
        """Complete an action and return next"""
        kg = self.graphs.get(graph_type)
        if not kg:
            return None
        
        pending = kg.get_pending_actions()
        for action in pending:
            if action_text.lower() in action.get("text", "").lower():
                kg.mark_action_complete(action["id"])
                return kg.get_next_action()
        return None
    
    def get_pending_actions(self, graph_type: str = "combined") -> List[Dict]:
        """Get all pending actions"""
        kg = self.graphs.get(graph_type)
        if kg:
            return kg.get_pending_actions()
        return []
    
    def get_action_summary(self) -> Dict[str, int]:
        """Get action counts for all graphs"""
        return {
            name: len(self.graphs.get(name).get_pending_actions()) 
            if self.graphs.get(name) else 0
            for name in self.graphs.names()
        }


def main():
    parser = argparse.ArgumentParser(
        description="X Knowledge Graph CLI - Multi-Graph Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  xkg build tweets                    # Build tweets graph only
  xkg build likes                     # Build likes graph only  
  xkg build grok                      # Build Grok conversations graph
  xkg build all --x /path/to/x --grok /path/to/grok  # Build all graphs
  
  xkg status                          # Show action counts per graph
  xkg next tweets                     # Show next action in tweets graph
  xkg next combined                   # Show next action in combined graph
  xkg complete tweets "action text"   # Complete an action
  
  xkg export combined graph.json      # Export combined graph for viz
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Build command
    build_parser = subparsers.add_parser("build", help="Build knowledge graphs")
    build_parser.add_argument("graph_type", nargs="?", default="combined",
                             choices=["grok", "tweets", "likes", "combined", "all"],
                             help="Which graph to build (default: combined)")
    build_parser.add_argument("--x", help="Path to X export directory")
    build_parser.add_argument("--grok", help="Path to Grok export directory")
    
    # Status command
    subparsers.add_parser("status", help="Show status of all graphs")
    
    # Next command
    next_parser = subparsers.add_parser("next", help="Show next action")
    next_parser.add_argument("graph_type", nargs="?", default="combined",
                            choices=["grok", "tweets", "likes", "combined"],
                            help="Which graph (default: combined)")
    
    # Complete command
    complete_parser = subparsers.add_parser("complete", help="Complete an action")
    complete_parser.add_argument("graph_type", choices=["grok", "tweets", "likes", "combined"],
                                help="Which graph")
    complete_parser.add_argument("action_text", help="Text to match (partial)")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export graph for visualization")
    export_parser.add_argument("graph_type", choices=["grok", "tweets", "likes", "combined"],
                              help="Which graph to export")
    export_parser.add_argument("-o", "--output", default="graph.json", help="Output file")
    
    # Shell command
    subparsers.add_parser("shell", help="Interactive mode")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize manager
    manager = MultiGraphManager()
    
    if args.command == "build":
        if args.graph_type == "all":
            results = manager.build_all(args.x, args.grok)
            print("\n✅ All Graphs Built Successfully!")
            for name, stats in results.items():
                print(f"\n📊 {name.upper()}:")
                print(f"   Tweets: {stats['tweets']}")
                print(f"   Likes: {stats['likes']}")
                print(f"   Grok: {stats['grok']}")
                print(f"   Actions: {stats['actions']}")
                print(f"   Topics: {stats['topics']}")
                print(f"   Nodes: {stats['nodes']}")
                print(f"   Edges: {stats['edges']}")
        else:
            stats = manager.build_graph(args.graph_type, args.x, args.grok)
            print(f"\n✅ {args.graph_type.upper()} Graph Built!")
            print(f"   Tweets: {stats['tweets']}")
            print(f"   Likes: {stats['likes']}")
            print(f"   Grok: {stats['grok']}")
            print(f"   Actions: {stats['actions']}")
            print(f"   Topics: {stats['topics']}")
            print(f"   Nodes: {stats['nodes']}")
            print(f"   Edges: {stats['edges']}")
    
    elif args.command == "status":
        summary = manager.get_action_summary()
        print("\n📊 Graph Status:")
        for name in manager.graphs.names():
            count = summary[name]
            status = "✓ Loaded" if manager.graphs.get(name) else "✗ Not built"
            print(f"   {name.upper()}: {count} actions ({status})")
    
    elif args.command == "next":
        action = manager.get_next_action(args.graph_type)
        if action:
            print(f"\n🎯 Next Action ({args.graph_type}):")
            print(f"   {action['text']}")
            print(f"   Topic: {action.get('topic', 'General')}")
            print(f"   Priority: {action.get('priority', 'medium')}")
        else:
            print(f"\n✅ No pending actions in {args.graph_type}")
    
    elif args.command == "complete":
        next_action = manager.complete_action(args.graph_type, args.action_text)
        if next_action:
            print(f"\n✓ Completed! Next action in {args.graph_type}:")
            print(f"   {next_action['text'][:80]}...")
        else:
            print(f"\n⚠️ Action not found or already complete")
    
    elif args.command == "export":
        kg = manager.graphs.get(args.graph_type)
        if not kg:
            print(f"Error: {args.graph_type} graph not built")
            sys.exit(1)
        
        export = kg.to_cytoscape_format()
        with open(args.output, 'w') as f:
            json.dump(export, f, indent=2)
        print(f"\n✓ Exported {args.graph_type} to {args.output}")
        print(f"   Nodes: {len(export['nodes'])}")
        print(f"   Edges: {len(export['edges'])}")
    
    elif args.command == "shell":
        print("\n🟢 X Knowledge Graph Interactive Shell (Multi-Graph Mode)")
        print("Commands: build, status, next, complete, export, switch, help, quit")
        print()
        
        current_graph = "combined"
        
        while True:
            try:
                cmd = input(f"xkg({current_graph})> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break
            
            if not cmd:
                continue
            
            parts = cmd.split()
            action = parts[0].lower()
            
            if action in ["quit", "exit", "q"]:
                print("Bye!")
                break
            
            elif action == "help":
                print("""
Available commands:
  build [grok|tweets|likes|combined|all]  - Build a graph
  switch <name>                            - Switch active graph
  status                                   - Show all graph statuses
  next                                     - Show next action in current graph
  complete <text>                          - Complete action matching text
  export <file.json>                       - Export current graph
  list                                     - List all graphs
  help                                     - Show this help
  quit                                     - Exit
                """)
            
            elif action == "switch":
                if len(parts) > 1 and parts[1] in manager.graphs.names():
                    current_graph = parts[1]
                    print(f"Switched to {current_graph}")
                else:
                    print(f"Available graphs: {', '.join(manager.graphs.names())}")
            
            elif action == "list":
                print("\nAvailable graphs:")
                for name in manager.graphs.names():
                    loaded = "✓" if manager.graphs.get(name) else "✗"
                    print(f"   {loaded} {name}")
            
            elif action == "build":
                gtype = parts[1] if len(parts) > 1 else "combined"
                if gtype == "all":
                    manager.build_all()
                    print("Built all graphs")
                elif gtype in manager.graphs.names():
                    manager.build_graph(gtype)
                    print(f"Built {gtype}")
                else:
                    print(f"Unknown graph type: {gtype}")
            
            elif action == "status":
                summary = manager.get_action_summary()
                for name in manager.graphs.names():
                    loaded = "✓" if manager.graphs.get(name) else "✗"
                    print(f"   {loaded} {name}: {summary[name]} actions")
            
            elif action == "next":
                action = manager.get_next_action(current_graph)
                if action:
                    print(f"\n🎯 {action['text'][:80]}...")
                    print(f"   Topic: {action.get('topic', 'General')}")
                else:
                    print("No pending actions")
            
            elif action == "complete":
                if len(parts) > 1:
                    text = " ".join(parts[1:])
                    next_action = manager.complete_action(current_graph, text)
                    if next_action:
                        print(f"✓ Next: {next_action['text'][:60]}...")
                    else:
                        print("Action not found")
                else:
                    print("Usage: complete <action text>")
            
            elif action == "export":
                kg = manager.graphs.get(current_graph)
                if kg:
                    fname = parts[1] if len(parts) > 1 else f"{current_graph}.json"
                    export = kg.to_cytoscape_format()
                    with open(fname, 'w') as f:
                        json.dump(export, f, indent=2)
                    print(f"Exported to {fname}")
                else:
                    print("Graph not built")
            
            else:
                print(f"Unknown command: {action}. Type 'help' for options.")


if __name__ == "__main__":
    main()
