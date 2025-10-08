export function LogPrint(message: string): void;
export function LogInfo(message: string): void;
export function LogWarning(message: string): void;
export function LogError(message: string): void;
export function EventsOn(eventName: string, callback: (...args: any[]) => void): void;
export function EventsOff(eventName: string): void;
