import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import RegisterPage from './RegisterPage';

const { registerAuthMock, getMeMock, registerGymMock, connectWhatsAppMock, getWhatsAppStatusMock, sendOnboardingWelcomeMock } = vi.hoisted(() => ({
  registerAuthMock: vi.fn(),
  getMeMock: vi.fn(),
  registerGymMock: vi.fn(),
  connectWhatsAppMock: vi.fn(),
  getWhatsAppStatusMock: vi.fn(),
  sendOnboardingWelcomeMock: vi.fn(),
}));

vi.mock('../services/api', () => ({
  authService: {
    register: registerAuthMock,
    getMe: getMeMock,
  },
  gymService: {
    register: registerGymMock,
    connectWhatsApp: connectWhatsAppMock,
    getWhatsAppStatus: getWhatsAppStatusMock,
    sendOnboardingWelcome: sendOnboardingWelcomeMock,
  },
}));

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not show instance-name input and requires WhatsApp number before QR step', async () => {
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByPlaceholderText('owner@gym.com'), {
      target: { value: 'owner@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText('At least 8 chars'), {
      target: { value: 'password123' },
    });
    fireEvent.change(screen.getByPlaceholderText('Repeat password'), {
      target: { value: 'password123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));

    fireEvent.change(screen.getByPlaceholderText('Your gym brand'), {
      target: { value: 'My Gym' },
    });
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));

    expect(screen.queryByPlaceholderText(/instance name/i)).not.toBeInTheDocument();
    const whatsappInput = screen.getByPlaceholderText('WhatsApp number for pairing (required)');
    expect(whatsappInput).toBeRequired();

    fireEvent.submit(whatsappInput.closest('form')!);
    expect(connectWhatsAppMock).not.toHaveBeenCalled();
  });
});
