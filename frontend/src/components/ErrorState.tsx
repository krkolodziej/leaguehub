import { errorMessage } from '../lib/errors'

type ErrorStateProps = { error: unknown; retry?: () => void }

export function ErrorState({ error, retry }: ErrorStateProps) {
  return (
    <div className="state-message error-message" role="alert">
      <p>{errorMessage(error)}</p>
      {retry && <button className="button button-secondary" onClick={retry}>Try again</button>}
    </div>
  )
}
