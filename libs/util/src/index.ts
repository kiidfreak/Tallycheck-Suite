// @omni/util — framework-agnostic helpers shared across apps.

/** Current time as HH:mm (matches the prototype's clock formatting). */
export function nowHHmm(date: Date = new Date()): string {
  return date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
}

/** Initials from a full name, e.g. "Clinton Sang" → "CS". */
export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? '')
    .join('');
}
