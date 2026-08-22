import { test, expect } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import { loginViaAuthelia } from '../helpers/auth'
import { register, requestAccess, uploadLocation } from '../helpers/fmd'

const syncloudUser = process.env.PLAYWRIGHT_USER!
const syncloudPassword = process.env.PLAYWRIGHT_PASSWORD!

const devicePassword = 'Str0ngTestPassword1'
const battery = 73

test('pairs a phone with the registration token and shows where it is', async ({ page, request }, info) => {
  await page.goto('/')
  await shoot(page, info, 'fmd-login')

  await page.locator('a[href="/syncloud"]').click()
  await loginViaAuthelia(page, syncloudUser, syncloudPassword)

  await expect(page).toHaveURL(/\/syncloud$/)
  const token = (await page.locator('.token').innerText()).trim()
  expect(token).toMatch(/^[0-9a-f]{32}$/)
  await shoot(page, info, 'token-page')

  const username = 'pw-' + Date.now().toString(36)
  const account = await register(request, token, username, devicePassword)
  const accessToken = await requestAccess(request, account)
  await uploadLocation(request, account, accessToken, {
    lat: 52.3676,
    lon: 4.9041,
    bat: battery,
    date: Date.now(),
    time: new Date().toISOString(),
    provider: 'playwright'
  })

  await page.goto('/')
  await page.locator('input[autocomplete="username"]').fill(username)
  await page.locator('input[autocomplete="current-password"]').fill(devicePassword)
  await shoot(page, info, 'fmd-login-filled')
  await page.locator('button[type="submit"]').click()

  await expect(page.getByText(`${battery}%`)).toBeVisible({ timeout: 90_000 })
  await expect(page.locator('.leaflet-container')).toBeVisible()
  await shoot(page, info, 'fmd-located')
})

test('registration without the token is refused', async ({ request }) => {
  const response = await request.put('/api/v1/device', {
    data: { Salt: 'x', HashedPassword: 'x', PubKey: 'x', PrivKey: 'x', RequestedUsername: 'nope' }
  })
  expect(response.status()).toBe(401)
})
