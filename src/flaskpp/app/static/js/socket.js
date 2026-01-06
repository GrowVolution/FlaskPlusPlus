const socketScript = document.getElementById("fppSocketScript");

export function connectSocket() {
    const domain = socketScript.dataset.socketDomain;
    return io(domain, {
        transports: ['websocket'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        timeout: 20000,
    })
}

export let socket = connectSocket();


export const namespace = document.querySelector('meta[name="sio:namespace"]')?.content;

export function emit(event, data=null, callback=null) {
    if (namespace) event = `${event}@${namespace}`;

    socket.emit('default_event', {
        event: event,
        payload: data
    }, callback);
}

export function emitAsync(event, payload) {
    return new Promise(resolve => {
        emit(event, payload, resolve);
    });
}