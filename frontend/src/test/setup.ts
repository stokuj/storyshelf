import { resetStore } from '@/api/store'

// The fake store is module state: every test starts from the fixtures
afterEach(resetStore)
