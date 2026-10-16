/*
 * Criptografia ponta-a-ponta das mensagens (E2E).
 *
 * Cada usuário tem um par de chaves ECDH P-256 gerado no próprio navegador.
 * A chave privada fica apenas no dispositivo (IndexedDB) e nunca é enviada ao
 * servidor; só a chave pública é publicada. A chave da conversa é derivada
 * (ECDH + HKDF) entre as duas chaves públicas, de modo que só os dois
 * participantes conseguem cifrar/decifrar. O servidor guarda apenas ciphertext.
 */
(() => {
    const DB_NAME = 'etewitter-e2e';
    const STORE = 'keys';
    const KEY_ID = 'identity';
    const encoder = new TextEncoder();
    const decoder = new TextDecoder();
    const TEXT_PREFIX = 'e1:';

    function openDb() {
        return new Promise((resolve, reject) => {
            if (!('indexedDB' in window)) return reject(new Error('IndexedDB indisponível'));
            const request = indexedDB.open(DB_NAME, 1);
            request.onupgradeneeded = () => {
                if (!request.result.objectStoreNames.contains(STORE)) {
                    request.result.createObjectStore(STORE);
                }
            };
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    function idbGet(key) {
        return openDb().then((db) => new Promise((resolve, reject) => {
            const tx = db.transaction(STORE, 'readonly').objectStore(STORE).get(key);
            tx.onsuccess = () => resolve(tx.result);
            tx.onerror = () => reject(tx.error);
        }));
    }

    function idbPut(key, value) {
        return openDb().then((db) => new Promise((resolve, reject) => {
            const tx = db.transaction(STORE, 'readwrite').objectStore(STORE).put(value, key);
            tx.onsuccess = () => resolve();
            tx.onerror = () => reject(tx.error);
        }));
    }

    function toBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.length; i += 1) binary += String.fromCharCode(bytes[i]);
        return btoa(binary);
    }

    function fromBase64(text) {
        const binary = atob(text);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
        return bytes;
    }

    const pairPromises = new Map();

    // O par de chaves é POR USUÁRIO. Sem isso, duas contas no mesmo navegador
    // compartilham a mesma chave e bagunçam as chaves publicadas no servidor.
    function currentUserId() {
        const id = (typeof window !== 'undefined' && window.__E2E_USER_ID__) ? window.__E2E_USER_ID__ : '';
        return id ? String(id) : 'shared';
    }

    function getPair() {
        const id = currentUserId();
        if (!pairPromises.has(id)) {
            const promise = (async () => {
                const stored = await idbGet(KEY_ID + ':' + id);
                if (stored && stored.privateKey && stored.publicKey) return stored;
                // Migração: se já existe a chave antiga ("identity"), adota-a para
                // este usuário — mas só se o servidor ainda publicar essa chave
                // para ele. Assim não colidimos a chave com outra conta.
                try {
                    const legacy = await idbGet(KEY_ID);
                    if (legacy && legacy.privateKey && legacy.publicKey) {
                        const legacyStr = JSON.stringify(await crypto.subtle.exportKey('jwk', legacy.publicKey));
                        const response = await fetch(`/messages/keys/${id}/`, {credentials: 'same-origin'});
                        if (response.ok && (await response.json()).public_key === legacyStr) {
                            try { await idbPut(KEY_ID + ':' + id, legacy); } catch (err) { /* modo efêmero */ }
                            return legacy;
                        }
                    }
                } catch (err) { /* segue para gerar uma chave nova */ }
                const pair = await crypto.subtle.generateKey(
                    {name: 'ECDH', namedCurve: 'P-256'}, true, ['deriveKey'],
                );
                try { await idbPut(KEY_ID + ':' + id, pair); } catch (err) { /* modo efêmero */ }
                return pair;
            })();
            pairPromises.set(id, promise);
        }
        return pairPromises.get(id);
    }

    async function publicKeyString() {
        const pair = await getPair();
        const jwk = await crypto.subtle.exportKey('jwk', pair.publicKey);
        return JSON.stringify(jwk);
    }

    const sessionKeys = new Map();

    function sessionKeyFor(peerPublicKey) {
        if (!peerPublicKey) return Promise.resolve(null);
        let jwk;
        try {
            jwk = typeof peerPublicKey === 'string' ? JSON.parse(peerPublicKey) : peerPublicKey;
        } catch (err) {
            return Promise.resolve(null);
        }
        const cacheKey = JSON.stringify(jwk);
        if (sessionKeys.has(cacheKey)) return sessionKeys.get(cacheKey);
        const promise = (async () => {
            const pair = await getPair();
            const peerKey = await crypto.subtle.importKey(
                'jwk', jwk, {name: 'ECDH', namedCurve: 'P-256'}, false, [],
            );
            return crypto.subtle.deriveKey(
                {name: 'ECDH', public: peerKey},
                pair.privateKey,
                {name: 'AES-GCM', length: 256},
                false,
                ['encrypt', 'decrypt'],
            );
        })().catch(() => null);
        sessionKeys.set(cacheKey, promise);
        return promise;
    }

    async function encryptText(key, text) {
        if (!key) return text;
        const iv = crypto.getRandomValues(new Uint8Array(12));
        const cipher = await crypto.subtle.encrypt({name: 'AES-GCM', iv}, key, encoder.encode(text));
        return TEXT_PREFIX + toBase64(iv) + ':' + toBase64(cipher);
    }

    async function decryptText(key, payload) {
        if (typeof payload !== 'string' || !payload.startsWith(TEXT_PREFIX)) return payload;
        if (!key) return payload; // ainda sem chave: mantém o ciphertext para tentar depois
        const parts = payload.slice(TEXT_PREFIX.length).split(':');
        if (parts.length !== 2) return null;
        try {
            const plain = await crypto.subtle.decrypt(
                {name: 'AES-GCM', iv: fromBase64(parts[0])}, key, fromBase64(parts[1]),
            );
            return decoder.decode(plain);
        } catch (err) {
            return null; // falhou (chave errada/desatualizada): quem chama decide
        }
    }

    async function encryptBytes(key, arrayBuffer) {
        const iv = crypto.getRandomValues(new Uint8Array(12));
        const cipher = await crypto.subtle.encrypt({name: 'AES-GCM', iv}, key, arrayBuffer);
        const out = new Uint8Array(iv.length + cipher.byteLength);
        out.set(iv, 0);
        out.set(new Uint8Array(cipher), iv.length);
        return out;
    }

    async function decryptBytes(key, arrayBuffer) {
        const bytes = new Uint8Array(arrayBuffer);
        return crypto.subtle.decrypt(
            {name: 'AES-GCM', iv: bytes.slice(0, 12)}, key, bytes.slice(12),
        );
    }

    async function uploadPublicKey(csrfToken) {
        try {
            const jwk = await publicKeyString();
            const cacheKey = 'etewitter-public-key:' + currentUserId();
            if (localStorage.getItem(cacheKey) === jwk) {
                // Mesmo em cache local, confirma que o servidor ainda tem esta
                // chave (outra conta/dispositivo pode tê-la sobrescrito).
                try {
                    const response = await fetch(`/messages/keys/${currentUserId()}/`, {credentials: 'same-origin'});
                    if (response.ok && (await response.json()).public_key === jwk) return jwk;
                } catch (err) {
                    return jwk;
                }
            }
            const saved = await fetch('/messages/keys/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken},
                credentials: 'same-origin',
                body: JSON.stringify({public_key: jwk}),
            });
            if (saved.ok) localStorage.setItem(cacheKey, jwk);
            return jwk;
        } catch (err) {
            return null;
        }
    }

    window.E2E = {
        getPair,
        publicKeyString,
        sessionKeyFor,
        encryptText,
        decryptText,
        encryptBytes,
        decryptBytes,
        toBase64,
        fromBase64,
        uploadPublicKey,
        textPrefix: TEXT_PREFIX,
    };
})();
