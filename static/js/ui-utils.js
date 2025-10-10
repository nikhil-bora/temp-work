// UI Utilities - Professional Confirmations, Toasts, and Modals

// Toast Notification System
class ToastNotification {
    constructor() {
        this.container = this.createContainer();
    }

    createContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }

    show(message, type = 'info', duration = 4000) {
        console.log('[TOAST]', type.toUpperCase(), message);

        const toast = document.createElement('div');
        toast.className = `toast ${type} fade-in`;

        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#06b6d4'
        };

        toast.innerHTML = `
            <div style="display: flex; align-items: start; gap: 12px;">
                <div style="
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    background: ${colors[type]};
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 700;
                    flex-shrink: 0;
                ">${icons[type]}</div>
                <div style="flex: 1; min-width: 0;">
                    <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 2px;">
                        ${type.charAt(0).toUpperCase() + type.slice(1)}
                    </div>
                    <div style="color: var(--text-secondary); font-size: 0.875rem; line-height: 1.4;">
                        ${message}
                    </div>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" style="
                    background: none;
                    border: none;
                    color: var(--text-muted);
                    cursor: pointer;
                    font-size: 1.25rem;
                    line-height: 1;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 4px;
                    transition: all 0.2s;
                " onmouseover="this.style.background='rgba(0,0,0,0.05)'" onmouseout="this.style.background='none'">&times;</button>
            </div>
        `;

        this.container.appendChild(toast);

        // Auto-remove after duration
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);

        return toast;
    }

    success(message, duration) {
        return this.show(message, 'success', duration);
    }

    error(message, duration) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration) {
        return this.show(message, 'info', duration);
    }
}

// Slide out animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Global toast instance
window.toast = new ToastNotification();

// Confirmation Dialog
function showConfirmDialog(options) {
    return new Promise((resolve) => {
        console.log('[CONFIRM] Showing dialog:', options.title);

        const {
            title = 'Confirm Action',
            message = 'Are you sure you want to proceed?',
            confirmText = 'Confirm',
            cancelText = 'Cancel',
            type = 'warning', // 'warning', 'danger', 'info'
            onConfirm = () => {},
            onCancel = () => {}
        } = options;

        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay fade-in';
        overlay.style.cssText = `
            position: fixed;
            inset: 0;
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        `;

        // Icon and colors based on type
        const typeConfig = {
            warning: { icon: '⚠️', color: '#f59e0b' },
            danger: { icon: '🗑️', color: '#ef4444' },
            info: { icon: 'ℹ️', color: '#06b6d4' }
        };

        const config = typeConfig[type] || typeConfig.info;

        // Create modal
        const modal = document.createElement('div');
        modal.className = 'modal-content slide-up';
        modal.style.maxWidth = '450px';
        modal.innerHTML = `
            <div style="text-align: center; margin-bottom: 24px;">
                <div style="
                    width: 64px;
                    height: 64px;
                    margin: 0 auto 16px;
                    background: ${config.color}15;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 2rem;
                ">${config.icon}</div>
                <h2 style="
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: var(--text-primary);
                    margin-bottom: 8px;
                ">${title}</h2>
                <p style="
                    color: var(--text-secondary);
                    font-size: 0.9375rem;
                    line-height: 1.6;
                ">${message}</p>
            </div>
            <div style="display: flex; gap: 12px; justify-content: center;">
                <button class="btn-secondary" id="cancelBtn" style="
                    padding: 0.75rem 2rem;
                    min-width: 120px;
                ">${cancelText}</button>
                <button class="btn-${type === 'danger' ? 'danger' : 'primary'}" id="confirmBtn" style="
                    padding: 0.75rem 2rem;
                    min-width: 120px;
                ">${confirmText}</button>
            </div>
        `;

        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        // Focus confirm button
        setTimeout(() => modal.querySelector('#confirmBtn').focus(), 100);

        // Handle confirm
        modal.querySelector('#confirmBtn').onclick = () => {
            console.log('[CONFIRM] User confirmed');
            overlay.style.animation = 'fadeOut 0.2s ease';
            setTimeout(() => overlay.remove(), 200);
            onConfirm();
            resolve(true);
        };

        // Handle cancel
        const handleCancel = () => {
            console.log('[CONFIRM] User cancelled');
            overlay.style.animation = 'fadeOut 0.2s ease';
            setTimeout(() => overlay.remove(), 200);
            onCancel();
            resolve(false);
        };

        modal.querySelector('#cancelBtn').onclick = handleCancel;
        overlay.onclick = (e) => {
            if (e.target === overlay) handleCancel();
        };

        // ESC key to cancel
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                handleCancel();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);
    });
}

