import { Settings, Phone, Bot } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <Settings size={24} />
        Settings
      </h1>
      <div className="space-y-6">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Gym Profile</h2>
          <form className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium mb-1">Gym Name</label>
              <input type="text" className="input-field" placeholder="Your Gym Name" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <input type="email" className="input-field" placeholder="gym@example.com" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Phone</label>
              <input type="tel" className="input-field" placeholder="+1234567890" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Address</label>
              <input type="text" className="input-field" placeholder="123 Main St" />
            </div>
            <div className="md:col-span-2">
              <button type="submit" className="btn-primary">Save Changes</button>
            </div>
          </form>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Phone size={20} />
            Phone Numbers
          </h2>
          <p className="text-gray-500 dark:text-gray-400">No phone numbers linked</p>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Bot size={20} />
            AI Auto-Responder
          </h2>
          <form className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">AI Provider</label>
              <select className="input-field">
                <option value="openai">OpenAI</option>
                <option value="gemini">Google Gemini</option>
                <option value="openrouter">OpenRouter</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">API Key</label>
              <input type="password" className="input-field" placeholder="Enter API key" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Base Prompt</label>
              <textarea
                className="input-field min-h-[100px]"
                placeholder="Enter the base prompt for AI responses..."
              />
            </div>
            <button type="submit" className="btn-primary">Save AI Settings</button>
          </form>
        </div>
      </div>
    </div>
  );
}
