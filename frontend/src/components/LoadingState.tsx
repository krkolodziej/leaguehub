type LoadingStateProps = { label?: string }

export function LoadingState({ label = 'Loading…' }: LoadingStateProps) {
  return <p className="state-message" role="status">{label}</p>
}
