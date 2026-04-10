import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { gymService } from '../services/api';

function isConnectedStatus(status: string) {
  return ['open', 'connected', 'online'].includes(status.toLowerCase());
}

export default function GymSetupPage() {
  const navigate = useNavigate();
  const [gymName, setGymName] = useState('');
  const [gymEmail, setGymEmail] = useState('');
  const [gymPhone, setGymPhone] = useState('');
  const [gymAddress, setGymAddress] = useState('');
  const [gymCurrency, setGymCurrency] = useState('UGX');
  const [evolutionApiKey, setEvolutionApiKey] = useState('');
  const [instanceName, setInstanceName] = useState('');
  const [pairingPhone, setPairingPhone] = useState('');
  const [qrCode, setQrCode] = useState('');
  const [pairingCode, setPairingCode] = useState('');
  const [status, setStatus] = useState('');
  const [gymId, setGymId] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submitSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const registerRes = await gymService.register({
        name: gymName,
        address: gymAddress,
        phone: gymPhone,
        email: gymEmail,
        preferred_currency: gymCurrency,
      });

      const createdGymId = registerRes.data.data.id as number;
      setGymId(createdGymId);
      localStorage.setItem('active_gym_id', String(createdGymId));
      localStorage.setItem('active_gym_currency', String(registerRes.data.data.preferred_currency || 'UGX'));

      const resolvedInstanceName = instanceName || `gym-${createdGymId}`;
      await gymService.setEvolutionCredentials(createdGymId, {
        api_key: evolutionApiKey,
        instance_name: resolvedInstanceName,
      });

      const connectRes = await gymService.connectWhatsApp(createdGymId, {
        phone_number: pairingPhone,
      });

      const connectData = connectRes.data.data;
      setQrCode(connectData.qr_code || '');
      setPairingCode(connectData.pairing_code || '');

      const statusRes = await gymService.getWhatsAppStatus(createdGymId);
      const currentStatus = String(statusRes.data.data.status || 'unknown');
      setStatus(currentStatus);

      if (pairingPhone && isConnectedStatus(currentStatus)) {
        await gymService.sendOnboardingWelcome(createdGymId, {
          phone_number: pairingPhone,
        });
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message;
      setError(msg || 'Failed to complete gym setup');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold mb-2">Gym Setup and WhatsApp Connection</h1>
      <p className="text-sm text-gray-600 mb-6">
        Register your gym, then connect your WhatsApp line using QR code or pairing code.
      </p>

      {error && <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      <form onSubmit={submitSetup} className="space-y-4 card">
        <input
          type="text"
          placeholder="Gym name"
          value={gymName}
          onChange={(e) => setGymName(e.target.value)}
          className="input-field"
          required
        />
        <input
          type="email"
          placeholder="Gym email"
          value={gymEmail}
          onChange={(e) => setGymEmail(e.target.value)}
          className="input-field"
          required
        />
        <input
          type="text"
          placeholder="Gym phone"
          value={gymPhone}
          onChange={(e) => setGymPhone(e.target.value)}
          className="input-field"
        />
        <input
          type="text"
          placeholder="Gym address"
          value={gymAddress}
          onChange={(e) => setGymAddress(e.target.value)}
          className="input-field"
        />
        <select
          value={gymCurrency}
          onChange={(e) => setGymCurrency(e.target.value.toUpperCase())}
          className="input-field"
        >
          <option value="UGX">UGX (default)</option>
          <option value="USD">USD</option>
          <option value="KES">KES</option>
          <option value="TZS">TZS</option>
          <option value="EUR">EUR</option>
        </select>
        <input
          type="text"
          placeholder="Evolution API key (instance token)"
          value={evolutionApiKey}
          onChange={(e) => setEvolutionApiKey(e.target.value)}
          className="input-field"
          required
        />
        <input
          type="text"
          placeholder="Instance name (optional)"
          value={instanceName}
          onChange={(e) => setInstanceName(e.target.value)}
          className="input-field"
        />
        <input
          type="text"
          placeholder="Phone number for pairing code (optional)"
          value={pairingPhone}
          onChange={(e) => setPairingPhone(e.target.value)}
          className="input-field"
        />

        <div className="flex gap-3">
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Setting up...' : 'Register Gym and Connect WhatsApp'}
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => navigate('/app')}
          >
            Skip for now
          </button>
        </div>
      </form>

      {(gymId || status || qrCode || pairingCode) && (
        <div className="mt-6 card">
          <h2 className="text-lg font-semibold mb-3">Connection Details</h2>
          {gymId && <p className="text-sm mb-2">Gym ID: {gymId}</p>}
          {status && <p className="text-sm mb-2">Connection status: {status}</p>}
          {pairingCode && <p className="text-sm mb-2">Pairing code: {pairingCode}</p>}
          {qrCode && (
            <div>
              <p className="text-sm mb-2">QR code:</p>
              <img src={qrCode} alt="WhatsApp QR code" className="max-w-xs rounded-md border" />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
