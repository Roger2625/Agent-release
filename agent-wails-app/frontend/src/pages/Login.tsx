import { useState } from 'react'
import { ValidateAPIKey, SaveConfiguration } from '../../wailsjs/go/main/App'
import styles from './Login.module.css'

interface LoginProps {
  onLogin: () => void
}

function Login({ onLogin }: LoginProps) {
  const [serverURL, setServerURL] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!serverURL.trim()) {
      setError('Please enter the server URL')
      return
    }

    if (!apiKey.trim()) {
      setError('Please enter an API key')
      return
    }

    setIsLoading(true)

    try {
      const url = serverURL.endsWith('/') ? serverURL : serverURL + '/'
      const response = await ValidateAPIKey(url, apiKey)

      if (response && response.token) {
        await SaveConfiguration(url, response.token as string)
        onLogin()
      } else {
        setError('Server did not return a token')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.formCard}>
        <div className={styles.header}>
          <h1 className={styles.title}>AGENT</h1>
          <p className={styles.subtitle}>Login</p>
        </div>

        <form onSubmit={handleLogin} className={styles.form}>
          <div className={styles.formGroup}>
            <label htmlFor="serverURL" className={styles.label}>
              Server URL
            </label>
            <input
              id="serverURL"
              type="text"
              value={serverURL}
              onChange={(e) => setServerURL(e.target.value)}
              className={styles.input}
              placeholder="https://example.com"
              disabled={isLoading}
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="apiKey" className={styles.label}>
              API Key
            </label>
            <input
              id="apiKey"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className={styles.input}
              placeholder="Enter your API key"
              disabled={isLoading}
            />
          </div>

          {error && <div className={styles.error}>{error}</div>}

          <button
            type="submit"
            className={styles.button}
            disabled={isLoading}
          >
            {isLoading ? 'Connecting...' : 'Login'}
          </button>

          <p className={styles.forgotLink}>Forgot API Key?</p>
        </form>
      </div>
    </div>
  )
}

export default Login
