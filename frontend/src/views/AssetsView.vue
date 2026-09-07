<template>
  <div class="page-container">
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between">
        <span>Имущество</span>
        <div class="d-flex align-center">
          <v-text-field
            v-model="query"
            label="Поиск"
            prepend-inner-icon="mdi-magnify"
            density="compact"
            hide-details
            class="mr-2"
            style="max-width: 240px"
            clearable
            @keyup.enter="load"
          />
          <v-select
            v-model="statusFilter"
            :items="statusOptions"
            label="Статус"
            density="compact"
            hide-details
            clearable
            class="mr-2"
            style="max-width: 180px"
            @update:model-value="load"
          />
          <v-btn
            v-if="auth.isZavhoz"
            color="primary"
            prepend-icon="mdi-plus"
            @click="openCreate"
          >
            Добавить
          </v-btn>
        </div>
      </v-card-title>

      <v-data-table
        :headers="headers"
        :items="assets"
        :loading="loading"
        density="compact"
        item-value="id"
        @click:row="openDetail"
      >
        <template #[`item.status`]="{ item }">
          <v-chip :color="statusColor(item.status)" size="small">
            {{ statusLabel(item.status) }}
          </v-chip>
        </template>
        <template #[`item.quantity`]="{ item }">
          {{ item.quantity }} {{ item.unit ?? '' }}
        </template>
        <template #[`item.cost`]="{ item }">
          {{ formatMoney(item.cost) }}
        </template>
      </v-data-table>
    </v-card>

    <!-- Диалог создания карточки -->
    <v-dialog v-model="createDialog" max-width="600" persistent>
      <v-card>
        <v-card-title>Новая карточка имущества</v-card-title>
        <v-card-text>
          <v-form ref="formRef" v-model="valid">
            <v-select
              v-model="form.asset_type_id"
              :items="assetTypes"
              item-title="name"
              item-value="id"
              label="Тип объекта"
              required
            />
            <v-text-field v-model="form.name" label="Наименование" required />
            <v-text-field v-model="form.model" label="Модель" />
            <v-text-field v-model="form.brand" label="Бренд" />
            <v-text-field v-model="form.serial_number" label="Серийный номер" />
            <v-switch v-model="form.use_custom_number" label="Свой инвентарный номер" />
            <v-text-field
              v-if="form.use_custom_number"
              v-model="form.inventory_number"
              label="Инвентарный номер"
            />
            <v-text-field v-model.number="form.cost" label="Стоимость" type="number" />
            <v-text-field v-model.number="form.quantity" label="Количество" type="number" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="createDialog = false">Отмена</v-btn>
          <v-btn color="primary" :loading="saving" @click="save">Сохранить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { assetsApi, referenceApi } from '@/api/endpoints'
import { useAuthStore } from '@/store/auth'
import type { Asset, AssetType } from '@/types'

const router = useRouter()
const auth = useAuthStore()

const assets = ref<Asset[]>([])
const assetTypes = ref<AssetType[]>([])
const loading = ref(false)
const saving = ref(false)
const query = ref('')
const statusFilter = ref<string | null>(null)
const createDialog = ref(false)
const valid = ref(false)
const formRef = ref()

const statusOptions = [
  { title: 'На учёте', value: 'IN_STOCK' },
  { title: 'Перемещено', value: 'MOVED' },
  { title: 'В ремонте', value: 'ON_REPAIR' },
  { title: 'Выдано', value: 'ISSUED' },
  { title: 'Списано', value: 'WRITTEN_OFF' },
  { title: 'Зарезервировано', value: 'RESERVED' },
]

const headers = [
  { title: 'Инв. номер', key: 'inventory_number', sortable: true },
  { title: 'Наименование', key: 'name', sortable: true },
  { title: 'Статус', key: 'status', sortable: true },
  { title: 'Кол-во', key: 'quantity', sortable: true },
  { title: 'Стоимость', key: 'cost', sortable: true },
]

const defaultForm = () => ({
  asset_type_id: '',
  name: '',
  model: '',
  brand: '',
  serial_number: '',
  cost: null as number | null,
  quantity: 1,
  use_custom_number: false,
  inventory_number: '',
})

const form = ref(defaultForm())

function statusLabel(s: string): string {
  return statusOptions.find((o) => o.value === s)?.title ?? s
}

function statusColor(s: string): string {
  const map: Record<string, string> = {
    IN_STOCK: 'success',
    MOVED: 'info',
    ON_REPAIR: 'warning',
    ISSUED: 'secondary',
    WRITTEN_OFF: 'error',
    RESERVED: 'grey',
  }
  return map[s] ?? 'default'
}

function formatMoney(v: number | null | undefined): string {
  if (v === null || v === undefined) return '—'
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(v)
}

async function load(): Promise<void> {
  loading.value = true
  try {
    assets.value = await assetsApi.list({
      query: query.value || undefined,
      status: statusFilter.value || undefined,
    })
  } catch {
    assets.value = []
  } finally {
    loading.value = false
  }
}

function openDetail(_e: Event, row: { item: Asset }): void {
  router.push({ name: 'asset-detail', params: { id: row.item.id } })
}

function openCreate(): void {
  form.value = defaultForm()
  createDialog.value = true
}

async function save(): Promise<void> {
  const ok = await formRef.value?.validate?.()
  if (ok === false) return
  saving.value = true
  try {
    await assetsApi.create({
      asset_type_id: form.value.asset_type_id,
      name: form.value.name,
      model: form.value.model || null,
      brand: form.value.brand || null,
      serial_number: form.value.serial_number || null,
      cost: form.value.cost,
      quantity: form.value.quantity,
      use_custom_number: form.value.use_custom_number,
      inventory_number: form.value.use_custom_number ? form.value.inventory_number : null,
    })
    createDialog.value = false
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await load()
  try {
    assetTypes.value = await referenceApi.assetTypes()
  } catch {
    assetTypes.value = []
  }
})
</script>