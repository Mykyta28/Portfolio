document.addEventListener('DOMContentLoaded', function() {
    const messages = document.querySelectorAll('.message-alert');

    messages.forEach((msg, index) => {
        // Auto remove after animation completes (3.5s)
        setTimeout(() => {
            if (msg.parentElement) {
                msg.remove();

                // Remove container if empty
                const container = document.querySelector('.messages-container');
                if (container && container.children.length === 0) {
                    container.remove();
                }
            }
        }, 3500);

        // Manual close button
        const closeBtn = msg.querySelector('.close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                msg.style.animation = 'fadeOut 0.4s ease forwards';
                setTimeout(() => {
                    msg.remove();

                    const container = document.querySelector('.messages-container');
                    if (container && container.children.length === 0) {
                        container.remove();
                    }
                }, 400);
            });
        }
    });
});