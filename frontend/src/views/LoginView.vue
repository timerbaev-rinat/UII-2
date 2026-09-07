<template>
  <v-app>
    <v-main class="d-flex align-center justify-center login-bg">
      <v-card class="login-card" elevation="8">
        <v-card-title class="text-center pt-6">
          <v-icon size="56" color="primary" class="mb-2">mdi-school</v-icon>
          <div class="text-h5 font-weight-bold">Учёт имущества школы</div>
        </v-card-title>
        <v-card-text>
          <v-form @submit.prevent="submit">
            <v-text-field
              v-model="login"
              label="Логин"
              prepend-inner-icon="mdi-account"
              autocomplete="username"
              required
            />
            <v-text-field
              v-model="password"
              label="Пароль"
              prepend-inner-icon="mdi-lock"
              type="password"
              autocomplete="current-password"
              required
            />
            <v-alert v-if="error" type="error" class="mb-3" density="compact">
              {{ error }}
            </v-alert>
            <v-btn
              type="submit"
              color="primary"
              block
              size="large"
              :loading="auth.loading"
              class="mt-2"
            >
              Войти
            </v-btn>
          </v-form>
        </v-card-text>
      </v-card>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const auth = useAuthStore()

const login = ref('')
const password = ref('')
const error = ref('')

async function submit(): Promise<void> {
  error.value = ''
  try {
    await auth.login(login.value, password.value)
    router.push({ name: 'dashboard' })
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Не удалось войти'
  }
}
</script>

<style scoped>
.login-bg {
  background: linear-gradient(135deg, #1976d2 0%, #42a5f5 100%);
}
.login-card {
  width: 100%;
  max-width: 400px;
  margin: 16px;
}
</style>