// List-Only Rich Text Editor - Structured approach without content loss

document.addEventListener('DOMContentLoaded', function() {
    // Convert textareas to list-only editors
    const contentTextareas = document.querySelectorAll('textarea[name="content"]');
    contentTextareas.forEach(textarea => {
        if (!textarea.classList.contains('list-editor-processed')) {
            createListOnlyEditor(textarea);
            textarea.classList.add('list-editor-processed');
        }
    });
    
    // Format existing list content for viewing
    const listContentElements = document.querySelectorAll('.list-content');
    listContentElements.forEach(element => {
        formatContentForDisplay(element);
    });
});

function createListOnlyEditor(textarea) {
    // Create wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'list-editor-wrapper';
    
    // Create toolbar
    const toolbar = document.createElement('div');
    toolbar.className = 'list-toolbar';
    toolbar.innerHTML = `
        <button type="button" class="toolbar-btn" data-action="bold" title="Bold">
            <strong>B</strong>
        </button>
        <button type="button" class="toolbar-btn" data-action="italic" title="Italic">
            <em>I</em>
        </button>
        <span class="toolbar-divider">|</span>
        <button type="button" class="toolbar-btn" data-action="add-item" title="Add New Item">
            ➕ Add Item
        </button>
    `;
    
    // Create list container
    const listContainer = document.createElement('div');
    listContainer.className = 'list-container';
    listContainer.innerHTML = '<div class="list-items"></div>';
    
    // Style the components
    const styles = `
        .list-editor-wrapper {
            border: 1px solid var(--border-color, #ddd);
            border-radius: 8px;
            background: white;
            margin-top: 4px;
        }
        .list-toolbar {
            padding: 8px 12px;
            background: linear-gradient(to bottom, #f8f9fa, #e9ecef);
            border-bottom: 1px solid var(--border-color, #ddd);
            display: flex;
            gap: 8px;
            align-items: center;
            font-size: 12px;
        }
        .list-container {
            min-height: 150px;
            padding: 12px;
        }
        .list-items {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .list-item {
            display: flex;
            align-items: flex-start;
            margin-bottom: 8px;
            group: item;
        }
        .list-item-content {
            flex: 1;
            background: #f8f9fa;
            border: 1px solid transparent;
            border-left: 3px solid #007bff;
            border-radius: 4px;
            padding: 8px 12px;
            outline: none;
            font-family: inherit;
            font-size: inherit;
            line-height: 1.5;
            min-height: 20px;
            cursor: text;
            position: relative;
        }
        .list-item-content:hover {
            border-color: #007bff;
        }   
        .list-item-content:focus {
            border-color: #007bff;
            background: white;
            box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
        }
        .list-item-content:empty::before {
            content: "Type your list item...";
            color: #999;
            pointer-events: none;
        }
        .list-item-actions {
            display: flex;
            margin-left: 8px;
        }
        .item-btn {
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 4px 8px;
            font-size: 12px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .item-btn:hover {
            background: #c82333;
        }
        .toolbar-btn {
            padding: 4px 8px;
            border: 1px solid #ccc;
            background: white;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
        }
        .toolbar-btn:hover {
            background: #007bff;
            color: white;
        }
        .toolbar-divider {
            color: #ccc;
            margin: 0 4px;
        }
        .toolbar-info {
            color: #666;
            font-style: italic;
        }
    `;
    
    // Add styles if not already added
    if (!document.getElementById('list-editor-styles')) {
        const styleElement = document.createElement('style');
        styleElement.id = 'list-editor-styles';
        styleElement.textContent = styles;
        document.head.appendChild(styleElement);
    }
    
    // Assemble wrapper
    wrapper.appendChild(toolbar);
    wrapper.appendChild(listContainer);
    
    // Insert after textarea and hide textarea
    textarea.parentNode.insertBefore(wrapper, textarea.nextSibling);
    textarea.style.display = 'none';
    
    // Initialize with existing content or empty item
    const listItemsContainer = listContainer.querySelector('.list-items');
    initializeListItems(textarea.value, listItemsContainer);
    
    // Bind events
    toolbar.addEventListener('click', handleToolbarClick);
    listItemsContainer.addEventListener('click', handleListClick);
    listItemsContainer.addEventListener('keydown', handleKeyDown);
    listItemsContainer.addEventListener('input', updateTextarea);
    
    // Sync on form submit
    const form = textarea.closest('form');
    if (form) {
        form.addEventListener('submit', updateTextarea);
    }
    
    function handleToolbarClick(e) {
        const btn = e.target.closest('.toolbar-btn');
        if (!btn) return;
        
        e.preventDefault();
        const action = btn.getAttribute('data-action');
        
        if (action === 'bold' || action === 'italic') {
            document.execCommand(action, false, null);
        } else if (action === 'add-item') {
            const lastItem = listItemsContainer.querySelector('.list-item:last-child');
            addItemAfter(lastItem);
        }
    }
    
    function handleListClick(e) {
        if (e.target.matches('.item-btn[data-action="delete"]')) {
            e.preventDefault();
            const listItem = e.target.closest('.list-item');
            deleteItem(listItem);
        }
    }
    
    function handleKeyDown(e) {
        if (e.target.matches('.list-item-content')) {
            // Allow Enter to work normally within list items
            if (e.key === 'Enter') {
                // Let Enter work normally - don't create new list items
                return;
            }
        }
    }
    
    function initializeListItems(content, container) {
        if (!content || content.trim() === '') {
            // Start with one empty item
            addListItem(container, '', true);
            return;
        }
        
        // Parse existing markdown content
        const lines = content.split('\n')
            .map(line => line.trim())
            .filter(line => line);
            
        if (lines.length === 0) {
            addListItem(container, '', true);
            return;
        }
        
        // Convert each line to a list item
        lines.forEach((line, index) => {
            const cleanText = line.replace(/^[•\-\*]\s*/, '');
            const htmlText = cleanText
                .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
                .replace(/\*([^*]+)\*/g, '<em>$1</em>')
                .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
            addListItem(container, htmlText, index === 0);
        });        
    }
    
    function addListItem(container, content = '', focus = false) {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'list-item';
        itemDiv.innerHTML = `
            <div class="list-item-content" contenteditable="true">${content}</div>
            <div class="list-item-actions">
                <button type="button" class="item-btn" data-action="delete" title="Delete this item">×</button>
            </div>
        `;
        
        container.appendChild(itemDiv);
        
        if (focus) {
            const contentDiv = itemDiv.querySelector('.list-item-content');
            setTimeout(() => {
                contentDiv.focus();
                // Put cursor at end
                const range = document.createRange();
                const sel = window.getSelection();
                range.selectNodeContents(contentDiv);
                range.collapse(false);
                sel.removeAllRanges();
                sel.addRange(range);
            }, 10);
        }
    }
    
    function addItemAfter(currentItem) {
        const newItem = document.createElement('div');
        newItem.className = 'list-item';
        newItem.innerHTML = `
            <div class="list-item-content" contenteditable="true"></div>
            <div class="list-item-actions">
                <button type="button" class="item-btn" data-action="delete" title="Delete this item">×</button>
            </div>
        `;
        
        currentItem.parentNode.insertBefore(newItem, currentItem.nextSibling);
        
        // Focus new item
        const contentDiv = newItem.querySelector('.list-item-content');
        setTimeout(() => contentDiv.focus(), 10);
        
        updateTextarea();
    }
    
    function deleteItem(item) {
        const container = item.parentNode;
        if (container.children.length <= 1) {
            // Don't delete the last item, just clear it
            const content = item.querySelector('.list-item-content');
            content.innerHTML = '';
            content.focus();
        } else {
            item.remove();
        }
        updateTextarea();
    }
    
    function updateTextarea() {
        const items = listItemsContainer.querySelectorAll('.list-item-content');
        const content = Array.from(items).map(item => {
            let text = item.innerHTML;
            // Convert HTML formatting back to markdown
            text = text.replace(/<strong[^>]*>(.*?)<\/strong>/gi, '**$1**');
            text = text.replace(/<em[^>]*>(.*?)<\/em>/gi, '*$1*');
            text = text.replace(/<b[^>]*>(.*?)<\/b>/gi, '**$1**');
            text = text.replace(/<i[^>]*>(.*?)<\/i>/gi, '*$1*');
            // Strip other HTML but preserve links
            text = text.replace(/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/gi, '$2');
            text = text.replace(/<[^>]*>/g, '');
            text = text.trim();
            return text ? `• ${text}` : '';
        }).filter(line => line).join('\n');
        
        textarea.value = content;
    }
    
    updateTextarea(); // Initial sync
}

function formatContentForDisplay(element) {
    const content = element.textContent || element.innerText || '';
    if (!content.trim()) return;
    
    const lines = content.split('\n')
        .map(line => line.trim())
        .filter(line => line);
        
    if (lines.length === 0) return;
    
    const html = lines.map(line => {
        const cleaned = line.replace(/^[•\-\*]\s*/, '');
        const formatted = cleaned
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\*([^*]+)\*/g, '<em>$1</em>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
        return `<li>${formatted}</li>`;
    }).join('');
    
    element.innerHTML = `<ul>${html}</ul>`;
}