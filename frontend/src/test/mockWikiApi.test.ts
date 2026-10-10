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

const create = (body: unknown) =>
  api<{ path: string; content: string }>('/wiki/pages/', {
    method: 'POST',
    body: JSON.stringify(body),
  })

test('POST builds the backend Path and Template for a character', async () => {
  const page = await create({ type: 'character', title: 'Ciri', book: '/books/krew-elfow.md' })
  expect(page.path).toBe('/characters/ciri--krew-elfow.md')
  expect(page.content).toContain('book: "/books/krew-elfow.md"')
  expect(page.content).toContain('status: draft')
  expect(page.content).toContain('## Rola w książce')
})

test('POST of a universe has only the Template heading Opis', async () => {
  const page = await create({ type: 'universe', title: 'Ziemiomorze' })
  expect(page.path).toBe('/universes/ziemiomorze.md')
  expect(page.content).toContain('## Opis')
  expect(page.content).not.toContain('## Streszczenie')
})

test('POST on a taken Path is 409, a character without a book is 400', async () => {
  const taken = await create({ type: 'book', title: 'Solaris' }).catch((e: unknown) => e)
  expect((taken as ApiError).status).toBe(409)
  const noBook = await create({ type: 'place', title: 'Ithaka' }).catch((e: unknown) => e)
  expect((noBook as ApiError).status).toBe(400)
  expect((noBook as ApiError).body).toEqual({ book: ['This field is required.'] })
})
