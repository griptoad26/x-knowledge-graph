#!/usr/bin/env python3
"""
Neo4j Import Module for X Knowledge Graph

This module provides Neo4j integration for XKG, enabling:
- Graph database storage and querying
- Relationship-based queries
- Integration with LLM workflows (LangChain, GraphRAG)

Requirements:
    pip install neo4j

Usage:
    from neo4j_import import Neo4jConnector, import_to_neo4j

    # Connect to Neo4j
    connector = Neo4jConnector(uri="bolt://localhost:7687", user="neo4j", password="password")
    
    # Import data
    import_to_neo4j(graph_data, connector=connector)
    
    # Query the graph
    results = connector.query("MATCH (a:Action) RETURN a LIMIT 5")
"""

import json
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime

# Optional Neo4j dependency
try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import ServiceUnavailable, AuthError
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False


@dataclass
class Neo4jConfig:
    """Neo4j connection configuration."""
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "neo4j_password"
    database: str = "neo4j"
    encrypted: bool = False
    


class Neo4jConnector:
    """
    Neo4j database connector for XKG.
    
    Provides connection management, query execution,
    and graph operations for the X Knowledge Graph.
    """
    
    def __init__(self, config: Optional[Neo4jConfig] = None, **kwargs):
        """
        Initialize Neo4j connector.
        
        Args:
            config: Neo4jConfig instance or None (uses defaults + env vars)
            **kwargs: Override config attributes
        """
        if config is None:
            config = Neo4jConfig(
                uri=kwargs.get('uri', os.getenv('NEO4J_URI', 'bolt://localhost:7687')),
                user=kwargs.get('user', os.getenv('NEO4J_USER', 'neo4j')),
                password=kwargs.get('password', os.getenv('NEO4J_PASSWORD', 'neo4j_password')),
                database=kwargs.get('database', os.getenv('NEO4J_DATABASE', 'neo4j')),
            )
        self.config = config
        self._driver = None
        self._connected = False
        
    def connect(self) -> bool:
        """
        Establish connection to Neo4j.
        
        Returns:
            bool: True if connected successfully
        """
        if not NEO4J_AVAILABLE:
            print("WARNING: neo4j package not installed. Run: pip install neo4j")
            return False
            
        try:
            self._driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password),
                
            )
            # Verify connection
            self._driver.verify_connectivity()
            self._connected = True
            print(f"Connected to Neo4j at {self.config.uri}")
            return True
        except ServiceUnavailable as e:
            print(f"WARNING: Could not connect to Neo4j: {e}")
            return False
        except AuthError as e:
            print(f"WARNING: Authentication failed: {e}")
            return False
            
    def close(self):
        """Close the Neo4j connection."""
        if self._driver:
            self._driver.close()
            self._connected = False
            
    def is_connected(self) -> bool:
        """Check if connected to Neo4j."""
        return self._connected
        
    def query(self, cypher: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Execute a Cypher query.
        
        Args:
            cypher: Cypher query string
            params: Query parameters
            
        Returns:
            List of result dictionaries
        """
        if not self._connected:
            if not self.connect():
                return []
                
        with self._driver.session(database=self.config.database) as session:
            result = session.run(cypher, params or {})
            return [record.data() for record in result]
            
    def create_constraints(self) -> bool:
        """
        Create Neo4j constraints for XKG schema.
        
        Returns:
            bool: True if successful
        """
        constraints = [
            "CREATE CONSTRAINT grok_id IF NOT EXISTS FOR (g:Grok) REQUIRE g.id IS UNIQUE",
            "CREATE CONSTRAINT action_id IF NOT EXISTS FOR (a:Action) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT topic_name IF NOT EXISTS FOR (t:Topic) REQUIRE t.topic IS UNIQUE",
            "CREATE CONSTRAINT tweet_id IF NOT EXISTS FOR (t:Tweet) REQUIRE t.id IS UNIQUE",
        ]
        
        try:
            for cypher in constraints:
                self.query(cypher)
            print("Created Neo4j constraints")
            return True
        except Exception as e:
            print(f"WARNING: Could not create constraints: {e}")
            return False
            
    def create_indexes(self) -> bool:
        """
        Create indexes for query performance.
        
        Returns:
            bool: True if successful
        """
        indexes = [
            "CREATE INDEX grok_created IF NOT EXISTS FOR (n:Grok) ON (n.created_at)",
            "CREATE INDEX grok_author IF NOT EXISTS FOR (n:Grok) ON (n.author_id)",
            "CREATE INDEX action_priority IF NOT EXISTS FOR (n:Action) ON (n.priority)",
            "CREATE INDEX action_topic IF NOT EXISTS FOR (n:Action) ON (n.topic)",
            "CREATE INDEX action_source IF NOT EXISTS FOR (n:Action) ON (n.source_id)",
            "CREATE INDEX topic_created IF NOT EXISTS FOR (n:Topic) ON (n.created_at)",
        ]
        
        try:
            for cypher in indexes:
                self.query(cypher)
            print("Created Neo4j indexes")
            return True
        except Exception as e:
            print(f"WARNING: Could not create indexes: {e}")
            return False


def node_to_cypher(node: Dict) -> tuple:
    """
    Convert XKG node to Cypher MERGE statement.
    
    Args:
        node: Node dictionary from XKG
        
    Returns:
        Tuple of (cypher, params, node_type)
    """
    node_id = node.get('id', '')
    node_type = node.get('type', 'unknown')
    
    # Map XKG types to Neo4j labels
    type_label_map = {
        'grok': 'Grok',
        'action': 'Action',
        'topic': 'Topic',
        'tweet': 'Tweet',
        'conversation': 'Conversation',
    }
    
    label = type_label_map.get(node_type, node_type.capitalize())
    
    # Build properties
    properties = {
        'id': node_id,
        'label': node.get('label', ''),
        'text': node.get('text', ''),
        'topic': node.get('topic', 'general'),
        'source': node.get('source', node_type),
    }
    
    # Add type-specific properties
    if node_type == 'grok':
        properties['created_at'] = node.get('created_at', '')
        properties['author_id'] = node.get('author_id', '')
        properties['conversation_id'] = node.get('conversation_id', '')
        properties['conversation_title'] = node.get('conversation_title', '')
    elif node_type == 'action':
        properties['priority'] = node.get('priority', 'medium')
        properties['status'] = node.get('status', 'pending')
        properties['source_id'] = node.get('source_id', '')
        properties['extracted_at'] = node.get('extracted_at', '')
    elif node_type == 'topic':
        properties['created_at'] = node.get('created_at', '')
    
    # Build Cypher
    cypher = f"""
    MERGE (n:`{label}` {{id: $id}})
    SET n += $properties
    RETURN n
    """
    
    return cypher, {'id': node_id, 'properties': properties}, label


def edge_to_cypher(edge: Dict) -> tuple:
    """
    Convert XKG edge to Cypher relationship statement.
    
    Args:
        edge: Edge dictionary from XKG
        
    Returns:
        Tuple of (cypher, params, source_type, target_type)
    """
    source_id = edge.get('source', '')
    target_id = edge.get('target', '')
    edge_type = edge.get('type', 'RELATED')
    
    # Map edge types to Neo4j relationship types
    type_map = {
        'extracts': 'EXTRACTS',
        'belongs_to': 'BELONGS_TO',
        'replies_to': 'REPLIES_TO',
        'mentions': 'MENTIONS',
        'related': 'RELATED',
        'contains': 'CONTAINS',
    }
    
    rel_type = type_map.get(edge_type.lower(), edge_type.upper())
    
    # Build properties
    properties = {}
    if 'created_at' in edge:
        properties['created_at'] = edge['created_at']
    if 'confidence' in edge:
        properties['confidence'] = edge['confidence']
        
    cypher = f"""
    MATCH (source {{id: $source_id}})
    MATCH (target {{id: $target_id}})
    MERGE (source)-[r:`{rel_type}`]->(target)
    SET r += $properties
    RETURN r
    """
    
    params = {
        'source_id': source_id,
        'target_id': target_id,
        'properties': properties
    }
    
    return cypher, params, edge_type


def import_to_neo4j(
    graph_data: Dict, 
    connector: Optional[Neo4jConnector] = None,
    config: Optional[Neo4jConfig] = None,
    create_schema: bool = True
) -> Dict[str, Any]:
    """
    Import XKG graph data to Neo4j.
    
    Args:
        graph_data: XKG graph dictionary with 'nodes' and 'edges'
        connector: Neo4jConnector instance (creates if None)
        config: Neo4jConfig for new connector
        create_schema: Whether to create constraints/indexes
        
    Returns:
        Dict with import statistics
    """
    # Create connector if not provided
    if connector is None:
        connector = Neo4jConnector(config)
        if not connector.connect():
            return {
                'success': False,
                'error': 'Could not connect to Neo4j',
                'nodes_imported': 0,
                'edges_imported': 0
            }
    
    stats = {
        'success': True,
        'nodes_imported': 0,
        'edges_imported': 0,
        'errors': []
    }
    
    try:
        # Create schema
        if create_schema:
            connector.create_constraints()
            connector.create_indexes()
        
        # Import nodes
        nodes = graph_data.get('nodes', [])
        print(f"Importing {len(nodes)} nodes...")
        
        node_types = {}
        for node in nodes:
            try:
                cypher, params, node_type = node_to_cypher(node)
                connector.query(cypher, params)
                stats['nodes_imported'] += 1
                node_types[node_type] = node_types.get(node_type, 0) + 1
            except Exception as e:
                stats['errors'].append(f"Node {node.get('id')}: {e}")
        
        print(f"  Node counts: {node_types}")
        
        # Import edges
        edges = graph_data.get('edges', [])
        print(f"Importing {len(edges)} edges...")
        
        edge_types = {}
        for edge in edges:
            try:
                cypher, params, edge_type = edge_to_cypher(edge)
                connector.query(cypher, params)
                stats['edges_imported'] += 1
                edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
            except Exception as e:
                stats['errors'].append(f"Edge {edge.get('source')}->{edge.get('target')}: {e}")
        
        print(f"  Edge counts: {edge_types}")
        
    finally:
        connector.close()
    
    return stats


def test_with_sample_data():
    """
    Test Neo4j import with sample XKG data.
    
    Creates a small graph with:
    - 3 Grok posts
    - 2 Action items
    - 1 Topic
    - Relationships between them
    """
    sample_data = {
        "nodes": [
            {
                "id": "grok_001",
                "type": "grok",
                "label": "New feature shipped",
                "text": "Just shipped the new feature to production. Need to monitor error logs.",
                "topic": "general",
                "source": "grok",
                "created_at": "2024-01-15T08:00:00Z",
                "author_id": "user_001"
            },
            {
                "id": "grok_002",
                "type": "grok",
                "label": "API documentation",
                "text": "TODO: Update API documentation for new endpoints with code examples.",
                "topic": "general",
                "source": "grok",
                "created_at": "2024-01-15T11:30:00Z",
                "author_id": "user_001"
            },
            {
                "id": "grok_003",
                "type": "grok",
                "label": "1:1 scheduled",
                "text": "Going to schedule 1:1 with team lead to discuss Q2 priorities.",
                "topic": "general",
                "source": "grok",
                "created_at": "2024-01-16T09:30:00Z",
                "author_id": "user_001"
            },
            {
                "id": "action_001",
                "type": "action",
                "label": "Monitor error logs",
                "text": "Need to monitor the error logs tomorrow morning.",
                "topic": "monitoring",
                "source": "grok_001",
                "priority": "high",
                "status": "pending",
                "extracted_at": "2024-01-15T08:05:00Z"
            },
            {
                "id": "action_002",
                "type": "action",
                "label": "Update API docs",
                "text": "Update API documentation with code examples.",
                "topic": "documentation",
                "source": "grok_002",
                "priority": "medium",
                "status": "pending",
                "extracted_at": "2024-01-15T11:35:00Z"
            },
            {
                "id": "topic_monitoring",
                "type": "topic",
                "label": "Monitoring",
                "text": "Monitoring",
                "topic": "monitoring",
                "source": "system",
                "created_at": "2024-01-15T08:00:00Z"
            },
            {
                "id": "topic_documentation",
                "type": "topic",
                "label": "Documentation",
                "text": "Documentation",
                "topic": "documentation",
                "source": "system",
                "created_at": "2024-01-15T11:30:00Z"
            }
        ],
        "edges": [
            {
                "source": "grok_001",
                "target": "action_001",
                "type": "extracts",
                "created_at": "2024-01-15T08:05:00Z"
            },
            {
                "source": "grok_002",
                "target": "action_002",
                "type": "extracts",
                "created_at": "2024-01-15T11:35:00Z"
            },
            {
                "source": "action_001",
                "target": "topic_monitoring",
                "type": "belongs_to",
                "created_at": "2024-01-15T08:05:00Z"
            },
            {
                "source": "action_002",
                "target": "topic_documentation",
                "type": "belongs_to",
                "created_at": "2024-01-15T11:35:00Z"
            }
        ]
    }
    
    print("\n=== Neo4j Import Test ===\n")
    
    # Try to import (will fail gracefully if Neo4j not available)
    stats = import_to_neo4j(sample_data)
    
    if stats['success']:
        print(f"\n✓ Import successful!")
        print(f"  Nodes imported: {stats['nodes_imported']}")
        print(f"  Edges imported: {stats['edges_imported']}")
        if stats['errors']:
            print(f"  Errors: {len(stats['errors'])}")
    else:
        print(f"\n✗ Import failed: {stats.get('error', 'Unknown error')}")
    
    return stats


def demo_queries(connector: Neo4jConnector):
    """
    Demonstrate common Neo4j queries for XKG data.
    """
    print("\n=== Demo Queries ===\n")
    
    queries = [
        # Get all actions
        ("All Actions", "MATCH (a:Action) RETURN a.id, a.text, a.priority, a.status"),
        
        # Get high priority actions
        ("High Priority Actions", "MATCH (a:Action {priority: 'high'}) RETURN a.text, a.topic"),
        
        # Get actions by topic
        ("Actions per Topic", """
            MATCH (a:Action)-[:BELONGS_TO]->(t:Topic)
            RETURN t.topic, collect(a.text) as actions, count(a) as count
        """),
        
        # Trace action to source
        ("Action Source Tracing", """
            MATCH (g:Grok)-[:EXTRACTS]->(a:Action)
            WHERE a.id = 'action_001'
            RETURN g.text, a.text
        """),
        
        # Count actions by priority
        ("Priority Distribution", """
            MATCH (a:Action)
            RETURN a.priority, count(a) as count
            ORDER BY count DESC
        """)
    ]
    
    for name, query in queries:
        print(f"--- {name} ---")
        try:
            results = connector.query(query.strip())
            for r in results[:5]:  # Limit output
                print(f"  {r}")
            if len(results) > 5:
                print(f"  ... and {len(results) - 5} more")
        except Exception as e:
            print(f"  Error: {e}")
        print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='XKG Neo4j Import Tool')
    parser.add_argument('--uri', default='bolt://localhost:7687', help='Neo4j URI')
    parser.add_argument('--user', default='neo4j', help='Neo4j user')
    parser.add_argument('--password', default='neo4j_password', help='Neo4j password')
    parser.add_argument('--file', '-f', help='Import from JSON file')
    parser.add_argument('--test', action='store_true', help='Run sample data test')
    parser.add_argument('--demo', action='store_true', help='Run demo queries')
    
    args = parser.parse_args()
    
    if args.test:
        test_with_sample_data()
    elif args.file:
        with open(args.file) as f:
            data = json.load(f)
        config = Neo4jConfig(uri=args.uri, user=args.user, password=args.password)
        stats = import_to_neo4j(data, config=config)
        print(f"\nImport stats: {stats}")
    elif args.demo:
        config = Neo4jConfig(uri=args.uri, user=args.user, password=args.password)
        connector = Neo4jConnector(config)
        if connector.connect():
            demo_queries(connector)
            connector.close()
    else:
        # Default: show help
        parser.print_help()
        print("\nAlso running sample data test...")
        test_with_sample_data()
