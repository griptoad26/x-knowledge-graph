#!/usr/bin/env python3
"""
xkg_mvp - Grok Content Converter v0.0.1
Convert Grok conversations to Reddit-style searchable content
"""

import os
import json
import argparse
from flask import Flask, request, jsonify, send_from_directory
from core.grok_parser import GrokParser
from core.converter import RedditConverter

app = Flask(__name__, static_folder='frontend', static_url_path='')

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize components
grok_parser = GrokParser()
converter = RedditConverter()


@app.route('/')
def index():
    """Serve main HTML interface"""
    return send_from_directory('frontend', 'index.html')


@app.route('/api/import', methods=['POST'])
def import_grok():
    """Import and parse Grok JSON file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    try:
        data = json.load(file)
        conversations = grok_parser.parse(data)
        return jsonify({
            'status': 'success',
            'conversations': conversations,
            'count': len(conversations)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/conversation/<conversation_id>')
def get_conversation(conversation_id):
    """Get specific conversation"""
    try:
        conv = grok_parser.get_conversation(conversation_id)
        if conv:
            return jsonify({'status': 'success', 'conversation': conv})
        return jsonify({'error': 'Not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/search')
def search():
    """Search conversations"""
    query = request.args.get('q', '')
    results = grok_parser.search(query)
    return jsonify({'status': 'success', 'results': results})


@app.route('/api/export/markdown/<conversation_id>')
def export_markdown(conversation_id):
    """Export conversation as Markdown"""
    try:
        conv = grok_parser.get_conversation(conversation_id)
        if not conv:
            return jsonify({'error': 'Not found'}), 404
        
        markdown = converter.to_markdown(conv)
        return jsonify({
            'status': 'success',
            'markdown': markdown,
            'filename': f'grok_{conversation_id}.md'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/export/json/<conversation_id>')
def export_json(conversation_id):
    """Export conversation as JSON"""
    try:
        conv = grok_parser.get_conversation(conversation_id)
        if not conv:
            return jsonify({'error': 'Not found'}), 404
        
        return jsonify({
            'status': 'success',
            'conversation': conv
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'version': 'v0.0.1',
        'name': 'xkg_mvp'
    })


def main():
    parser = argparse.ArgumentParser(description='xkg_mvp - Grok Content Converter')
    parser.add_argument('--port', type=int, default=51339, help='Port to run on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    args = parser.parse_args()
    
    print(f"========================================")
    print(f"  xkg_mvp v0.0.1 - Grok Content Converter")
    print(f"========================================")
    print(f"Server at: http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == '__main__':
    main()
