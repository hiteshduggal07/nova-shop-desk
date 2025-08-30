// Main exports for the AI Agent module
export { CommandBar } from './CommandBar';
export { useNavigator } from './useNavigator';
export { collectInteractiveElements, highlightElement, scrollToElement } from './DomObserver';
export { executeAction, validateAction } from './Executor';
export { AI_AGENT_CONFIG } from './config';
export * from './utils';
export type { DOMElement, AgentAction, NavigatorRequest, NavigatorResponse } from './types';
