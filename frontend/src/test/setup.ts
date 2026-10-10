import { resetStore } from '@/api/store'
import { mockFetch } from './mockFetch'

// The fake store is module state: every test starts from the fixtures
afterEach(resetStore)
// Every test starts logged in; auth tests override routes with mockFetch({...})
beforeEach(() => mockFetch())
