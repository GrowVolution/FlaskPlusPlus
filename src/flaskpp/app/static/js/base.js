import { socket, emit } from "/fpp-static/js/socket.js";


function getFocusable(elem) {
    return (
        elem.querySelector(
            "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
        )
    );
}

function showModal(elem) {
    elem._trigger = document.activeElement;

    elem.classList.remove("hidden");
    elem.classList.add("flex");
    elem.removeAttribute("inert");

    const focusable = getFocusable(elem);
    focusable?.focus();
}

function hideModal(elem) {
    elem.classList.add("hidden");
    elem.classList.remove("flex");
    elem.setAttribute("inert", "");

    if (elem._trigger) {
        elem._trigger.focus();
        elem._trigger = null;
    }
}

function bindModalCloseEvents(modalElem) {
    modalElem.querySelectorAll("[data-modal-close]").forEach(btn => {
        btn.addEventListener("click", () => hideModal(modalElem));
    });

    modalElem.addEventListener("mousedown", (ev) => {
        if (ev.target === modalElem) hideModal(modalElem);
    });
}

document.addEventListener("keydown", ev => {
    if (ev.key !== "Escape") return;

    const openModal = document.querySelector(".modal:not(.hidden)");
    if (openModal) hideModal(openModal);
});


const confirmModal = document.getElementById('confirmModal');
const confirmTitle = document.getElementById('dialogConfirmTitle');
const confirmText = document.getElementById('dialogConfirmText');
const confirmBody = document.getElementById('dialogConfirmBody');
const confirmBtn = document.getElementById('dialogConfirmBtn');
const dismissBtn = document.getElementById('dialogDismissBtn');

const infoModal = document.getElementById('infoModal');
const infoTitle = document.getElementById('infoModalTitle');
const infoText = document.getElementById('infoModalText');
const infoBody = document.getElementById('infoModalBody');


export async function confirmDialog(title, message, html, category) {
    confirmTitle.textContent = title;
    confirmBtn.className =
        `inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-semibold
         focus:outline-none focus:ring-2 focus:ring-primary/40 transition text-white
         ${category === 'danger' ? 'bg-red-600 hover:bg-red-700' : ''}
         ${category === 'success' ? 'bg-green-600 hover:bg-green-700' : ''}
         ${category === 'info' ? 'bg-blue-600 hover:bg-blue-700' : ''}
         ${category === 'warning' ? 'bg-yellow-600 hover:bg-yellow-700' : ''}
        `;

    if (message) {
        confirmBody.classList.add('hidden');
        confirmText.classList.remove('hidden');
        confirmText.textContent = message.replace(/\n/g, "<br>");
    } else {
        confirmText.classList.add('hidden');
        confirmBody.classList.remove('hidden');
        confirmBody.innerHTML = html;
    }

    return new Promise((resolve) => {
        function onConfirm() {
            cleanup();
            resolve(true);
        }

        function onDismiss() {
            cleanup();
            resolve(false);
        }

        function cleanup() {
            confirmBtn.removeEventListener('click', onConfirm);
            dismissBtn.removeEventListener('click', onDismiss);
            hideModal(confirmModal);
        }

        confirmBtn.addEventListener('click', onConfirm);
        dismissBtn.addEventListener('click', onDismiss);

        showModal(confirmModal);
    });
}

export function showInfo(title, message, html) {
    infoTitle.textContent = title;
    if (message) {
        infoBody.classList.add('hidden');
        infoText.classList.remove('hidden');
        infoText.textContent = message.replace(/\n/g, "<br>");
    } else {
        infoText.classList.add('hidden');
        infoBody.classList.remove('hidden');
        infoBody.innerHTML = html;
    }

    showModal(infoModal);
}


const flashContainer = document.getElementById('flashContainer');

export function flash(message, category) {
    flashContainer.innerHTML = `
    <div class="flash ${category}">
      <span class="flash-text">
        ${message}
      </span>
      <button type="button"
              onclick="this.parentElement.remove()">
        &times;
      </button>
    </div>
    `
}


export function safe_(fn, rethrow=false) {
    return function (...args) {
        try {
            return fn(...args);
        } catch (e) {
            _("Failed to execute function safely: ").then((message) => {
                console.error(message, e);
            });
            if (rethrow) throw e;
        }
    }
}


export async function _(key) {
    return new Promise((resolve) => {
        emit("_", key, (response) => {
            resolve(response);
        });
    });
}

export async function _n(singular, plural, count) {
    return new Promise((resolve) => {
        emit("_n", {
            s: singular,
            p: plural,
            n: count
        }, (response) => {
            resolve(response);
        });
    });
}


export function socketHtmlInject(key, dom_block) {
    function handleHtml(html) {
        dom_block.innerHTML = html;

        const scripts = dom_block.querySelectorAll("script");
        scripts.forEach(oldScript => {
            const newScript = document.createElement("script");

            if (oldScript.src) newScript.src = oldScript.src;
            else newScript.textContent = oldScript.innerHTML;

            document.body.appendChild(newScript);
            oldScript.remove();
        });
    }
    emit("html", key, safe_(html => handleHtml(html)));
}


socket.on('flash', (data) => {
    flash(data['msg'], data['cat']);
});

socket.on('error', async (message) => {
    console.error(message);
    const title = await _("Socket Error");
    const errMsg = await _("There was an error while executing this event.\n");
    const errLabel = await _("Error Message:");

    showInfo(title, `${errMsg}${errLabel} "${message}".`);
});


window.FPP = {
    confirmDialog: confirmDialog,
    showInfo: showInfo,
    flash: flash,
    safe_: safe_,
    _: _,
    _n: _n,
    socketHtmlInject: socketHtmlInject,
    socket: socket,
    emit: emit
}


document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".modal").forEach(modal => {
        modal.setAttribute("inert", "");
        hideModal(modal);
        bindModalCloseEvents(modal);
    });
});