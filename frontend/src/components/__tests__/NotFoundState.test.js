import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import NotFoundState from '../NotFoundState.vue'

describe('NotFoundState', () => {
  it('renders the title', () => {
    const wrapper = mount(NotFoundState, {
      props: { title: 'Nie znaleziono' },
    })

    expect(wrapper.text()).toContain('Nie znaleziono')
  })

  it('renders the message when provided', () => {
    const wrapper = mount(NotFoundState, {
      props: { title: 'Test', message: 'Opis błędu' },
    })

    expect(wrapper.text()).toContain('Opis błędu')
  })

  it('does not render message when not provided', () => {
    const wrapper = mount(NotFoundState, {
      props: { title: 'Test' },
    })

    const paragraphs = wrapper.findAll('p')
    const messagePara = paragraphs.filter(p => p.text() !== '')
    expect(messagePara.length).toBe(0)
  })

  it('renders the home link by default', () => {
    const wrapper = mount(NotFoundState, {
      props: { title: 'Test' },
      global: {
        stubs: {
          RouterLink: {
            template: '<a><slot /></a>',
          },
        },
      },
    })

    expect(wrapper.text()).toContain('Wróć do strony głównej')
  })

  it('hides home link when homeLink prop is false', () => {
    const wrapper = mount(NotFoundState, {
      props: { title: 'Test', homeLink: false },
      global: {
        stubs: {
          RouterLink: {
            template: '<a><slot /></a>',
          },
        },
      },
    })

    expect(wrapper.text()).not.toContain('Wróć do strony głównej')
  })

  it('home link points to "/"', () => {
    const wrapper = mount(NotFoundState, {
      props: { title: 'Test' },
      global: {
        stubs: {
          RouterLink: {
            template: '<a :href="to"><slot /></a>',
            props: ['to'],
          },
        },
      },
    })

    const link = wrapper.find('a')
    expect(link.attributes('href')).toBe('/')
  })
})
