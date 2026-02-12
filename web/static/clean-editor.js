// Simple Rich Text Editor - Clean Integration with Existing Forms

document.addEventListener('DOMContentLoaded', function() {
    // Convert textareas to rich text editors
    const contentTextareas = document.querySelectorAll('textarea[name="content"]');
    contentTextareas.forEach(textarea => {
        if (!textarea.classList.contains('rich-editor-processed')) {
            createSimpleRichEditor(textarea);
            textarea.classList.add('rich-editor-processed');
        }
    });
    
    // Format existing list content for viewing
    const listContentElements = document.querySelectorAll('.list-content');
    console.log('Found list content elements:', listContentElements.length); // Debug
    listContentElements.forEach(element => {
        console.log('Processing element:', element); // Debug
        formatContentForDisplay(element);
    });
});

function createSimpleRichEditor(textarea) {
    // Create wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'rich-editor-wrapper';
    
    // Create simple toolbar
    const toolbar = document.createElement('div');
    toolbar.className = 'rich-toolbar';
    toolbar.innerHTML = `
        <button type="button" class="rich-btn" data-action="bold" title="Bold">
            <strong>B</strong>
        </button>
        <button type="button" class="rich-btn" data-action="italic" title="Italic">
            <em>I</em>
        </button>
        <span class="rich-divider">|</span>
        <button type="button" class="rich-btn" data-action="addItem" title="Add List Item">
            ➕
        </button>
    `;
    
    // Create rich text area
    const richArea = document.createElement('div');
    richArea.className = 'rich-area';
    richArea.contentEditable = true;
    richArea.innerHTML = convertToRichText(textarea.value);
    
    // Style the wrapper to match form textarea
    wrapper.style.cssText = `
        border: 1px solid var(--border-color, #ddd);
        border-radius: 8px;
        background: white;
        margin-top: 4px;
    `;
    
    toolbar.style.cssText = `
        padding: 8px 12px;
        background: linear-gradient(to bottom, #f8f9fa, #e9ecef);
        border-bottom: 1px solid var(--border-color, #ddd);
        display: flex;
        gap: 8px;
        align-items: center;
    `;
    
    richArea.style.cssText = `
        min-height: 150px;
        padding: 12px;
        outline: none;
        font-family: inherit;
        font-size: inherit;
        line-height: 1.5;
    `;
    
    // Add styles for toolbar buttons
    const btnStyle = `
        .rich-btn {
            padding: 4px 8px !important;
            border: 1px solid #ccc !important;
            background: white !important;
            border-radius: 4px !important;
            cursor: pointer !important;
            font-size: 14px !important;
            transition: all 0.2s !important;
        }
        .rich-btn:hover {
            background: #007bff !important;
            color: white !important;
        }
        .rich-divider {
            color: #ccc;
            margin: 0 4px;
        }
        .rich-area ul {
            list-style: none !important;
            padding-left: 0 !important;
        }
        .rich-area li {
            background: #f8f9fa !important;
            margin: 4px 0 !important;
            padding: 8px !important;
            border-left: 3px solid #007bff !important;
            border-radius: 4px !important;
        }
        .rich-area li:before {
            content: "• ";
            color: #007bff;
            font-weight: bold;
        }
    `;
    
    if (!document.getElementById('rich-editor-styles')) {
        const style = document.createElement('style');
        style.id = 'rich-editor-styles';
        style.textContent = btnStyle;
        document.head.appendChild(style);
    }
    
    // Assemble
    wrapper.appendChild(toolbar);
    wrapper.appendChild(richArea);
    
    // Insert after textarea and hide textarea
    textarea.parentNode.insertBefore(wrapper, textarea.nextSibling);
    textarea.style.display = 'none';
    
    // Bind events
    toolbar.addEventListener('click', (e) => {
        const btn = e.target.closest('.rich-btn');
        if (!btn) return;
        
        e.preventDefault();
        const action = btn.getAttribute('data-action');
        
        if (action === 'bold') {
            document.execCommand('bold', false, null);
        } else if (action === 'italic') {
            document.execCommand('italic', false, null);
        } else if (action === 'addItem') {
            addNewListItem(richArea);
        }
        
        richArea.focus();
        updateTextarea();
    });
    
    // Update textarea on content change
    richArea.addEventListener('input', updateTextarea);
    richArea.addEventListener('keyup', updateTextarea);
    
    // Sync on form submit
    const form = textarea.closest('form');
    if (form) {
        form.addEventListener('submit', updateTextarea);
    }
    
    function updateTextarea() {
        console.log('updateTextarea called');
        console.log('richArea.innerHTML:', richArea.innerHTML);
        const content = convertToMarkdown(richArea.innerHTML);
        console.log('convertToMarkdown result:', content);
        textarea.value = content;
        console.log('textarea.value set to:', textarea.value);
    }
    
    function addNewListItem(area) {
        let ul = area.querySelector('ul');
        if (!ul) {
            ul = document.createElement('ul');
            area.appendChild(ul);
        }
        
        const li = document.createElement('li');
        li.textContent = 'New item';
        ul.appendChild(li);
        
        // Focus on new item
        const range = document.createRange();
        range.selectNodeContents(li);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
    }
    
    updateTextarea(); // Initial sync
}

