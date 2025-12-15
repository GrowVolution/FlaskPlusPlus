import { socket, emit } from "/fpp-static/js/socket.js";


function showModal(elem) {
    elem.classList.remove("hidden");
    elem.classList.add("flex");
}

function hideModal(elem) {
    elem.classList.add("hidden");
    elem.classList.remove("flex");
}

function bindModalCloseEvents(modalElem) {
    modalElem.querySelectorAll("[data-modal-close]").forEach(btn => {
        btn.addEventListener("click", () => hideModal(modalElem));
    });

    modalElem.addEventListener("mousedown", (ev) => {
        if (ev.target === modalElem) hideModal(modalElem);
    });
}

document.querySelectorAll("[data-modal]").forEach(modal => {
    hideModal(modal);
    bindModalCloseEvents(modal);
});


const confirmModal = document.getElementById('confirmModal');
const confirmText = document.getElementById('dialogConfirmText');
const confirmBtn = document.getElementById('dialogConfirmBtn');
const dismissBtn = document.getElementById('dialogDismissBtn');

const infoModal = document.getElementById('infoModal');
const infoTitle = document.getElementById('infoModalTitle');
const infoText = document.getElementById('infoModalText');
const infoBody = document.getElementById('infoModalBody');


export async function confirmDialog(message, category) {
    confirmText.innerHTML = message.replace(/\n/g, "<br>");
    confirmBtn.className =
        `px-4 py-2 rounded text-white 
         ${category === 'danger' ? 'bg-red-600 hover:bg-red-700' : ''}
         ${category === 'success' ? 'bg-green-600 hover:bg-green-700' : ''}
         ${category === 'info' ? 'bg-blue-600 hover:bg-blue-700' : ''}
         ${category === 'warning' ? 'bg-yellow-600 hover:bg-yellow-700' : ''}
        `;

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
        infoText.textContent = message;
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
    <div class="flash p-4 mb-3 rounded border-l-4 
        ${category === 'success' ? 'bg-green-100 border-green-600 text-green-800' : ''}
        ${category === 'warning' ? 'bg-yellow-100 border-yellow-600 text-yellow-800' : ''}
        ${category === 'danger' ? 'bg-red-100 border-red-600 text-red-800' : ''}
        ${category === 'info' ? 'bg-blue-100 border-blue-600 text-blue-800' : ''}
    ">
      ${message}
      <button type="button"
              class="ml-3 text-xl leading-none cursor-pointer float-right"
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