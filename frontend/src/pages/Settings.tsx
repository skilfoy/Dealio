import { useState } from 'react'
import { Key, Store, Ticket, Bell, Activity } from 'lucide-react'
import ApiKeyManager from '../components/settings/ApiKeyManager'
import RetailerManager from '../components/settings/RetailerManager'
import CouponManager from '../components/settings/CouponManager'
import NotificationSettings from '../components/settings/NotificationSettings'
import ScraperHealth from '../components/settings/ScraperHealth'

const TABS = [
  { id: 'api-keys', label: 'API Keys', icon: Key },
  { id: 'retailers', label: 'Retailers', icon: Store },
  { id: 'coupons', label: 'Coupons', icon: Ticket },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'health', label: 'Scraper Health', icon: Activity },
]

export default function Settings() {
  const [activeTab, setActiveTab] = useState('api-keys')

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 overflow-x-auto pb-2 border-b border-gray-200 dark:border-gray-800">
        {TABS.map((tab) => {
          const Icon = tab.icon
          const active = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-lg whitespace-nowrap transition-colors ${
                active
                  ? 'bg-white dark:bg-gray-900 text-blue-600 dark:text-blue-400 border border-b-0 border-gray-200 dark:border-gray-800'
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Content */}
      {activeTab === 'api-keys' && <ApiKeyManager />}
      {activeTab === 'retailers' && <RetailerManager />}
      {activeTab === 'coupons' && <CouponManager />}
      {activeTab === 'notifications' && <NotificationSettings />}
      {activeTab === 'health' && <ScraperHealth />}
    </div>
  )
}
