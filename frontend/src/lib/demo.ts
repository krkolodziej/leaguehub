export type DemoAccount = {
  email: string
  password: string
}

const DEFAULT_EMAIL = 'demo@leaguehub.app'
const DEFAULT_PASSWORD = 'demo1234'

/**
 * The demo account offered on the sign-in screen, or null when the deployment
 * has switched it off by building with an empty `VITE_DEMO_EMAIL`.
 */
export function getDemoAccount(): DemoAccount | null {
  const email = (import.meta.env.VITE_DEMO_EMAIL as string | undefined) ?? DEFAULT_EMAIL
  const password = (import.meta.env.VITE_DEMO_PASSWORD as string | undefined) ?? DEFAULT_PASSWORD
  if (!email) return null
  return { email, password }
}
