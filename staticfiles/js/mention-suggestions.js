(function () {
    const fields = document.querySelectorAll('.composer-form textarea[name="tweet"], .reply-form input[name="body"], .search-form input[name="query"]');
    fields.forEach((field, index) => {
        const isSearch = field.name === 'query';
        const wrapper = isSearch ? field.closest('.search-form') : field.parentElement;
        if (!wrapper) return;
        wrapper.classList.add('mention-suggestions-anchor');
        const list = document.createElement('div');
        list.className = 'mention-suggestions';
        list.id = `mention-suggestions-${index}`;
        list.setAttribute('role', 'listbox');
        list.hidden = true;
        wrapper.append(list);
        field.setAttribute('aria-autocomplete', 'list');
        field.setAttribute('aria-controls', list.id);
        field.setAttribute('aria-expanded', 'false');

        let matches = [];
        let selected = 0;
        let token = null;
        let requestId = 0;
        let timer;
        let controller;

        function currentToken() {
            const caret = field.selectionStart;
            if (caret === null || (isSearch && caret !== field.value.length)) return null;
            const before = field.value.slice(0, caret);
            const found = /(?:^|[^\w@])@([A-Za-z0-9]{0,25})$/.exec(before);
            if (!found) return null;
            return {start: caret - found[1].length - 1, end: caret, query: found[1]};
        }

        function close() {
            clearTimeout(timer);
            controller?.abort();
            requestId++;
            token = null;
            matches = [];
            list.hidden = true;
            list.replaceChildren();
            field.setAttribute('aria-expanded', 'false');
            field.removeAttribute('aria-activedescendant');
        }

        function highlight() {
            [...list.children].forEach((option, i) => {
                option.setAttribute('aria-selected', String(i === selected));
                option.classList.toggle('is-selected', i === selected);
            });
            const active = list.children[selected];
            if (active) {
                field.setAttribute('aria-activedescendant', active.id);
                active.scrollIntoView({block: 'nearest'});
            }
        }

        function choose(user) {
            if (isSearch) {
                window.location.assign(`/${encodeURIComponent(user.username)}/`);
                return;
            }
            const current = currentToken();
            if (!current) return close();
            const insertion = `@${user.username} `;
            field.setRangeText(insertion, current.start, current.end, 'end');
            field.dispatchEvent(new Event('input', {bubbles: true}));
            close();
            field.focus();
        }

        function show(users) {
            matches = users;
            selected = 0;
            list.replaceChildren();
            users.forEach((user, i) => {
                const option = document.createElement('button');
                option.type = 'button';
                option.id = `${list.id}-option-${i}`;
                option.className = 'mention-suggestion';
                option.setAttribute('role', 'option');
                const avatar = document.createElement('img');
                avatar.src = user.avatar;
                avatar.alt = '';
                const identity = document.createElement('span');
                const name = document.createElement('strong');
                name.textContent = user.name;
                const handle = document.createElement('small');
                handle.textContent = `@${user.username}`;
                identity.append(name, handle);
                option.append(avatar, identity);
                option.addEventListener('mouseenter', () => { selected = i; highlight(); });
                option.addEventListener('mousedown', event => event.preventDefault());
                option.addEventListener('click', () => choose(user));
                list.append(option);
            });
            list.hidden = users.length === 0;
            field.setAttribute('aria-expanded', String(users.length > 0));
            if (users.length) highlight();
            else field.removeAttribute('aria-activedescendant');
        }

        function update() {
            clearTimeout(timer);
            controller?.abort();
            const current = currentToken();
            if (!current) return close();
            token = current;
            const thisRequest = ++requestId;
            timer = setTimeout(async () => {
                controller = new AbortController();
                try {
                    const response = await fetch(`/mention-suggestions/?q=${encodeURIComponent(current.query)}`, {
                        credentials: 'same-origin', signal: controller.signal,
                    });
                    if (!response.ok || response.redirected) return close();
                    const data = await response.json();
                    if (thisRequest === requestId && currentToken()?.query === current.query) show(data.users);
                } catch (error) {
                    if (error.name !== 'AbortError') close();
                }
            }, 120);
        }

        field.addEventListener('input', update);
        field.addEventListener('click', update);
        field.addEventListener('keyup', event => {
            if (['ArrowUp', 'ArrowDown', 'Enter', 'Escape'].includes(event.key)) return;
            if (!list.hidden && !currentToken()) close();
        });
        field.addEventListener('keydown', event => {
            if (list.hidden || !matches.length) {
                if (event.key === 'Escape') close();
                return;
            }
            if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                event.preventDefault();
                selected = (selected + (event.key === 'ArrowDown' ? 1 : -1) + matches.length) % matches.length;
                highlight();
            } else if (event.key === 'Enter') {
                event.preventDefault();
                choose(matches[selected]);
            } else if (event.key === 'Escape') {
                event.preventDefault();
                close();
            }
        });
        field.addEventListener('blur', () => setTimeout(() => {
            if (!wrapper.contains(document.activeElement)) close();
        }, 120));
        field.closest('form')?.addEventListener('submit', close);
    });
})();
