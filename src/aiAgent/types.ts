export interface DOMElement {
  id: number;
  tag: string;
  text: string;
  type?: string;
  placeholder?: string;
  value?: string;
}

export interface AgentAction {
  action: 'CLICK' | 'TYPE' | 'DONE';
  elementId?: number;
  text?: string;
  summary?: string;
}

export interface NavigatorRequest {
  query: string;
  dom_snapshot: DOMElement[];
  history: AgentAction[];
}

export interface NavigatorResponse {
  action: 'CLICK' | 'TYPE' | 'DONE';
  elementId?: number;
  text?: string;
  summary?: string;
  reasoning?: string;
  confidence?: number;
}
