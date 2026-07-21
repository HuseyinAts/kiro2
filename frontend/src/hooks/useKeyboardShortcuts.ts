/**
 * useKeyboardShortcuts Hook
 *
 * Simple single-key shortcut binding for fast workflows
 * (e.g. curator queue: V=verify, R=reject, A=archive).
 *
 * Ignores keypresses when:
 *  - user is typing in an input/textarea/contenteditable
 *  - meta/ctrl/alt modifiers are held (preserve browser shortcuts)
 *
 * Usage:
 *   useKeyboardShortcut('v', () => verify(), { enabled: !loading });
 */

import { useEffect } from 'react';

export interface KeyboardShortcutOptions {
  /** Disable the binding without unmounting the component. Default: true */
  enabled?: boolean;
  /** Allow firing while focused on input/textarea (rare, default: false) */
  allowInInputs?: boolean;
}

function isTypingInField(target: EventTarget | null): boolean {
  if (!target || !(target instanceof HTMLElement)) {return false;}
  const tag = target.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') {return true;}
  if (target.isContentEditable) {return true;}
  return false;
}

export function useKeyboardShortcut(
  key: string,
  handler: (e: KeyboardEvent) => void,
  options: KeyboardShortcutOptions = {},
): void {
  const { enabled = true, allowInInputs = false } = options;

  useEffect(() => {
    if (!enabled) {return;}

    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) {return;}
      if (!allowInInputs && isTypingInField(e.target)) {return;}
      if (e.key.toLowerCase() !== key.toLowerCase()) {return;}

      e.preventDefault();
      handler(e);
    };

    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [key, handler, enabled, allowInInputs]);
}

/**
 * Bind multiple shortcuts at once.
 *
 * Usage:
 *   useKeyboardShortcuts({
 *     v: () => verify(),
 *     r: () => reject(),
 *     a: () => archive(),
 *   }, { enabled: !loading });
 */
export function useKeyboardShortcuts(
  bindings: Record<string, (e: KeyboardEvent) => void>,
  options: KeyboardShortcutOptions = {},
): void {
  const { enabled = true, allowInInputs = false } = options;

  useEffect(() => {
    if (!enabled) {return;}

    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) {return;}
      if (!allowInInputs && isTypingInField(e.target)) {return;}

      const handler = bindings[e.key] || bindings[e.key.toLowerCase()];
      if (!handler) {return;}

      e.preventDefault();
      handler(e);
    };

    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [bindings, enabled, allowInInputs]);
}

export default useKeyboardShortcut;
