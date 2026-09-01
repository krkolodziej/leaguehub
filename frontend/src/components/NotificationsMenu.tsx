import { Bell } from 'lucide-react'

import { useMarkNotificationRead, useNotifications } from '../lib/notifications'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from './ui/dropdown-menu'

export function NotificationsMenu() {
  const notifications = useNotifications()
  const markRead = useMarkNotificationRead()
  const unreadCount = notifications.data?.filter((item) => !item.read_at).length ?? 0

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="relative grid size-9 place-items-center rounded-[var(--radius-control)] text-ink-muted transition-colors hover:bg-ink/[0.06] hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pitch/40"
        aria-label={unreadCount > 0 ? `Notifications, ${unreadCount} unread` : 'Notifications'}
      >
        <Bell className="size-[18px]" aria-hidden="true" />
        {unreadCount > 0 && (
          <span className="absolute right-1 top-1 grid min-w-4 place-items-center rounded-full bg-pitch px-1 font-condensed text-[0.625rem] font-bold leading-4 text-white">
            {unreadCount}
          </span>
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>
          Notifications
          {unreadCount > 0 && <span className="font-normal normal-case tracking-normal text-ink-muted">{unreadCount} unread</span>}
        </DropdownMenuLabel>
        {notifications.isPending ? (
          <p className="px-4 py-6 text-center text-sm text-ink-muted">Loading notifications…</p>
        ) : notifications.isError ? (
          <p className="border-l-[3px] border-ink px-4 py-4 text-sm text-ink">
            Could not load notifications. Reopen this menu to try again.
          </p>
        ) : notifications.data.length === 0 ? (
          <p className="px-4 py-6 text-center text-sm text-ink-muted">
            Nothing yet. Finished matches and upcoming kick-offs will land here.
          </p>
        ) : (
          <div className="max-h-80 overflow-y-auto">
            {notifications.data.slice(0, 10).map((item) => (
              <DropdownMenuItem
                key={item.id}
                onSelect={(event) => {
                  event.preventDefault()
                  if (!item.read_at) markRead.mutate(item.id)
                }}
              >
                <span className="flex items-baseline gap-2">
                  {!item.read_at && (
                    <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-pitch" aria-hidden="true" />
                  )}
                  <span className="font-condensed text-sm font-semibold text-ink">{item.title}</span>
                </span>
                <span className="mt-0.5 block text-sm text-ink-muted">{item.message}</span>
                <span className="mt-1 block text-2xs uppercase tracking-[0.08em] text-ink-muted">
                  {formatNotificationDate(item.created_at)}
                </span>
              </DropdownMenuItem>
            ))}
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function formatNotificationDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value))
}
