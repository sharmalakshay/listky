// listky.top - List Item Management & Rich Text Editor

class ListEditor {
    constructor(textarea) {
        this.textarea = textarea;
        this.container = null;
        this.items = [];
        this.init();
    }

    init() {
        this.createListInterface();
        this.parseExistingContent();
        this.bindEvents();
    }

    createListInterface() {
        // Create the visual list editor
        this.container = document.createElement('div');
        this.container.className = 'list-editor';
        this.container.innerHTML = `
            <div class="list-editor-header">
                <h3>📝 List Items</h3>
                <button type="button" class="btn btn-secondary add-item-btn">➕ Add Item</button>
            </div>
            <div class="list-items"></div>
            <div class="list-editor-footer">
                <label class="checkbox-wrapper">
                    <input type="checkbox" id="rich-text-mode" /> Enable rich text formatting
                </label>
            </div>
        `;

        // Insert before the textarea
        this.textarea.parentNode.insertBefore(this.container, this.textarea);
        
        // Hide the original textarea but keep it for form submission
        this.textarea.style.display = 'none';
        
        this.itemsContainer = this.container.querySelector('.list-items');
    }

    parseExistingContent() {
        const content = this.textarea.value.trim();
        if (content) {
            const lines = content.split('\n').filter(line => line.trim());
            lines.forEach(line => this.addItem(line.trim()));
        }
        
        if (this.items.length === 0) {
            this.addItem(''); // Start with one empty item
        }
    }

    addItem(content = '', focus = false) {
        const itemIndex = this.items.length;
        const itemElement = document.createElement('div');
        itemElement.className = 'list-item-editor';
        itemElement.innerHTML = `
            <div class="list-item-content">
                <button type="button" class="drag-handle" title="Drag to reorder">⋮⋮</button>
                <input type="text" class="list-item-input" placeholder="Enter list item..." value="${content}" />
                <div class="list-item-actions">
                    <button type="button" class="btn-small format-btn bold-btn" title="Bold"><strong>B</strong></button>
                    <button type="button" class="btn-small format-btn italic-btn" title="Italic"><em>I</em></button>
                    <button type="button" class="btn-small color-btn" title="Text Color" style="background: #ff4757;">A</button>
                    <button type="button" class="btn-small remove-btn" title="Remove item">❌</button>
                </div>
            </div>
        `;

        this.itemsContainer.appendChild(itemElement);
        this.items.push({ element: itemElement, content: content });

        // Bind events for this item
        this.bindItemEvents(itemElement, itemIndex);

        if (focus) {
            itemElement.querySelector('.list-item-input').focus();
        }

        this.updateTextarea();
        return itemElement;
    }

    bindItemEvents(itemElement, index) {
        const input = itemElement.querySelector('.list-item-input');
        const removeBtn = itemElement.querySelector('.remove-btn');
        const boldBtn = itemElement.querySelector('.bold-btn');
        const italicBtn = itemElement.querySelector('.italic-btn');
        const colorBtn = itemElement.querySelector('.color-btn');

        // Update content on input
        input.addEventListener('input', () => {
            this.updateTextarea();
        });

        // Add new item on Enter
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const newItem = this.addItem('', true);
                // Move cursor to end of content for current item
                const currentContent = input.value;
                const cursorPos = input.selectionStart;
                const beforeCursor = currentContent.slice(0, cursorPos);
                const afterCursor = currentContent.slice(cursorPos);
                
                input.value = beforeCursor;
                newItem.querySelector('.list-item-input').value = afterCursor;
                newItem.querySelector('.list-item-input').focus();
                this.updateTextarea();
            }
            
