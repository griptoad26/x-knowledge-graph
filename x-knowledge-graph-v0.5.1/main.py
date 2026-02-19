#!/usr/bin/env python3
"""
X Knowledge Graph v0.5.1 - Self-Contained Standalone Application
Features: Graph visualization, action extraction, task flows, Todoist export
"""

import sys
import os
import webbrowser
import socket
import threading
import argparse
from datetime import datetime
import base64

# Determine base directory for bundled resources
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # PyInstaller --onefile mode: files extracted to temp directory (_MEIPASS)
    BASE_DIR = sys._MEIPASS
elif getattr(sys, 'frozen', False):
    # PyInstaller --onedir mode: files are alongside the exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running from source
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add core folder to path for imports
CORE_DIR = os.path.join(BASE_DIR, 'core')
if CORE_DIR not in sys.path:
    sys.path.insert(0, CORE_DIR)

os.chdir(BASE_DIR)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Debug: print paths when running
print(f"BASE_DIR: {BASE_DIR}")
print(f"sys.executable: {sys.executable}")
print(f"Frontend exists: {os.path.exists(os.path.join(BASE_DIR, 'frontend', 'index.html'))}")

# ==================== CLI ARGUMENT PARSING ====================

def parse_cli_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='X Knowledge Graph - Parse X exports and visualize',
        add_help=False
    )
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='Port to run on (default: auto-select)'
    )
    parser.add_argument(
        '--export-todoist',
        metavar='TOKEN',
        help='Export actions to Todoist using the provided API token'
    )
    parser.add_argument(
        '--export-actions',
        metavar='FILE',
        help='Export actions to JSON file'
    )
    parser.add_argument(
        '--export-graph',
        metavar='FILE',
        help='Export graph to JSON file'
    )
    return parser.parse_known_args()

CLI_ARGS, _ = parse_cli_args()

graph_data = {'graph': {}, 'actions': [], 'topics': {}, 'flows': {}}

# Analytics data storage
analytics_data = {}

# Load analytics module
try:
    from core.analytics import AnalyticsEngine
    analytics_engine = AnalyticsEngine()
    HAS_ANALYTICS = True
except ImportError as e:
    print(f"Analytics module not available: {e}")
    HAS_ANALYTICS = False
    analytics_engine = None

# Search engine instance
search_engine = None

def get_search_engine():
    """Get or initialize the search engine"""
    global search_engine
    if search_engine is None:
        try:
            from core.semantic_search import SemanticSearchEngine
            search_engine = SemanticSearchEngine()
        except Exception as e:
            print(f"Warning: Could not initialize search engine: {e}")
            search_engine = None
    return search_engine

# Native folder picker state
selected_folder_path = None
folder_selected_event = threading.Event()

def native_folder_picker():
    """Thread-safe native folder picker using tkinter"""
    import tkinter as tk
    from tkinter import filedialog
    
    global selected_folder_path
    selected_folder_path = None
    
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    folder = filedialog.askdirectory(
        title='Select Export Folder',
        initialdir=os.path.expanduser('~')
    )
    
    if folder:
        selected_folder_path = folder
    
    folder_selected_event.set()
    root.destroy()

def find_port():
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def find_file_in_bundle(filename, subdirs=['frontend', 'core', '.']):
    for subdir in subdirs:
        path = os.path.join(BASE_DIR, subdir, filename)
        if os.path.exists(path):
            return path
    return None

@app.route('/')
def index():
    # Try multiple locations for index.html
    index_locations = [
        os.path.join(BASE_DIR, 'frontend', 'index.html'),
        os.path.join(BASE_DIR, 'index.html'),
    ]
    for index_path in index_locations:
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                return f.read()
    # Return helpful error
    return f"""<!DOCTYPE html>
<html><head><title>Error</title></head><<body>
<h1>index.html not found</h1>
<p>BASE_DIR: {BASE_DIR}</p>
<p>Frontend exists: {os.path.exists(os.path.join(BASE_DIR, 'frontend'))}</p>
</body></html>""", 500

