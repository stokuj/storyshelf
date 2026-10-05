import { listPages } from '@/api/store'
import { groupByType, pagePath, pageSplat, universeMembers } from '@/wiki'

const pages = listPages()

test('groupByType puts every page in its type group', () => {
  const groups = groupByType(pages)
  expect(groups.book).toHaveLength(3)
  expect(groups.character).toHaveLength(8)
  expect(groups.place).toHaveLength(3)
  expect(groups.universe).toHaveLength(1)
})

test('universeMembers resolves characters and places through their book', () => {
  const m = universeMembers(pages, '/universes/wiedzmin.md')
  expect(m.books.map((p) => p.path).sort()).toEqual([
    '/books/krew-elfow.md',
    '/books/ostatnie-zyczenie.md',
  ])
  expect(m.characters).toHaveLength(5)
  expect(m.places).toHaveLength(2)
  const all = [...m.books, ...m.characters, ...m.places]
  expect(all.some((p) => p.path.includes('solaris'))).toBe(false)
})

test('pagePath reverses pageSplat', () => {
  expect(pageSplat('/books/krew-elfow.md')).toBe('books/krew-elfow')
  for (const p of pages) expect(pagePath(pageSplat(p.path))).toBe(p.path)
})
