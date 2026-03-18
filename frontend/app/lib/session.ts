/**
 * Session management utilities (no authentication required).
 * Uses localStorage to persist session ID across page reloads.
 */

const SESSION_STORAGE_KEY = 'routemind_session_id';

/**
 * Generate a UUID v4 session ID.
 */
export function generateSessionId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * Get existing session ID from localStorage or create a new one.
 */
export function getSessionId(): string {
  if (typeof window === 'undefined') {
    // SSR - return empty string, will be set client-side
    return '';
  }

  let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);

  if (!sessionId) {
    sessionId = generateSessionId();
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  }

  return sessionId;
}

/**
 * Set a new session ID (useful for testing or manual session management).
 */
export function setSessionId(sessionId: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
}

/**
 * Clear the current session ID.
 */
export function clearSessionId(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(SESSION_STORAGE_KEY);
}

/**
 * Check if a session ID exists.
 */
export function hasSessionId(): boolean {
  if (typeof window === 'undefined') return false;
  return localStorage.getItem(SESSION_STORAGE_KEY) !== null;
}
