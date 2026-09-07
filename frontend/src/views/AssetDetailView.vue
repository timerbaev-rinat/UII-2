<template>
  <div class="page-container">
    <v-card v-if="asset">
      <v-card-title class="d-flex align-center">
        <v-btn icon="mdi-arrow-left" variant="text" @click="router.back()" class="mr-2" />
        <div>
          <div class="text-h6">{{ asset.name }}</div>
          <div class="text-subtitle-2 text-grey">Инв. № {{ asset.inventory_number }}</div>
        </div>
        <v-spacer />
        <v-chip :color="statusColor(asset.status)">
          {{ statusLabel(asset.status) }}
        </v-chip>
      </v-card-title>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <v-list density="compact">
              <v-list-item>
                <template #prepend><v-icon>mdi-package-variant</v-icon></template>
                <v-list-item-title>Тип</v-list-item-title>
                <v-list-item-subtitle>{{ assetTypeName }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="asset.model">
                <template #prepend><v-icon>mdi-tag</v-icon></template>
                <v-list-item-title>Модель</v-list-item-title>
                <v-list-item-subtitle>{{ asset.model }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="asset.serial_number">
                <template #prepend><v-icon>mdi-barcode</v-icon></template>
                <v-list-item-title>Серийный номер</v-list-item-title>
                <v-list-item-subtitle>{{ asset.serial_number }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="asset.cost != null">
                <template #prepend><v-icon>mdi-currency-rub</v-icon></template>
                <v-list-item-title>Стоимость</v-list-item-title>
                <v-list-item-subtitle>{{ formatMoney(asset.cost) }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="asset.purchase_year">
                <template #prepend><v-icon>mdi-calendar</v-icon></template>
                <v-list-item-title>Год закупки</v-list-item-title>
                <v-list-item-subtitle>{{ asset.purchase_year }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template #prepend><v-icon>mdi-home</v-icon></template>
                <v-list-item-title>Помещение</v-list-item-title>
                <v-list-item-subtitle>{{ roomName || '—' }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-col>
        </v-row>

        <v-divider class="my-4" />

        <div v-if="auth.isZavhoz" class="d-flex flex-wrap gap-2">
          <v-btn color="info" prepend-icon="mdi-arrow-right" @click="moveDialog = true">
            Переместить
          </v-btn>
          <v-btn color="warning" prepend-icon="mdi-wrench" @click="repairDialog = true">
            В ремонт
          </v-btn>
          <v-btn color="secondary" prepend-icon="mdi-hand-okay" @click="issueDialog = true">
            Выдать
          </v-btn>
          <v-btn color="error" prepend-icon="mdi-delete" @click="writeOffDialog = true">
            Списать
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <v-alert v-else type="info" class="mt-4">Карточка не найдена</v-alert>

    <!-- Диалог перемещения -->
    <v-dialog v-model="moveDialog" max-width="500">
      <v-card>
        <v-card-title>Перемещение</v-card-title>
        <v-card-text>
          <v-select
            v-model="moveToRoomId"
            :items="rooms"
            item-title="name"
            item-value="id"
            label="Помещение назначения"
          />
          <v-text-field v-model="moveReason" label="Причина" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="moveDialog = false">Отмена</v-btn>
          <v-btn color="primary" :loading="busy" @click="doMove">Переместить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог ремонта -->
    <v-dialog v-model="repairDialog" max-width="500">
      <v-card>
        <v-card-title>В ремонт</v-card-title>
        <v-card-text>
          <v-text-field v-model="repairForm.contractor" label="Подрядчик" />
          <v-text-field v-model="repairForm.description" label="Описание" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="repairDialog = false">Отмена</v-btn>
          <v-btn color="primary" :loading="busy" @click="doRepair">Направить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог выдачи -->
    <v-dialog v-model="issueDialog" max-width="500">
      <v-card>
        <v-card-title>Выдача</v-card-title>
        <v-card-text>
          <v-select
            v-model="issueToId"
            :items="users"
            item-title="full_name"
            item-value="id"
            label="Кому"
          />
          <v-text-field v-model="issueReason" label="Причина" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="issueDialog = false">Отмена</v-btn>
          <v-btn color="primary" :loading="busy" @click="doIssue">Выдать</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог списания -->
    <v-dialog v-model="writeOffDialog" max-width="500">
      <v-card>
        <v-card-title>Списание</v-card-title>
        <v-card-text>
          <v-textarea v-model="writeOffReason" label="Причина" required />
          <v-text-field v-model="writeOffCommission" label="Состав комиссии" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="writeOffDialog = false">Отмена</v-btn>
          <v-btn color="error" :loading="busy" @click="doWriteOff">Списать</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { assetsApi, referenceApi, structureApi, usersApi } from '@/api/endpoints'
import { useAuthStore } from '@/store/auth'
import type { Asset, AssetType, Room, User } from '@/types'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const asset = ref<Asset | null>(null)
const assetTypes = ref<AssetType[]>([])
const rooms = ref<Room[]>([])
const users = ref<User[]>([])
const busy = ref(false)

const moveDialog = ref(false)
const repairDialog = ref(false)
const issueDialog = ref(false)
const writeOffDialog = ref(false)

const moveToRoomId = ref<string | null>(null)
const moveReason = ref('')
const repairForm = ref({ contractor: '', description: '' })
const issueToId = ref<string | null>(null)
const issueReason = ref('')
const writeOffReason = ref('')
const writeOffCommission = ref('')

const assetTypeName = computed(
  () => assetTypes.value.find((t) => t.id === asset.value?.asset_type_id)?.name ?? '—',
)
const roomName = computed(
  () => rooms.value.find((r) => r.id === asset.value?.room_id)?.name ?? null,
)

const statusOptions = [
  { title: 'На учёте', value: 'IN_STOCK' },
  { title: 'Перемещено', value: 'MOVED' },
  { title: 'В ремонте', value: 'ON_REPAIR' },
  { title: 'Выдано', value: 'ISSUED' },
  { title: 'Списано', value: 'WRITTEN_OFF' },
  { title: 'Зарезервировано', value: 'RESERVED' },
]

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

async function loadAsset(): Promise<void> {
  try {
    asset.value = await assetsApi.get(String(route.params.id))
  } catch {
    asset.value = null
  }
}

async function doMove(): Promise<void> {
  if (!asset.value) return
  busy.value = true
  try {
    await assetsApi.createMove({
      asset_id: asset.value.id,
      to_room_id: moveToRoomId.value,
      reason: moveReason.value || undefined,
    })
    moveDialog.value = false
    await loadAsset()
  } finally {
    busy.value = false
  }
}

async function doRepair(): Promise<void> {
  if (!asset.value) return
  busy.value = true
  try {
    await assetsApi.createRepair({
      asset_id: asset.value.id,
      contractor: repairForm.value.contractor || null,
      description: repairForm.value.description || undefined,
    })
    repairDialog.value = false
    await loadAsset()
  } finally {
    busy.value = false
  }
}

async function doIssue(): Promise<void> {
  if (!asset.value || !issueToId.value) return
  busy.value = true
  try {
    await assetsApi.createIssuance({
      asset_id: asset.value.id,
      issued_to_id: issueToId.value,
      reason: issueReason.value || undefined,
    })
    issueDialog.value = false
    await loadAsset()
  } finally {
    busy.value = false
  }
}

async function doWriteOff(): Promise<void> {
  if (!asset.value || !writeOffReason.value) return
  busy.value = true
  try {
    await assetsApi.createWriteOff({
      asset_id: asset.value.id,
      reason: writeOffReason.value,
      commission_members: writeOffCommission.value || null,
    })
    writeOffDialog.value = false
    await loadAsset()
  } finally {
    busy.value = false
  }
}

onMounted(async () => {
  await loadAsset()
  try {
    assetTypes.value = await referenceApi.assetTypes()
  } catch {
    assetTypes.value = []
  }
  try {
    rooms.value = await structureApi.rooms()
  } catch {
    rooms.value = []
  }
  try {
    users.value = await usersApi.listActive()
  } catch {
    users.value = []
  }
})
</script>