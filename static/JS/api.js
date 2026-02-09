// Lightweight API client for consistent fetch() handling across the app.
// Provides: apiGet, apiPostJson, apiPostForm, apiRequest

(function () {
    async function safeParseJson(response) {
        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('application/json')) return null;
        try {
            return await response.json();
        } catch (_) {
            return null;
        }
    }

    function unwrapPayload(payload) {
        if (payload && typeof payload === 'object' && payload.status && Object.prototype.hasOwnProperty.call(payload, 'data')) {
            return payload.data;
        }
        return payload;
    }

    function extractMessage(payload, fallback) {
        if (!payload) return fallback;
        if (typeof payload === 'string') return payload;
        return payload.message || payload.error || fallback;
    }

    async function apiRequest(url, options) {
        const opts = options || {};
        const response = await fetch(url, opts);

        const payload = (await safeParseJson(response)) ?? { message: await response.text().catch(() => '') };
        const data = unwrapPayload(payload);

        if (!response.ok) {
            const message = extractMessage(payload, `Request failed (${response.status})`);
            const err = new Error(message);
            err.status = response.status;
            err.payload = payload;
            throw err;
        }

        return { data, payload, response };
    }

    async function apiGet(url) {
        const { data } = await apiRequest(url, { method: 'GET' });
        return data;
    }

    async function apiPostJson(url, json) {
        const { data } = await apiRequest(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(json ?? {})
        });
        return data;
    }

    async function apiPostForm(url, formData) {
        const { data } = await apiRequest(url, {
            method: 'POST',
            body: formData
        });
        return data;
    }

    function getApiErrorMessage(error, fallback) {
        if (!error) return fallback || 'Something went wrong';
        return error.message || fallback || 'Something went wrong';
    }

    window.apiRequest = apiRequest;
    window.apiGet = apiGet;
    window.apiPostJson = apiPostJson;
    window.apiPostForm = apiPostForm;
    window.getApiErrorMessage = getApiErrorMessage;
})();
