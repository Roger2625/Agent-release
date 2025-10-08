import styles from './Sidebar.module.css'

interface SidebarProps {
  activeView: string
  onViewChange: (view: string) => void
  onLogout: () => void
}

function Sidebar({ activeView, onViewChange, onLogout }: SidebarProps) {
  const menuItems = [
    { id: 'terminal', label: 'Terminal', icon: '>' },
    { id: 'reports', label: 'Reports', icon: '📄' },
    { id: 'settings', label: 'Settings', icon: '⚙' },
  ]

  return (
    <div className={styles.sidebar}>
      <div className={styles.header}>
        <h2 className={styles.title}>AGENT</h2>
      </div>

      <nav className={styles.nav}>
        {menuItems.map((item) => (
          <button
            key={item.id}
            className={`${styles.navItem} ${activeView === item.id ? styles.active : ''}`}
            onClick={() => onViewChange(item.id)}
          >
            <span className={styles.icon}>{item.icon}</span>
            <span className={styles.label}>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className={styles.footer}>
        <button className={styles.logoutButton} onClick={onLogout}>
          Logout
        </button>
      </div>
    </div>
  )
}

export default Sidebar
