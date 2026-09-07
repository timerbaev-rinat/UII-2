<template>
  <div class="page-container">
    <v-card>
      <v-card-title class="d-flex align-center">
        Инвентаризация
        <v-spacer />
        <v-btn v-if="auth.isZavhoz" color="primary" prepend-icon="mdi-plus" @click="createDialog = true">
          Создать
        </v-btn>
      </v-card-title>

      <v-tabs v-model="tab">
        <v-tab value="list">Список</v-tab>
        <v-tab value="active">Активная</v-tab>
        <v-tab value="discrepancies">Расхождения</v-tab>
      </v-tabs>

      <v-card-text>
        <!-- Список инвентаризаций -->
        <v-list v-if="tab === 'list'" density="compact">
          <v-list-item
            v-for="inv in inventories"
            :key="inv.id"
            :title="inv.name"
            :subtitle="`Статус: ${invStatus(inv.status)} · Создана: ${formatDate(inv.created_at)}`"
            @click="selectInventory(inv)"
          >
            <template #append>
              <v-chip :color="invColor(inv.status)" size="small">{{ invStatus(inv.status) }}</v-chip>
            </template>
          </v-list-item>
        </v-list>

        <!-- Активная инвентаризация (мобильный сценарий) -->
        <template v-if="tab === 'active' && selected">
          <div class="d-flex align-center mb-2">
            <div class="text-subtitle-1 font-weight-bold">{{ selected.name }}</div>
            <v-spacer />
            <v-btn size="small" color="success" :loading="busy" @click="complete">Завершить</v-btn>
          </div>
          <div class="d-flex align-center mb-3">
            <v-text-field
              v-model="itemFilter"
              label="Фильтр по наименованию"
              density="compact"
              hide-details
              clearable
            />
          </div>
          <v-list density="compact">
            <v-list-item
              v-for="item in filteredItems"
              :key="item.id"
              :class="item.is_checked ? 'inventory-checked' : ''"
            >
              <template #prepend>
                <v-checkbox :model-value="item.is_checked" @change="toggleItem(item)" />
              </template>
              <v-list-item-title>{{ item.asset_id }}</v-list-item-title>
              <v-list-item-subtitle>
                Учёт: {{ item.accounting_quantity ?? '—' }} · Факт: {{ item.actual_quantity ?? '—' }}
              </v-list-item-subtitle>
              <template #append>
                <v-menu>
                  <template #activator="{ props }">
                    <v-btn icon="mdi-dots-vertical" v-bind="props" size="small" variant="text" />
                  </template>
                  <v-list density="compact">
                    <v-list-item @click="openItemEditor(item)">
                      <v-list-item-title>Ввести факт</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </template>
            </v-list-item>
          </v-list>
          <v-progress-linear
            :model-value="progressPercent"
            height="20"
            color="primary"
            class="mt-3"
          >
            {{ checkedCount }}/{{ selectedItems.length }}
          </v-progress-linear>
        </template>

        <!-- Расхождения -->
        <template v-if="tab === 'discrepancies'">
          <v-btn
            v-if="selected"
            size="small"
            class="mb-3"
            @click="loadDiscrepancies"
          >
            Обновить
          </v-btn>
          <v-data-table
            v-if="discrepancies.length"
            :headers="discHeaders"
            :items="discrepancies"
            density="compact"
            item-value="id"
          >
            <template #[`item.discrepancy_type`]="{ item }">
              <v-chip :color="item.discrepancy_type === 'SURPLUS' ? 'success' : 'error'" size="small">
                {{ item.discrepancy_type === 'SURPLUS' ? 'Излишек' : 'Недостача' }}
              </v-chip>
            </template>
          </v-data-table>
          <v-alert v-else type="info">Расхождений нет</v-alert>
        </template>

        <v-alert v-if="tab !== 'list' && !selected" type="info" class="mt-2">
          Выберите инвентаризацию из списка
        </v-alert>
      </v-card-text>
    </v-card>

    <!-- Диалог создания -->
    <v-dialog v-model="createDialog" max-width="500">
      <v-card>
        <v-card-title>Новая инвентаризация</v-card-title>
        <v-card-text>
          <v-text-field v-model="createForm.name" label="Название" required />
          <v-select
            v-model="createForm.inv_type"
            :items="typeOptions"
            item-title="title"
            item-value="value"
            label="Тип"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="createDialog = false">Отмена</v-btn>
          <v-btn color="primary" @click="createInventory">Создать</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог ввода факта -->
    <v-dialog v-model="itemEditor" max-width="400">
      <v-card>
        <v-card-title>Ввод фактических данных</v-card-title>
        <v-card-text>
          <v-text-field
            v-model.number="itemEditForm.actual_quantity"
            label="Фактическое количество"
            type="number"
          />
          <v-textarea v-model="itemEditForm.actual_condition" label="Состояние" />
          <v-textarea v-model="itemEditForm.comment" label="Комментарий" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="itemEditor = false">Отмена</v-btn>
          <v-btn color="primary" @click="saveItemFact">Сохранить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { inventoryApi } from '@/api/endpoints'
