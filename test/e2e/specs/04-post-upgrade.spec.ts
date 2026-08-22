import { test, expect } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import { loadAccount } from '../helpers/account'

test('the phone paired before the refresh is still there', async ({ page }, info) => {
  const account = loadAccount()

  await page.goto('/')
  await page.locator('input[autocomplete="username"]').fill(account.username)
  await page.locator('input[autocomplete="current-password"]').fill(account.password)
  await page.locator('button[type="submit"]').click()

  await expect(page.getByText(`${account.battery}%`)).toBeVisible({ timeout: 90_000 })
  await expect(page.locator('.leaflet-container')).toBeVisible()
  await shoot(page, info, 'after-upgrade')
})
