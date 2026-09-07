// Конфигурация маршрутов приложения с guard'ами авторизации.

import { createRouter, createWebHistory } from 'vue-router'
import { getAccessToken } from '@/api/client'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/views/AppLayout.vue'),
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
        },
        {
          path: 'assets',
          name: 'assets',
          component: () => import('@/views/AssetsView.vue'),
        },
        {
          path: 'assets/:id',
          name: 'asset-detail',
          component: () => import('@/views/AssetDetailView.vue'),
        },
        {
          path: 'rooms',
          name: 'rooms',
          component: () => import('@/views/RoomsView.vue'),
        },
        {
          path: 'inventory',
          name: 'inventory',
          component: () => import('@/views/InventoryView.vue'),
        },
        {
          path: 'reports',
          name: 'reports',
          component: () => import('@/views/ReportsView.vue'),
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('@/views/UsersView.vue'),
        },
        {
          path: 'audit',
          name: 'audit',
          component: () => import('@/views/AuditView.vue'),
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach((to) => {
  const isPublic = to.meta.public
  const authed = !!getAccessToken()
  if (!isPublic && !authed) {
    return { name: 'login' }
  }
  if (isPublic && authed) {
    return { name: 'dashboard' }
  }
  return true
})

export default router