import { useAuthStore } from '@/store/auth'
import type { Discrepancy, Inventory, InventoryItem } from '@/types'

const auth = useAuthStore()

const tab = ref('list')
const inventories = ref<Inventory[]>([])
const selected = ref<Inventory | null>(null)
const selectedItems = ref<InventoryItem[]>([])
const discrepancies = ref<Discrepancy[]>([])
const busy = ref(false)
const itemFilter = ref('')
const createDialog = ref(false)
const itemEditor = ref(false)

const createForm = ref({ name: '', inv_type: 'PLANNED' })
const itemEditForm = ref<{ actual_quantity: number | null; actual_condition: string; comment: string }>({
  actual_quantity: null,
  actual_condition: '',
  comment: '',
})
let editingItem: InventoryItem | null = null

const typeOptions = [
  { title: 'Плановая', value: 'PLANNED' },
  { title: 'Внеплановая', value: 'UNPLANNED' },
  { title: 'Выборочная', value: 'SAMPLE' },
]

const discHeaders = [
  { title: 'Тип', key: 'discrepancy_type' },
  { title: 'Учёт', key: 'accounting_quantity' },
  { title: 'Факт', key: 'actual_quantity' },
  { title: 'Разница', key: 'difference' },
  { title: 'Статус', key: 'status' },
]

const filteredItems = computed(() => {
  if (!itemFilter.value) return selectedItems.value
  const q = itemFilter.value.toLowerCase()
  return selectedItems.value.filter((i) => i.asset_id.toLowerCase().includes(q))
})

const checkedCount = computed(() => selectedItems.value.filter((i) => i.is_checked).length)
const progressPercent = computed(() => {
  if (!selectedItems.value.length) return 0
  return Math.round((checkedCount.value / selectedItems.value.length) * 100)
})

function invStatus(s: string): string {
  const map: Record<string, string> = {
    DRAFT: 'Черновик',
    IN_PROGRESS: 'В процессе',
    COMPLETED: 'Завершена',
    APPROVED: 'Утверждена',
  }
  return map[s] ?? s
}

function invColor(s: string): string {
  const map: Record<string, string> = {
    DRAFT: 'grey',
    IN_PROGRESS: 'info',
    COMPLETED: 'warning',
    APPROVED: 'success',
  }
  return map[s] ?? 'default'
}

function formatDate(v: string): string {
  return new Date(v).toLocaleDateString('ru-RU')
}

async function loadInventories(): Promise<void> {
  try {
    inventories.value = await inventoryApi.list()
  } catch {
    inventories.value = []
  }
}

async function selectInventory(inv: Inventory): Promise<void> {
  selected.value = inv
  tab.value = inv.status === 'IN_PROGRESS' ? 'active' : 'list'
  await loadItems()
}

async function loadItems(): Promise<void> {
  if (!selected.value) return
  try {
    selectedItems.value = await inventoryApi.items(selected.value.id)
  } catch {
    selectedItems.value = []
  }
}

async function loadDiscrepancies(): Promise<void> {
  if (!selected.value) return
  try {
    discrepancies.value = await inventoryApi.discrepancies(selected.value.id)
  } catch {
    discrepancies.value = []
  }
}

async function createInventory(): Promise<void> {
  await inventoryApi.create(createForm.value)
  createDialog.value = false
  createForm.value = { name: '', inv_type: 'PLANNED' }
  await loadInventories()
}

function toggleItem(item: InventoryItem): void {
  void inventoryApi
    .updateItem(selected.value!.id, item.id, { is_checked: !item.is_checked })
    .then((updated) => {
      const idx = selectedItems.value.findIndex((i) => i.id === updated.id)
      if (idx !== -1) selectedItems.value[idx] = updated
    })
}

function openItemEditor(item: InventoryItem): void {
  editingItem = item
  itemEditForm.value = {
    actual_quantity: item.actual_quantity,
    actual_condition: item.actual_condition ?? '',
    comment: item.comment ?? '',
  }
  itemEditor.value = true
}

async function saveItemFact(): Promise<void> {
  if (!selected.value || !editingItem) return
  const updated = await inventoryApi.updateItem(selected.value.id, editingItem.id, {
    actual_quantity: itemEditForm.value.actual_quantity,
    actual_condition: itemEditForm.value.actual_condition || null,
    comment: itemEditForm.value.comment || null,
  })
  const idx = selectedItems.value.findIndex((i) => i.id === updated.id)
  if (idx !== -1) selectedItems.value[idx] = updated
  itemEditor.value = false
}

async function complete(): Promise<void> {
  if (!selected.value) return
  busy.value = true
  try {
    await inventoryApi.complete(selected.value.id)
    await loadInventories()
    selected.value = inventories.value.find((i) => i.id === selected.value?.id) ?? null
  } finally {
    busy.value = false
  }
}

onMounted(() => {
  void loadInventories()
})
</script>

<style scoped>
.inventory-checked {
  opacity: 0.6;
}
</style>