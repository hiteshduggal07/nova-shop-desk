import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AIAgent } from './AIAgent';

// Mock the store context
const mockStore = {
  state: {
    cart: [],
    searchQuery: '',
    category: ''
  },
  dispatch: jest.fn()
};

jest.mock('@/contexts/StoreContext', () => ({
  useStore: () => mockStore
}));

// Mock the toast hook
jest.mock('@/hooks/use-toast', () => ({
  toast: jest.fn()
}));

// Mock speech recognition and synthesis
Object.defineProperty(window, 'webkitSpeechRecognition', {
  value: jest.fn(),
  writable: true
});

Object.defineProperty(window, 'speechSynthesis', {
  value: {
    speak: jest.fn()
  },
  writable: true
});

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('AIAgent', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the floating action button', () => {
    renderWithRouter(<AIAgent />);
    const button = screen.getByRole('button', { name: /ai shopping assistant/i });
    expect(button).toBeInTheDocument();
  });

  it('shows the AI agent panel when clicked', () => {
    renderWithRouter(<AIAgent />);
    const button = screen.getByRole('button', { name: /ai shopping assistant/i });
    
    button.click();
    
    expect(screen.getByText('AI Shopping Assistant')).toBeInTheDocument();
    expect(screen.getByText('Voice & Text')).toBeInTheDocument();
  });

  it('displays welcome message', () => {
    renderWithRouter(<AIAgent />);
    const button = screen.getByRole('button', { name: /ai shopping assistant/i });
    button.click();
    
    expect(screen.getByText(/Hello! I'm your AI shopping assistant/)).toBeInTheDocument();
  });

  it('has text input field', () => {
    renderWithRouter(<AIAgent />);
    const button = screen.getByRole('button', { name: /ai shopping assistant/i });
    button.click();
    
    const input = screen.getByPlaceholderText('Type your request...');
    expect(input).toBeInTheDocument();
  });

  it('has voice and text input buttons', () => {
    renderWithRouter(<AIAgent />);
    const button = screen.getByRole('button', { name: /ai shopping assistant/i });
    button.click();
    
    const sendButton = screen.getByRole('button', { name: /send/i });
    const micButton = screen.getByRole('button', { name: /microphone/i });
    
    expect(sendButton).toBeInTheDocument();
    expect(micButton).toBeInTheDocument();
  });
});
