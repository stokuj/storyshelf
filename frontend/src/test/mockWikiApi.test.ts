import { ApiError, api } from '@/api/client'
import type { Paginated } from '@/api/types'

interface Detail {
  version: number
  content: string
}

const SOLARIS = '/wiki/pages/books/solaris.md'

test('serves the backend fixtures', async () => {
  expect(await api<unknown[]>('/wiki/pages/')).toHaveLength(15)
  const page = await api<Detail>(SOLARIS)
  expect(page.content.startsWith('---\ntype: book\n')).toBe(true)
})

test('PUT with the current version adds a Version, a stale one is 409', async () => {
  const { version, content } = await api<Detail>(SOLARIS)
  const put = (base_version: number) =>
    api<Detail>(SOLARIS, {
      method: 'PUT',
      body: JSON.stringify({ content: content + 'x', base_version }),
    })

  const err = await put(version - 1).catch((e: unknown) => e)
  expect((err as ApiError).status).toBe(409)

  expect((await put(version)).version).toBeGreaterThan(version)
  const versions = await api<Paginated<{ kind: string }>>(`${SOLARIS}/versions/`)
  expect(versions.total).toBe(2)
  expect(versions.data[0].kind).toBe('edit')
})

test('unknown page is 404', async () => {
  const err = await api('/wiki/pages/books/nope.md').catch((e: unknown) => e)
  expect((err as ApiError).status).toBe(404)
})
