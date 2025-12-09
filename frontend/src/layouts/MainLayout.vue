<!-- File: frontend/src/layouts/MainLayout.vue -->
<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn flat dense round icon="menu" @click="leftDrawerOpen = !leftDrawerOpen" aria-label="Menu"/>
        <q-toolbar-title>Ứng dụng an ninh nội bộ - Local Security App</q-toolbar-title>
        <div v-if="auth.user" class="row items-center q-gutter-sm">
          <q-chip :label="auth.user.full_name" icon="person" />
          <q-badge color="primary" :label="auth.user.role" />
          <q-btn flat icon="logout" label="Đăng xuất" @click="logout"/>
        </div>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered>
      <q-list>
        <q-item v-if="['admin','manager'].includes(auth.user?.role)" clickable v-ripple to="/dashboard">
          <q-item-section avatar><q-icon name="dashboard"/></q-item-section>
          <q-item-section>Dashboard</q-item-section>
        </q-item>

        <q-item v-if="['admin','manager'].includes(auth.user?.role)" clickable v-ripple to="/reports">
          <q-item-section avatar><q-icon name="assessment"/></q-item-section>
          <q-item-section>Báo cáo & Phân tích</q-item-section>
        </q-item>

        <q-separator v-if="['admin','manager'].includes(auth.user?.role)" />

        <q-item v-if="['admin','manager','staff'].includes(auth.user?.role)" clickable v-ripple to="/register-guest">
          <q-item-section avatar><q-icon name="person_add"/></q-item-section>
          <q-item-section>Đăng ký khách</q-item-section>
        </q-item>
        
        <q-item v-if="['admin','manager','staff'].includes(auth.user?.role)" clickable v-ripple to="/long-term-guests">
          <q-item-section avatar><q-icon name="event_repeat"/></q-item-section>
          <q-item-section>Khách dài hạn</q-item-section>
        </q-item>
        <!-- === CHECKLIST 2.10: Thêm 2 link menu Tài sản === -->
        <q-separator v-if="['admin','manager','staff'].includes(auth.user?.role)" />

        <q-item v-if="['admin','manager','staff'].includes(auth.user?.role)" clickable v-ripple to="/register-asset">
          <q-item-section avatar><q-icon name="outbox"/></q-item-section>
          <q-item-section>Đăng ký Tài sản</q-item-section>
        </q-item>

        <q-item v-if="['admin','manager','staff'].includes(auth.user?.role)" clickable v-ripple to="/asset-management">
          <q-item-section avatar><q-icon name="inventory"/></q-item-section>
          <q-item-section>Quản lý Tài sản</q-item-section>
        </q-item>

        <q-separator />
        <!-- === KẾT THÚC CHECKLIST 2.10 === -->

        <q-item v-if="['admin','guard'].includes(auth.user?.role)" clickable v-ripple to="/guard-gate">
          <q-item-section avatar><q-icon name="login"/></q-item-section>
          <q-item-section>Cổng bảo vệ</q-item-section>
        </q-item>

        <!-- MỤC MENU MỚI CHO NHẬT KÝ XE -->
        <q-item v-if="['admin','manager'].includes(auth.user?.role)" clickable v-ripple to="/vehicle-log">
          <q-item-section avatar><q-icon name="local_shipping" /></q-item-section>
          <q-item-section>Nhật ký xe</q-item-section>
        </q-item>

        <q-item v-if="['admin','manager'].includes(auth.user?.role)" clickable v-ripple to="/suppliers">
          <q-item-section avatar><q-icon name="store"/></q-item-section>
          <q-item-section>Nhà cung cấp</q-item-section>
        </q-item>

        <q-item v-if="['admin','manager'].includes(auth.user?.role)" clickable v-ripple to="/users">
          <q-item-section avatar><q-icon name="group"/></q-item-section>
          <q-item-section>Người dùng</q-item-section>
        </q-item>

        <q-separator v-if="['admin','manager'].includes(auth.user?.role)" />

        <q-item v-if="['admin','manager'].includes(auth.user?.role)" clickable v-ripple to="/purchasing">
          <q-item-section avatar><q-icon name="shopping_cart"/></q-item-section>
          <q-item-section>Quản lý Mua bán</q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view/>
    </q-page-container>

    <!-- Notification Dialog -->
    <q-dialog v-model="notificationDialog" persistent>
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6 text-negative">⚠️ Nhắc nhở quan trọng</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <div v-for="notif in notificationList" :key="notif.id" class="q-mb-md">
            <div class="text-weight-bold">{{ notif.title }}</div>
            <div style="white-space: pre-line;">{{ notif.message }}</div>
            <q-separator class="q-my-sm" />
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Đã hiểu" color="primary" @click="confirmRead" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import api from '../api'

const auth = useAuthStore()
const router = useRouter()
const leftDrawerOpen = ref(true)

// Notifications
const notificationDialog = ref(false)
const notificationList = ref([])

onMounted(async () => {
  // Auto-hide menu
  setTimeout(() => {
    leftDrawerOpen.value = false
  }, 5000)

  // Initial check
  if (auth.isAuthenticated) {
    fetchNotifications()
  }
})

// Watch for login
import { watch } from 'vue'
watch(() => auth.isAuthenticated, (newVal) => {
  if (newVal) {
    fetchNotifications()
  }
})

async function fetchNotifications() {
  try {
    const res = await api.get('/notifications/unread')
    if (res.data && res.data.length > 0) {
      notificationList.value = res.data
      notificationDialog.value = true
    }
  } catch (e) {
    console.error("Failed to fetch notifications", e)
  }
}


async function confirmRead() {
  try {
    // Mark all as read
    // Using Promise.all to run in parallel
    const promises = notificationList.value.map(n => api.post(`/notifications/${n.id}/read`))
    await Promise.all(promises)
    
    // Close
    notificationDialog.value = false
    notificationList.value = []
  } catch (e) {
    console.error("Failed to mark notifications as read", e)
  }
}

function logout () {
  auth.logout()
  router.push('/login')
}
</script>

