(() => {
    const interactive = 'a,button,form,input,textarea,select,label,summary,details,[contenteditable="true"],[role="button"]';
    document.addEventListener('click', (event) => {
        const deleteButton = event.target.closest('[data-delete-id]');
        const deleteDialog = document.getElementById('post-delete-dialog');
        if (deleteButton) {
            deleteButton.closest('details')?.removeAttribute('open');
            deleteDialog.querySelector('[name="tweetid"]').value = deleteButton.dataset.deleteId;
            deleteDialog.querySelector('[name="content_type"]').value = deleteButton.dataset.deleteKind;
            deleteDialog.querySelector('[name="next"]').value = window.location.pathname === deleteButton.dataset.deleteUrl
                ? deleteButton.dataset.parentUrl : window.location.pathname + window.location.search;
            deleteDialog.showModal();
            deleteDialog.querySelector('[data-close-delete]').focus();
            return;
        }
        if (event.target.closest('[data-close-delete]')) { deleteDialog.close(); return; }
        const reportButton = event.target.closest('[data-report-id]');
        const dialog = document.getElementById('post-report-dialog');
        if (reportButton) {
            reportButton.closest('details')?.removeAttribute('open');
            dialog.querySelector('[name="tweetid"]').value = reportButton.dataset.reportId;
            dialog.querySelector('[name="content_type"]').value = reportButton.dataset.reportKind;
            dialog.querySelector('[name="reason"]').value = '';
            dialog.showModal();
            dialog.querySelector('[name="reason"]').focus();
            return;
        }
        if (event.target.closest('[data-close-report]')) { dialog.close(); return; }
        document.querySelectorAll('.post-options[open]').forEach((menu) => {
            if (!menu.contains(event.target)) menu.removeAttribute('open');
        });
        const card = event.target.closest('[data-card-url]');
        if (!card || event.defaultPrevented || event.target.closest(interactive) || window.getSelection()?.toString()) return;
        if (event.ctrlKey || event.metaKey || event.shiftKey) {
            window.open(card.dataset.cardUrl, '_blank', 'noopener');
        } else {
            window.location.assign(card.dataset.cardUrl);
        }
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            document.querySelectorAll('.post-options[open]').forEach((menu) => {
                menu.removeAttribute('open');
                menu.querySelector('summary').focus();
            });
        }
        const card = event.target.closest('[data-card-url]');
        if (card && event.target === card && (event.key === 'Enter' || event.key === ' ')) {
            event.preventDefault();
            window.location.assign(card.dataset.cardUrl);
        }
    });
})();
