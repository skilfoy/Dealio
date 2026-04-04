import { useState } from 'react'
import { Bell, MessageSquare, Mail, Smartphone } from 'lucide-react'

export default function NotificationSettings() {
  const [scoreThreshold, setScoreThreshold] = useState(70)
  const [priceErrors, setPriceErrors] = useState(true)
  const [historicalLows, setHistoricalLows] = useState(true)

  return (
    <div>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
        Configure when you want to be notified about deals. Add notification service API keys in the API Keys tab to enable delivery channels.
      </p>

      {/* Score threshold */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 mb-6">
        <h3 className="font-medium mb-4">Deal Score Threshold</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
          Only notify for deals scoring above this threshold (0-100)
        </p>
        <div className="flex items-center gap-4">
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={scoreThreshold}
            onChange={(e) => setScoreThreshold(parseInt(e.target.value))}
            className="flex-1"
          />
          <span className="text-2xl font-bold w-16 text-right">{scoreThreshold}</span>
        </div>
      </div>

      {/* Alert types */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 mb-6">
        <h3 className="font-medium mb-4">Alert Types</h3>
        <div className="space-y-3">
          <label className="flex items-center justify-between">
            <span className="text-sm">Price Errors & Glitches</span>
            <input
              type="checkbox"
              checked={priceErrors}
              onChange={(e) => setPriceErrors(e.target.checked)}
              className="rounded"
            />
          </label>
          <label className="flex items-center justify-between">
            <span className="text-sm">Historical Lows</span>
            <input
              type="checkbox"
              checked={historicalLows}
              onChange={(e) => setHistoricalLows(e.target.checked)}
              className="rounded"
            />
          </label>
        </div>
      </div>

      {/* Delivery channels */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
        <h3 className="font-medium mb-4">Delivery Channels</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { icon: MessageSquare, label: 'Discord', slug: 'discord', description: 'Webhook notifications' },
            { icon: MessageSquare, label: 'Slack', slug: 'slack', description: 'Channel notifications' },
            { icon: Bell, label: 'Telegram', slug: 'telegram', description: 'Bot messages' },
            { icon: Bell, label: 'Pushover', slug: 'pushover', description: 'Push notifications' },
            { icon: Mail, label: 'Email (SendGrid)', slug: 'sendgrid', description: 'Email alerts' },
            { icon: Smartphone, label: 'SMS (Twilio)', slug: 'twilio', description: 'Text messages' },
          ].map((channel) => {
            const Icon = channel.icon
            return (
              <div
                key={channel.slug}
                className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700"
              >
                <Icon className="w-5 h-5 text-gray-400" />
                <div>
                  <div className="text-sm font-medium">{channel.label}</div>
                  <div className="text-xs text-gray-500">{channel.description}</div>
                </div>
                <span className="ml-auto text-xs text-gray-400">Add key in API Keys tab</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
