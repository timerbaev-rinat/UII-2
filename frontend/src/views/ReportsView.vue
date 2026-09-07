<template>
  <div class="page-container">
    <v-row>
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>Новый отчёт</v-card-title>
          <v-card-text>
            <v-select
              v-model="form.report_type"
              :items="reportTypes"
              item-title="title"
              item-value="value"
              label="Тип отчёта"
            />
            <v-select
              v-model="form.format"
              :items="formatOptions"
              item-title="title"
              item-value="value"
              label="Формат"
            />
            <v-btn color="primary" block :loading="creating" @click="createReport">
              Сформировать
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <v-card>
          <v-card-title>Задачи отчётов</v-card-title>
          <v-data-table
            :headers="headers"
            :items="jobs"
            density="compact"
            item-value="id"
          >
            <template #[`item.status`]="{ item }">
              <v-chip :color="jobColor(item.status)" size="small">{{ item.status }}</v-chip>
            </template>
            <template #[`item.created_at`]="{ item }">
              {{ formatDate(item.created_at) }}
            </template>
            <template #[`item.actions`]="{ item }">
              <v-btn
                v-if="item.status === 'COMPLETED'"
                size="small"
                color="primary"
                variant="tonal"
                :href="downloadUrl(item.id)"
                target="_blank"
              >
                Скачать
              </v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { reportsApi } from '@/api/endpoints'
import type { ReportJob } from '@/types'

const jobs = ref<ReportJob[]>([])
const creating = ref(false)
const form = ref({ report_type: 'inventory_list', format: 'EXCEL' })

const reportTypes = [
  { title: 'Инвентарная опись', value: 'inventory_list' },
  { title: 'Ведомость по местам хранения', value: 'asset_statement' },
  { title: 'Реестр расхождений', value: 'discrepancies' },
  { title: 'Акт списания', value: 'write_off_act' },
]

const formatOptions = [
  { title: 'Excel', value: 'EXCEL' },
  { title: 'PDF', value: 'PDF' },
  { title: 'CSV', value: 'CSV' },
  { title: 'JSON', value: 'JSON' },
]

const headers = [
  { title: 'Тип', key: 'report_type' },
  { title: 'Формат', key: 'format' },
  { title: 'Статус', key: 'status' },
  { title: 'Создан', key: 'created_at' },
  { title: 'Действия', key: 'actions', sortable: false },
]

function jobColor(s: string): string {
  const map: Record<string, string> = {
    PENDING: 'grey',
    RUNNING: 'info',
    COMPLETED: 'success',
    FAILED: 'error',
  }
  return map[s] ?? 'default'
}

function formatDate(v: string): string {
  return new Date(v).toLocaleString('ru-RU')
}

function downloadUrl(id: string): string {
  return reportsApi.downloadUrl(id)
}

async function load(): Promise<void> {
  try {
    jobs.value = await reportsApi.list()
  } catch {
    jobs.value = []
  }
}

async function createReport(): Promise<void> {
  creating.value = true
  try {
    await reportsApi.create(form.value)
    await load()
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  void load()
})
</script>