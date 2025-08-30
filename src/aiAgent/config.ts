/**
 * Configuration settings for the AI Navigator Agent
 */
export const AI_AGENT_CONFIG = {
  // API Configuration
  DEFAULT_API_ENDPOINT: 'http://localhost:9000/plan',
  REQUEST_TIMEOUT: 30000, // 30 seconds
  
  // Execution Configuration
  MAX_STEPS: 6,
  STEP_DELAY: 500, // ms between steps
  HIGHLIGHT_DURATION: 1500, // ms to highlight elements
  TYPING_SPEED: 50, // ms between characters when typing
  
  // UI Configuration
  KEYBOARD_SHORTCUTS: {
    OPEN_COMMAND_BAR: ['cmd+k', 'ctrl+k'],
    CLOSE_COMMAND_BAR: ['escape']
  },
  
  // DOM Configuration
  MAX_TEXT_LENGTH: 100, // Maximum text length for DOM elements
  INTERACTIVE_SELECTORS: [
    'button',
    'a[href]',
    '[role="button"]',
    'input[type="text"]',
    'input[type="search"]',
    'input[type="email"]',
    'input[type="password"]',
    'input[type="number"]',
    'input[type="tel"]',
    'input[type="url"]',
    'input[type="submit"]',
    'textarea',
    'select',
    '[onclick]',
    '[data-testid]',
    '.clickable',
    '[tabindex="0"]'
  ],
  
  // Error Messages
  ERROR_MESSAGES: {
    NO_INTERACTIVE_ELEMENTS: 'No interactive elements found on the page',
    ELEMENT_NOT_FOUND: 'Element not found on the page',
    INVALID_ACTION: 'Invalid action received from backend',
    API_ERROR: 'Failed to communicate with AI backend',
    MAX_STEPS_EXCEEDED: 'Command execution stopped to prevent infinite loop',
    EMPTY_COMMAND: 'Please enter a command',
    ALREADY_PROCESSING: 'Navigator is already processing a command'
  }
} as const;

export type AIAgentConfig = typeof AI_AGENT_CONFIG;
