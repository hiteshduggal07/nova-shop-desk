import { DOMElement } from './types';
import { AI_AGENT_CONFIG } from './config';
import { isElementVisible, isElementDisabled, getElementText } from './utils';

/**
 * Scans the DOM for interactive elements and assigns data-agent-id attributes
 * Returns a simplified JSON array of interactive elements
 */
export function collectInteractiveElements(): DOMElement[] {
  const selectors = AI_AGENT_CONFIG.INTERACTIVE_SELECTORS.join(', ');

  const elements = Array.from(document.querySelectorAll(selectors)) as HTMLElement[];
  
  // Filter out hidden or non-interactive elements
  const visibleElements = elements.filter(el => {
    return isElementVisible(el) && !isElementDisabled(el);
  });

  return visibleElements.map((el, index) => {
    // Assign unique data-agent-id
    el.dataset.agentId = index.toString();
    
    // Extract meaningful text content
    const text = getElementText(el);

    const domElement: DOMElement = {
      id: index,
      tag: el.tagName.toLowerCase(),
      text,
    };

    // Add input-specific properties
    if (el instanceof HTMLInputElement) {
      domElement.type = el.type;
      domElement.placeholder = el.placeholder;
      domElement.value = el.value;
    }

    return domElement;
  });
}

/**
 * Highlights an element for visual feedback
 */
export function highlightElement(elementId: number, duration: number = AI_AGENT_CONFIG.HIGHLIGHT_DURATION): void {
  const element = document.querySelector(`[data-agent-id="${elementId}"]`) as HTMLElement;
  
  if (!element) return;

  // Store original styles
  const originalOutline = element.style.outline;
  const originalBoxShadow = element.style.boxShadow;
  const originalZIndex = element.style.zIndex;

  // Apply highlight styles
  element.style.outline = '3px solid #ff6b6b';
  element.style.boxShadow = '0 0 10px rgba(255, 107, 107, 0.5)';
  element.style.zIndex = '9999';
  element.style.transition = 'all 0.3s ease';

  // Remove highlight after duration
  setTimeout(() => {
    element.style.outline = originalOutline;
    element.style.boxShadow = originalBoxShadow;
    element.style.zIndex = originalZIndex;
  }, duration);
}

/**
 * Scrolls an element into view smoothly
 */
export function scrollToElement(elementId: number): void {
  const element = document.querySelector(`[data-agent-id="${elementId}"]`) as HTMLElement;
  
  if (!element) return;

  element.scrollIntoView({
    behavior: 'smooth',
    block: 'center',
    inline: 'center'
  });
}
