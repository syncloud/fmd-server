import { Page } from '@playwright/test'

export async function loginViaAuthelia (page: Page, username: string, password: string) {
  await page.waitForURL((url) => url.host.startsWith('auth.'))

  await page.locator('input#username-textfield').fill(username)
  await page.locator('input#password-textfield').fill(password)
  await page.locator('button#sign-in-button').click()
}
