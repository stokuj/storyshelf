import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

vi.mock('../../api', () => ({
  fetchBookDetails: vi.fn(),
  fetchReviews: vi.fn(),
  addToBookshelf: vi.fn(),
  updateBookshelfStatus: vi.fn(),
  removeFromBookshelf: vi.fn(),
  createReview: vi.fn(),
}))

vi.mock('../../auth', () => ({
  authState: { authenticated: false, initialized: true },
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { id: '1' } }),
}))

import { fetchBookDetails, fetchReviews } from '../../api'
import BookDetailView from '../BookDetailView.vue'

const stubComponents = {
  global: {
    stubs: {
      RouterLink: { template: '<a><slot /></a>' },
      AlertMessage: { template: '<div />' },
      LoadingSpinner: { template: '<div />' },
      NotFoundState: { template: '<div />' },
    },
  },
}

describe('BookDetailView — API contract', () => {
  beforeEach(() => {
    fetchReviews.mockResolvedValue([])
  })

  it('renders avg_rating from backend response', async () => {
    fetchBookDetails.mockResolvedValue({
      book: { id: 1, title: 'Dune', author: 'Herbert', avg_rating: 4.5, ratingsCount: 10 },
      shelfEntry: null,
      characters: [],
      relations: [],
    })

    const wrapper = mount(BookDetailView, stubComponents)
    await flushPromises()

    expect(wrapper.text()).toContain('4.5')
  })

  it('does NOT render undefined for rating', async () => {
    fetchBookDetails.mockResolvedValue({
      book: { id: 1, title: 'Dune', author: 'Herbert', avg_rating: 4.5, ratingsCount: 10 },
      shelfEntry: null,
      characters: [],
      relations: [],
    })

    const wrapper = mount(BookDetailView, stubComponents)
    await flushPromises()

    expect(wrapper.text()).not.toContain('undefined')
  })

  it('shows review error when reviews fail to load', async () => {
    fetchBookDetails.mockResolvedValue({
      book: { id: 1, title: 'Dune', author: 'Herbert', avg_rating: 0, ratingsCount: 0 },
      shelfEntry: null,
      characters: [],
      relations: [],
    })
    fetchReviews.mockRejectedValue(new Error('Network error'))

    const wrapper = mount(BookDetailView, {
      global: {
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
          AlertMessage: { props: ['message'], template: '<div class="alert">{{ message }}</div>' },
          LoadingSpinner: { template: '<div />' },
          NotFoundState: { template: '<div />' },
        },
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('recenzji')
  })

  it('renders relation_type from backend response', async () => {
    fetchBookDetails.mockResolvedValue({
      book: { id: 1, title: 'Dune', author: 'Herbert', avg_rating: 3.0, ratingsCount: 2 },
      shelfEntry: null,
      characters: [],
      relations: [
        { id: 1, sourceCharacterName: 'Paul', targetCharacterName: 'Jessica', relation_type: 'matka' },
      ],
    })

    const wrapper = mount(BookDetailView, stubComponents)
    await flushPromises()

    expect(wrapper.text()).toContain('matka')
  })
})
