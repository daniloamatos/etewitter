(function () {
    const popup = document.getElementById('profile-preview');
    if (!popup || document.body.classList.contains('profile-page')) return;

    let activeLink = null;
    let openTimer = null;
    let closeTimer = null;
    let requestNumber = 0;

    function profileLink(node) {
        const link = node.closest && node.closest('a[href]');
        if (!link || (!link.closest('.main-column') && !link.classList.contains('sidebar-profile-link'))) return null;
        if (!link.matches('.sidebar-profile-link, .search-person, .profile-avatar-link, .profile-handle-link, .retweet-label a') &&
            !link.querySelector('.avatar, strong') && !link.textContent.trim().startsWith('@')) return null;
        const url = new URL(link.href, location.href);
        if (url.origin !== location.origin || !/^\/[a-zA-Z0-9]{4,25}\/$/.test(url.pathname)) return null;
        return link;
    }

    function hide() {
        clearTimeout(openTimer);
        clearTimeout(closeTimer);
        activeLink = null;
        requestNumber++;
        popup.hidden = true;
        popup.replaceChildren();
    }

    function scheduleClose() {
        clearTimeout(closeTimer);
        closeTimer = setTimeout(hide, 220);
    }

    function element(tag, className, content) {
        const node = document.createElement(tag);
        node.className = className;
        if (content != null) node.textContent = content;
        return node;
    }

    function position(link) {
        const rect = link.getBoundingClientRect();
        const width = popup.offsetWidth;
        const height = popup.offsetHeight;
        const left = Math.max(8, Math.min(rect.left, innerWidth - width - 8));
        const below = rect.bottom + 10;
        popup.style.left = `${left}px`;
        popup.style.top = `${below + height <= innerHeight - 8 ? below : Math.max(8, rect.top - height - 10)}px`;
    }

    function render(person, link) {
        popup.replaceChildren();
        const heading = element('div', 'profile-preview-heading');
        const avatar = element('img', 'avatar profile-preview-avatar');
        avatar.src = person.picture;
        avatar.alt = person.name;
        const avatarLink = element('a', 'profile-preview-avatar-link');
        avatarLink.href = `/${encodeURIComponent(person.username)}/`;
        avatarLink.append(avatar);
        const identity = element('div', 'profile-preview-identity');
        const name = element('a', 'profile-preview-name', person.name || person.username);
        name.href = `/${encodeURIComponent(person.username)}/`;
        const handle = element('a', 'profile-preview-handle', `@${person.username}`);
        handle.href = name.href;
        identity.append(name, handle);
        heading.append(avatarLink, identity);

        if (!person.is_self) {
            if (person.authenticated) {
                const follow = element('button', 'primary-button profile-preview-follow', person.is_following ? popup.dataset.unfollow : popup.dataset.follow);
                follow.type = 'button';
                follow.addEventListener('click', async () => {
                    follow.disabled = true;
                    try {
                        const body = new FormData();
                        body.set('userP', person.id);
                        const response = await fetch('/follow/', {
                            method: 'POST', body,
                            headers: {'X-CSRFToken': popup.dataset.csrf, 'X-Requested-With': 'XMLHttpRequest'},
                            credentials: 'same-origin',
                        });
                        if (!response.ok) throw new Error('follow failed');
                        const result = await response.json();
                        person.is_following = result.following;
                        person.followers = result.followers;
                        render(person, link);
                    } catch (error) {
                        follow.disabled = false;
                    }
                });
                heading.append(follow);
            } else {
                const login = element('a', 'primary-button profile-preview-follow', popup.dataset.login);
                login.href = '/login/';
                heading.append(login);
            }
        }
        popup.append(heading);
        if (person.follows_you) popup.append(element('span', 'profile-follows-you', popup.dataset.followsYou));
        if (person.bio) popup.append(element('p', 'profile-preview-bio', person.bio));
        const stats = element('div', 'profile-preview-stats');
        stats.append(element('span', '', ''), element('span', '', ''));
        stats.children[0].append(element('strong', '', person.following), ` ${popup.dataset.following}`);
        stats.children[1].append(element('strong', '', person.followers), ` ${popup.dataset.followers}`);
        popup.append(stats);
        popup.hidden = false;
        position(link);
    }

    async function open(link) {
        const id = ++requestNumber;
        const username = new URL(link.href).pathname.slice(1, -1);
        try {
            const response = await fetch(`/profile-preview/${encodeURIComponent(username)}/`, {credentials: 'same-origin'});
            if (!response.ok) return;
            const person = await response.json();
            if (id === requestNumber && activeLink === link) render(person, link);
        } catch (error) { /* O link continua funcionando quando a prévia falha. */ }
    }

    document.addEventListener('mouseover', (event) => {
        const link = profileLink(event.target);
        if (!link) return;
        clearTimeout(closeTimer);
        if (activeLink === link) return;
        if (activeLink && !popup.hidden && new URL(activeLink.href).pathname === new URL(link.href).pathname) {
            activeLink = link;
            position(link);
            return;
        }
        clearTimeout(openTimer);
        popup.hidden = true;
        activeLink = link;
        requestNumber++;
        openTimer = setTimeout(() => open(link), 300);
    });
    document.addEventListener('mouseout', (event) => {
        const link = profileLink(event.target);
        if (link && !link.contains(event.relatedTarget)) scheduleClose();
    });
    document.addEventListener('focusin', (event) => {
        const link = profileLink(event.target);
        if (!link) return;
        clearTimeout(closeTimer);
        clearTimeout(openTimer);
        activeLink = link;
        open(link);
    });
    document.addEventListener('focusout', (event) => {
        if (profileLink(event.target)) scheduleClose();
    });
    popup.addEventListener('mouseenter', () => clearTimeout(closeTimer));
    popup.addEventListener('mouseleave', scheduleClose);
    popup.addEventListener('focusin', () => clearTimeout(closeTimer));
    popup.addEventListener('focusout', scheduleClose);
    document.addEventListener('keydown', (event) => { if (event.key === 'Escape') hide(); });
    window.addEventListener('scroll', () => { if (!popup.hidden && activeLink) position(activeLink); }, true);
    window.addEventListener('resize', () => { if (!popup.hidden && activeLink) position(activeLink); });
})();
