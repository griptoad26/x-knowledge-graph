// xkg_mvp - Frontend JavaScript v0.0.2

class XkgMvp {
    constructor() {
        this.conversations = [];
        this.tweets = [];
        this.currentConversation = null;
        this.apiBase = '/api';
        this.isFolderMode = true;
        
        this.initElements();
        this.initEvents();
    }
    
    initElements() {
        // Sections
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        this.singleFileInput = document.getElementById('singleFileInput');
        this.toggleInputType = document.getElementById('toggleInputType');
        this.statusEl = document.getElementById('status');
        this.searchSection = document.getElementById('searchSection');
        this.searchInput = document.getElementById('searchInput');
        this.searchBtn = document.getElementById('searchBtn');
        this.statsEl = document.getElementById('stats');
        this.conversationsSection = document.getElementById('conversationsSection');
        this.conversationList = document.getElementById('conversationList');
        this.viewerSection = document.getElementById('viewerSection');
        this.viewerContent = document.getElementById('viewerContent');
        
        // Buttons
        this.backBtn = document.getElementById('backBtn');
        this.exportMdBtn = document.getElementById('exportMdBtn');
        this.exportJsonBtn = document.getElementById('exportJsonBtn');
        this.exportHtmlBtn = document.getElementById('exportHtmlBtn');
        this.exportBookmarksBtn = document.getElementById('exportBookmarksBtn');
        this.clearBtn = document.getElementById('clearBtn');
        
        // Modal
        this.modal = document.getElementById('exportModal');
        this.exportContent = document.getElementById('exportContent');
        this.closeModal = document.getElementById('closeModal');
        this.copyBtn = document.getElementById('copyBtn');
        this.downloadBtn = document.getElementById('downloadBtn');
    }
    
