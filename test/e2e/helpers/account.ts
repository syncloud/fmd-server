import * as fs from 'node:fs'
import * as path from 'node:path'

const file = path.resolve('../../build/upgrade-account.json')

export interface SavedAccount {
  username: string
  password: string
  battery: number
}

export const saveAccount = (account: SavedAccount) => {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, JSON.stringify(account))
}

export const loadAccount = (): SavedAccount => {
  if (!fs.existsSync(file)) {
    throw new Error(`${file} is missing, the pre-upgrade spec has to run first`)
  }
  return JSON.parse(fs.readFileSync(file, 'utf8')) as SavedAccount
}
