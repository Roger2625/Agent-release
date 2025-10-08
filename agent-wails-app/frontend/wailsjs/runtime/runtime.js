// Runtime stub for development
export function LogPrint(message) {
  console.log(message);
}

export function LogInfo(message) {
  console.info(message);
}

export function LogWarning(message) {
  console.warn(message);
}

export function LogError(message) {
  console.error(message);
}

export function EventsOn(eventName, callback) {
  window.addEventListener(eventName, (e) => callback(e.detail));
}

export function EventsOff(eventName) {
  window.removeEventListener(eventName);
}
