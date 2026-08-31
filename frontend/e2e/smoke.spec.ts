import { expect, test } from '@playwright/test'

test('anonymous visitor can open the login page', async ({ page }) => {
  await page.route('**/api/v1/auth/me/', (route) => route.fulfill({ status: 401, contentType: 'application/json', body: '{"detail":"Authentication credentials were not provided."}' }))
  await page.goto('/login')
  await expect(page.getByRole('heading', { name: 'Sign in to LeagueHub' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Create an account' })).toBeVisible()
})
