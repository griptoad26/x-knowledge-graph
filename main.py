#!/usr/bin/env python3
"""
X Knowledge Graph v0.4.19 - Self-Contained Standalone Application
Features: Graph visualization, action extraction, task flows, Todoist export, Dark Mode
"""

import sys
import os
import webbrowser
import socket
import threading
import argparse

# Determine base directory for bundled app
if getattr(sys, 'frozen', False):
    # Running as frozen exe - files extracted to temp directory
    BASE_DIR = sys._MEIPASS
    os.chdir(BASE_DIR)
else:
    # Running as Python script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    os.chdir(BASE_DIR)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'frontend'),
            static_folder=os.path.join(BASE_DIR, 'frontend'))
CORS(app)

# ==================== CLI ARGUMENT PARSING ====================

def parse_cli_args():
    parser = argparse.ArgumentParser(
        description='X Knowledge Graph - Parse X exports and visualize',
        add_help=False
    )
    parser.add_argument('--export-todoist', metavar='TOKEN', help='Export actions to Todoist')
    parser.add_argument('--export-actions', metavar='FILE', help='Export actions to JSON file')
    parser.add_argument('--export-graph', metavar='FILE', help='Export graph to JSON file')
    return parser.parse_known_args()

CLI_ARGS, _ = parse_cli_args()
graph_data = {'graph': {}, 'actions': [], 'topics': {}, 'flows': {}}

# ==================== FOLDER PICKER ====================

selected_folder_path = None
folder_selected_event = threading.Event()

def native_folder_picker():
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

# ==================== FLASK ROUTES ====================

@app.route('/')
def index():
    index_path = os.path.join(BASE_DIR, 'frontend', 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "ERROR: index.html not found in " + BASE_DIR, 500

@app.route('/<path:filename>')
def static_files(filename):
    # Serve static files from frontend directory
    allowed_dirs = ['frontend', 'css', 'js']
    
    # Prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return "Forbidden", 403
    
    file_path = os.path.join(BASE_DIR, 'frontend', filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(os.path.join(BASE_DIR, 'frontend'), filename)
    
    return f"NOT FOUND: {filename}", 404

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'version': '0.4.19'})

@app.route('/api/select-folder', methods=['POST'])
def select_folder():
    global selected_folder_path, folder_selected_event
    folder_selected_event.clear()
    selected_folder_path = None
    t = threading.Thread(target=native_folder_picker)
    t.daemon = True
    t.start()
    return jsonify({'status': 'started', 'message': 'Folder picker opened'})

@app.route('/api/get-selected-folder', methods=['GET'])
def get_selected_folder():
    global selected_folder_path, folder_selected_event
    if folder_selected_event.is_set():
        return jsonify({'status': 'done', 'path': selected_folder_path if selected_folder_path else None})
    return jsonify({'status': 'waiting'})

@app.route('/api/parse-export', methods=['POST'])
def parse_export():
    global graph_data
    
    data = request.json or {}
    x_path = data.get('x_path', '').strip()
    grok_path = data.get('grok_path', '').strip()
    export_type = data.get('export_type', 'x')
    graph_mode = data.get('graph_mode', 'all')
    
    if x_path and not os.path.exists(x_path):
        return jsonify({'error': 'X folder not found: ' + x_path}), 400
    if grok_path and not os.path.exists(grok_path):
        return jsonify({'error': 'Grok folder not found: ' + grok_path}), 400
    if not x_path and not grok_path:
        return jsonify({'error': 'Please select a folder first'}), 400
    
    try:
        core_path = os.path.join(BASE_DIR, 'core', 'xkg_core.py')
        if not os.path.exists(core_path):
            return jsonify({'error': 'core/xkg_core.py not found'}), 500
        
        core_dir = os.path.dirname(core_path)
        if core_dir not in sys.path:
            sys.path.insert(0, core_dir)
        
        from xkg_core import KnowledgeGraph
        
        kg = KnowledgeGraph()
        
        if export_type == 'both' and x_path and grok_path:
            result = kg.build_from_both(x_path, grok_path)
        elif export_type == 'grok' and grok_path:
            result = kg.build_from_grok(grok_path)
        elif x_path:
            result = kg.build_from_export(x_path, 'x')
        elif grok_path:
            result = kg.build_from_export(grok_path, 'grok')
        else:
            return jsonify({'error': 'No valid export path provided'}), 400
        
        if 'error' in result:
            return jsonify(result), 400
        
        all_nodes = kg.export_for_d3().get('nodes', [])
        all_edges = kg.export_for_d3().get('edges', [])
        
        if graph_mode == 'twitter':
            nodes = [n for n in all_nodes if n.get('type') in ['tweet', 'action', 'topic']]
        elif graph_mode == 'grok':
            nodes = [n for n in all_nodes if n.get('type') in ['grok', 'action', 'topic']]
        else:
            nodes = all_nodes
        
        node_ids = set(n.get('id') for n in nodes)
        edges = [e for e in all_edges if e.get('source') in node_ids and e.get('target') in node_ids]
        
        graph_export = {'nodes': nodes, 'edges': edges}
        
        graph_data = {
            'actions': result.get('actions', []),
            'topics': result.get('topics', {}),
            'flows': result.get('flows', {}),
            'graph': graph_export
        }
        
        return jsonify({
            'stats': result['stats'],
            'graph': graph_export,
            'actions': graph_data['actions'],
            'topics': graph_data['topics'],
            'flows': graph_data['flows']
        })
        
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

@app.route('/api/flows')
def get_flows():
    return jsonify(graph_data.get('flows', {}))

@app.route('/api/export-todoist', methods=['POST'])
def export_todoist():
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

# ==================== MAIN ====================

def main():
    port = find_port()
    
    print("=" * 50)
    print("X Knowledge Graph v0.4.19")
    print("=" * 50)
    print(f"Server at: http://localhost:{port}")
    print(f"Base dir: {BASE_DIR}")
    print("\nOpening browser...")
    
    webbrowser.open(f'http://localhost:{port}')
    
    try:
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
