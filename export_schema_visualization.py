#!/usr/bin/env python3
"""
Export schema visualization for X Knowledge Graph.
Run: python3 export_schema_visualization.py
Outputs: schema.json (for Neo4j) + console visualization
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, 'core')
from xkg_core import KnowledgeGraph, FlexibleXParser, FlexibleGrokParser


def export_graph_with_timestamps():
    """Export graph with ISO timestamps for all nodes"""
    
    kg = KnowledgeGraph()
    
    # Parse both exports
    print("Parsing X export...")
    x_result = kg.build_from_export('./test_data/x_export', 'x')
    
    print("Parsing Grok export...")
    grok_result = kg.build_from_export('./test_data/grok_export', 'grok')
    
    print("Building combined graph...")
    combined = kg.build_from_both('./test_data/x_export', './test_data/grok_export')
    
    # Export with enhanced structure
    graph = kg.export_for_d3()
    
    # Add conversation nodes
    for conv in grok_result.get('grok_conversations', []):
        graph['nodes'].append({
            'id': f"conv_{conv['id']}",
            'type': 'conversation',
            'label': conv.get('title', 'Untitled')[:50],
            'title': conv.get('title', ''),
            'message_count': conv.get('message_count', 0),
            'start_date': conv.get('create_time', ''),
            'source': 'grok'
        })
    
    # Add conversation links
    for node in graph['nodes']:
        if node.get('type') == 'grok' and node.get('conversation_id'):
            graph['edges'].append({
                'source': node['id'],
                'target': f"conv_{node['conversation_id']}",
                'type': 'part_of'
            })
    
    return graph, combined


def print_schema_visualization(graph):
    """Print ASCII visualization of the schema"""
    
    print("\n" + "="*70)
    print("SCHEMA VISUALIZATION (Neo4j-Ready)")
    print("="*70)
    
    # Count by type
    node_counts = {}
    for node in graph['nodes']:
        t = node.get('type', 'unknown')
        node_counts[t] = node_counts.get(t, 0) + 1
    
    print("\n📊 NODE COUNTS:")
    for t, count in sorted(node_counts.items()):
        print(f"   {t:20} : {count:3} nodes")
    
    print("\n🔗 EDGE COUNTS:")
    edge_counts = {}
    for edge in graph['edges']:
        t = edge.get('type', 'unknown')
        edge_counts[t] = edge_counts.get(t, 0) + 1
    for t, count in sorted(edge_counts.items()):
        print(f"   {t:20} : {count:3} edges")
    
    print("\n" + "-"*70)
    print("SAMPLE NODE STRUCTURES:")
    print("-"*70)
    
    # Show sample of each node type
    shown = set()
    for node in graph['nodes']:
        ntype = node.get('type', 'unknown')
        if ntype in shown:
            continue
        shown.add(ntype)
        
        print(f"\n{ntype.upper()} Node:")
        # Print key fields only
        sample = {
            'id': node.get('id', '')[:30],
            'label': node.get('label', '')[:40],
            'source': node.get('source', ''),
            'created_at': node.get('created_at', '')[:10] if node.get('created_at') else 'N/A'
        }
        for k, v in sample.items():
            print(f"   {k}: {v}")
    
    print("\n" + "-"*70)
    print("SAMPLE EDGE STRUCTURES:")
    print("-"*70)
    
    shown_edges = set()
    for edge in graph['edges']:
        etype = edge.get('type', 'unknown')
        if etype in shown_edges:
            continue
        shown_edges.add(etype)
        print(f"\n{etype.upper()} Edge:")
        print(f"   source: {edge.get('source', '')[:30]}...")
        print(f"   target: {edge.get('target', '')[:30]}...")
    
    print("\n" + "="*70)
    print("GRAPH FLOW DIAGRAM:")
    print("="*70)
    print("""
    ┌─────────────────────────────────────────────────────────────┐
    │                     DATA FLOW                              │
    └─────────────────────────────────────────────────────────────┘
    
    ┌──────────┐                    ┌────────────────────┐
    │   X      │  tweets            │  Grok Export       │
    │  Export  │───────────────────►│  (posts.json)      │
    └──────────┘                    └────────────────────┘
          │                                 │
          ▼                                 ▼
    ┌──────────┐                    ┌────────────────────┐
    │ Flexible │                    │  FlexibleGrokParser│
    │X Parser  │                    │  + Conversations   │
    └──────────┘                    └────────────────────┘
          │                                 │
          ▼                                 ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                  KNOWLEDGE GRAPH                           │
    ├─────────────────────────────────────────────────────────────┤
    │  Nodes:                                                     │
    │    • tweet (5)    • grok (10)                               │
    │    • action (19)  • topic (10)  • conversation (0)          │
    │                                                             │
    │  Edges:                                                     │
    │    • tweet → action (extracts)                              │
    │    • grok → action (extracts)                              │
    │    • action → topic (belongs_to)                            │
    │    • grok → conversation (part_of)                          │
    └─────────────────────────────────────────────────────────────┘
          │                                 │
          ▼                                 ▼
    ┌──────────┐                    ┌────────────────────┐
    │   D3.js  │                    │  Neo4j Import      │
    │ Graph    │                    │  (schema.json)    │
    └──────────┘                    └────────────────────┘
    """)


def export_neo4j_cypher(graph, filename='schema_for_neo4j.json'):
    """Export graph in format ready for Neo4j import"""
    
    # Add missing conversation_id to nodes
    for node in graph['nodes']:
        if 'conversation_id' not in node:
            node['conversation_id'] = None
        if 'created_at' not in node:
            from datetime import datetime
            node['created_at'] = datetime.now().isoformat()
    
    with open(filename, 'w') as f:
        json.dump(graph, f, indent=2)
    
    print(f"\n✅ Exported to {filename}")
    print(f"   Nodes: {len(graph['nodes'])}")
    print(f"   Edges: {len(graph['edges'])}")
    
    return filename


if __name__ == '__main__':
    print("\n" + "="*70)
    print("X KNOWLEDGE GRAPH - SCHEMA EXPORT & VISUALIZATION")
    print("="*70)
    
    # Export with improvements
    graph, stats = export_graph_with_timestamps()
    
    # Print visualization
    print_schema_visualization(graph)
    
    # Export for Neo4j
    export_neo4j_cypher(graph)
    
    # Print stats
    print("\n" + "="*70)
    print("STATISTICS:")
    print("="*70)
    for k, v in stats['stats'].items():
        print(f"   {k:25} : {v}")
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("""
    1. ✅ Schema exported (schema_for_neo4j.json)
    2. ⏳ Import to Neo4j: ./neo4j_import.py --password your_password
    3. ⏳ Run Cypher queries for insights
    4. ⏳ Add more exports (AI conversations, etc.)
    """)

