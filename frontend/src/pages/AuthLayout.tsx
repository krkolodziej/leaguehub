import { Outlet } from 'react-router-dom'

import { Brand } from '../components/Brand'

export function AuthLayout() {
  return (
    <main className="grid min-h-screen place-items-center bg-paper px-4 py-8">
      <div className="w-full max-w-[26rem] border border-chalk bg-paper-raised p-6 sm:p-8">
        <Brand to="/" />
        <Outlet />
      </div>
    </main>
  )
}