    initEvents() {
        // Toggle between folder and file mode
        this.toggleInputType.addEventListener('click', () => {
            this.isFolderMode = !this.isFolderMode;
            this.toggleInputType.textContent = this.isFolderMode ? 'Switch to File' : 'Switch to Folder';
            this.fileInput.style.display = this.isFolderMode ? 'block' : 'none';
            this.singleFileInput.style.display = this.isFolderMode ? 'none' : 'block';
        });
        
        // File upload
        this.dropZone.addEventListener('click', () => {
            if (this.isFolderMode) {
                this.fileInput.click();
            } else {
                this.singleFileInput.click();
            }
        });
        
        this.fileInput.addEventListener('change', (e) => this.handleFolder(e.target.files));
        this.singleFileInput.addEventListener('change', (e) => this.handleFile(e.target.files[0]));
        
        // Quick actions
        this.exportBookmarksBtn.addEventListener('click', () => this.exportBookmarks());
        this.clearBtn.addEventListener('click', () => this.clearAll());
        
        // Drag and drop
        this.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropZone.classList.add('dragover');
        });
        this.dropZone.addEventListener('dragleave', () => {
            this.dropZone.classList.remove('dragover');
        });
        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('dragover');
            
            const items = e.dataTransfer.items;
            if (items.length > 1) {
                // Folder or multiple files
                const files = [];
                for (let i = 0; i < items.length; i++) {
                    const item = items[i].webkitGetAsEntry();
                    if (item) {
                        this.collectFiles(item, files);
                    }
                }
                this.handleFolder(files);
            } else {
                // Single file
                const file = e.dataTransfer.files[0];
                this.handleFile(file);
            }
        });
        
        // Search
        this.searchBtn.addEventListener('click', () => this.search());
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.search();
        });
        
        // Navigation
        this.backBtn.addEventListener('click', () => this.showList());
        
        // Exports
        this.exportMdBtn.addEventListener('click', () => this.exportMarkdown());
        this.exportJsonBtn.addEventListener('click', () => this.exportJson());
        this.exportHtmlBtn.addEventListener('click', () => this.exportHtml());
        
        // Modal
        this.closeModal.addEventListener('click', () => this.hideModal());
        this.copyBtn.addEventListener('click', () => this.copyToClipboard());
        this.downloadBtn.addEventListener('click', () => this.downloadExport());
    }
    
    async handleFolder(files) {
        if (!files || files.length === 0) {
            this.showStatus('No files selected', 'error');
            return;
        }
        
        this.showStatus('Processing folder...', 'success');
        
        // Get first file's path to determine folder
        if (files[0].webkitRelativePath) {
            const folderPath = files[0].webkitRelativePath.split('/')[0];
            await this.importFolder(folderPath);
        } else {
            this.showStatus('Please drop a folder', 'error');
        }
    }
    
    async importFolder(folderPath) {
        const formData = new FormData();
        formData.append('folder', folderPath);
        formData.append('type', 'auto');
        
        try {
            const response = await fetch(`${this.apiBase}/import`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.conversations = data.conversations;
                this.showStatus(`Loaded ${data.count} conversations from ${data.imported_files?.length || 0} files`, 'success');
                this.showList();
            } else {
                this.showStatus(data.error || 'Error processing folder', 'error');
            }
        } catch (error) {
            this.showStatus('Error: ' + error.message, 'error');
        }
    }
    
    async handleFile(file) {
        if (!file) return;
        
        if (!file.name.endsWith('.json')) {
            this.showStatus('Please upload a JSON file', 'error');
            return;
        }
        
        this.showStatus('Processing...', 'success');
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(`${this.apiBase}/import`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.conversations = data.conversations;
                this.showStatus(`Loaded ${data.count} conversations`, 'success');
                this.showList();
            } else {
                this.showStatus(data.error || 'Error processing file', 'error');
            }
        } catch (error) {
            this.showStatus('Error uploading file: ' + error.message, 'error');
        }
    }
    
    async exportBookmarks() {
        try {
            const response = await fetch(`${this.apiBase}/export/bookmarks`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showStatus(`Found ${data.count} bookmarked tweets`, 'success');
                this.showExportModal(data.markdown, data.filename);
            } else {
                this.showStatus(data.error || 'No bookmarks found', 'error');
            }
        } catch (error) {
            this.showStatus('Error: ' + error.message, 'error');
        }
    }
    
    clearAll() {
        this.conversations = [];
        this.tweets = [];
        this.currentConversation = null;
        this.showStatus('Cleared all data', 'success');
        this.conversationsSection.style.display = 'none';
        this.searchSection.style.display = 'none';
        this.viewerSection.style.display = 'none';
        this.conversationList.innerHTML = '';
    }
    
    showStatus(message, type) {
        this.statusEl.textContent = message;
        this.statusEl.className = 'status ' + type;
    }
    
    showList() {
        this.viewerSection.style.display = 'none';
        this.conversationsSection.style.display = 'block';
        this.searchSection.style.display = 'block';
        
        this.renderConversationList(this.conversations);
    }
    
    renderConversationList(conversations) {
        this.conversationList.innerHTML = '';
        this.statsEl.textContent = `${conversations.length} conversations`;
        
        conversations.forEach(conv => {
            const item = document.createElement('div');
            item.className = 'conversation-item';
            
            const msgCount = conv.messages ? conv.messages.length : 0;
            const preview = conv.messages && conv.messages[0] 
                ? conv.messages[0].content.substring(0, 80) + '...' 
                : 'No content';
            
            item.innerHTML = `
                <h3>${this.escapeHtml(conv.title)}</h3>
                <p class="meta">${msgCount} messages · ID: ${conv.id}</p>
            `;
            
            item.addEventListener('click', () => this.viewConversation(conv));
            this.conversationList.appendChild(item);
        });
    }
    
    async viewConversation(conv) {
        try {
            const response = await fetch(`${this.apiBase}/conversation/${conv.id}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.currentConversation = data.conversation;
                this.renderConversation(data.conversation);
            }
        } catch (error) {
            this.showStatus('Error loading conversation: ' + error.message, 'error');
        }
    }
    
    renderConversation(conv) {
        this.conversationsSection.style.display = 'none';
        this.searchSection.style.display = 'none';
        this.viewerSection.style.display = 'block';
        
        let html = `
            <h2>${this.escapeHtml(conv.title)}</h2>
            <p class="meta">${conv.messages.length} messages · Created: ${conv.created_at || 'Unknown'}</p>
            <hr>
        `;
        
        conv.messages.forEach(msg => {
            const role = (msg.role || 'user').toLowerCase();
            const icon = role === 'user' ? '👤' : role === 'assistant' || role === 'grok' ? '🤖' : '💬';
            const content = this.escapeHtml(msg.content || '');
            const timestamp = msg.timestamp || '';
            
            html += `
                <div class="message ${role}">
                    <div class="message-header">
                        <span>${icon} ${role.charAt(0).toUpperCase() + role.slice(1)}</span>
                        ${timestamp ? `<span class="timestamp">${timestamp}</span>` : ''}
                    </div>
                    <div class="content">${this.formatContent(content)}</div>
                </div>
            `;
        });
        
        this.viewerContent.innerHTML = html;
    }
    
    async search() {
        const query = this.searchInput.value.trim();
        if (!query) {
            this.renderConversationList(this.conversations);
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                // Filter conversations that have matches
                const matchedIds = new Set(data.results.map(r => r.conversation_id));
                const filtered = this.conversations.filter(c => matchedIds.has(c.id));
                this.renderConversationList(filtered);
                this.statsEl.textContent = `Found ${data.results.length} matches in ${filtered.length} conversations`;
            }
        } catch (error) {
            this.showStatus('Search error: ' + error.message, 'error');
        }
    }
    
    async exportMarkdown() {
        if (!this.currentConversation) return;
        
        try {
            const response = await fetch(`${this.apiBase}/export/markdown/${this.currentConversation.id}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showExportModal(data.markdown, `${data.filename}`);
            }
        } catch (error) {
            this.showStatus('Export error: ' + error.message, 'error');
        }
    }
    
    async exportJson() {
        if (!this.currentConversation) return;
        
        try {
            const response = await fetch(`${this.apiBase}/export/json/${this.currentConversation.id}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                const json = JSON.stringify(data.conversation, null, 2);
                this.showExportModal(json, `grok_${this.currentConversation.id}.json`);
            }
        } catch (error) {
            this.showStatus('Export error: ' + error.message, 'error');
        }
    }
    
    async exportHtml() {
        if (!this.currentConversation) return;
        
        // Generate HTML client-side for MVP
        const html = this.generateHtml(this.currentConversation);
        this.showExportModal(html, `grok_${this.currentConversation.id}.html`);
    }
    
    generateHtml(conv) {
        let html = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>${conv.title}</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .message { margin: 15px 0; padding: 15px; border-radius: 8px; }
        .user { background: #f0f0f0; }
        .assistant { background: #e8f4ea; }
        .role { font-weight: bold; margin-bottom: 5px; }
        .timestamp { color: #666; font-size: 0.9em; }
        .content { white-space: pre-wrap; }
    </style>
</head>
<body>
    <h1>${conv.title}</h1>
    <p><em>ID: ${conv.id}</em></p>
`;
        conv.messages.forEach(msg => {
            const role = (msg.role || 'user').toLowerCase();
            const content = msg.content || '';
            const timestamp = msg.timestamp || '';
            
            html += `
    <div class="message ${role}">
        <div class="role">${role.charAt(0).toUpperCase() + role.slice(1)}</div>
        ${timestamp ? `<div class="timestamp">${timestamp}</div>` : ''}
        <div class="content">${content}</div>
    </div>
`;
        });
        
        html += '</body></html>';
        return html;
    }
    
    showExportModal(content, filename) {
        this.currentExport = { content, filename };
        this.exportContent.textContent = content;
        this.modal.style.display = 'flex';
    }
    
    hideModal() {
        this.modal.style.display = 'none';
    }
    
    copyToClipboard() {
        navigator.clipboard.writeText(this.currentExport.content)
            .then(() => {
                this.copyBtn.textContent = '✓ Copied!';
                setTimeout(() => this.copyBtn.textContent = '📋 Copy', 2000);
            });
    }
    
    downloadExport() {
        const blob = new Blob([this.currentExport.content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = this.currentExport.filename;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    formatContent(content) {
        // Simple markdown-like formatting
        return content
            .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    window.app = new XkgMvp();
});
