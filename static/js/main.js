/* =============================================================
   Pantry Nova - Main JS (interactions, theme, animations)
   ============================================================= */

(function () {
    'use strict';

    // ===== Dark mode toggle =====
    const THEME_KEY = 'pn-theme';
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(THEME_KEY, theme);
        const icon = document.querySelector('#themeToggle i');
        if (icon) {
            icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
        }
    }
    const savedTheme = localStorage.getItem(THEME_KEY) || 'light';
    applyTheme(savedTheme);

    document.addEventListener('click', function (e) {
        const t = e.target.closest('#themeToggle');
        if (t) {
            const cur = document.documentElement.getAttribute('data-theme') || 'light';
            applyTheme(cur === 'light' ? 'dark' : 'light');
        }
        // Sidebar toggle
        const st = e.target.closest('#sidebarToggle');
        if (st) {
            const sb = document.querySelector('.pn-sidebar');
            if (sb) sb.classList.toggle('open');
        }
    });

    // ===== Toasts =====
    window.pnToast = function (message, type = 'success', duration = 3500) {
        let container = document.querySelector('.pn-toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'pn-toast-container';
            document.body.appendChild(container);
        }
        const t = document.createElement('div');
        t.className = `pn-toast ${type}`;
        t.innerHTML = message;
        container.appendChild(t);
        setTimeout(() => {
            t.style.animation = 'pnSlideIn 0.3s ease reverse';
            setTimeout(() => t.remove(), 300);
        }, duration);
    };

    // ===== Modal helpers =====
    window.pnOpenModal = function (id) {
        const m = document.getElementById(id);
        if (m) m.classList.add('active');
    };
    window.pnCloseModal = function (id) {
        const m = document.getElementById(id);
        if (m) m.classList.remove('active');
    };
    document.addEventListener('click', function (e) {
        const open = e.target.closest('[data-modal-open]');
        if (open) {
            e.preventDefault();
            window.pnOpenModal(open.dataset.modalOpen);
        }
        const close = e.target.closest('[data-modal-close]');
        if (close) {
            const overlay = close.closest('.pn-modal-overlay');
            if (overlay) overlay.classList.remove('active');
        }
        if (e.target.classList.contains('pn-modal-overlay')) {
            e.target.classList.remove('active');
        }
    });

    // ===== Auto-dismiss Django messages as toasts =====
    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('[data-pn-msg]').forEach(el => {
            window.pnToast(el.dataset.pnMsg, el.dataset.pnLevel || 'success');
            el.remove();
        });
    });

    // ===== Count-up animation =====
    function animateCount(el, target, duration = 1500) {
        const start = 0;
        const startTime = performance.now();
        function step(now) {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const value = Math.floor(start + (target - start) * eased);
            el.textContent = value.toLocaleString();
            if (progress < 1) requestAnimationFrame(step);
            else el.textContent = target.toLocaleString();
        }
        requestAnimationFrame(step);
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('[data-counter]').forEach(el => {
            const target = parseFloat(el.dataset.counter || '0');
            const isFloat = !Number.isInteger(target);
            if (isFloat) {
                el.textContent = target.toLocaleString();
            } else {
                animateCount(el, target);
            }
        });
    });

    // ===== Password strength meter =====
    document.addEventListener('input', function (e) {
        if (!e.target.matches('[data-password-strength]')) return;
        const val = e.target.value;
        const meter = document.querySelector(e.target.dataset.passwordStrength);
        if (!meter) return;
        let score = 0;
        if (val.length >= 6) score++;
        if (val.length >= 10) score++;
        if (/[A-Z]/.test(val)) score++;
        if (/[0-9]/.test(val)) score++;
        if (/[^A-Za-z0-9]/.test(val)) score++;
        const colors = ['#E63946', '#E63946', '#F4A261', '#F4A261', '#52B788', '#1B4332'];
        meter.style.width = (score / 5 * 100) + '%';
        meter.style.background = colors[score];
    });

    // ===== Show/hide password =====
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('[data-toggle-password]');
        if (!btn) return;
        const target = document.querySelector(btn.dataset.togglePassword);
        if (!target) return;
        if (target.type === 'password') {
            target.type = 'text';
            btn.innerHTML = '<i class="bi bi-eye-slash"></i>';
        } else {
            target.type = 'password';
            btn.innerHTML = '<i class="bi bi-eye"></i>';
        }
    });

    // ===== OTP input handling =====
    document.addEventListener('DOMContentLoaded', function () {
        const otpInputs = document.querySelectorAll('.pn-otp-input');
        if (!otpInputs.length) return;
        otpInputs.forEach((input, idx) => {
            input.addEventListener('input', function () {
                this.value = this.value.replace(/[^0-9]/g, '').slice(0, 1);
                if (this.value && idx < otpInputs.length - 1) {
                    otpInputs[idx + 1].focus();
                }
                const hidden = document.getElementById('otpHidden');
                if (hidden) {
                    hidden.value = Array.from(otpInputs).map(i => i.value).join('');
                }
            });
            input.addEventListener('keydown', function (e) {
                if (e.key === 'Backspace' && !this.value && idx > 0) {
                    otpInputs[idx - 1].focus();
                }
            });
            input.addEventListener('paste', function (e) {
                e.preventDefault();
                const pasted = (e.clipboardData || window.clipboardData).getData('text');
                const digits = pasted.replace(/[^0-9]/g, '').slice(0, otpInputs.length);
                digits.split('').forEach((d, i) => {
                    if (otpInputs[i]) otpInputs[i].value = d;
                });
                const hidden = document.getElementById('otpHidden');
                if (hidden) hidden.value = digits;
            });
        });
    });

    // ===== Confirm prompts =====
    document.addEventListener('click', function (e) {
        const el = e.target.closest('[data-confirm]');
        if (!el) return;
        if (!confirm(el.dataset.confirm)) {
            e.preventDefault();
            e.stopPropagation();
        }
    });

    // ===== Copy-to-clipboard =====
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('[data-copy]');
        if (!btn) return;
        const text = btn.dataset.copy;
        navigator.clipboard.writeText(text).then(() => {
            window.pnToast('🌿 Copied to clipboard!', 'success', 2000);
        });
    });

    // ===== AOS init (if available) =====
    if (window.AOS) {
        window.AOS.init({
            duration: 700,
            once: true,
            offset: 60,
        });
    }

    // ===== GSAP basic landing animations =====
    if (window.gsap) {
        gsap.from('[data-gsap="hero-title"]', {
            opacity: 0, y: 40, duration: 0.9, ease: 'power3.out'
        });
        gsap.from('[data-gsap="hero-sub"]', {
            opacity: 0, y: 30, duration: 0.9, delay: 0.2, ease: 'power3.out'
        });
        gsap.from('[data-gsap="hero-cta"]', {
            opacity: 0, y: 20, duration: 0.7, delay: 0.4, ease: 'power3.out'
        });
    }

    // ===== Chatbot send (if on chatbot page) =====
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        const messagesEl = document.getElementById('chatMessages');
        const inputEl = document.getElementById('chatInput');

        function appendMsg(text, who) {
            const d = document.createElement('div');
            d.className = `pn-chat-msg ${who}`;
            d.textContent = text;
            messagesEl.appendChild(d);
            messagesEl.scrollTop = messagesEl.scrollHeight;
            return d;
        }

        function showTyping() {
            const d = document.createElement('div');
            d.className = 'pn-chat-msg bot pn-chat-typing';
            d.id = 'chatTyping';
            d.innerHTML = '<span></span><span></span><span></span>';
            messagesEl.appendChild(d);
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }
        function hideTyping() {
            const d = document.getElementById('chatTyping');
            if (d) d.remove();
        }

        async function sendMsg(text) {
            appendMsg(text, 'user');
            inputEl.value = '';
            showTyping();
            try {
                const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
                const res = await fetch('/chatbot/send/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrf,
                    },
                    body: JSON.stringify({ message: text }),
                });
                const data = await res.json();
                hideTyping();
                if (data.success) {
                    appendMsg(data.response, 'bot');
                } else {
                    appendMsg('🌿 Sorry, I could not respond. ' + (data.error || ''), 'bot');
                }
            } catch (err) {
                hideTyping();
                appendMsg('🌿 Connection issue. Please try again.', 'bot');
            }
        }

        chatForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const text = inputEl.value.trim();
            if (!text) return;
            sendMsg(text);
        });

        inputEl.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.requestSubmit();
            }
        });

        // Quick prompts
        document.querySelectorAll('.pn-chat-prompt').forEach(p => {
            p.addEventListener('click', function () {
                sendMsg(this.textContent.trim());
            });
        });

        // Auto-scroll to bottom on load
        if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight;

        // Auto-resize textarea
        if (inputEl) {
            inputEl.addEventListener('input', function () {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 120) + 'px';
            });
        }
    }

    // ===== View toggle (table <-> cards) =====
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('[data-view-switch]');
        if (!btn) return;
        const view = btn.dataset.viewSwitch;
        document.querySelectorAll('[data-view]').forEach(el => {
            el.style.display = el.dataset.view === view ? '' : 'none';
        });
        document.querySelectorAll('[data-view-switch]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    });

    // ===== Inline edit for shopping list (toggle purchased) =====
    document.addEventListener('change', function (e) {
        if (!e.target.matches('[data-shop-toggle]')) return;
        const id = e.target.dataset.shopToggle;
        const csrf = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        const row = e.target.closest('.shop-row');
        if (row) row.classList.toggle('pn-strike', e.target.checked);
        fetch(`/manager/shopping-list/toggle/${id}/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrf || '' },
        }).then(r => r.json()).catch(() => {});
    });

    // ===== DataTables init =====
    document.addEventListener('DOMContentLoaded', function () {
        if (window.jQuery && jQuery.fn.DataTable) {
            jQuery('table.pn-datatable').DataTable({
                pageLength: 10,
                order: [],
                language: {
                    search: '🔍',
                    lengthMenu: 'Show _MENU_',
                },
            });
        }
    });

    // ===== Edit modal autofill =====
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('[data-edit-modal]');
        if (!btn) return;
        const modalId = btn.dataset.editModal;
        const data = btn.dataset;
        const modal = document.getElementById(modalId);
        if (!modal) return;
        Object.keys(data).forEach(k => {
            if (k === 'editModal') return;
            const field = modal.querySelector(`[name="${k}"]`);
            if (field) field.value = data[k];
        });
        window.pnOpenModal(modalId);
    });
})();
