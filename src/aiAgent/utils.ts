import { AI_AGENT_CONFIG } from './config';

/**
 * Utility functions for the AI Agent
 */

/**
 * Debounce function to prevent rapid successive calls
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout | undefined;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

/**
 * Check if an element is visible and interactable
 */
export function isElementVisible(element: HTMLElement): boolean {
  const style = window.getComputedStyle(element);
  const rect = element.getBoundingClientRect();
  
  return (
    style.display !== 'none' &&
    style.visibility !== 'hidden' &&
    style.opacity !== '0' &&
    rect.width > 0 &&
    rect.height > 0 &&
    !element.hidden &&
    !element.hasAttribute('aria-hidden')
  );
}

/**
 * Check if an element is disabled
 */
export function isElementDisabled(element: HTMLElement): boolean {
  if (element instanceof HTMLInputElement || 
      element instanceof HTMLButtonElement || 
      element instanceof HTMLSelectElement ||
      element instanceof HTMLTextAreaElement) {
    return element.disabled;
  }
  
  return element.hasAttribute('disabled') || 
         element.getAttribute('aria-disabled') === 'true';
}

/**
 * Get meaningful text content from an element
 */
export function getElementText(element: HTMLElement): string {
  let text = '';
  
  if (element instanceof HTMLInputElement) {
    text = element.placeholder || 
           element.value || 
           element.getAttribute('aria-label') || 
           element.getAttribute('title') || '';
  } else if (element instanceof HTMLSelectElement) {
    text = element.getAttribute('aria-label') || 
           element.getAttribute('title') || 
           'Select dropdown';
  } else {
    text = element.innerText?.trim() || 
           element.textContent?.trim() || 
           element.getAttribute('aria-label') || 
           element.getAttribute('title') || 
           element.getAttribute('alt') || '';
  }

  return text.substring(0, AI_AGENT_CONFIG.MAX_TEXT_LENGTH);
}

/**
 * Create a safe delay function that can be cancelled
 */
export function createCancellableDelay(ms: number): {
  promise: Promise<void>;
  cancel: () => void;
} {
  let timeoutId: NodeJS.Timeout;
  let cancelled = false;
  
  const promise = new Promise<void>((resolve) => {
    timeoutId = setTimeout(() => {
      if (!cancelled) {
        resolve();
      }
    }, ms);
  });
  
  const cancel = () => {
    cancelled = true;
    clearTimeout(timeoutId);
  };
  
  return { promise, cancel };
}

/**
 * Validate if a string is a valid URL
 */
export function isValidUrl(string: string): boolean {
  try {
    new URL(string);
    return true;
  } catch {
    return false;
  }
}

/**
 * Generate a unique ID for DOM elements
 */
export function generateElementId(index: number, element: HTMLElement): string {
  const tag = element.tagName.toLowerCase();
  const id = element.id;
  const className = Array.from(element.classList).slice(0, 2).join('-');
  
  return `${index}-${tag}${id ? `-${id}` : ''}${className ? `-${className}` : ''}`;
}

/**
 * Sanitize text input for API requests
 */
export function sanitizeInput(input: string): string {
  return input
    .trim()
    .replace(/\s+/g, ' ') // Replace multiple spaces with single space
    .substring(0, 500); // Limit length
}

/**
 * Format error messages for user display
 */
export function formatError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  
  if (typeof error === 'string') {
    return error;
  }
  
  return 'An unexpected error occurred';
}

/**
 * Check if the current environment supports the required APIs
 */
export function checkBrowserSupport(): {
  supported: boolean;
  missingFeatures: string[];
} {
  const requiredFeatures = [
    'fetch',
    'Promise',
    'addEventListener',
    'querySelector',
    'dataset'
  ];
  
  const missingFeatures: string[] = [];
  
  requiredFeatures.forEach(feature => {
    if (!(feature in window) && !(feature in document)) {
      missingFeatures.push(feature);
    }
  });
  
  return {
    supported: missingFeatures.length === 0,
    missingFeatures
  };
}
