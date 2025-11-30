import { socket, emit } from "/static/js/socket.js";

const flashContainer = document.getElementById('flashContainer');

const confirmModal = new bootstrap.Modal(document.getElementById('confirmModal'));
const confirmText = document.getElementById('dialogConfirmText');
const confirmBtn = document.getElementById('dialogConfirmBtn');
const dismissBtn = document.getElementById('dialogDismissBtn');

const infoModal = new bootstrap.Modal(document.getElementById('infoModal'));
const infoTitle = document.getElementById('infoModalTitle');
const infoText = document.getElementById('infoModalText');
const infoBody = document.getElementById('infoModalBody');


export function flash(message, category) {
    flashContainer.innerHTML = `
    <div class="alert alert-${category} alert-dismissible fade show" role="alert">
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
    `
}


export async function confirmDialog(message, category) {
    confirmText.innerHTML = message.replace(/\n/g, "<br>");
    confirmBtn.className = `btn btn-${category}`;

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
            confirmModal.hide();
        }

        confirmBtn.addEventListener('click', onConfirm);
        dismissBtn.addEventListener('click', onDismiss);

        confirmModal.show();
    });
}


export function showInfo(title, message, html) {
    infoTitle.textContent = title;
    if (message) {
        infoBody.classList.add('d-none');
        infoText.classList.remove('d-none')
        infoText.textContent = message;
    } else {
        infoText.classList.add('d-none');
        infoBody.classList.remove('d-none');
        infoBody.innerHTML = html;
    }
    infoModal.show();
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