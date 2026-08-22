import { test, expect } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import { loginViaAuthelia } from '../helpers/auth'
import { register, requestAccess, uploadLocation } from '../helpers/fmd'
import { saveAccount } from '../helpers/account'

const syncloudUser = process.env.PLAYWRIGHT_USER!
const syncloudPassword = process.env.PLAYWRIGHT_PASSWORD!

const password = 'Str0ngUpgradePassword1'
const battery = 42

test('pairs a phone on the released version', async ({ page, request }, info) => {
  await page.goto('/')
  await page.locator('a[href="/syncloud"]').click()
  await loginViaAuthelia(page, syncloudUser, syncloudPassword)
  const token = (await page.locator('.token').innerText()).trim()

  const username = 'upgrade-' + Date.now().toString(36)
  const account = await register(request, token, username, password)
  const accessToken = await requestAccess(request, account)
  await uploadLocation(request, account, accessToken, {
    lat: 48.8584,
    lon: 2.2945,
    bat: battery,
    date: Date.now(),
    time: new Date().toISOString(),
    provider: 'playwright-pre-upgrade'
  })
  saveAccount({ username, password, battery })

  await page.goto('/')
  await page.locator('input[autocomplete="username"]').fill(username)
  await page.locator('input[autocomplete="current-password"]').fill(password)
  await page.locator('button[type="submit"]').click()

  await expect(page.getByText(`${battery}%`)).toBeVisible({ timeout: 90_000 })
  await shoot(page, info, 'before-upgrade')
})
