<template>
  <div class="page-container">
    <v-card>
      <v-card-title class="d-flex align-center">
        Журнал аудита
        <v-spacer />
        <v-btn size="small" color="info" variant="tonal" @click="integrityDialog = true">
          Проверка целостности
        </v-btn>
      </v-card-title>
      <v-card-text>
        <div class="d-flex flex-wrap mb-3 gap-2">
          <v-text-field
            v-model="filters.action"
            label="Действие"
            density="compact"
            hide-details
            clearable
            class="mr-2"
            style="max-width: 180px"
          />
          <v-text-field
            v-model="filters.entity_type"
            label="Сущность"
            density="compact"
            hide-details
            clearable
            class="mr-2"
            style="max-width: 180px"
          />
          <v-btn color="primary" @click="load">Применить</v-btn>
        </div>

        <v-data-table :headers="headers" :items="entries" density="compact" item-value="id">
          <template #[`item.created_at`]="{ item }">
            {{ formatDate(item.created_at) }}
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- Диалог целостности -->
    <v-dialog v-model="integrityDialog" max-width="600">
      <v-card>
        <v-card-title>Проверка целостности</v-card-title>
        <v-card-text>
          <template v-if="integrity">
            <v-alert :type="integrity.status === 'ok' ? 'success' : 'warning'" class="mb-3">
              Статус: {{ integrity.status === 'ok' ? 'ОК' : 'Предупреждения' }}
            </v-alert>
            <v-list v-if="integrity.issues.length" density="compact">
              <v-list-item v-for="(issue, i) in integrity.issues" :key="i">
                <v-list-item-title>{{ (issue as { message: string }).message }}</v-list-item-title>
              </v-list-item>
            </v-list>
            <div class="text-subtitle-2">
              Всего карточек: {{ integrity.counts.assets }} · Помещений: {{ integrity.counts.rooms }}
            </div>
          </template>
          <v-btn color="primary" :loading="checking" @click="checkIntegrity">Проверить</v-btn>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="integrityDialog = false">Закрыть</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { auditApi } from '@/api/endpoints'
import type { AuditLogEntry } from '@/types'

const entries = ref<AuditLogEntry[]>([])
const integrityDialog = ref(false)
const checking = ref(false)
const integrity = ref<{ status: string; issues: unknown[]; counts: Record<string, number> } | null>(
  null,
)

const filters = ref({ action: '', entity_type: '' })

const headers = [
  { title: 'Время', key: 'created_at' },
  { title: 'Действие', key: 'action' },
  { title: 'Сущность', key: 'entity_type' },
  { title: 'ID', key: 'entity_id' },
  { title: 'IP', key: 'ip_address' },
]

function formatDate(v: string): string {
  return new Date(v).toLocaleString('ru-RU')
}

async function load(): Promise<void> {
  try {
    entries.value = await auditApi.list({
      action: filters.value.action || undefined,
      entity_type: filters.value.entity_type || undefined,
    })
  } catch {
    entries.value = []
  }
}

async function checkIntegrity(): Promise<void> {
  checking.value = true
  try {
    integrity.value = await auditApi.integrity()
  } finally {
    checking.value = false
  }
}

onMounted(() => {
  void load()
})
</script>