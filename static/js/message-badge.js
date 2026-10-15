(() => {
    let socket;
    let retry;
    let stopped = false;
    function connect() {
        if (stopped || (socket && socket.readyState < WebSocket.CLOSING)) return;
        socket = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/notifications/`);
        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'unread_messages') {
                document.querySelectorAll('.messages-nav').forEach((link) => {
                    link.querySelector('.unread-dot').hidden = !data.unread;
                    link.setAttribute('aria-label', data.unread ? 'Mensagens não lidas' : 'Mensagens');
                });
            } else if (data.type === 'notification') {
                window.dispatchEvent(new CustomEvent('site-notification', {detail: data}));
            }
        };
        socket.onclose = () => { if (!stopped) retry = setTimeout(connect, 2000); };
    }
    window.addEventListener('pagehide', () => { stopped = true; clearTimeout(retry); socket?.close(); });
    window.addEventListener('pageshow', () => { stopped = false; connect(); });
    connect();
})();
