import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import SettingsPage from './SettingsPage';

const { getMineMock, getPhoneNumbersMock, updateMock } = vi.hoisted(() => ({
  getMineMock: vi.fn(),
  getPhoneNumbersMock: vi.fn(),
  updateMock: vi.fn(),
}));

vi.mock('../services/api', () => ({
  gymService: {
    getMine: getMineMock,
    getPhoneNumbers: getPhoneNumbersMock,
    update: updateMock,
  },
}));

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getMineMock.mockResolvedValue({
      data: {
        data: {
          id: 1,
          name: 'Alpha Gym',
          email: 'alpha@gym.com',
          phone: '+5511999999999',
          address: 'Main Street 10',
        },
      },
    });
    getPhoneNumbersMock.mockResolvedValue({ data: { data: [] } });
    updateMock.mockResolvedValue({ data: { success: true } });
  });

  it('loads gym profile and hides AI runtime block', async () => {
    render(<SettingsPage />);

    expect(await screen.findByDisplayValue('Alpha Gym')).toBeInTheDocument();
    expect(screen.queryByText('AI Runtime (Server Managed)')).not.toBeInTheDocument();
    expect(screen.getByText('Workspace Safeguards')).toBeInTheDocument();
  });

  it('saves updated gym profile', async () => {
    render(<SettingsPage />);

    const gymNameInput = await screen.findByDisplayValue('Alpha Gym');
    fireEvent.change(gymNameInput, { target: { value: 'Alpha Gym Pro' } });

    fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));

    await waitFor(() => {
      expect(updateMock).toHaveBeenCalledWith(1, {
        name: 'Alpha Gym Pro',
        email: 'alpha@gym.com',
        phone: '+5511999999999',
        address: 'Main Street 10',
      });
    });

    expect(await screen.findByText('Gym settings saved successfully.')).toBeInTheDocument();
  });
});
