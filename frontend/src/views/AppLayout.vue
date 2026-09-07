<template>
  <v-app>
    <v-navigation-drawer v-model="drawer" app :permanent="!isMobile">
      <v-list>
        <v-list-item
          prepend-icon="mdi-school"
          title="Учёт имущества"
          subtitle="Школа"
          class="px-4 pt-3 pb-2"
        />
        <v-divider class="my-2" />

        <v-list-item
          v-for="item in navItems"
          :key="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
          :to="item.to"
          :value="item.to"
          color="primary"
        />
      </v-list>

      <template #append>
        <v-divider class="mb-2" />
        <v-list>
          <v-list-item :title="user?.full_name ?? 'Пользователь'" prepend-icon="mdi-account">
            <template #append>
              <v-btn icon="mdi-logout" size="small" variant="text" @click="handleLogout" />
            </template>
          </v-list-item>
        </v-list>
      </template>
    </v-navigation-drawer>

    <v-app-bar app color="primary" dark>
      <v-app-bar-nav-icon @click="drawer = !drawer" />
      <v-app-bar-title>{{ currentTitle }}</v-app-bar-title>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const { mobile } = useDisplay()
const auth = useAuthStore()

const drawer = ref(true)
const isMobile = computed(() => mobile.value)

const user = computed(() => auth.user)

const navItems = [
  { title: 'Дашборд', icon: 'mdi-view-dashboard', to: '/' },
  { title: 'Имущество', icon: 'mdi-package-variant', to: '/assets' },
  { title: 'Помещения', icon: 'mdi-door-open', to: '/rooms' },
  { title: 'Инвентаризация', icon: 'mdi-clipboard-check', to: '/inventory' },
  { title: 'Отчёты', icon: 'mdi-file-chart', to: '/reports' },
]

if (auth.isAdmin || auth.hasRole(['MUNICIPALITY', 'INSPECTOR'])) {
  navItems.push({ title: 'Аудит', icon: 'mdi-history', to: '/audit' })
}

const titles: Record<string, string> = {
  dashboard: 'Дашборд',
  assets: 'Имущество',
  'asset-detail': 'Карточка имущества',
  rooms: 'Помещения',
  inventory: 'Инвентаризация',
  reports: 'Отчёты',
  users: 'Пользователи',
  audit: 'Журнал аудита',
}

const currentTitle = computed(() => titles[String(route.name)] ?? 'Учёт имущества')

function handleLogout(): void {
  auth.logout()
  router.push({ name: 'login' })
}

onMounted(() => {
  void auth.fetchMe()
})
</script>