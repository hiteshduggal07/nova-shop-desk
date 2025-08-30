import { useState, useCallback } from 'react';
import { AgentAction, NavigatorRequest, NavigatorResponse } from './types';
import { collectInteractiveElements } from './DomObserver';
import { executeAction, validateAction } from './Executor';
import { AI_AGENT_CONFIG } from './config';
import { sanitizeInput, formatError } from './utils';

interface UseNavigatorState {
  isProcessing: boolean;
  history: AgentAction[];
  error: string | null;
  lastAction: AgentAction | null;
}

interface UseNavigatorReturn extends UseNavigatorState {
  executeCommand: (query: string) => Promise<void>;
  clearHistory: () => void;
  resetError: () => void;
}

/**
 * Custom hook for AI navigation agent
 */
export function useNavigator(apiEndpoint: string = AI_AGENT_CONFIG.DEFAULT_API_ENDPOINT): UseNavigatorReturn {
  const [state, setState] = useState<UseNavigatorState>({
    isProcessing: false,
    history: [],
    error: null,
    lastAction: null
  });

  /**
   * Sends a request to the backend AI service
   */
  const sendToBackend = useCallback(async (
    query: string, 
    domSnapshot: ReturnType<typeof collectInteractiveElements>, 
    history: AgentAction[]
  ): Promise<NavigatorResponse> => {
    const payload: NavigatorRequest = {
      query,
      dom_snapshot: domSnapshot,
      history
    };

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), AI_AGENT_CONFIG.REQUEST_TIMEOUT);

      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Validate response structure
      if (!data.action || !['CLICK', 'TYPE', 'DONE'].includes(data.action)) {
        throw new Error('Invalid response format from backend');
      }

      return data as NavigatorResponse;
    } catch (error) {
      console.error('Backend communication error:', error);
      throw error;
    }
  }, [apiEndpoint]);

  /**
   * Executes a command by sending it to the backend and performing the returned actions
   */
  const executeCommand = useCallback(async (query: string): Promise<void> => {
    if (state.isProcessing) {
      console.warn('Navigator is already processing a command');
      return;
    }

    const sanitizedQuery = sanitizeInput(query);
    if (!sanitizedQuery) {
      setState(prev => ({ ...prev, error: AI_AGENT_CONFIG.ERROR_MESSAGES.EMPTY_COMMAND }));
      return;
    }

    setState(prev => ({ 
      ...prev, 
      isProcessing: true, 
      error: null,
      lastAction: null
    }));

    try {
      let currentHistory = [...state.history];
      let stepCount = 0;

      while (stepCount < AI_AGENT_CONFIG.MAX_STEPS) {
        stepCount++;

        // Collect current DOM state
        const domSnapshot = collectInteractiveElements();

        if (domSnapshot.length === 0) {
          throw new Error(AI_AGENT_CONFIG.ERROR_MESSAGES.NO_INTERACTIVE_ELEMENTS);
        }

        // Send request to backend
        const action = await sendToBackend(sanitizedQuery, domSnapshot, currentHistory);

        // Update state with the action
        setState(prev => ({ ...prev, lastAction: action }));

        // Check if we're done
        if (action.action === 'DONE') {
          setState(prev => ({ 
            ...prev, 
            isProcessing: false,
            history: [...currentHistory, action]
          }));

          // Show success message
          if (action.summary) {
            console.log('Command completed:', action.summary);
            // You can also show a toast notification here
          }
          
          return;
        }

        // Validate the action before executing
        if (!validateAction(action)) {
          throw new Error(`${AI_AGENT_CONFIG.ERROR_MESSAGES.ELEMENT_NOT_FOUND}: ${action.elementId}`);
        }

        // Execute the action
        await executeAction(action);

        // Add action to history
        currentHistory = [...currentHistory, action];

        // Update state
        setState(prev => ({ 
          ...prev, 
          history: currentHistory
        }));

        // Add delay between steps for better UX
        await new Promise(resolve => setTimeout(resolve, AI_AGENT_CONFIG.STEP_DELAY));
      }

      // If we reach here, we've hit the max steps limit
      throw new Error(AI_AGENT_CONFIG.ERROR_MESSAGES.MAX_STEPS_EXCEEDED);

    } catch (error) {
      console.error('Command execution failed:', error);
      
      const errorMessage = formatError(error);

      setState(prev => ({ 
        ...prev, 
        isProcessing: false, 
        error: errorMessage
      }));
    }
  }, [state.isProcessing, state.history, sendToBackend]);

  /**
   * Clears the action history
   */
  const clearHistory = useCallback(() => {
    setState(prev => ({ 
      ...prev, 
      history: [],
      lastAction: null,
      error: null
    }));
  }, []);

  /**
   * Resets the error state
   */
  const resetError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    ...state,
    executeCommand,
    clearHistory,
    resetError
  };
}
