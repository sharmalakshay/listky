// Simple List Editor - Fixed and Clean

document.addEventListener('DOMContentLoaded', function() {
    const contentTextareas = document.querySelectorAll('textarea[name="content"]');
    contentTextareas.forEach(textarea => {
        if (!textarea.classList.contains('list-editor-processed')) {
            createListEditor(textarea);
            textarea.classList.add('list-editor-processed');
        }
    });
    
    // Format existing list content for viewing
    const listContentElements = document.querySelectorAll('.list-content');
    listContentElements.forEach(element => {
        formatContentForDisplay(element);
    });
});

function createListEditor(textarea) {
    // Create wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'list-editor';
    
    // Create toolbar with Add button
    const toolbar = document.createElement('div');
    toolbar.className = 'list-toolbar';
    toolbar.innerHTML = `
        <button type="button" class="format-btn" data-action="bold" title="Bold">
            <strong>B</strong>
        </button>
        <button type="button" class="format-btn" data-action="italic" title="Italic">
            <em>I</em>
        </button>
    `;
    
    // Create list container
    const listContainer = document.createElement('div');
    listContainer.className = 'list-items';
    
    // Create add button below items
    const addButton = document.createElement('button');
    addButton.type = 'button';
    addButton.className = 'add-item-btn';
    addButton.innerHTML = '➕ Add Item';
    addButton.title = 'Add New Item';
    
    // Add styles
    if (!document.getElementById('simple-list-editor-styles')) {
        const style = document.createElement('style');
        style.id = 'simple-list-editor-styles';
        style.textContent = `
            .list-editor {
                border: 1px solid #ddd;
                border-radius: 8px;
                background: white;
                margin-top: 4px;
                max-width: 100%;
            }
            .list-toolbar {
                padding: 8px 12px;
                background: #f8f9fa;
                border-bottom: 1px solid #ddd;
                display: flex;
                gap: 8px;
                align-items: center;
            }
            .format-btn {
                padding: 4px 8px;
                border: 1px solid #ccc;
                background: white;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.2s;
            }
            .format-btn:hover {
                background: #007bff;
                color: white;
            }
            .add-item-btn {
                width: 100%;
                padding: 8px 12px;
                margin-top: 12px;
                background: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                transition: background 0.2s;
            }
            .add-item-btn:hover {
                background: #218838;
            }
            .list-items {
                padding: 12px;
                max-width: 100%;
            }
            .list-item-wrapper {
                position: relative;
                margin-bottom: 8px;
            }
            .list-item-input {
                display: block;
                width: 100%;
                background: #f8f9fa;
                border: 1px solid transparent;
                border-left: 3px solid #007bff;
                border-radius: 4px;
                padding: 8px 12px;
                padding-right: 32px;
                outline: none;
                font-family: inherit;
                font-size: inherit;
                line-height: 1.5;
                min-height: 20px;
                word-wrap: break-word;
                resize: none;
                overflow: hidden;
            }
            .list-item-input:focus {
                border-color: #007bff;
                background: white;
                box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
            }
            .list-item-input:empty::before {
                content: "Type your list item...";
                color: #999;
                pointer-events: none;
            }
            .delete-btn {
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 10px;
                cursor: pointer;
                position: absolute;
                right: 4px;
                top: 4px;
                z-index: 10;
                opacity: 0;
                transition: opacity 0.2s;
            }
            .list-item-wrapper:hover .delete-btn {
                opacity: 1;
            }
            .delete-btn:hover {
                background: #c82333;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Assemble wrapper
    wrapper.appendChild(toolbar);
    wrapper.appendChild(listContainer);
    wrapper.appendChild(addButton);
    
    // Insert after textarea and hide textarea
    textarea.parentNode.insertBefore(wrapper, textarea.nextSibling);
    textarea.style.display = 'none';
    
    // Initialize with existing content or empty item
    initializeListItems(textarea.value, listContainer);
    
    // Bind events
    toolbar.addEventListener('click', handleToolbarClick);
    addButton.addEventListener('click', handleAddClick);
    listContainer.addEventListener('click', handleListClick);
    listContainer.addEventListener('keydown', handleKeyDown);
    listContainer.addEventListener('input', updateTextarea);
    
    // Sync on form submit
    const form = textarea.closest('form');
    if (form) {
        form.addEventListener('submit', updateTextarea);
    }
    
    function handleToolbarClick(e) {
        const btn = e.target.closest('button');
        if (!btn) return;
        
        e.preventDefault();
        const action = btn.getAttribute('data-action');
        
        if (action === 'bold' || action === 'italic') {
            document.execCommand(action, false, null);
        }
    }
    
    function handleAddClick(e) {
        e.preventDefault();
        addNewItem();
    }
    
    function handleListClick(e) {
        if (e.target.matches('.delete-btn')) {
            e.preventDefault();
            const wrapper = e.target.closest('.list-item-wrapper');
            const input = wrapper.querySelector('.list-item-input');
            deleteItem(input, wrapper);
        }
    }
    
    function handleKeyDown(e) {
        if (e.target.matches('.list-item-input')) {
            // Handle both Enter and Shift+Enter the same way - create line breaks within the item
            if (e.key === 'Enter') {
                e.preventDefault();
                // Insert a proper line break
                document.execCommand('insertHTML', false, '<br>');
                updateTextarea();
                return false;
            }
        }
    }
    
    function initializeListItems(content, container) {
        container.innerHTML = ''; // Clear container
        
        if (!content || content.trim() === '') {
            addListItem(container, '', true);
            return;
        }
        
        // Split by bullet points, not by newlines, to preserve internal line breaks
        const items = content.split(/^• /m).filter(item => item.trim());
        
        if (items.length === 0) {
            addListItem(container, '', true);
            return;
        }
        
        items.forEach((item, index) => {
            // Remove any leading bullet if it exists and trim
            const cleanText = item.replace(/^[•\-\*]\s*/, '').trim();
            if (!cleanText) return;
            
            // Convert markdown to HTML and preserve internal line breaks
            const htmlText = cleanText
                .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
                .replace(/\*([^*]+)\*/g, '<em>$1</em>')
                .replace(/\n/g, '<br>'); // Convert newlines to <br> tags
            addListItem(container, htmlText, index === 0);
        });        
        
        // If no items were created, create an empty one
        if (container.children.length === 0) {
            addListItem(container, '', true);
        }
    }
    
    function addListItem(container, content = '', focus = false) {
        const wrapper = document.createElement('div');
        wrapper.className = 'list-item-wrapper';
        
        const input = document.createElement('div');
        input.className = 'list-item-input';
        input.contentEditable = true;
        input.innerHTML = content;
        
        const deleteBtn = document.createElement('button');
        deleteBtn.type = 'button';
        deleteBtn.className = 'delete-btn';
        deleteBtn.innerHTML = '×';
        deleteBtn.title = 'Delete this item';
        
        wrapper.appendChild(input);
        wrapper.appendChild(deleteBtn);
        container.appendChild(wrapper);
        
        if (focus) {
            setTimeout(() => {
                input.focus();
                // Put cursor at end
                const range = document.createRange();
                const sel = window.getSelection();
                range.selectNodeContents(input);
                range.collapse(false);
                sel.removeAllRanges();
                sel.addRange(range);
            }, 10);
        }
    }
    
    function addNewItem() {
        addListItem(listContainer, '', true);
        updateTextarea();
    }
    
    function deleteItem(input, wrapper) {
        if (listContainer.children.length <= 1) {
            // Don't delete the last item, just clear it
            input.innerHTML = '';
            input.focus();
        } else {
            wrapper.remove();
        }
        updateTextarea();
    }
    
    function updateTextarea() {
        const items = listContainer.querySelectorAll('.list-item-input');
        const content = Array.from(items).map(item => {
            let text = item.innerHTML;
            // First convert <br> tags to newlines to preserve line breaks
            text = text.replace(/<br\s*\/?>/gi, '\n');
            // Then convert formatting back to markdown
            text = text.replace(/<strong[^>]*>(.*?)<\/strong>/gi, '**$1**');
            text = text.replace(/<em[^>]*>(.*?)<\/em>/gi, '*$1*');
            text = text.replace(/<b[^>]*>(.*?)<\/b>/gi, '**$1**');
            text = text.replace(/<i[^>]*>(.*?)<\/i>/gi, '*$1*');
            // Clean up any remaining HTML tags
            text = text.replace(/<[^>]*>/g, '');
            // Decode HTML entities
            text = text.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
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
        // Convert markdown to HTML and handle line breaks
        const formatted = cleaned
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\*([^*]+)\*/g, '<em>$1</em>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>')
            .replace(/\n/g, '<br>'); // Convert newlines to <br> for display
        return `<li>${formatted}</li>`;
    }).join('');
    
    element.innerHTML = `<ul>${html}</ul>`;
}