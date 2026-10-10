import { FIXTURES, summary } from '@/test/mockWikiApi'
import {
  addVerified,
  bookPath,
  groupByType,
  pagePath,
  pageSplat,
  parsePage,
  previewPath,
  slugify,
  universeMembers,
} from '@/wiki'

const pages = Object.entries(FIXTURES).map(([path, content]) => summary(path, content))

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

test('parsePage splits frontmatter from body', () => {
  const { frontmatter, body } = parsePage(FIXTURES['/books/ostatnie-zyczenie.md'])
  expect(frontmatter.type).toBe('book')
  expect(frontmatter.verified?.[0].by).toBe('human:stokuj')
  expect(body.startsWith('## Streszczenie')).toBe(true)
})

test('parsePage rejects content without frontmatter', () => {
  expect(() => parsePage('## Just a body')).toThrow('Missing frontmatter')
})

const OZ = FIXTURES['/books/ostatnie-zyczenie.md']

test('parsePage accepts CRLF line endings', () => {
  const crlf = parsePage(OZ.replaceAll('\n', '\r\n'))
  expect(crlf.frontmatter).toEqual(parsePage(OZ).frontmatter)
  expect(crlf.body.startsWith('## Streszczenie')).toBe(true)
})

test('parsePage treats an empty frontmatter block as {}', () => {
  expect(parsePage('---\n---\n## Opis\n')).toEqual({ frontmatter: {}, body: '## Opis\n' })
})

test('parsePage accepts a UTF-8 BOM', () => {
  expect(parsePage('﻿---\ntype: universe\n---\n## Opis\n').frontmatter.type).toBe('universe')
})

test('addVerified keeps CRLF line endings', () => {
  const out = addVerified(OZ.replaceAll('\n', '\r\n'), 'human:x', 't')
  expect(out.replaceAll('\r\n', '')).not.toContain('\n')
})

test('addVerified appends to an existing verified list and keeps the body', () => {
  const out = addVerified(OZ, 'human:stokuj', '2026-10-05T10:00:00.000Z')
  expect(parsePage(out).frontmatter.verified).toEqual([
    { by: 'human:stokuj', at: '2026-10-02T08:30:00Z' },
    { by: 'human:stokuj', at: '2026-10-05T10:00:00.000Z' },
  ])
  expect(parsePage(out).body).toBe(parsePage(OZ).body)
})

test('addVerified reports broken YAML', () => {
  expect(() => addVerified('---\ntype: [book\n---\n## Opis\n', 'human:x', 't')).toThrow(
    /^Invalid frontmatter: /,
  )
})

test('addVerified creates the verified list when missing', () => {
  const out = addVerified('---\ntype: universe\n---\n## Opis\n', 'human:x', 't')
  expect(parsePage(out)).toEqual({
    frontmatter: { type: 'universe', verified: [{ by: 'human:x', at: 't' }] },
    body: '## Opis\n',
  })
})

test('slugify makes ASCII path slugs', () => {
  expect(slugify('Krew elfów')).toBe('krew-elfow')
  expect(slugify('Ostatnie życzenie')).toBe('ostatnie-zyczenie')
  expect(slugify('Łódź, Ślęża!')).toBe('lodz-sleza')
  expect(slugify('  Diuna: Mesjasz  ')).toBe('diuna-mesjasz')
})

test('bookPath matches every fixture book', () => {
  for (const p of pages.filter((p) => p.type === 'book')) expect(bookPath(p.title)).toBe(p.path)
})

test.each(['books/solaris', 'books/solaris/', 'books/solaris.md', 'books/solaris.md/'])(
  'pagePath normalises %s',
  (splat) => expect(pagePath(splat)).toBe('/books/solaris.md'),
)

test.each([
  ['book', 'Krew elfów', '', '/books/krew-elfow.md'],
  ['universe', 'Wiedźmin', '', '/universes/wiedzmin.md'],
  [
    'character',
    'Geralt',
    '/books/ostatnie-zyczenie.md',
    '/characters/geralt--ostatnie-zyczenie.md',
  ],
  ['place', 'Kaer Morhen', '/books/krew-elfow.md', '/places/kaer-morhen--krew-elfow.md'],
  ['character', 'Geralt', '', null],
  ['book', '  !!  ', '', null],
] as const)('previewPath %s %j %j', (type, title, book, expected) => {
  expect(previewPath(type, title, book)).toBe(expected)
})
