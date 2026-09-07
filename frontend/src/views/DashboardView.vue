<template>
  <div class="page-container">
    <v-row>
      <v-col cols="12" md="6" lg="4">
        <v-card>
          <v-card-title>Всего карточек</v-card-title>
          <v-card-text class="text-h3 font-weight-bold text-primary">
            {{ stats?.total ?? '—' }}
          </v-card-text>
        </v-card>
      </v-col>
      <v-col
        v-for="(value, key) in statusNames"
        :key="key"
        cols="6"
        md="3"
        lg="2"
      >
        <v-card>
          <v-card-title class="text-subtitle-1">{{ value }}</v-card-title>
          <v-card-text class="text-h4 font-weight-bold">
            {{ (stats?.by_status as Record<string, number> | undefined)?.[key] ?? 0 }}
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-card class="mt-4">
      <v-card-title>Быстрые действия</v-card-title>
      <v-card-text>
        <v-btn
          v-if="auth.isZavhoz"
          color="primary"
          prepend-icon="mdi-plus"
          :to="{ name: 'assets' }"
          class="mr-2"
        >
          Добавить имущество
        </v-btn>
        <v-btn
          color="secondary"
          prepend-icon="mdi-clipboard-check"
          :to="{ name: 'inventory' }"
          class="mr-2"
        >
          Инвентаризация
        </v-btn>
        <v-btn color="info" prepend-icon="mdi-file-chart" :to="{ name: 'reports' }">
          Отчёты
        </v-btn>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { assetsApi } from '@/api/endpoints'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()

interface AssetStats {
  total: number
  by_status: Record<string, number>
}

const stats = ref<AssetStats | null>(null)

const statusNames: Record<string, string> = {
  IN_STOCK: 'На учёте',
  MOVED: 'Перемещено',
  ON_REPAIR: 'В ремонте',
  ISSUED: 'Выдано',
  WRITTEN_OFF: 'Списано',
  RESERVED: 'Зарезервировано',
}

onMounted(async () => {
  try {
    stats.value = await assetsApi.stats()
  } catch {
    // статистика недоступна — оставляем пусто
  }
})
</script>