import { reactive } from 'vue'
import { fetchAuthMe, logoutUser } from './api'

export const authState = reactive({
  initialized: false,
  authenticated: false,
  email: null,
  username: null,
  role: null,
})

function applySession(data) {
  authState.initialized = true
  authState.authenticated = Boolean(data?.authenticated)
  authState.email = data?.email ?? null
  authState.username = data?.username ?? null
  authState.role = data?.role ?? null
}

export async function refreshAuth() {
  try {
    const session = await fetchAuthMe()
    applySession(session)
  } catch {
    applySession(null)
  }
}

export function setAuthenticatedUser(data) {
  applySession({ authenticated: true, ...data })
}

export async function signOut() {
  await logoutUser()
  applySession(null)
}
