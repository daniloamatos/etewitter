(function () {
    document.addEventListener('click', async (event) => {
        const button = event.target.closest('[data-expand-replies]');
        if (!button) return;
        event.preventDefault();
        event.stopPropagation();

        const expanded = document.getElementById(button.getAttribute('aria-controls'));
        if (expanded) {
            expanded.hidden = !expanded.hidden;
            const isExpanded = !expanded.hidden;
            button.setAttribute('aria-expanded', String(isExpanded));
            button.textContent = isExpanded ? button.dataset.lessLabel : button.dataset.moreLabel;
            return;
        }

        button.disabled = true;
        try {
            const response = await fetch(button.dataset.expandReplies, {credentials: 'same-origin'});
            if (!response.ok) throw new Error('Could not load replies');
            const template = document.createElement('template');
            template.innerHTML = await response.text();
            const replies = template.content.querySelector('.expanded-replies');
            if (!replies || !replies.children.length) {
                button.remove();
                return;
            }
            button.after(replies);
            button.setAttribute('aria-expanded', 'true');
            button.textContent = button.dataset.lessLabel;
        } catch (error) {
            button.disabled = false;
        }
    });
})();
