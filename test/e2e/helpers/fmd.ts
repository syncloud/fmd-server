import { argon2id } from '@noble/hashes/argon2.js'
import type { APIRequestContext } from '@playwright/test'

const ARGON2 = { t: 1, p: 4, m: 131072, dkLen: 32 }
const LOGIN_CONTEXT = 'context:loginAuthentication'
const KEY_WRAP_CONTEXT = 'context:asymmetricKeyWrap'

const encoder = new TextEncoder()

const encode = (bytes: Uint8Array) => Buffer.from(bytes).toString('base64')
const decode = (text: string) => new Uint8Array(Buffer.from(text, 'base64'))

const join = (...parts: Uint8Array[]) => {
  const all = new Uint8Array(parts.reduce((size, part) => size + part.length, 0))
  let offset = 0
  for (const part of parts) {
    all.set(part, offset)
    offset += part.length
  }
  return all
}

const pem = (label: string, bytes: Uint8Array) =>
  `-----BEGIN ${label}-----\n${encode(bytes).replace(/(.{64})/g, '$1\n')}\n-----END ${label}-----`

export const loginHash = (password: string, salt: string) => {
  const hash = argon2id(encoder.encode(LOGIN_CONTEXT + password), decode(salt), ARGON2)
  const hashBase64 = encode(hash).replace(/=+$/, '')
  return `$argon2id$v=19$m=${ARGON2.m},t=${ARGON2.t},p=${ARGON2.p}$${salt}$${hashBase64}`
}

const wrapPrivateKey = async (password: string, privateKeyPem: string) => {
  const salt = crypto.getRandomValues(new Uint8Array(16))
  const iv = crypto.getRandomValues(new Uint8Array(12))

  const raw = argon2id(encoder.encode(KEY_WRAP_CONTEXT + password), salt, ARGON2)
  const key = await crypto.subtle.importKey('raw', raw, 'AES-GCM', false, ['encrypt'])
  const wrapped = new Uint8Array(
    await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, encoder.encode(privateKeyPem))
  )

  return encode(join(salt, iv, wrapped))
}

export const encryptForDevice = async (publicKey: CryptoKey, plaintext: string) => {
  const rawAesKey = crypto.getRandomValues(new Uint8Array(32))
  const iv = crypto.getRandomValues(new Uint8Array(12))

  const aesKey = await crypto.subtle.importKey('raw', rawAesKey, 'AES-GCM', false, ['encrypt'])
  const data = new Uint8Array(
    await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, aesKey, encoder.encode(plaintext))
  )
  const wrappedAesKey = new Uint8Array(
    await crypto.subtle.encrypt({ name: 'RSA-OAEP' }, publicKey, rawAesKey)
  )

  return encode(join(wrappedAesKey, iv, data))
}

const call = async (request: APIRequestContext, method: 'put' | 'post', path: string, data: object) => {
  const response = await request[method](path, { data })
  const body = await response.text()
  if (response.status() !== 200) {
    throw new Error(`${method.toUpperCase()} ${path} failed with ${response.status()}: ${body}`)
  }
  return body
}

export interface Account {
  username: string
  password: string
  publicKey: CryptoKey
}

export interface Location {
  lat: number
  lon: number
  bat: number
  date: number
  time: string
  provider: string
}

export const register = async (
  request: APIRequestContext,
  registrationToken: string,
  username: string,
  password: string
): Promise<Account> => {
  const salt = encode(crypto.getRandomValues(new Uint8Array(16)))

  const keys = await crypto.subtle.generateKey(
    {
      name: 'RSA-OAEP',
      modulusLength: 3072,
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: 'SHA-256'
    },
    true,
    ['encrypt', 'decrypt']
  )

  const privateKey = new Uint8Array(await crypto.subtle.exportKey('pkcs8', keys.privateKey))
  const publicKey = new Uint8Array(await crypto.subtle.exportKey('spki', keys.publicKey))

  await call(request, 'put', '/api/v1/device', {
    Salt: salt,
    HashedPassword: loginHash(password, salt),
    PubKey: pem('PUBLIC KEY', publicKey),
    PrivKey: await wrapPrivateKey(password, pem('PRIVATE KEY', privateKey)),
    RequestedUsername: username,
    RegistrationToken: registrationToken
  })

  return { username, password, publicKey: keys.publicKey }
}

export const requestAccess = async (request: APIRequestContext, account: Account) => {
  const salt = JSON.parse(
    await call(request, 'put', '/api/v1/salt', { IDT: account.username, Data: 'unused' })
  ).Data as string

  const access = JSON.parse(
    await call(request, 'put', '/api/v1/requestAccess', {
      IDT: account.username,
      Data: loginHash(account.password, salt),
      SessionDurationSeconds: 0
    })
  ).Data as string

  return access
}

export const uploadLocation = async (
  request: APIRequestContext,
  account: Account,
  accessToken: string,
  location: Location
) => {
  await call(request, 'post', '/api/v1/location', {
    IDT: accessToken,
    Data: await encryptForDevice(account.publicKey, JSON.stringify(location))
  })
}