            if (e.key === 'Backspace' && input.value === '' && this.items.length > 1) {
                // Remove empty item and focus previous
                this.removeItem(itemElement);
                const prevItem = itemElement.previousElementSibling;
                if (prevItem) {
                    prevItem.querySelector('.list-item-input').focus();
                }
            }
        });

        // Remove item
        removeBtn.addEventListener('click', () => {
            if (this.items.length > 1) {
                this.removeItem(itemElement);
            }
        });

        // Rich text formatting
        boldBtn.addEventListener('click', () => this.toggleFormat(input, '**'));
        italicBtn.addEventListener('click', () => this.toggleFormat(input, '*'));
        
        colorBtn.addEventListener('click', () => {
            const colors = ['#ff4757', '#2ed573', '#3742fa', '#ffa502', '#ff6b81', '#a4b0be'];
            let currentIndex = colors.indexOf(colorBtn.style.backgroundColor);
            currentIndex = (currentIndex + 1) % colors.length;
            colorBtn.style.backgroundColor = colors[currentIndex];
            this.applyColor(input, colors[currentIndex]);
        });
    }

    toggleFormat(input, marker) {
        const start = input.selectionStart;
        const end = input.selectionEnd;
        const selectedText = input.value.slice(start, end);
        
        if (selectedText) {
            const beforeText = input.value.slice(0, start);
            const afterText = input.value.slice(end);
            
            // Check if already formatted
            if (selectedText.startsWith(marker) && selectedText.endsWith(marker)) {
                // Remove formatting
                const unformatted = selectedText.slice(marker.length, -marker.length);
                input.value = beforeText + unformatted + afterText;
                input.setSelectionRange(start, start + unformatted.length);
            } else {
                // Add formatting
                const formatted = marker + selectedText + marker;
                input.value = beforeText + formatted + afterText;
                input.setSelectionRange(start, start + formatted.length);
            }
            
            this.updateTextarea();
        }
    }

    applyColor(input, color) {
        const start = input.selectionStart;
        const end = input.selectionEnd;
        const selectedText = input.value.slice(start, end);
        
        if (selectedText) {
            const beforeText = input.value.slice(0, start);
            const afterText = input.value.slice(end);
            const coloredText = `<span style="color: ${color}">${selectedText}</span>`;
            
            input.value = beforeText + coloredText + afterText;
            this.updateTextarea();
        }
    }

    removeItem(itemElement) {
        const index = this.items.findIndex(item => item.element === itemElement);
        if (index > -1) {
            this.items.splice(index, 1);
            itemElement.remove();
            this.updateTextarea();
        }
    }

    updateTextarea() {
        const content = this.items
            .map(item => {
                const input = item.element.querySelector('.list-item-input');
                return input.value.trim();
            })
            .filter(content => content.length > 0)
            .join('\n');
            
        this.textarea.value = content;
    }

    bindEvents() {
        // Add item button
        this.container.querySelector('.add-item-btn').addEventListener('click', () => {
            this.addItem('', true);
        });

        // Rich text mode toggle
        const richTextToggle = this.container.querySelector('#rich-text-mode');
        richTextToggle.addEventListener('change', (e) => {
            this.container.classList.toggle('rich-text-mode', e.target.checked);
        });

        // Make items sortable (simple implementation)
        this.initSortable();
    }

    initSortable() {
        let draggedElement = null;

        this.itemsContainer.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('drag-handle')) {
                draggedElement = e.target.closest('.list-item-editor');
                draggedElement.classList.add('dragging');
            }
        });

        this.itemsContainer.addEventListener('dragend', (e) => {
            if (draggedElement) {
                draggedElement.classList.remove('dragging');
                draggedElement = null;
                this.updateTextarea();
            }
        });

        this.itemsContainer.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        this.itemsContainer.addEventListener('drop', (e) => {
            e.preventDefault();
            
            if (draggedElement) {
                const afterElement = this.getDragAfterElement(e.clientY);
                
                if (afterElement == null) {
                    this.itemsContainer.appendChild(draggedElement);
                } else {
                    this.itemsContainer.insertBefore(draggedElement, afterElement);
                }
                
                this.rebuildItemsArray();
            }
        });
    }

    getDragAfterElement(y) {
        const draggableElements = [...this.itemsContainer.querySelectorAll('.list-item-editor:not(.dragging)')];
        
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    rebuildItemsArray() {
        this.items = [...this.itemsContainer.querySelectorAll('.list-item-editor')].map(element => ({
            element: element,
            content: element.querySelector('.list-item-input').value
        }));
    }
}

// Rich text content parser for display
class RichTextParser {
    static parse(content) {
        if (!content) return '';
        
        // Parse markdown-style formatting
        let parsed = content
            // Bold text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Italic text  
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Headings
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            // Line breaks
            .replace(/\n/g, '<br>');

        return parsed;
    }

    static parseListItems(content) {
        if (!content) return [];
        
        return content.split('\n')
            .filter(line => line.trim())
            .map(line => ({
                raw: line.trim(),
                formatted: this.parse(line.trim())
            }));
    }
}

// Initialize list editors when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize list editors for content textareas
    const contentTextareas = document.querySelectorAll('textarea[name="content"]');
    contentTextareas.forEach(textarea => {
        if (textarea.classList.contains('list-editor-enabled')) return; // Already initialized
        
        new ListEditor(textarea);
        textarea.classList.add('list-editor-enabled');
    });

    // Format existing list content in view mode
    const listContentElements = document.querySelectorAll('.list-content');
    listContentElements.forEach(element => {
        const rawContent = element.textContent || element.innerText;
        const listItems = RichTextParser.parseListItems(rawContent);
        
        if (listItems.length > 1) {
            element.innerHTML = '<ul class="formatted-list">' +
                listItems.map(item => `<li class="formatted-list-item">${item.formatted}</li>`).join('') +
                '</ul>';
        } else {
            element.innerHTML = RichTextParser.parse(rawContent);
        }
        
        element.classList.add('rich-content');
    });
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ListEditor, RichTextParser };
}