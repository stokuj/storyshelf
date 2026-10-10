import { resetStore } from '@/api/store'
import { mockWikiApi } from './mockWikiApi'

// The fake store is module state: every test starts from the seed
afterEach(resetStore)
// Every test starts logged in with the backend fixtures served; override with mockWikiApi({...}) or mockFetch({...})
beforeEach(() => mockWikiApi())
