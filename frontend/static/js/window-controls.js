// Window dragging and zooming functionality
class WindowController {
    constructor(windowElement) {
        this.window = windowElement;
        this.isDragging = false;
        this.currentX = 0;
        this.currentY = 0;
        this.initialX = 0;
        this.initialY = 0;
        this.xOffset = 0;
        this.yOffset = 0;
        this.scale = 1;
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Drag handlers
        this.window.querySelector('.title-bar').addEventListener('mousedown', (e) => this.dragStart(e));
        document.addEventListener('mousemove', (e) => this.drag(e));
        document.addEventListener('mouseup', () => this.dragEnd());

        // Zoom handlers
        const maximizeBtn = this.window.querySelector('[aria-label="Maximize"]');
        if (maximizeBtn) {
            maximizeBtn.addEventListener('click', () => this.toggleZoom());
        }
    }

    dragStart(e) {
        if (e.target.closest('.title-bar-controls')) return;
        
        this.initialX = e.clientX - this.xOffset;
        this.initialY = e.clientY - this.yOffset;

        if (e.target.closest('.title-bar')) {
            this.isDragging = true;
            this.window.style.cursor = 'grabbing';
        }
    }

    drag(e) {
        if (!this.isDragging) return;

        e.preventDefault();
        this.currentX = e.clientX - this.initialX;
        this.currentY = e.clientY - this.initialY;

        this.xOffset = this.currentX;
        this.yOffset = this.currentY;

        this.setTranslate(this.currentX, this.currentY);
    }

    dragEnd() {
        this.isDragging = false;
        this.window.style.cursor = 'default';
    }

    setTranslate(xPos, yPos) {
        this.window.style.transform = `translate3d(${xPos}px, ${yPos}px, 0) scale(${this.scale})`;
    }

    toggleZoom() {
        if (this.scale === 1) {
            this.scale = 1.5;
            this.window.classList.add('maximized');
        } else {
            this.scale = 1;
            this.window.classList.remove('maximized');
        }
        this.setTranslate(this.xOffset, this.yOffset);
    }
}

// Initialize window controls
document.addEventListener('DOMContentLoaded', () => {
    const windows = document.querySelectorAll('.window');
    windows.forEach(window => {
        new WindowController(window);
    });
}); 