import { useState } from 'react'

import { useMarkNotificationRead, useNotifications } from '../lib/notifications'

export function NotificationsMenu() {
  const [open, setOpen] = useState(false)
  const notifications = useNotifications()
  const markRead = useMarkNotificationRead()
  const unreadCount = notifications.data?.filter((item) => !item.read_at).length ?? 0

  return <div className="notifications-menu"><button className="button button-ghost notification-button" onClick={() => setOpen((value) => !value)} aria-expanded={open}>Notifications{unreadCount > 0 && <span className="notification-count">{unreadCount}</span>}</button>{open && <div className="notification-popover"><div className="notification-header"><strong>Notifications</strong>{unreadCount > 0 && <span className="muted">{unreadCount} unread</span>}</div>{notifications.isPending ? <p className="muted">Loading notifications…</p> : notifications.isError ? <p className="error-message">Could not load notifications.</p> : notifications.data.length === 0 ? <p className="muted">No notifications yet.</p> : <div className="notification-list">{notifications.data.slice(0, 10).map((item) => <button className={item.read_at ? 'notification-item read' : 'notification-item'} key={item.id} onClick={() => { if (!item.read_at) markRead.mutate(item.id) }}><strong>{item.title}</strong><span>{item.message}</span><small>{formatNotificationDate(item.created_at)}</small></button>)}</div>}</div>}</div>
}

function formatNotificationDate(value: string) { return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value)) }
