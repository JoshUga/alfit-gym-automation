import { CreditCard, DollarSign } from 'lucide-react';

export default function BillingPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Billing & Subscription</h1>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {['Basic', 'Pro', 'Enterprise'].map((plan) => (
          <div key={plan} className="card text-center">
            <h3 className="text-xl font-bold mb-2">{plan}</h3>
            <p className="text-3xl font-bold text-primary-600 mb-4">
              {plan === 'Basic' ? '$29' : plan === 'Pro' ? '$79' : '$199'}
              <span className="text-sm text-gray-500">/mo</span>
            </p>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2 mb-6">
              <li>{plan === 'Basic' ? '1' : plan === 'Pro' ? '5' : 'Unlimited'} phone numbers</li>
              <li>{plan === 'Basic' ? '100' : plan === 'Pro' ? '1000' : 'Unlimited'} AI messages</li>
              <li>{plan === 'Basic' ? 'Email' : 'Priority'} support</li>
            </ul>
            <button className={`w-full ${plan === 'Pro' ? 'btn-primary' : 'btn-secondary'}`}>
              {plan === 'Pro' ? 'Current Plan' : 'Select Plan'}
            </button>
          </div>
        ))}
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <CreditCard size={20} />
          Payment History
        </h2>
        <p className="text-gray-500 dark:text-gray-400 text-center py-8">No payments yet</p>
      </div>
    </div>
  );
}
