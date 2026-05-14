import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'

vi.mock('../../auth', () => ({
  authState: { initialized: true, authenticated: false, username: null },
  signOut: vi.fn(),
}))

import App from '../../App.vue'

const stubs = {
  global: {
    stubs: {
      RouterLink: { template: '<a><slot /></a>' },
      RouterView: { template: '<div />' },
    },
  },
}

describe('App.vue — hamburger accessibility', () => {
  it('hamburger button has aria-expanded=false when closed', () => {
    const wrapper = mount(App, stubs)
    const btn = wrapper.find('button[aria-label="Menu"]')
    expect(btn.attributes('aria-expanded')).toBe('false')
  })

  it('hamburger button has aria-expanded=true after click', async () => {
    const wrapper = mount(App, stubs)
    const btn = wrapper.find('button[aria-label="Menu"]')
    await btn.trigger('click')
    expect(btn.attributes('aria-expanded')).toBe('true')
  })

  it('Enter key opens the menu', async () => {
    const wrapper = mount(App, stubs)
    const btn = wrapper.find('button[aria-label="Menu"]')
    await btn.trigger('keydown', { key: 'Enter' })
    expect(btn.attributes('aria-expanded')).toBe('true')
  })

  it('Space key opens the menu', async () => {
    const wrapper = mount(App, stubs)
    const btn = wrapper.find('button[aria-label="Menu"]')
    await btn.trigger('keydown', { key: ' ' })
    expect(btn.attributes('aria-expanded')).toBe('true')
  })

  it('dropdown has role="menu" when open', async () => {
    const wrapper = mount(App, stubs)
    const btn = wrapper.find('button[aria-label="Menu"]')
    await btn.trigger('click')
    expect(wrapper.find('ul[role="menu"]').exists()).toBe(true)
  })
})
