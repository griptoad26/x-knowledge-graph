#!/usr/bin/env python3
"""
xkg_mvp - Grok/X Content Converter v0.0.2
Convert Grok/X conversations to Reddit-style searchable content
Supports folders, individual files, and bookmarked tweets
"""

import os
import json
import glob
import argparse
from flask import Flask, request, jsonify, send_from_directory
from core.grok_parser import GrokParser
from core.converter import RedditConverter
from core.x_parser import XParser

app = Flask(__name__, static_folder='frontend', static_url_path='')

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Version
VERSION_FILE = os.path.join(os.path.dirname(__file__), 'VERSION.txt')
if os.path.exists(VERSION_FILE):
    VERSION = open(VERSION_FILE).read().strip()
else:
    VERSION = 'v0.0.2'

# Initialize components
grok_parser = GrokParser()
x_parser = XParser()
converter = RedditConverter()


@app.route('/')
def index():
    """Serve main HTML interface"""
    return send_from_directory('frontend', 'index.html')


@app.route('/api/import', methods=['POST'])
def import_data():
    """Import and parse data file(s) or folder"""
    if 'file' not in request.files and 'folder' not in request.form:
        return jsonify({'error': 'No file or folder specified'}), 400
    
    all_conversations = []
    imported_files = []
    
    # Handle folder import
    if 'folder' in request.form:
        folder_path = request.form['folder']
        folder_type = request.form.get('type', 'auto')  # grok, x, auto
        
        if not os.path.exists(folder_path):
            return jsonify({'error': f'Folder not found: {folder_path}'}), 400
        
        conversations, files = _import_folder(folder_path, folder_type)
        all_conversations.extend(conversations)
        imported_files.extend(files)
    
    # Handle file import
    if 'file' in request.files:
        file = request.files['file']
        try:
            data = json.load(file)
            conversations = grok_parser.parse(data)
            all_conversations.extend(conversations)
            imported_files.append(file.filename)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    return jsonify({
        'status': 'success',
        'conversations': all_conversations,
        'count': len(all_conversations),
        'imported_files': imported_files
    })


def _import_folder(folder_path, folder_type='auto'):
    """Import all JSON files from a folder"""
    conversations = []
    imported_files = []
    
    # Find all JSON files recursively
    json_files = glob.glob(os.path.join(folder_path, '**/*.json'), recursive=True)
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Auto-detect type or use specified type
            detected_type = _detect_data_type(data, json_file)
            
            if folder_type != 'auto' and folder_type != detected_type:
                continue
            
            if detected_type == 'grok':
                parsed = grok_parser.parse(data)
                conversations.extend(parsed)
            elif detected_type == 'x':
                parsed = x_parser.parse(data)
                conversations.extend(parsed)
            else:
                # Try both
                parsed = grok_parser.parse(data)
                if not parsed:
                    parsed = x_parser.parse(data)
                conversations.extend(parsed)
            
            imported_files.append(json_file)
        except Exception as e:
            print(f"Error parsing {json_file}: {e}")
            continue
    
    return conversations, imported_files


def _detect_data_type(data, filepath=''):
    """Detect if data is Grok or X format"""
    filepath_lower = filepath.lower()
    
    # Check filepath first
    if 'grok' in filepath_lower:
        return 'grok'
    if 'tweet' in filepath_lower or 'x_export' in filepath_lower:
        return 'x'
    
    # Check data structure
    if isinstance(data, dict):
        # Grok format indicators
        if 'results' in data and isinstance(data['results'], list):
            if data['results'] and isinstance(data['results'][0], dict):
                if 'conversation' in data['results'][0] or 'task_result_id' in data['results'][0]:
                    return 'grok'
        if 'conversations' in data:
            return 'grok'
        
        # X format indicators (tweet.js)
        if isinstance(data.get(''), list):
            return 'x'
        if data.get('__typename') == 'User':
            return 'x'
    
    # Check for array of tweets
    if isinstance(data, list):
        if data and isinstance(data[0], dict):
            if 'retweeted_status' in data[0] or 'favorite_count' in data[0]:
                return 'x'
    
    return 'unknown'


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
            # Try X parser
            conv = x_parser.get_conversation(conversation_id)
        if not conv:
            return jsonify({'error': 'Not found'}), 404
        
        return jsonify({
            'status': 'success',
            'conversation': conv
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/export/bookmarks')
def export_bookmarks():
    """Export all bookmarked tweets in Reddit-style format"""
    try:
        bookmarks = x_parser.get_bookmarked_tweets()
        
        # Generate combined Reddit-style output
        output = ["# X Bookmarks Export\n"]
        output.append(f"*Exported: {len(bookmarks)} tweets*\n")
        
        for tweet in bookmarks:
            output.append(f"## {tweet.get('source', 'X')} - @{tweet.get('username', 'unknown')}")
            output.append(f"*{tweet.get('timestamp', '')}*")
            output.append("")
            output.append(tweet.get('content', ''))
            output.append("")
            output.append(f"❤️ {tweet.get('likes', 0)} | 🔄 {tweet.get('retweets', 0)} | 💬 {tweet.get('replies', 0)}")
            output.append("---")
            output.append("")
        
        markdown = "\n".join(output)
        return jsonify({
            'status': 'success',
            'bookmarks': bookmarks,
            'count': len(bookmarks),
            'markdown': markdown,
            'filename': 'x_bookmarks.md'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/x/import', methods=['POST'])
def import_x_data():
    """Import X/tweet.js data"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    try:
        data = json.load(file)
        tweets = x_parser.parse(data)
        return jsonify({
            'status': 'success',
            'tweets': tweets,
            'count': len(tweets)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'version': VERSION,
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
