import { useState, useEffect, useRef } from 'react'
import { ExecuteCommand, GetSessionHistory } from '../../wailsjs/go/main/App'
import Terminal from '../components/Terminal'
import Sidebar from '../components/Sidebar'
import styles from './Dashboard.module.css'

interface DashboardProps {
  onLogout: () => void
}

interface HistoryItem {
  command: string
  output: string
  timestamp: string
  success: boolean
}

function Dashboard({ onLogout }: DashboardProps) {
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [activeView, setActiveView] = useState('terminal')

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    try {
      const data = await GetSessionHistory()
      setHistory(data as HistoryItem[])
    } catch (error) {
      console.error('Failed to load history:', error)
    }
  }

  const handleExecuteCommand = async (command: string) => {
    try {
      const output = await ExecuteCommand(command)
      await loadHistory()
      return output
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Command failed'
      await loadHistory()
      return errorMsg
    }
  }

  return (
    <div className={styles.container}>
      <Sidebar
        activeView={activeView}
        onViewChange={setActiveView}
        onLogout={onLogout}
      />
      <div className={styles.mainContent}>
        {activeView === 'terminal' && (
          <Terminal
            onExecuteCommand={handleExecuteCommand}
            history={history}
          />
        )}
        {activeView === 'reports' && (
          <div className={styles.placeholder}>
            <h2>Reports</h2>
            <p>Report generator coming soon...</p>
          </div>
        )}
        {activeView === 'settings' && (
          <div className={styles.placeholder}>
            <h2>Settings</h2>
            <p>Configuration settings coming soon...</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