function convertToRichText(markdown) {
    if (!markdown || markdown.trim() === '') {
        return '<p>Start typing...</p>';
    }
    
    const lines = markdown.split('\n')
        .map(line => line.trim())
        .filter(line => line);
    
    if (lines.length === 0) return '<p>Start typing...</p>';
    
    if (lines.length === 1) {
        // Single line
        const formatted = lines[0]
            .replace(/^[•\-\*]\s*/, '')
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\*([^*]+)\*/g, '<em>$1</em>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
        return `<p>${formatted}</p>`;
    } else {
        // Multiple lines - create list
        const items = lines.map(line => {
            const cleaned = line.replace(/^[•\-\*]\s*/, '');
            const formatted = cleaned
                .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
                .replace(/\*([^*]+)\*/g, '<em>$1</em>')
                .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
            return `<li>${formatted}</li>`;
        }).join('');
        
        return `<ul>${items}</ul>`;
    }
}
    } else {
        // Multiple lines - create list
        const items = lines.map(line => {
            const cleaned = line.replace(/^[•\-\*]\s*/, '');
            const formatted = cleaned
                .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
                .replace(/\*([^*]+)\*/g, '<em>$1</em>')
                .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
            return `<li>${formatted}</li>`;
        }).join('');
        
        return `<ul>${items}</ul>`;
    }
}

function convertToMarkdown(html) {
    console.log('convertToMarkdown called with HTML:', html);
    
    // Create temp element
    const temp = document.createElement('div');
    temp.innerHTML = html;
    
    // Get list items
    const listItems = temp.querySelectorAll('li');
    if (listItems.length > 0) {
        console.log('Found', listItems.length, 'list items');
        const result = Array.from(listItems).map(li => {
            console.log('Processing li innerHTML:', li.innerHTML);
            let text = li.innerHTML
                .replace(/<strong>(.*?)<\/strong>/g, '**$1**')
                .replace(/<em>(.*?)<\/em>/g, '*$1*')
                .replace(/<[^>]*>/g, '');
            console.log('Processed li text:', text);
            return `• ${text.trim()}`;
        }).join('\n');
        console.log('Final list result:', result);
        return result;
    }
    
    // Handle paragraphs
    const paragraphs = temp.querySelectorAll('p');
    if (paragraphs.length > 0) {
        console.log('Found', paragraphs.length, 'paragraphs');
        const result = Array.from(paragraphs).map(p => {
            console.log('Processing p innerHTML:', p.innerHTML);
            const processed = p.innerHTML
                .replace(/<strong>(.*?)<\/strong>/g, '**$1**')
                .replace(/<em>(.*?)<\/em>/g, '*$1*')
                .replace(/<[^>]*>/g, '');
            console.log('Processed p text:', processed);
            return processed;
        }).join('\n');
        console.log('Final paragraph result:', result);
        return result;
    }
    
    // Fallback
    console.log('Fallback to textContent');
    return temp.textContent || '';
}
function convertMarkdownToHTML(text) {
    console.log('convertMarkdownToHTML called with:', text); // Debug
    
    if (!text || text.trim() === '') return '';
    
    // Simple test - if we see **test** anywhere, make it bold
    if (text.includes('**')) {
        console.log('Found ** in text, processing...'); // Debug
    }
    
    const lines = text.split('\n')
        .map(line => line.trim())
        .filter(line => line);
    
    if (lines.length === 0) return '';
    
    if (lines.length === 1) {
        // Single line - just format it as a paragraph
        const formatted = lines[0]
            .replace(/^[•\-\*]\s*/, '')
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\*([^*]+)\*/g, '<em>$1</em>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
        console.log('Single line formatted:', formatted); // Debug
        return `<p>${formatted}</p>`;
    } else {
        // Multiple lines - create list
        const items = lines.map(line => {
            const cleaned = line.replace(/^[•\-\*]\s*/, '');
            const formatted = cleaned
                .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
                .replace(/\*([^*]+)\*/g, '<em>$1</em>')
                .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
            return `<li>${formatted}</li>`;
        }).join('');
        
        const result = `<ul>${items}</ul>`;
        console.log('Multi-line formatted:', result); // Debug
        return result;
    }
}

function formatContentForDisplay(element) {
    const content = element.textContent || '';
    if (!content.trim()) return;
    
    console.log('Raw content from element:', content); // Debug log
    
    // Convert markdown-style formatting to HTML for display
    const formatted = convertMarkdownToHTML(content);
    console.log('Formatted HTML result:', formatted); // Debug log
    
    if (formatted && formatted !== content) {
        element.innerHTML = formatted;
        console.log('Updated element HTML'); // Debug log
    }
}