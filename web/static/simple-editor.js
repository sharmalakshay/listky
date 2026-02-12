// Simple Rich Text Editor for listky.top

// Rich text parser for content display
function parseRichText(text) {
    if (!text) return '';
    
    return text
        // Remove bullet points at start of lines and clean them up
        .replace(/^[•\-\*]\s*/gm, '')
        // Bold text **text**
        .replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>')
        // Italic text *text*
        .replace(/\*([^\*]+)\*/g, '<em>$1</em>')
        // URLs
        .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>')
        // Line breaks
        .replace(/\n/g, '<br>');
}

// Parse content into list items
function parseListItems(content) {
    if (!content) return [];
    
    return content.split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
        .map(line => {
            // Remove any existing bullet points
            const cleaned = line.replace(/^[•\-\*]\s*/, '');
            return parseRichText(cleaned);
        });
}

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    // Format list content on view pages
    const listContentElements = document.querySelectorAll('.list-content');
    listContentElements.forEach(element => {
        const rawContent = element.textContent || element.innerText;
        const listItems = parseListItems(rawContent);
        
        if (listItems.length > 1) {
            // Create a proper list
            element.innerHTML = '<ul class="formatted-list">' +
                listItems.map(item => `<li>${item}</li>`).join('') +
                '</ul>';
        } else if (listItems.length === 1) {
            // Single item, just show parsed content
            element.innerHTML = listItems[0];
        }
    });
    
    // Add simple formatting buttons to textareas
    const contentTextareas = document.querySelectorAll('textarea[name="content"]');
    contentTextareas.forEach(textarea => {
        addSimpleEditor(textarea);
    });
});

function addSimpleEditor(textarea) {
    // Create toolbar
    const toolbar = document.createElement('div');
    toolbar.className = 'simple-toolbar';
    toolbar.innerHTML = `
        <button type="button" onclick="formatSelection(this, '**', '**')" title="Bold">
            <strong>B</strong>
        </button>
        <button type="button" onclick="formatSelection(this, '*', '*')" title="Italic">
            <em>I</em>
        </button>
        <button type="button" onclick="addListItem(this)" title="Add Item">
            ➕ Add Item
        </button>
    `;
    
    // Insert toolbar before textarea
    textarea.parentNode.insertBefore(toolbar, textarea);
    
    // Add CSS if not already added
    if (!document.querySelector('#simple-editor-styles')) {
        const style = document.createElement('style');
        style.id = 'simple-editor-styles';
        style.textContent = `
            .simple-toolbar {
                background: var(--surface-light);
                padding: 0.5rem;
                border: 1px solid var(--border-color);
                border-bottom: none;
                border-radius: var(--radius-md) var(--radius-md) 0 0;
                display: flex;
                gap: 0.5rem;
            }
            .simple-toolbar button {
                padding: 0.25rem 0.5rem;
                border: 1px solid var(--border-color);
                background: var(--white);
                border-radius: var(--radius-sm);
                cursor: pointer;
                font-size: 0.875rem;
            }
            .simple-toolbar button:hover {
                background: var(--primary-blue);
                color: white;
            }
            .simple-toolbar + textarea {
                border-radius: 0 0 var(--radius-md) var(--radius-md);
                margin-top: 0;
            }
            .formatted-list {
                list-style: none !important;
                padding: 0 !important;
            }
            .formatted-list li {
                background: var(--white);
                padding: var(--spacing-md);
                margin: var(--spacing-sm) 0;
                border-radius: var(--radius-md);
                box-shadow: var(--shadow-sm);
                border-left: 3px solid var(--primary-blue);
            }
        `;
        document.head.appendChild(style);
    }
}

function formatSelection(button, startTag, endTag) {
    const toolbar = button.parentNode;
    const textarea = toolbar.nextElementSibling;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    
    if (selectedText) {
        const replacement = startTag + selectedText + endTag;
        textarea.setRangeText(replacement, start, end, 'end');
    } else {
        // Insert tags at cursor
        const replacement = startTag + 'text' + endTag;
        textarea.setRangeText(replacement, start, end, 'end');
        textarea.setSelectionRange(start + startTag.length, start + startTag.length + 4);
    }
    textarea.focus();
}

function addListItem(button) {
    const toolbar = button.parentNode;
    const textarea = toolbar.nextElementSibling;
    const cursorPos = textarea.selectionStart;
    const textBefore = textarea.value.substring(0, cursorPos);
    const textAfter = textarea.value.substring(cursorPos);
    
    // Add new line if not at start of line
    const newItem = (textBefore && !textBefore.endsWith('\n') ? '\n' : '') + '• ';
    
    textarea.value = textBefore + newItem + textAfter;
    textarea.setSelectionRange(cursorPos + newItem.length, cursorPos + newItem.length);
    textarea.focus();
}