// Fade out animation
const fadeOutStyle = document.createElement('style');
fadeOutStyle.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
`;
document.head.appendChild(fadeOutStyle);

// Loading Overlay
function showLoadingOverlay(message = 'Loading...') {
    console.log('[LOADING] Showing overlay:', message);

    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'modal-overlay fade-in';
    overlay.innerHTML = `
        <div style="text-align: center;">
            <div class="spinner" style="margin: 0 auto 20px;"></div>
            <div style="
                color: white;
                font-size: 1rem;
                font-weight: 600;
                text-shadow: 0 2px 4px rgba(0,0,0,0.2);
            ">${message}</div>
        </div>
    `;
    document.body.appendChild(overlay);
    return overlay;
}

function hideLoadingOverlay() {
    console.log('[LOADING] Hiding overlay');
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.animation = 'fadeOut 0.2s ease';
        setTimeout(() => overlay.remove(), 200);
    }
}

// Skeleton Loader Component
function createSkeletonLoader(type = 'card', count = 1) {
    const skeletons = {
        card: () => `
            <div class="skeleton" style="height: 200px; border-radius: 16px; margin-bottom: 16px;"></div>
        `,
        text: () => `
            <div class="skeleton" style="height: 20px; width: 100%; margin-bottom: 12px; border-radius: 8px;"></div>
        `,
        circle: () => `
            <div class="skeleton" style="width: 48px; height: 48px; border-radius: 50%;"></div>
        `,
        message: () => `
            <div style="display: flex; gap: 12px; margin-bottom: 20px;">
                <div class="skeleton" style="width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0;"></div>
                <div style="flex: 1;">
                    <div class="skeleton" style="height: 16px; width: 30%; margin-bottom: 8px; border-radius: 8px;"></div>
                    <div class="skeleton" style="height: 60px; width: 100%; border-radius: 12px;"></div>
                </div>
            </div>
        `
    };

    const html = Array(count).fill(skeletons[type]()).join('');
    return html;
}

// Pagination Helper
function createPagination(currentPage, totalPages, onPageChange) {
    console.log('[PAGINATION] Creating pagination:', currentPage, '/', totalPages);

    const container = document.createElement('div');
    container.className = 'pagination';

    // Previous button
    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.textContent = '‹ Previous';
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => onPageChange(currentPage - 1);
    container.appendChild(prevBtn);

    // Page numbers
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);

    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }

    if (startPage > 1) {
        const firstBtn = document.createElement('button');
        firstBtn.className = 'pagination-btn';
        firstBtn.textContent = '1';
        firstBtn.onclick = () => onPageChange(1);
        container.appendChild(firstBtn);

        if (startPage > 2) {
            const dots = document.createElement('span');
            dots.textContent = '...';
            dots.style.cssText = 'padding: 0.5rem 0.75rem; color: var(--text-muted);';
            container.appendChild(dots);
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `pagination-btn ${i === currentPage ? 'active' : ''}`;
        pageBtn.textContent = i;
        pageBtn.onclick = () => onPageChange(i);
        container.appendChild(pageBtn);
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const dots = document.createElement('span');
            dots.textContent = '...';
            dots.style.cssText = 'padding: 0.5rem 0.75rem; color: var(--text-muted);';
            container.appendChild(dots);
        }

        const lastBtn = document.createElement('button');
        lastBtn.className = 'pagination-btn';
        lastBtn.textContent = totalPages;
        lastBtn.onclick = () => onPageChange(totalPages);
        container.appendChild(lastBtn);
    }

    // Next button
    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.textContent = 'Next ›';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = () => onPageChange(currentPage + 1);
    container.appendChild(nextBtn);

    return container;
}

// Export functions for global use
window.showConfirm = showConfirmDialog;
window.showLoading = showLoadingOverlay;
window.hideLoading = hideLoadingOverlay;
window.createSkeleton = createSkeletonLoader;
window.createPagination = createPagination;

console.log('[UI-UTILS] Loaded successfully');