@app.route('/<path:filename>')
def static_files(filename):
    # Try frontend folder first, then root
    path = os.path.join(BASE_DIR, 'frontend', filename)
    if os.path.exists(path):
        return send_from_directory(os.path.join(BASE_DIR, 'frontend'), filename)
    # Try root folder
    path = os.path.join(BASE_DIR, filename)
    if os.path.exists(path):
        return send_from_directory(BASE_DIR, filename)
    return f"NOT FOUND: {filename}", 404

@app.route('/api/health')
def health():
    # Read version from VERSION.txt file
    version_file = os.path.join(BASE_DIR, 'VERSION.txt')
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            version = f.read().strip()
    else:
        version = 'unknown'
    return jsonify({'status': 'ok', 'version': version})

@app.route('/api/select-folder', methods=['POST'])
def select_folder():
    """Trigger native folder picker dialog"""
    global selected_folder_path, folder_selected_event
    
    folder_selected_event.clear()
    selected_folder_path = None
    
    t = threading.Thread(target=native_folder_picker)
    t.daemon = True
    t.start()
    
    return jsonify({'status': 'started', 'message': 'Folder picker opened'})

@app.route('/api/get-selected-folder', methods=['GET'])
def get_selected_folder():
    """Check if folder has been selected"""
    global selected_folder_path, folder_selected_event
    
    if folder_selected_event.is_set():
        return jsonify({
            'status': 'done',
            'path': selected_folder_path if selected_folder_path else None
        })
    else:
        return jsonify({'status': 'waiting'})

@app.route('/api/parse-export', methods=['POST'])
def parse_export():
    global graph_data
    
    # Check content type
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    x_path = data.get('x_path', '').strip()
    grok_path = data.get('grok_path', '').strip()
    ai_path = data.get('ai_path', '').strip()  # New AI export path
    export_type = data.get('export_type', 'x')  # 'x', 'grok', 'ai', or 'both'
    graph_mode = data.get('graph_mode', 'all')
    
    if x_path and not os.path.exists(x_path):
        return jsonify({'error': 'X folder not found: ' + x_path}), 400
    if grok_path and not os.path.exists(grok_path):
        return jsonify({'error': 'Grok folder not found: ' + grok_path}), 400
    if ai_path and not os.path.exists(ai_path):
        return jsonify({'error': 'AI export folder not found: ' + ai_path}), 400
    if not x_path and not grok_path and not ai_path:
        return jsonify({'error': 'Please select a folder first'}), 400
    
    try:
        core_path = find_file_in_bundle('xkg_core.py', ['core'])
        if not core_path or not os.path.exists(core_path):
            return jsonify({'error': 'core/xkg_core.py not found'}), 500
        
        core_dir = os.path.dirname(core_path)
        if core_dir not in sys.path:
            sys.path.insert(0, core_dir)
        
        from xkg_core import KnowledgeGraph
        
        kg = KnowledgeGraph()
        
        # Parse based on export type
        if export_type == 'ai' and ai_path:
            result = kg.build_from_export(ai_path, 'ai')
        elif export_type == 'both' and x_path and grok_path:
            result = kg.build_from_both(x_path, grok_path)
        elif export_type == 'grok' and grok_path:
            result = kg.build_from_export(grok_path, 'grok')
        elif x_path:
            result = kg.build_from_export(x_path, 'x')
        elif grok_path:
            result = kg.build_from_export(grok_path, 'grok')
        else:
            return jsonify({'error': 'No valid export path provided'}), 400
        
        if 'error' in result:
            return jsonify(result), 400
        
        tweets_count = result['stats'].get('total_tweets', 0)
        topics_count = result['stats'].get('topics_count', 0)
        actions_count = result['stats'].get('total_actions', 0)
        
        all_nodes = kg.export_for_d3().get('nodes', [])
        all_edges = kg.export_for_d3().get('edges', [])
        
        # Filter nodes based on graph mode
        if graph_mode == 'twitter':
            nodes = [n for n in all_nodes if n.get('type') in ['tweet', 'action', 'topic']]
        elif graph_mode == 'grok':
            nodes = [n for n in all_nodes if n.get('type') in ['grok', 'action', 'topic']]
        elif graph_mode == 'ai':
            nodes = [n for n in all_nodes if n.get('type') in ['message', 'action', 'topic', 'conversation']]
        else:
            nodes = all_nodes
        
        node_ids = set(n.get('id') for n in nodes)
        edges = [e for e in all_edges if e.get('source') in node_ids and e.get('target') in node_ids]
        
        graph_export = {'nodes': nodes, 'edges': edges}
        
        graph_data = {
            'actions': result.get('actions', []),
            'topics': result.get('topics', {}),
            'grok_topics': result.get('grok_topics', {}),
            'ai_topics': result.get('ai_topics', {}),
            'grok_conversations': result.get('grok_conversations', []),
            'ai_conversations': result.get('ai_conversations', []),
            'flows': result.get('flows', {}),
            'graph': graph_export
        }

        # Auto-index data for search
        search_indexed = None
        try:
            engine = get_search_engine()
            if engine:
                from core.semantic_search import index_knowledge_graph
                from core.xkg_core import KnowledgeGraph

                # Build a temporary KnowledgeGraph from parsed data
                kg = KnowledgeGraph()
                kg.actions = [
                    type('Action', (), {'id': a.get('id', ''), 'text': a.get('text', ''),
                                       'source_id': a.get('source_id', ''), 'source_type': a.get('source_type', 'tweet'),
                                       'topic': a.get('topic', 'general'), 'priority': a.get('priority', 'medium'),
                                       'status': a.get('status', 'pending'), 'amazon_link': a.get('amazon_link')})()
                    for a in result.get('actions', [])
                ]
                # Index the data
                search_indexed = index_knowledge_graph(kg, engine)
        except Exception as index_err:
            print(f"Warning: Could not auto-index for search: {index_err}")

        response = {
            'status': 'success',
            'stats': result['stats'],
            'graph': graph_export,
            'actions': graph_data['actions'],
            'topics': graph_data['topics'],
            'grok_topics': graph_data['grok_topics'],
            'ai_topics': graph_data['ai_topics'],
            'grok_conversations': graph_data['grok_conversations'],
            'ai_conversations': graph_data['ai_conversations'],
            'flows': graph_data['flows']
        }

        if search_indexed:
            response['search_indexed'] = search_indexed

        return jsonify(response)
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/graph')
def get_graph():
    return jsonify(graph_data.get('graph', {'nodes': [], 'edges': []}))

