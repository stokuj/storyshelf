import { getPage, listPages } from '@/api/store'
import {
  addVerified,
  groupByType,
  pagePath,
  pageSplat,
  parsePage,
  universeMembers,
  validateEdit,
} from '@/wiki'

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

test('parsePage splits frontmatter from body', () => {
  const { frontmatter, body } = parsePage(getPage('/books/ostatnie-zyczenie.md').content)
  expect(frontmatter.type).toBe('book')
  expect(frontmatter.verified?.[0].by).toBe('human:stokuj')
  expect(body.startsWith('## Streszczenie')).toBe(true)
})

test('parsePage rejects content without frontmatter', () => {
  expect(() => parsePage('## Just a body')).toThrow('Missing frontmatter')
})

const OZ = getPage('/books/ostatnie-zyczenie.md').content

test('parsePage accepts CRLF line endings', () => {
  const crlf = parsePage(OZ.replaceAll('\n', '\r\n'))
  expect(crlf.frontmatter).toEqual(parsePage(OZ).frontmatter)
  expect(crlf.body.startsWith('## Streszczenie')).toBe(true)
})

test('parsePage treats an empty frontmatter block as {}', () => {
  expect(parsePage('---\n---\n## Opis\n')).toEqual({ frontmatter: {}, body: '## Opis\n' })
})

test('every fixture page passes validateEdit', () => {
  for (const p of pages) expect(validateEdit(p.content, p.type), p.path).toBeNull()
})

test('validateEdit accepts CRLF content', () => {
  expect(validateEdit(OZ.replaceAll('\n', '\r\n'), 'book')).toBeNull()
})

test('validateEdit rejects broken YAML', () => {
  expect(validateEdit(OZ.replace('type: book', 'type: [book'), 'book')).toMatch(
    /^Invalid frontmatter: /,
  )
})

test('validateEdit rejects a frontmatter that is not a mapping', () => {
  expect(validateEdit('---\njust text\n---\n## Opis\n', 'universe')).toBe(
    'Invalid frontmatter: not a mapping',
  )
})

test('validateEdit rejects a type change', () => {
  expect(validateEdit(OZ.replace('type: book', 'type: universe'), 'book')).toBe(
    "Page type can't change",
  )
})

test('validateEdit lists missing template headings', () => {
  const content = OZ.replace('## Postacie\n', '').replace('## Miejsca\n', '')
  expect(validateEdit(content, 'book')).toBe('Missing template headings: Postacie, Miejsca')
})

test('addVerified appends to an existing verified list and keeps the body', () => {
  const out = addVerified(OZ, 'human:stokuj', '2026-10-05T10:00:00.000Z')
  expect(parsePage(out).frontmatter.verified).toEqual([
    { by: 'human:stokuj', at: '2026-10-02T08:30:00Z' },
    { by: 'human:stokuj', at: '2026-10-05T10:00:00.000Z' },
  ])
  expect(parsePage(out).body).toBe(parsePage(OZ).body)
})

test('addVerified reports broken YAML like validateEdit does', () => {
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
