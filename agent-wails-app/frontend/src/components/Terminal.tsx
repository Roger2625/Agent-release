import { useState, useRef, useEffect } from 'react'
import styles from './Terminal.module.css'

interface TerminalProps {
  onExecuteCommand: (command: string) => Promise<string>
  history: Array<{
    command: string
    output: string
    timestamp: string
    success: boolean
  }>
}

function Terminal({ onExecuteCommand, history }: TerminalProps) {
  const [input, setInput] = useState('')
  const [isExecuting, setIsExecuting] = useState(false)
  const terminalRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [history])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!input.trim() || isExecuting) return

    setIsExecuting(true)
    const command = input.trim()
    setInput('')

    try {
      await onExecuteCommand(command)
    } catch (error) {
      console.error('Command execution failed:', error)
    } finally {
      setIsExecuting(false)
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString()
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Terminal</h2>
        <div className={styles.status}>
          {isExecuting ? (
            <span className={styles.executing}>Executing...</span>
          ) : (
            <span className={styles.ready}>Ready</span>
          )}
        </div>
      </div>

      <div className={styles.terminal} ref={terminalRef}>
        {history.length === 0 && (
          <div className={styles.welcome}>
            <p>Welcome to Agent Terminal</p>
            <p>Type a command to get started</p>
          </div>
        )}

        {history.map((item, index) => (
          <div key={index} className={styles.historyItem}>
            <div className={styles.commandLine}>
              <span className={styles.prompt}>$</span>
              <span className={styles.command}>{item.command}</span>
              <span className={styles.timestamp}>{formatTimestamp(item.timestamp)}</span>
            </div>
            {item.output && (
              <div className={`${styles.output} ${!item.success ? styles.error : ''}`}>
                {item.output}
              </div>
            )}
          </div>
        ))}
      </div>

      <form className={styles.inputForm} onSubmit={handleSubmit}>
        <span className={styles.inputPrompt}>$</span>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter command..."
          className={styles.input}
          disabled={isExecuting}
          autoFocus
        />
      </form>
    </div>
  )
}

export default Terminal
