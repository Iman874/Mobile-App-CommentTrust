<!-- Notification Container -->
<div id="notificationContainer" style="position: fixed; top: 20px; right: 20px; z-index: 9999; max-width: 450px; pointer-events: auto;">
    <!-- Notifications akan ditambahkan dinamis di sini -->
</div>

<script>
/**
 * Notification System - Reusable untuk seluruh aplikasi dengan Tailwind CSS
 * Usage:
 * notificationSystem.success('Success message');
 * notificationSystem.error('Error message', 'ERROR_CODE', 5000);
 * notificationSystem.warning('Warning message');
 * notificationSystem.info('Info message');
 */
class NotificationSystem {
    constructor() {
        this.container = document.getElementById('notificationContainer');
        this.animationDuration = 300;
    }

    /**
     * Show notification
     * @param {string} message - Notification message
     * @param {string} type - 'success', 'danger', 'warning', 'info'
     * @param {number} duration - Auto-close duration in ms (0 = no auto-close)
     */
    show(message, type = 'info', duration = 5000) {
        const id = 'notification-' + Date.now() + Math.random();
        
        // Tailwind color mapping
        const colors = {
            'success': { 
                bg: 'bg-green-500', 
                text: 'text-white', 
                border: 'border-green-600',
                icon: '✓' 
            },
            'danger': { 
                bg: 'bg-red-500', 
                text: 'text-white', 
                border: 'border-red-600',
                icon: '✕' 
            },
            'warning': { 
                bg: 'bg-yellow-500', 
                text: 'text-gray-900', 
                border: 'border-yellow-600',
                icon: '⚠' 
            },
            'info': { 
                bg: 'bg-blue-500', 
                text: 'text-white', 
                border: 'border-blue-600',
                icon: 'ℹ' 
            }
        };

        const color = colors[type] || colors['info'];

        // Create notification element
        const notifEl = document.createElement('div');
        notifEl.id = id;
        notifEl.className = `${color.bg} ${color.text} px-4 py-3 rounded-lg shadow-lg border-l-4 ${color.border} flex items-start gap-3 mb-3`;
        notifEl.style.cssText = 'animation: slideInRight 0.3s ease-in-out;';
        notifEl.innerHTML = `
            <span style="font-weight: 700; font-size: 18px; margin-top: 2px; flex-shrink: 0;">${color.icon}</span>
            <span style="flex: 1; line-height: 1.5;">${message}</span>
            <button onclick="notificationSystem.remove('${id}')" class="${color.text} hover:opacity-70 transition flex-shrink-0 font-bold text-xl" style="background: none; border: none; cursor: pointer; padding: 0; margin: -4px -4px 0 0;">×</button>
        `;

        this.container.appendChild(notifEl);

        // Auto-close if duration > 0
        if (duration > 0) {
            setTimeout(() => this.remove(id), duration);
        }

        return id;
    }

    /**
     * Remove notification
     */
    remove(id) {
        const notif = document.getElementById(id);
        if (!notif) return;

        notif.style.animation = 'slideOutRight 0.3s ease-in-out forwards';
        setTimeout(() => notif.remove(), this.animationDuration);
    }

    /**
     * Shortcut methods
     */
    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    }

    error(message, errorCode = null, duration = 6000) {
        let fullMessage = message;
        if (errorCode) {
            fullMessage += ` <small style="display: block; margin-top: 6px; opacity: 0.95; font-size: 0.9em;">(Error: ${errorCode})</small>`;
        }
        return this.show(fullMessage, 'danger', duration);
    }

    warning(message, duration = 5000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }

    /**
     * Clear all notifications
     */
    clearAll() {
        this.container.innerHTML = '';
    }
}

// Initialize global notification system
const notificationSystem = new NotificationSystem();
</script>

<style>
@keyframes slideInRight {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOutRight {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(400px);
        opacity: 0;
    }
}

#notificationContainer div {
    min-height: 60px;
    animation-fill-mode: forwards;
}

#notificationContainer div small {
    opacity: 0.95;
}

/* Responsive */
@media (max-width: 640px) {
    #notificationContainer {
        max-width: calc(100% - 20px);
        left: 10px !important;
        right: 10px !important;
    }
}
</style>
