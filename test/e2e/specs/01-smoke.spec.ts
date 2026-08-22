import { test, expect } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import { loginViaAuthelia } from '../helpers/auth'

const username = process.env.PLAYWRIGHT_USER!
const password = process.env.PLAYWRIGHT_PASSWORD!

test('serves the fmd login screen', async ({ page }, info) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/FMD Server/i)
  await expect(page.locator('#root')).not.toBeEmpty()
  await expect(page.locator('input[type="password"]')).toBeVisible()
  await shoot(page, info, 'fmd-login')
})

test('token page is reachable from the login screen after syncloud login', async ({ page }, info) => {
  await page.goto('/')
  const link = page.locator('a[href="/syncloud"]')
  await expect(link).toBeVisible()
  await link.click()

  await loginViaAuthelia(page, username, password)

  await expect(page).toHaveURL(/\/syncloud$/)
  await expect(page.locator('.token')).not.toBeEmpty()
  await shoot(page, info, 'fmd-token-page')
})

test('serves the api the fmd app talks to', async ({ request }) => {
  const response = await request.get('/api/v1/version', { maxRedirects: 0 })
  expect(response.status()).toBe(200)
  expect((await response.text()).trim()).not.toBe('')
})
