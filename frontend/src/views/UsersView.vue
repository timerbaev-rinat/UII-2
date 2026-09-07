<template>
  <div class="page-container">
    <v-card>
      <v-card-title class="d-flex align-center">
        Пользователи
        <v-spacer />
        <v-btn v-if="auth.isAdmin" color="primary" prepend-icon="mdi-account-plus" @click="openCreate">
          Добавить
        </v-btn>
      </v-card-title>
      <v-data-table :headers="headers" :items="users" density="compact" item-value="id">
        <template #[`item.is_active`]="{ item }">
          <v-chip :color="item.is_active ? 'success' : 'grey'" size="small">
            {{ item.is_active ? 'Активен' : 'Неактивен' }}
          </v-chip>
        </template>
        <template #[`item.roles`]="{ item }">
          <v-chip v-for="r in item.roles" :key="r.id" size="small" class="mr-1" color="info">
            {{ r.name }}
          </v-chip>
        </template>
      </v-data-table>
    </v-card>

    <!-- Диалог создания -->
    <v-dialog v-model="createDialog" max-width="500">
      <v-card>
        <v-card-title>Новый пользователь</v-card-title>
        <v-card-text>
          <v-text-field v-model="form.login" label="Логин" required />
          <v-text-field v-model="form.full_name" label="ФИО" required />
          <v-text-field v-model="form.position" label="Должность" />
          <v-text-field v-model="form.password" label="Пароль" type="password" required />
          <v-select
            v-model="form.role_codes"
            :items="roles"
            item-title="name"
            item-value="code"
            label="Роли"
            multiple
          />
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
import { usersApi } from '@/api/endpoints'
import { useAuthStore } from '@/store/auth'
import type { Role, User } from '@/types'

const auth = useAuthStore()

const users = ref<User[]>([])
const roles = ref<Role[]>([])
const createDialog = ref(false)
const saving = ref(false)
const form = ref({ login: '', full_name: '', position: '', password: '', role_codes: [] as string[] })

const headers = [
  { title: 'Логин', key: 'login' },
  { title: 'ФИО', key: 'full_name' },
  { title: 'Должность', key: 'position' },
  { title: 'Роли', key: 'roles' },
  { title: 'Статус', key: 'is_active' },
]

async function load(): Promise<void> {
  try {
    users.value = await usersApi.list()
  } catch {
    users.value = []
  }
  try {
    roles.value = await usersApi.roles()
  } catch {
    roles.value = []
  }
}

function openCreate(): void {
  form.value = { login: '', full_name: '', position: '', password: '', role_codes: [] }
  createDialog.value = true
}

async function save(): Promise<void> {
  saving.value = true
  try {
    await usersApi.create(form.value)
    createDialog.value = false
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  void load()
})
</script>