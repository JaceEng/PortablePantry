"use strict";
/* Shared building blocks used by every page: errors, session, API client, HTML helpers. */

class ApiError extends Error {
    constructor(message, status = 0) {
    super(message);
    this.name = "ApiError";
    this.status = status; // 0 = network problem or timeout
    }
}

/** Everything the browser remembers about who is using the site (cleared when the tab closes). */
class Session {
    static #store = window.sessionStorage;

    static get token() { return Session.#store.getItem("token"); }
    static get username() { return Session.#store.getItem("username") || "chef"; }
    static get isLoggedIn() { return Boolean(Session.token); }
    static get isGuest() { return Session.#store.getItem("guest") === "1"; }
    static get hasWelcomed() { return Session.#store.getItem("welcomed") === "1"; }

    static markWelcomed() { Session.#store.setItem("welcomed", "1"); }
    static startGuest() { Session.#store.setItem("guest", "1"); }

    static logIn({ token, username }) {
    Session.#store.setItem("token", token);
    Session.#store.setItem("username", username);
    Session.#store.removeItem("welcomed");
    Session.#store.removeItem("guest");
}

    static logOut() { Session.#store.clear(); }
}

/** One place that talks to the Flask backend. Adds the login token, timeouts, and clear errors. */
class ApiClient {
    #baseUrl;
    #timeoutMs;

    constructor({ baseUrl, timeoutMs = 130000 } = {}) {
    // Opened as a plain file (file://)? Fall back to the default Flask address.
    this.#baseUrl = baseUrl ?? (window.location.protocol === "file:" ? "http://localhost:5000" : "");
    this.#timeoutMs = timeoutMs;
    }

    get(path, query) { return this.#request("GET", path, { query }); }
    post(path, body) { return this.#request("POST", path, { body }); }
    delete(path) { return this.#request("DELETE", path); }

    async #request(method, path, { body, query } = {}) {
    const url = new URL(this.#baseUrl + path, window.location.origin);
    Object.entries(query || {}).forEach(([k, v]) => url.searchParams.set(k, v));

    const headers = {};
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (Session.token) headers.Authorization = "Bearer " + Session.token;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.#timeoutMs);

    let response;
    try {
        response = await fetch(url, {
        method, headers, signal: controller.signal,
        body: body === undefined ? undefined : JSON.stringify(body)
    });
    } catch (err) {
        throw new ApiError(
        err.name === "AbortError"
            ? "The server took too long to respond."
            : "Could not reach the server. Check that the backend is running."
        );
    } finally {
    clearTimeout(timer);
    }

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        if (response.status === 401 && Session.isLoggedIn) Session.logOut();
            throw new ApiError(data.error || `The server returned an error (${response.status}).`, response.status);
    }
    return data;
    }
}

class Html {
    static escape(text) {
    const div = document.createElement("div");
    div.textContent = text ?? "";
    return div.innerHTML;
    }
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));