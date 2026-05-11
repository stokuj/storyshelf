import { createRouter, createWebHistory } from 'vue-router'
import { authState } from './auth'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('./views/HomeView.vue'),
      meta: { title: 'Katalog książek' },
    },
    {
      path: '/book/:id',
      name: 'book-detail',
      component: () => import('./views/BookDetailView.vue'),
      meta: { title: 'Szczegóły książki' },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('./views/LoginView.vue'),
      meta: { title: 'Zaloguj się' },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('./views/RegisterView.vue'),
      meta: { title: 'Utwórz konto' },
    },
    {
      path: '/bookshelf',
      name: 'bookshelf',
      component: () => import('./views/BookshelfView.vue'),
      meta: { title: 'Moja półka', requiresAuth: true },
    },
    {
      path: '/profile/:username',
      name: 'profile',
      component: () => import('./views/ProfileView.vue'),
      meta: { title: 'Profil' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('./views/SettingsView.vue'),
      meta: { title: 'Ustawienia', requiresAuth: true },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('./views/NotFoundView.vue'),
      meta: { title: 'Nie znaleziono' },
    },
  ],
})

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !authState.authenticated) {
    next({ name: 'login', query: { next: to.fullPath } })
  } else {
    next()
  }
})

router.afterEach((to) => {
  const title = to.meta.title
  document.title = title ? `StoryShelf — ${title}` : 'StoryShelf'
})

export default router
