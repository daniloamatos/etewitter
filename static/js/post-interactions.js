(() => {
    const interactive = 'a,button,form,input,textarea,select,label,summary,details,[contenteditable="true"],[role="button"]';
    const isSavedPage = window.location.pathname === '/saveditems/';

    // Lê o atributo action diretamente (form.action pode ser "clobbado" por
    // um input/button com name="action" dentro do formulário).
    function formAction(form) {
        return form.getAttribute('action') || '';
    }

    // Limite e formatos de imagem aceitos (mesmos valores de main/image_utils.py).
    // 5 MB é o limite padrão do X/Twitter para fotos.
    const MAX_IMAGE_SIZE = 5 * 1024 * 1024;
    const MAX_IMAGE_SIZE_MB = 5;
    const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    const ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp'];

    // Pré-visualização da imagem anexada em qualquer compositor (tweet,
    // resposta, chat, etc.). O compositor deve conter um elemento ".composer-preview".
    function setupImagePreviews() {
        document.querySelectorAll('form input[type="file"]').forEach((input) => {
            const form = input.closest('form');
            if (!form) return;
            const box = form.querySelector('.composer-preview');
            if (!box) return;
            const img = box.querySelector('img');
            const removeBtn = box.querySelector('[data-remove-preview]');

            // Caixa de erro logo abaixo da pré-visualização.
            let errorBox = form.querySelector('.composer-image-error');
            if (!errorBox) {
                errorBox = document.createElement('p');
                errorBox.className = 'composer-image-error';
                errorBox.hidden = true;
                box.parentNode.insertBefore(errorBox, box.nextSibling);
            }

            const imageError = (file) => {
                if (!file) return '';
                const ext = (file.name.split('.').pop() || '').toLowerCase();
                const typeOk = ALLOWED_IMAGE_TYPES.includes(file.type)
                    || ALLOWED_IMAGE_EXTENSIONS.includes(ext);
                if (!typeOk) {
                    return 'Formato não suportado. Use JPG, PNG, GIF ou WEBP.';
                }
                if (file.size > MAX_IMAGE_SIZE) {
                    return `A imagem tem ${(file.size / 1048576).toFixed(1)} MB. O limite é ${MAX_IMAGE_SIZE_MB} MB.`;
                }
                return '';
            };

            const update = () => {
                let file = input.files && input.files[0];
                const error = imageError(file);
                if (error) {
                    input.value = '';
                    file = null;
                    errorBox.textContent = error;
                    errorBox.hidden = false;
                } else {
                    errorBox.hidden = true;
                    errorBox.textContent = '';
                }
                if (img) {
                    if (file) {
                        if (img.dataset.objectUrl) URL.revokeObjectURL(img.dataset.objectUrl);
                        const url = URL.createObjectURL(file);
                        img.dataset.objectUrl = url;
                        img.src = url;
                    } else {
                        if (img.dataset.objectUrl) {
                            URL.revokeObjectURL(img.dataset.objectUrl);
                            delete img.dataset.objectUrl;
                        }
                        img.removeAttribute('src');
                    }
                }
                box.hidden = !file;
            };

            input.addEventListener('change', update);
            if (removeBtn) {
                removeBtn.addEventListener('click', () => {
                    input.value = '';
                    update();
                });
            }
            update();
        });
    }

    setupImagePreviews();

    // Helper: envia interação via AJAX e atualiza o frontend
    function handleInteraction(form, event) {
        event.preventDefault();
        event.stopPropagation();

        const formData = new FormData(form);
        const button = form.querySelector('button[type="submit"]');
        const actionUrl = formAction(form);

        fetch(actionUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrfmiddlewaretoken') || ''
            },
            credentials: 'same-origin'
        })
        .then(async (response) => {
            if (response.status === 204) {
                // Sem JSON: toggle visual com base no estado atual
                if (actionUrl.includes('/save/')) {
                    const currentlySaved = button.classList.contains('is-saved');
                    button.classList.toggle('is-saved');
                    const label = currentlySaved ? 'Salvar' : 'Remover dos salvos';
                    button.setAttribute('aria-label', label);
                    button.setAttribute('title', label);

                    // Se está na página de salvos e removeu, some o card do DOM
                    if (isSavedPage && currentlySaved) {
                        const card = form.closest('article.tweet-card, article.search-reply-card, article.reply-tweet-card');
                        if (card) card.remove();
                    }
                }
                return;
            }
            const data = await response.json();

            if (actionUrl.includes('/likereply/') || actionUrl.includes('/like/')) {
                button.classList.toggle('is-liked', data.liked);
                const span = button.querySelector('span');
                if (span) span.textContent = data.count;
            } else if (actionUrl.includes('/retweet')) {
                button.classList.toggle('is-retweeted', data.retweeted);
                const span = button.querySelector('span');
                if (span) span.textContent = data.count;
            } else if (actionUrl.includes('/save/')) {
                button.classList.toggle('is-saved', data.saved);
                const label = data.saved ? 'Remover dos salvos' : 'Salvar';
                button.setAttribute('aria-label', label);
                button.setAttribute('title', label);

                // Se está na página de salvos e removeu, some o card do DOM
                if (isSavedPage && !data.saved) {
                    const card = form.closest('article.tweet-card, article.search-reply-card, article.reply-tweet-card');
                    if (card) card.remove();
                }
            }
        })
        .catch((err) => {
            console.error('Erro na interação:', err);
        });
    }

    document.addEventListener('click', (event) => {
        const form = event.target.closest('form.inline-form');
        if (form) {
            const action = formAction(form);
            if (
                action.includes('/like/') ||
                action.includes('/likereply/') ||
                action.includes('/retweet') ||
                action.includes('/save/')
            ) {
                handleInteraction(form, event);
                return;
            }
        }

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
