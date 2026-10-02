import { getToken, login } from './get-token.js'

/* ================= Login form ================= */
let loginForm = document.querySelector('.login form')

loginForm.addEventListener('submit', (event) => {
    login(event)
})


/* ================= Typing animation ================= */
class TextType {
    constructor(texts) {
        this.texts = texts
        this.wordIndex = 0
        this.sentenceIndex = 0
        this.isDeleting = false

        this.span = document.querySelector('.wrap')
    }

    typing() {
        let text = this.texts[this.sentenceIndex]
        this.delta = 100 - Math.random() * 100;

        if (this.isDeleting) {
            this.delta /= 2
            this.wordIndex -= 1
        } else {
            this.wordIndex += 1
        }

        this.span.textContent = text.substring(-1, this.wordIndex + 1)

        if (this.wordIndex == text.length - 1) {
            this.isDeleting = true
            this.delta = 2000
        }

        if (this.wordIndex == -1) {
            this.isDeleting = false
            this.delta = 500
            if (this.sentenceIndex == this.texts.length - 1) {
                this.sentenceIndex = 0
            } else {
                this.sentenceIndex += 1
            }
        }

        setTimeout(() => this.typing(), this.delta)
    }
}


/* ================= Bootstrap ================= */
window.onload = async function () {
    const elements = document.getElementsByClassName('typewrite')

    if (window.screen.width > 498 && elements.length) {
        const values = await fetchTypingValues()

        if (values.length) {
            for (let i = 0; i < elements.length; i++) {
                const type = new TextType(values)
                type.typing()
            }
        }
    }

    // INJECT CSS (always — cheap and used for the typing cursor)
    const css = document.createElement("style")
    css.type = "text/css"
    css.innerHTML = ".typewrite > .wrap { border-right: 0.08em solid #fff}"
    document.body.appendChild(css)
}


/* ================= Fetch typing features ================= */
async function fetchTypingValues() {
    const endpoint = document.body.dataset.typingEndpoint
        || '/landing/get-site-feature/'   // fallback

    const CACHE_KEY = 'typing_features_v1'

    // 1. Try session cache first
    try {
        const cached = sessionStorage.getItem(CACHE_KEY)
        if (cached) {
            const parsed = JSON.parse(cached)
            if (Array.isArray(parsed) && parsed.length) return parsed
        }
    } catch (_) { /* ignore broken cache */ }

    // 2. Fetch from API
    try {
        const res = await fetch(endpoint, {
            headers: { 'Accept': 'application/json' },
            credentials: 'same-origin',
        })

        if (!res.ok) throw new Error(`HTTP ${res.status}`)

        const data = await res.json()

        // Handle: plain array, paginated {results: [...]}, or strings
        const list = Array.isArray(data) ? data : (data.results || [])

        const values = list
            .map(item => (typeof item === 'string' ? item : item.text))
            .filter(Boolean)

        // 3. Cache for the session
        if (values.length) {
            try {
                sessionStorage.setItem(CACHE_KEY, JSON.stringify(values))
            } catch (_) { /* storage might be full/disabled */ }
        }

        return values

    } catch (err) {
        console.warn('Failed to load typing features:', err)
        return []
    }
}
