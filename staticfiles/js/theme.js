/*
 * Alternância de tema (claro/escuro).
 *
 * O tema é aplicado o quanto antes por um script inline no <head> (para não
 * "piscar"); aqui cuidamos do botão, da persistência e de reagir à preferência
 * do sistema quando o usuário ainda não escolheu manualmente.
 */
(() => {
    const STORE_KEY = 'etewitter-theme';

    function apply(theme) {
        document.documentElement.dataset.theme = theme;
        document.querySelectorAll('#theme-toggle').forEach((button) => {
            button.setAttribute('aria-checked', theme === 'dark' ? 'true' : 'false');
        });
    }

    function current() {
        return document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
    }

    document.addEventListener('click', (event) => {
        if (!event.target.closest('#theme-toggle')) return;
        const next = current() === 'dark' ? 'light' : 'dark';
        try { localStorage.setItem(STORE_KEY, next); } catch (err) { /* ignora */ }
        apply(next);
    });

    if (window.matchMedia) {
        const media = window.matchMedia('(prefers-color-scheme: dark)');
        const onChange = (event) => {
            let saved = null;
            try { saved = localStorage.getItem(STORE_KEY); } catch (err) { /* ignora */ }
            if (!saved) apply(event.matches ? 'dark' : 'light');
        };
        if (media.addEventListener) media.addEventListener('change', onChange);
    }

    window.addEventListener('DOMContentLoaded', () => apply(current()));
})();
