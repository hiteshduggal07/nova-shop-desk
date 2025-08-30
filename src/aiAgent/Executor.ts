import { AgentAction } from './types';
import { highlightElement, scrollToElement } from './DomObserver';
import { AI_AGENT_CONFIG } from './config';

/**
 * Executes an action on a DOM element
 */
export async function executeAction(action: AgentAction): Promise<void> {
  if (action.action === 'DONE') {
    return;
  }

  if (action.elementId === undefined) {
    console.warn('Action missing elementId:', action);
    return;
  }

  const element = document.querySelector(`[data-agent-id="${action.elementId}"]`) as HTMLElement;
  
  if (!element) {
    console.warn(`Element with agent-id ${action.elementId} not found`);
    return;
  }

  // Scroll to element and highlight it
  scrollToElement(action.elementId);
  highlightElement(action.elementId, 1500);

  // Add a small delay for visual feedback
  await new Promise(resolve => setTimeout(resolve, 300));

  try {
    switch (action.action) {
      case 'CLICK':
        await executeClick(element);
        break;
      
      case 'TYPE':
        if (action.text !== undefined) {
          await executeType(element, action.text);
        } else {
          console.warn('TYPE action missing text:', action);
        }
        break;
      
      default:
        console.warn('Unknown action type:', action);
    }
  } catch (error) {
    console.error('Error executing action:', error, action);
  }
}

/**
 * Executes a click action on an element
 */
async function executeClick(element: HTMLElement): Promise<void> {
  // Handle different types of clickable elements
  if (element instanceof HTMLAnchorElement) {
    // For links, we can either click or navigate programmatically
    element.click();
  } else if (element instanceof HTMLButtonElement) {
    element.click();
  } else if (element instanceof HTMLInputElement && element.type === 'submit') {
    element.click();
  } else {
    // For other elements with click handlers
    element.click();
  }

  // Add a small delay after click to allow DOM changes
  await new Promise(resolve => setTimeout(resolve, 100));
}

/**
 * Executes a type action on an input element
 */
async function executeType(element: HTMLElement, text: string): Promise<void> {
  if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) {
    // Focus the element first
    element.focus();
    
    // For React controlled components, we need to directly set the value
    // and trigger React's internal mechanisms
    
    // Get React's internal instance to trigger onChange properly
    const valueSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
    
    if (valueSetter) {
      // Use React's native value setter
      valueSetter.call(element, '');
      
      // Dispatch input event to clear
      element.dispatchEvent(new Event('input', { bubbles: true }));
      await new Promise(resolve => setTimeout(resolve, 50));
      
      // Set the final value and dispatch React-compatible events
      valueSetter.call(element, text);
      
      // Create and dispatch input event that React recognizes
      const inputEvent = new Event('input', { bubbles: true });
      element.dispatchEvent(inputEvent);
      
      // Also dispatch change event
      const changeEvent = new Event('change', { bubbles: true });
      element.dispatchEvent(changeEvent);
      
    } else {
      // Fallback to direct value setting
      element.value = text;
      element.dispatchEvent(new Event('input', { bubbles: true }));
      element.dispatchEvent(new Event('change', { bubbles: true }));
    }
    
    // For search inputs, also trigger form submission if needed
    if (element.type === 'search' || element.placeholder?.toLowerCase().includes('search')) {
      // Try to find and trigger the form submit or search button
      const form = element.closest('form');
      if (form) {
        // Small delay then submit the form
        await new Promise(resolve => setTimeout(resolve, 200));
        
        // Dispatch Enter key event first (some forms listen for this)
        element.dispatchEvent(new KeyboardEvent('keydown', { 
          key: 'Enter', 
          code: 'Enter', 
          bubbles: true,
          cancelable: true
        }));
        
        // Then submit the form
        const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
        form.dispatchEvent(submitEvent);
      }
    }
    
  } else if (element.isContentEditable) {
    // Handle contenteditable elements
    element.focus();
    element.innerText = text;
    
    // Dispatch input event
    element.dispatchEvent(new Event('input', { bubbles: true }));
  } else {
    console.warn('Element is not typeable:', element);
  }
}

/**
 * Validates if an action can be executed on the current DOM
 */
export function validateAction(action: AgentAction): boolean {
  if (action.action === 'DONE') {
    return true;
  }

  if (action.elementId === undefined) {
    return false;
  }

  const element = document.querySelector(`[data-agent-id="${action.elementId}"]`);
  return element !== null;
}
