<template>
  <div class="page-container">
    <v-row>
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title class="d-flex align-center">
            Здания
            <v-spacer />
            <v-btn v-if="auth.isZavhoz" icon="mdi-plus" size="small" @click="buildingDialog = true" />
          </v-card-title>
          <v-list density="compact">
            <v-list-item
              v-for="b in buildings"
              :key="b.id"
              :title="b.name"
              :subtitle="b.address"
              :active="selectedBuildingId === b.id"
              @click="selectBuilding(b.id)"
            />
          </v-list>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <v-card>
          <v-card-title class="d-flex align-center">
            Помещения
            <v-spacer />
            <v-btn
              v-if="auth.isZavhoz && selectedBuildingId"
              icon="mdi-plus"
              size="small"
              @click="roomDialog = true"
            />
          </v-card-title>
          <v-data-table :headers="headers" :items="rooms" density="compact" item-value="id">
            <template #[`item.room_number`]="{ item }">
              {{ item.room_number ?? '—' }}
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Диалог здания -->
    <v-dialog v-model="buildingDialog" max-width="500">
      <v-card>
        <v-card-title>Новое здание</v-card-title>
        <v-card-text>
          <v-text-field v-model="buildingForm.name" label="Название" required />
          <v-text-field v-model="buildingForm.address" label="Адрес" />
          <v-text-field v-model="buildingForm.building_code" label="Код здания" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="buildingDialog = false">Отмена</v-btn>
          <v-btn color="primary" @click="saveBuilding">Сохранить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог помещения -->
    <v-dialog v-model="roomDialog" max-width="500">
      <v-card>
        <v-card-title>Новое помещение</v-card-title>
        <v-card-text>
          <v-text-field v-model="roomForm.name" label="Название" required />
          <v-text-field v-model="roomForm.room_number" label="Номер" />
          <v-text-field v-model="roomForm.room_type" label="Тип помещения" />
          <v-text-field v-model="roomForm.department" label="Подразделение" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="roomDialog = false">Отмена</v-btn>
          <v-btn color="primary" @click="saveRoom">Сохранить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { structureApi } from '@/api/endpoints'
import { useAuthStore } from '@/store/auth'
import type { Building, Room } from '@/types'

const auth = useAuthStore()

const buildings = ref<Building[]>([])
const rooms = ref<Room[]>([])
const selectedBuildingId = ref<string | null>(null)
const buildingDialog = ref(false)
const roomDialog = ref(false)

const buildingForm = ref({ name: '', address: '', building_code: '' })
const roomForm = ref({ name: '', room_number: '', room_type: '', department: '' })

const headers = [
  { title: 'Название', key: 'name', sortable: true },
  { title: 'Номер', key: 'room_number', sortable: true },
  { title: 'Тип', key: 'room_type' },
  { title: 'Подразделение', key: 'department' },
]

async function loadBuildings(): Promise<void> {
  try {
    buildings.value = await structureApi.buildings()
    if (buildings.value.length && !selectedBuildingId.value) {
      selectedBuildingId.value = buildings.value[0].id
    }
  } catch {
    buildings.value = []
  }
}

async function loadRooms(): Promise<void> {
  if (!selectedBuildingId.value) {
    rooms.value = []
    return
  }
  try {
    rooms.value = await structureApi.rooms(selectedBuildingId.value)
  } catch {
    rooms.value = []
  }
}

function selectBuilding(id: string): void {
  selectedBuildingId.value = id
  void loadRooms()
}

async function saveBuilding(): Promise<void> {
  await structureApi.createBuilding(buildingForm.value)
  buildingDialog.value = false
  buildingForm.value = { name: '', address: '', building_code: '' }
  await loadBuildings()
}

async function saveRoom(): Promise<void> {
  if (!selectedBuildingId.value) return
  await structureApi.createRoom({
    ...roomForm.value,
    building_id: selectedBuildingId.value,
  })
  roomDialog.value = false
  roomForm.value = { name: '', room_number: '', room_type: '', department: '' }
  await loadRooms()
}

onMounted(async () => {
  await loadBuildings()
  await loadRooms()
})
</script>