@app.route('/api/actions')
def get_actions():
    return jsonify(graph_data.get('actions', []))

@app.route('/api/topics')
def get_topics():
    return jsonify(graph_data.get('topics', {}))

@app.route('/api/grok-topics')
def get_grok_topics():
    return jsonify(graph_data.get('grok_topics', {}))

@app.route('/api/grok-conversations')
def get_grok_conversations():
    return jsonify(graph_data.get('grok_conversations', []))

@app.route('/api/flows')
def get_flows():
    return jsonify(graph_data.get('flows', {}))

@app.route('/api/export-todoist', methods=['POST'])
def export_todoist():
    """Export actions to Todoist"""
    global graph_data

    data = request.json or {}
    api_token = data.get('api_token') or CLI_ARGS.export_todoist

    if not api_token:
        return jsonify({'error': 'No API token provided'}), 400

    actions = graph_data.get('actions', [])

    if not actions:
        return jsonify({'error': 'No actions to export'}), 400

    try:
        from core.todoist_exporter import TodoistExporter

        exporter = TodoistExporter(api_token=api_token)
        result = exporter.export_actions(actions)

        return jsonify({
            'success': True,
            'exported': result['success_count'],
            'failed': result['failed_count'],
            'task_ids': result.get('task_ids', []),
            'errors': result.get('errors', [])
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# ==================== ANALYTICS API ====================

@app.route('/api/analytics/stats', methods=['GET'])
def analytics_stats():
    """Get all analytics statistics as JSON"""
    global graph_data, analytics_engine, HAS_ANALYTICS
    
    if not HAS_ANALYTICS or analytics_engine is None:
        return jsonify({'error': 'Analytics module not available'}), 503
    
    try:
        # Update analytics engine with current data
        analytics_engine.set_data(graph_data)
        
        stats = analytics_engine.get_stats()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'generated_at': datetime.now().isoformat()
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/analytics/chart/<chart_type>', methods=['GET'])
def analytics_chart(chart_type):
    """Generate and return a specific chart as PNG"""
    global graph_data, analytics_engine, HAS_ANALYTICS
    
    valid_types = ['activity', 'topics', 'actions', 'sources', 'keywords', 'engagement']
    
    if chart_type not in valid_types:
        return jsonify({'error': f'Invalid chart type. Use: {", ".join(valid_types)}'}), 400
    
    if not HAS_ANALYTICS or analytics_engine is None:
        return jsonify({'error': 'Analytics module not available'}), 503
    
    try:
        # Update analytics engine with current data
        analytics_engine.set_data(graph_data)
        
        # Generate chart
        chart_methods = {
            'activity': analytics_engine.generate_activity_chart,
            'topics': analytics_engine.generate_topic_chart,
            'actions': analytics_engine.generate_action_completion_chart,
            'sources': analytics_engine.generate_source_breakdown_chart,
            'keywords': analytics_engine.generate_keywords_chart,
            'engagement': analytics_engine.generate_engagement_chart
        }
        
        chart_data = chart_methods[chart_type]()
        
        # Return as base64 image
        from flask import Response
        
        # Extract base64 data URL
        if chart_data.startswith('data:image/png;base64,'):
            base64_data = chart_data.split(',', 1)[1]
        else:
            base64_data = chart_data
        
        return Response(
            base64.b64decode(base64_data),
            mimetype='image/png',
            headers={
                'Content-Disposition': f'inline; filename={chart_type}.png',
                'Cache-Control': 'no-cache'
            }
        )
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/analytics/refresh', methods=['POST'])
def analytics_refresh():
    """Refresh analytics with current data"""
    global graph_data, analytics_engine, HAS_ANALYTICS
    
    if not HAS_ANALYTICS or analytics_engine is None:
        return jsonify({'error': 'Analytics module not available'}), 503
    
    try:
        # Update analytics engine with current data
        analytics_engine.set_data(graph_data)
        
        # Generate all charts
        import tempfile
        import os
        
        charts_dir = tempfile.mkdtemp()
        results = analytics_engine.generate_all_charts(charts_dir)
        
        charts = {}
        for filename, result in results.items():
            if result['status'] == 'success':
                with open(result['path'], 'rb') as f:
                    import base64
                    charts[filename.replace('.png', '')] = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
        
        # Clean up temp files
        import shutil
        shutil.rmtree(charts_dir, ignore_errors=True)
        
        return jsonify({
            'success': True,
            'charts': charts,
            'stats': analytics_engine.get_stats(),
            'generated_at': datetime.now().isoformat()
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# ==================== SEARCH API ====================

@app.route('/api/search', methods=['POST'])
def search():
    """
    Unified search endpoint for keyword and semantic search.
    
    Request body:
    {
        "query": "search term",
        "type": "keyword|semantic|hybrid",
        "item_types": ["tweet", "grok", "action", "conversation", "ai_conversation"],
        "sources": ["x", "grok", "ai"],
        "limit": 20
    }
    """
    global graph_data
    
    data = request.json or {}
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    search_type = data.get('type', 'keyword')
    item_types = data.get('item_types', None)
    sources = data.get('sources', None)
    limit = min(int(data.get('limit', 20)), 100)
    
    # Validate search type
    if search_type not in ['keyword', 'semantic', 'hybrid']:
        return jsonify({'error': 'Invalid search type. Use: keyword, semantic, or hybrid'}), 400
    
    try:
        engine = get_search_engine()
        
        if engine is None:
            return jsonify({
                'error': 'Search engine not available',
                'hint': 'Install sentence-transformers for semantic search'
            }), 503
        
        results = engine.unified_search(
            query=query,
            search_type=search_type,
            item_types=item_types,
            sources=sources,
            limit=limit
        )
        
        return jsonify({
            'query': query,
            'search_type': search_type,
            'total_results': len(results),
            'results': [r.to_dict() for r in results]
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/search/index', methods=['POST'])
def index_for_search():
    """
    Index the current graph data for search.
    Called automatically after loading data.
    """
    global graph_data
    
    try:
        engine = get_search_engine()
        
        if engine is None:
            return jsonify({
                'error': 'Search engine not available',
                'hint': 'Install sentence-transformers for semantic search'
            }), 503
        
        from core.xkg_core import KnowledgeGraph
        
        # Build a temporary KnowledgeGraph from current data
        kg = KnowledgeGraph()
        
        # Index actions
        actions = graph_data.get('actions', [])
        if actions:
            from core.xkg_core import ActionItem
            for action_data in actions:
                kg.actions.append(ActionItem(
                    id=action_data.get('id', ''),
                    text=action_data.get('text', ''),
                    source_id=action_data.get('source_id', ''),
                    source_type=action_data.get('source_type', 'tweet'),
                    topic=action_data.get('topic', 'general'),
                    priority=action_data.get('priority', 'medium'),
                    status=action_data.get('status', 'pending'),
                    amazon_link=action_data.get('amazon_link')
                ))
        
        # Import and use the indexer
        from core.semantic_search import index_knowledge_graph
        
        indexed = index_knowledge_graph(kg, engine)
        
        return jsonify({
            'success': True,
            'indexed': indexed
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/search/stats', methods=['GET'])
def search_stats():
    """Get search index statistics"""
    try:
        engine = get_search_engine()
        
        if engine is None:
            return jsonify({
                'search_available': False,
                'error': 'Search engine not initialized'
            })
        
        stats = engine.get_index_stats()
        stats['search_available'] = True
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/clear', methods=['POST'])
def clear_search_index():
    """Clear the search index"""
    try:
        engine = get_search_engine()
        
        if engine is None:
            return jsonify({'error': 'Search engine not available'}), 503
        
        data = request.json or {}
        source = data.get('source', None)
        
        engine.clear_index(source=source)
        
        return jsonify({
            'success': True,
            'message': f'Search index cleared{" for source: " + source if source else " (all data)"}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-pkm', methods=['POST'])
def export_pkm():
    """Export knowledge graph to PKM format (Obsidian/Logseq compatible)"""
    global graph_data
    
    data = request.json or {}
    export_format = data.get('format', 'obsidian')  # 'obsidian', 'logseq', or 'markdown'
    
    # Validate format
    if export_format not in ['obsidian', 'logseq', 'markdown']:
        return jsonify({'error': 'Invalid format. Use: obsidian, logseq, or markdown'}), 400
    
    # Check if there's data to export
    has_data = (
        graph_data.get('graph', {}).get('nodes') or
        graph_data.get('actions') or
        graph_data.get('topics') or
        graph_data.get('grok_conversations') or
        graph_data.get('ai_conversations')
    )
    
    if not has_data:
        return jsonify({'error': 'No data to export. Load data first.'}), 400
    
    try:
        from core.pkm_exporter import PKMExporter
        
        exporter = PKMExporter()
        zip_data = exporter.export(graph_data, format=export_format)
        
        from flask import Response
        
        return Response(
            zip_data,
            mimetype='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename=xkg-export-{export_format}.zip',
                'Content-Type': 'application/zip'
            }
        )
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# ==================== PKM IMPORT API ====================

@app.route('/api/import-notion', methods=['POST'])
def import_notion():
    """Import from Notion export folder"""
    global graph_data
    
    data = request.json or {}
    export_path = data.get('path', '').strip()
    
    if not export_path:
        return jsonify({'error': 'Path is required'}), 400
    
    if not os.path.exists(export_path):
        return jsonify({'error': 'Path not found: ' + export_path}), 400
    
    try:
        from core.pkm_importers import PKMImporter
        
        importer = PKMImporter()
        result = importer.import_notion(export_path)
        
        if result.success:
            # Merge into existing graph data
            importer = PKMImporter()
            nodes, edges = importer.merge_into_graph(
                graph_data.get('graph', {}).get('nodes', []),
                graph_data.get('graph', {}).get('edges', []),
                result
            )
            
            # Update graph data
            graph_data['graph'] = {'nodes': nodes, 'edges': edges}
            
            return jsonify({
                'success': True,
                'message': f'Imported {len(result.nodes)} nodes from Notion',
                'stats': result.stats,
                'nodes': result.nodes,
                'edges': result.edges
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Import failed',
                'errors': result.errors
            }), 400
            
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/import-evernote', methods=['POST'])
def import_evernote():
    """Import from Evernote ENEX file"""
    global graph_data
    
    data = request.json or {}
    enex_path = data.get('path', '').strip()
    
    if not enex_path:
        return jsonify({'error': 'Path is required'}), 400
    
    if not os.path.exists(enex_path):
        return jsonify({'error': 'File not found: ' + enex_path}), 400
    
    if not enex_path.lower().endswith('.enex'):
        return jsonify({'error': 'File must have .enex extension'}), 400
    
    try:
        from core.pkm_importers import PKMImporter
        
        importer = PKMImporter()
        result = importer.import_evernote(enex_path)
        
        if result.success:
            # Merge into existing graph data
            importer = PKMImporter()
            nodes, edges = importer.merge_into_graph(
                graph_data.get('graph', {}).get('nodes', []),
                graph_data.get('graph', {}).get('edges', []),
                result
            )
            
            # Update graph data
            graph_data['graph'] = {'nodes': nodes, 'edges': edges}
            
            return jsonify({
                'success': True,
                'message': f'Imported {len(result.nodes)} nodes from Evernote',
                'stats': result.stats,
                'nodes': result.nodes,
                'edges': result.edges
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Import failed',
                'errors': result.errors
            }), 400
            
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/import-markdown', methods=['POST'])
def import_markdown():
    """Import from markdown folder"""
    global graph_data
    
    data = request.json or {}
    folder_path = data.get('path', '').strip()
    
    if not folder_path:
        return jsonify({'error': 'Path is required'}), 400
    
    if not os.path.exists(folder_path):
        return jsonify({'error': 'Path not found: ' + folder_path}), 400
    
    if not os.path.isdir(folder_path):
        return jsonify({'error': 'Path must be a folder'}), 400
    
    try:
        from core.pkm_importers import PKMImporter
        
        importer = PKMImporter()
        result = importer.import_markdown_folder(folder_path)
        
        if result.success:
            # Merge into existing graph data
            importer = PKMImporter()
            nodes, edges = importer.merge_into_graph(
                graph_data.get('graph', {}).get('nodes', []),
                graph_data.get('graph', {}).get('edges', []),
                result
            )
            
            # Update graph data
            graph_data['graph'] = {'nodes': nodes, 'edges': edges}
            
            return jsonify({
                'success': True,
                'message': f'Imported {len(result.nodes)} nodes from markdown folder',
                'stats': result.stats,
                'nodes': result.nodes,
                'edges': result.edges
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Import failed',
                'errors': result.errors
            }), 400
            
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

def main():
    # Use CLI port if provided, otherwise auto-select
    if CLI_ARGS.port:
        port = CLI_ARGS.port
    else:
        port = find_port()
    
    # Read version from VERSION.txt
    version_file = os.path.join(BASE_DIR, 'VERSION.txt')
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            version = f.read().strip()
    else:
        version = 'unknown'
    
    print("=" * 50)
    print(f"X Knowledge Graph {version}")
    print("=" * 50)
    print(f"Server at: http://localhost:{port}")
    
    # Auto-export to Todoist if token provided via CLI
    if CLI_ARGS.export_todoist:
        print(f"\nTodoist token provided via CLI")
        print("Note: Export will be available via API after parsing actions")
    
    # Only open browser if not running in headless mode
    if not os.environ.get("HEADLESS", ""):
        print("\nOpening browser...")
        webbrowser.open(f'http://localhost:{port}')
    else:
        print("\nRunning in headless mode (no browser)")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
