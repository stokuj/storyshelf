import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import BookDetailView from './views/BookDetailView.vue'
import LoginView from './views/LoginView.vue'
import RegisterView from './views/RegisterView.vue'
import BookshelfView from './views/BookshelfView.vue'
import ProfileView from './views/ProfileView.vue'
import SettingsView from './views/SettingsView.vue'
import AdminLayoutView from './views/admin/AdminLayoutView.vue'
import AdminBooksView from './views/admin/AdminBooksView.vue'
import AdminAuthorsView from './views/admin/AdminAuthorsView.vue'
import AdminSeriesView from './views/admin/AdminSeriesView.vue'
import { authState, refreshAuth } from './auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/book/:id',
      name: 'book-detail',
      component: BookDetailView,
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
    },
    {
      path: '/bookshelf',
      name: 'bookshelf',
      component: BookshelfView,
    },
    {
      path: '/profile/:username',
      name: 'profile',
      component: ProfileView,
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
    },
    {
      path: '/admin',
      component: AdminLayoutView,
      meta: { requiresAuth: true, requiresModerator: true },
      children: [
        {
          path: '',
          redirect: '/admin/books',
        },
        {
          path: 'books',
          name: 'admin-books',
          component: AdminBooksView,
        },
        {
          path: 'authors',
          name: 'admin-authors',
          component: AdminAuthorsView,
        },
        {
          path: 'series',
          name: 'admin-series',
          component: AdminSeriesView,
        },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  if (!authState.initialized) {
    await refreshAuth()
  }

  if (to.meta.requiresAuth && !authState.authenticated) {
    return { path: '/login', query: { next: to.fullPath } }
  }

  if (to.meta.requiresModerator && authState.role !== 'MODERATOR') {
    return { path: '/' }
  }

  return true
})

export default router
