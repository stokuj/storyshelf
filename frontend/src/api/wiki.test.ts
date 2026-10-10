import { getPage } from './wiki'

test('a crafted page path is rejected before any request', async () => {
  vi.mocked(fetch).mockClear()
  await expect(getPage('/x/../../users/me/?a=.md')).rejects.toMatchObject({ status: 404 })
  expect(fetch).not.toHaveBeenCalled()
})
