<!-- File: security_mgmt_dev/frontend/src/pages/LoginPage.vue -->
<template>
  <div class="fullscreen bg-grey-2 flex flex-center">
    <q-card class="my-card">
      <q-card-section>
        <div class="text-h6">Đăng nhập</div>
        <div class="text-caption text-grey-7">Nhập mã nhân viên và mật khẩu</div>
      </q-card-section>
      <q-separator/>
      
      <q-card-section>
        <div class="q-gutter-md">
          <q-input v-model="username" label="Tên đăng nhập" dense outlined autofocus/>
          <q-input 
            v-model="password" 
            type="password" 
            label="Mật khẩu" 
            dense 
            outlined
            @keyup.enter.prevent="onSubmit"
          />
          <q-btn 
            type="button"
            @click.prevent="onSubmit" 
            label="Đăng nhập" 
            color="primary" 
            class="full-width"
          />
        </div>
      </q-card-section>
    </q-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import api from '../api'

const username = ref('')
const password = ref('')
const auth = useAuthStore()
const router = useRouter()
const $q = useQuasar()

// Check if already authenticated
onMounted(async () => {
  try {
    const token = localStorage.getItem('token');
    
    // If has token, try to verify it's still valid
    if (token && auth.isAuthenticated) {
      await router.push('/');
    }
  } catch (error) {
    console.error('[LoginPage] Mount error:', error);
  }
});

async function onSubmit() {
  try {
    if (!username.value || !password.value) {
      $q.notify({
        type: 'warning',
        message: 'Vui lòng nhập tên đăng nhập và mật khẩu',
        position: 'top'
      });
      return;
    }

    // TRIM whitespace to prevent autofill issues
    const cleanUsername = username.value.trim();
    const cleanPassword = password.value.trim();
    
    // USE AUTH STORE ACTION
    await auth.login(cleanUsername, cleanPassword);
    
    $q.notify({
      type: 'positive',
      message: 'Đăng nhập thành công! Đang chuyển trang...',
      position: 'top',
      timeout: 1000
    });
    
    // Redirect without reload
    router.push('/');
    
  } catch (e) {
    console.error("Login failed:", e);
    $q.notify({
      type: 'negative',
      message: e.response?.data?.detail || 'Sai tên đăng nhập hoặc mật khẩu',
      position: 'top',
      timeout: 5000
    });
  }
}
</script>

<style lang="scss" scoped>
.my-card {
  width: 100%;
  max-width: 400px;
  margin: 16px;
}
</style>
