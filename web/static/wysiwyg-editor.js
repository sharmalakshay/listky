// WYSIWYG Rich Text Editor for listky.top - No markdown syntax visible to users

document.addEventListener('DOMContentLoaded', function() {
    // Convert textareas to rich text editors
    const contentTextareas = document.querySelectorAll('textarea[name="content"]');
    contentTextareas.forEach(textarea => {
        createRichTextEditor(textarea);
    });
    
    // Format existing list content for viewing
    const listContentElements = document.querySelectorAll('.list-content');
    listContentElements.forEach(element => {
        formatListForDisplay(element);
    });
});

function createRichTextEditor(textarea) {
    // Create rich text editor container
    const editorContainer = document.createElement('div');
    editorContainer.className = 'rich-text-editor';
    
    // Create toolbar
    const toolbar = document.createElement('div');
    toolbar.className = 'editor-toolbar';
    toolbar.innerHTML = `
        <button type="button" class="format-btn" data-command="bold" title="Bold">
            <strong>B</strong>
        </button>
        <button type="button" class="format-btn" data-command="italic" title="Italic">
            <em>I</em>
        </button>
        <div class="toolbar-divider"></div>
        <button type="button" class="format-btn" data-command="insertUnorderedList" title="Bullet List">
            • List
        </button>
        <button type="button" class="add-item-btn" title="Add List Item">
            ➕ Add Item
        </button>
    `;
    
    // Create contenteditable div
    const editor = document.createElement('div');
    editor.className = 'rich-text-content';
    editor.contentEditable = true;
    editor.setAttribute('placeholder', 'Start typing your list items here...');
    editor.innerHTML = parseTextToHTML(textarea.value);
    
    // Assemble editor
    editorContainer.appendChild(toolbar);
    editorContainer.appendChild(editor);
    
    // Insert before textarea and hide textarea
    textarea.parentNode.insertBefore(editorContainer, textarea);
    textarea.style.display = 'none';
    textarea.classList.add('rich-editor-hidden');
    
    // Bind events
    bindEditorEvents(toolbar, editor, textarea);
    
    // Update textarea on content change
    editor.addEventListener('input', () => updateTextarea(editor, textarea));
    
    // Sync on form submit
    const form = textarea.closest('form');
    if (form) {
        form.addEventListener('submit', () => updateTextarea(editor, textarea));
    }
}

function bindEditorEvents(toolbar, editor, textarea) {
    // Toolbar buttons
    toolbar.addEventListener('click', (e) => {
        if (e.target.classList.contains('format-btn')) {
            e.preventDefault();
            const command = e.target.getAttribute('data-command');
            document.execCommand(command, false, null);
            editor.focus();
        }
        
        if (e.target.classList.contains('add-item-btn')) {
            e.preventDefault();
            addListItem(editor);
        }
    });
    
    // Handle Enter key for list items
    editor.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            // If we're in a list, add a new list item
            const selection = window.getSelection();
            if (selection.anchorNode) {
                const listItem = selection.anchorNode.closest('li');
                if (listItem) {
                    e.preventDefault();
                    const newItem = document.createElement('li');
                    newItem.innerHTML = '<br>';
                    listItem.parentNode.insertBefore(newItem, listItem.nextSibling);
                    
                    // Move cursor to new item
                    const range = document.createRange();
                    range.setStart(newItem, 0);
                    range.collapse(true);
                    selection.removeAllRanges();
                    selection.addRange(range);
                    
                    updateTextarea(editor, textarea);
                }
            }
        }
    });
    
    // Update textarea when content changes
    editor.addEventListener('input', () => updateTextarea(editor, textarea));
}

function addListItem(editor) {
    // Get current selection
    const selection = window.getSelection();
    let ul = editor.querySelector('ul');
    
    // Create list if it doesn't exist
    if (!ul) {
        ul = document.createElement('ul');
        editor.appendChild(ul);
    }
    
    // Add new list item
    const li = document.createElement('li');
    li.textContent = 'New item';
    ul.appendChild(li);
    
    // Focus on new item
    const range = document.createRange();
    range.selectNodeContents(li);
    selection.removeAllRanges();
    selection.addRange(range);
    
    editor.focus();
}

function updateTextarea(editor, textarea) {
    // Convert HTML back to markdown-style format for storage
    const htmlContent = editor.innerHTML;
    const textContent = htmlToMarkdown(htmlContent);
    textarea.value = textContent;
}

function htmlToMarkdown(html) {
    // Create temporary div to parse HTML
    const temp = document.createElement('div');
    temp.innerHTML = html;
    
    // Extract list items
    const listItems = temp.querySelectorAll('li');
    if (listItems.length > 0) {
        return Array.from(listItems)
            .map(li => {
                let text = li.innerHTML
                    .replace(/<strong>(.*?)<\/strong>/g, '**$1**')
                    .replace(/<em>(.*?)<\/em>/g, '*$1*')
                    .replace(/<a[^>]*>(.*?)<\/a>/g, '$1')
                    .replace(/<br>/g, ' ')
                    .replace(/<[^>]*>/g, '');
                return '• ' + text.trim();
            })
            .filter(text => text !== '• ')
            .join('\n');
    }
    
    // Handle paragraph content
    const paragraphs = temp.querySelectorAll('p');
    if (paragraphs.length > 0) {
        return Array.from(paragraphs)
            .map(p => {
                return p.innerHTML
                    .replace(/<strong>(.*?)<\/strong>/g, '**$1**')
                    .replace(/<em>(.*?)<\/em>/g, '*$1*')
                    .replace(/<a[^>]*>(.*?)<\/a>/g, '$1')
                    .replace(/<br>/g, ' ')
                    .replace(/<[^>]*>/g, '');
            })
            .filter(text => text.trim())
            .join('\n');
    }
    
    // Fallback to text content with formatting
function formatListForDisplay(element) {
    const rawContent = element.textContent || element.innerText;
    if (!rawContent) return;
    
    // Parse content into HTML for display
    const htmlContent = parseTextToHTML(rawContent);
    element.innerHTML = htmlContent;
}

function parseTextToHTML(text) {
    if (!text || text.trim() === '') return '';
    
    // Split into lines and create list items
    const lines = text.split('\n').map(line => line.trim()).filter(line => line);
    
    if (lines.length === 0) return '';
    
    // Create list if multiple lines
    if (lines.length > 1) {
        const listItems = lines.map(line => {
            // Remove existing bullet points
            const cleaned = line.replace(/^[•\-\*]\s*/, '');
            // Parse markdown-style formatting
            const formatted = cleaned
                .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
                .replace(/\*([^*]+)\*/g, '<em>$1</em>')
                .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
            return `<li>${formatted}</li>`;
        }).join('');
        
        return `<ul>${listItems}</ul>`;
    } else {
        // Single line, just format it
        const formatted = lines[0]
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\*([^*]+)\*/g, '<em>$1</em>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        return `<p>${formatted}</p>`;
    }
}