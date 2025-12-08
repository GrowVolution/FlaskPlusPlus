const socketScript = document.getElementById("fppSocketScript");

export function connectSocket() {
    const domain = socketScript.dataset.socketDomain;
    return io(domain, {
        transports: ['websocket'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        timeout: 20000
    })
}
export let socket = connectSocket();


export function emit(event, data=null, callback=null) {
    socket.emit('default_event', {
        event: event,
        payload: data
    }, callback);
}