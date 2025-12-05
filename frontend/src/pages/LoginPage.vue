<!-- File: security_mgmt_dev/frontend/src/pages/LoginPage.vue -->
<template>
  <div class="fullscreen bg-grey-2 flex flex-center">
    <q-card class="my-card">
      <q-card-section>
        <div class="text-h6">Đăng nhập</div>
        <div class="text-caption text-grey-7">Nhập mã nhân viên và mật khẩu</div>
      </q-card-section>
      <q-separator/>
      
      <!-- DEBUG PANEL (chỉ hiện khi có debug info) -->
      <q-card-section v-if="debugInfo.length > 0" class="bg-orange-1">
        <div class="text-caption text-weight-bold text-negative q-mb-sm">
          DEBUG INFO (long-press để copy):
        </div>
        <q-input
          v-model="debugText"
          type="textarea"
          outlined
          readonly
          dense
          rows="8"
          autogrow
          class="text-caption"
          style="font-family: monospace; font-size: 11px;"
        />
      </q-card-section>
      
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
          <!-- TEST BUTTON -->
          <q-btn 
            type="button"
            @click="testClick" 
            label="TEST (bấm để kiểm tra)" 
            color="orange" 
            class="full-width q-mt-sm"
          />
        </div>
      </q-card-section>
    </q-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import api from '../api'

const username = ref('')
const password = ref('')
const auth = useAuthStore()
const router = useRouter()
const $q = useQuasar()
const debugInfo = ref([])

// Computed: join debug info for textarea
const debugText = computed(() => debugInfo.value.join('\n'))

function addDebug(msg) {
  const timestamp = new Date().toLocaleTimeString();
  debugInfo.value.push(`[${timestamp}] ${msg}`);
  console.log(`[LoginPage] ${msg}`);
}

function testClick() {
  addDebug('TEST BUTTON CLICKED - Vue is working!');
  alert('TEST OK - Click works!');
}

// SIMPLIFIED: Only check if already authenticated
onMounted(async () => {
  addDebug('Page mounted');
  try {
    const token = localStorage.getItem('token');
    addDebug(`Token exists: ${!!token}`);
    
    // If has token, try to verify it's still valid
    if (token && auth.isAuthenticated) {
      addDebug('Already authenticated, redirecting...');
      await router.push('/');
    } else {
      addDebug('Not authenticated, showing login form');
    }
  } catch (error) {
    addDebug(`Mount error: ${error.message}`);
  }
});

async function onSubmit() {
  try {
    addDebug('🔥 onSubmit CALLED!');
    addDebug(`Username: "${username.value}" (len: ${username.value?.length})`);
    addDebug(`Password: "${password.value}" (len: ${password.value?.length})`);
    
    if (!username.value || !password.value) {
      addDebug('Validation failed - empty fields');
      $q.notify({
        type: 'warning',
        message: 'Vui lòng nhập tên đăng nhập và mật khẩu',
        position: 'top'
      });
      return;
    }

    addDebug('Calling /token API...');
    
    // CUSTOM LOGIN - Bypass auth store
    // TRIM whitespace to prevent autofill issues
    const cleanUsername = username.value.trim();
    const cleanPassword = password.value.trim();
    
    addDebug(`Sending: user="${cleanUsername}" (${cleanUsername.length}), pw="${cleanPassword}" (${cleanPassword.length})`);
    
    const res = await api.post('/token', new URLSearchParams({
      username: cleanUsername,
      password: cleanPassword
    }));
    
    addDebug('✅ Got tokens from server');
    
    // Save tokens
    const token = res.data.access_token;
    const refreshToken = res.data.refresh_token;
    
    localStorage.setItem('token', token);
    localStorage.setItem('refreshToken', refreshToken);
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    
    addDebug('✅ Tokens saved to localStorage');
    addDebug('✅ LOGIN SUCCESS!');
    
    $q.notify({
      type: 'positive',
      message: 'Đăng nhập thành công! Đang chuyển trang...',
      position: 'top',
      timeout: 2000
    });
    
    // Wait a bit then redirect
    addDebug('Redirecting in 1 second...');
    setTimeout(() => {
      window.location.href = '/';
    }, 1000);
    
  } catch (e) {
    addDebug(`❌ LOGIN ERROR: ${e.message || e}`);
    addDebug(`Detail: ${e.response?.data?.detail || 'No detail'}`);
    addDebug(`Status: ${e.response?.status || 'No status'}`);
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
