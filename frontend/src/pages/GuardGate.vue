<!-- File: frontend/src/pages/GuardGate.vue (Updated with PWA/Offline features) -->
<template>
  <q-page class="q-pa-md bg-grey-2">
    <!-- Header -->
    <div class="row items-center justify-between q-mb-md">
      <div class="col-auto">
        <div class="text-h5 text-bold">Cổng Bảo Vệ</div>
        <div class="text-caption text-grey-7">Quản lý khách chờ và đã vào cổng</div>
      </div>
      <div class="col-auto row items-center q-gutter-sm">
        <q-input dense outlined v-model="q" placeholder="Tìm kiếm..." style="min-width: 250px" clearable @clear="load" @keyup.enter="load">
          <template #append><q-icon name="search" /></template>
        </q-input>
        <q-btn 
          flat 
          round 
          @click="toggleAudio"
          :icon="audioEnabled ? 'volume_up' : 'volume_off'"
          :color="audioEnabled ? 'positive' : 'grey-8'"
        >
          <q-tooltip>{{ audioEnabled ? 'Tắt âm báo' : 'Bật âm báo khách mới' }}</q-tooltip>
        </q-btn>
        <q-badge v-if="offline" color="orange" text-color="black" class="q-pa-sm">
          <q-icon name="cloud_off" class="q-mr-xs" />
          Offline
          <q-tooltip>Đang ở chế độ ngoại tuyến. Dữ liệu có thể đã cũ.</q-tooltip>
        </q-badge>
      </div>
    </div>

    <!-- Bảng: Khách đang xử lý (Chờ vào + Đã vào) -->
    <q-card class="q-mb-lg">
       <q-card-section class="bg-primary text-white">
        <div class="text-subtitle1 text-bold">Khách Đang Xử Lý ({{ activeGuests.length }})</div>
      </q-card-section>
      <q-separator />
      
      <!-- Các comment chú thích đã được dời ra BÊN NGOÀI thẻ q-table -->
      <!-- Class 'blink-warning' sẽ được áp dụng khi quá hạn -->
      <q-table
        :rows="activeGuests"
        :columns="activeGuestsColumns"
        row-key="id"
        flat
        :pagination="{ rowsPerPage: 50 }"
        :loading="loading"
        :row-class="(row) => {
          const overdue = isOverdue(row);
          return overdue ? 'bg-red-1 text-black blink-warning' : '';
        }"
      >
        <!-- BẮT ĐẦU SỬA LỖI: Dòng comment lỗi đã bị xóa hoàn toàn khỏi đây -->

        <!-- NEW: Status chip column -->
        <template #body-cell-status_chip="props">
          <q-td :props="props">
            <q-chip 
              v-if="props.row.status === 'pending'"
              color="positive" 
              text-color="white"
              dense
              size="sm"
            >
              Chờ vào
            </q-chip>
            <q-chip 
              v-else-if="props.row.status === 'checked_in'"
              color="warning" 
              text-color="black"
              dense
              size="sm"
            >
              Đang ở trong
            </q-chip>
          </q-td>
        </template>

        <template #body-cell-actions="props">
          <q-td :props="props">
            <!-- Dynamic button based on status -->
            <q-btn 
              v-if="props.row.status === 'pending'"
              color="positive" 
              icon="login" 
              label="Vào" 
              @click="confirmIn(props.row)" 
              dense
            />
            <q-btn 
              v-else-if="props.row.status === 'checked_in' && props.row.license_plate"
              color="warning" 
              text-color="black"
              icon="logout" 
              label="Ra" 
              @click="confirmOut(props.row)" 
              dense
            />
            <!-- Khách checked_in nhưng không có xe sẽ không hiển thị nút Ra (tự động chuyển xuống bảng dưới) -->
          </q-td>
        </template>
        
        <!-- BẮT ĐẦU NÂNG CẤP: Định dạng ô Ngày & Giờ dự kiến -->
        <template #body-cell-estimated_datetime="props">
          <q-td :props="props">
            <q-chip 
              v-if="props.value" 
              icon="schedule" 
              :label="quasarDate.formatDate(quasarDate.addToDate(props.value, { hours: 7 }), 'DD/MM HH:mm')" 
              dense 
              outline 
              size="md"
              :color="isOverdue(props.row) ? 'red-9' : 'blue-grey'"
            />
          </q-td>
        </template>
        <!-- KẾT THÚC NÂNG CẤP -->

        <template #no-data>
            <div class="full-width row flex-center text-positive q-gutter-sm q-pa-md">
                <q-icon size="2em" name="check_circle" />
                <span>Không có khách nào đang chờ.</span>
            </div>
        </template>
      </q-table>
    </q-card>

    <!-- === CHECKLIST 3.4, 3.6, 3.7, 3.8, 3.10: Bảng Hàng Chờ Ra === -->
    <q-card class="q-mb-lg">
      <q-card-section class="bg-warning text-black">
        <div class="text-subtitle1 text-bold">Hàng Chờ Ra ({{ assetsPendingOut.length }})</div>
      </q-card-section>
      <q-separator />
      <q-table
        :rows="assetsPendingOut"
        :columns="assetsPendingColumns"
        row-key="id"
        flat
        :pagination="{ rowsPerPage: 10 }"
        :loading="loading"
        dense
      >
        <template #body-cell-actions="props">
          <q-td :props="props">
            <!-- (Checklist 3.8) Màu 'warning' (Cam) -->
            <!-- (Checklist 3.10) Gọi hàm 'confirmAssetCheckOut' -->
            <q-btn color="warning" text-color="black" icon="arrow_circle_up" label="Xác nhận ra" @click="confirmAssetCheckOut(props.row)" dense/>
          </q-td>
        </template>
        <template #no-data>
            <div class="full-width row flex-center text-grey-7 q-gutter-sm q-pa-md">
                <q-icon size="2em" name="inventory_2" />
                <span>Không có tài sản nào chờ ra.</span>
            </div>
        </template>
      </q-table>
    </q-card>
    <!-- === KẾT THÚC CHECKLIST 3.4 === -->

    <!-- === CHECKLIST 3.5, 3.6, 3.7, 3.9, 3.11: Bảng Hàng Đã Ra (Chờ Về) === -->
    <q-card class="q-mb-lg">
      <q-card-section class="bg-info text-white">
        <div class="text-subtitle1 text-bold">Hàng Đã Ra - Chờ Về ({{ assetsCheckedOut.length }})</div>
      </q-card-section>
      <q-separator />
      <q-table
        :rows="assetsCheckedOut"
        :columns="assetsCheckedInColumns"
        row-key="id"
        flat
        :pagination="{ rowsPerPage: 10 }"
        :loading="loading"
        dense
      >
        <template #body-cell-actions="props">
          <q-td :props="props">
            <!-- (Checklist 3.9) Màu 'info' (Xanh dương) -->
            <!-- (Checklist 3.11) Gọi hàm 'confirmAssetReturn' -->
            <q-btn color="info" icon="arrow_circle_down" label="Xác nhận về" @click="confirmAssetReturn(props.row)" dense/>
          </q-td>
        </template>
        <template #no-data>
            <div class="full-width row flex-center text-grey-7 q-gutter-sm q-pa-md">
                <q-icon size="2em" name="check_circle" />
                <span>Không có tài sản nào đang ở bên ngoài.</span>
            </div>
        </template>
      </q-table>
    </q-card>
    <!-- === KẾT THÚC CHECKLIST 3.5 === -->

    <!-- Bảng: Lịch sử khách đã ra về / đã vào không xe -->
     <q-card>
       <q-card-section class="bg-blue-grey-8 text-white">
        <div class="text-subtitle1 text-bold">Lịch Sử Khách ({{ historyGuests.length }}) </div>
      </q-card-section>
      <q-separator />
      <q-table
        :rows="historyGuests"
        :columns="historyGuestsColumns"
        row-key="id"
        flat
        :pagination="{ rowsPerPage: 10 }"
        :loading="loading"
      >
        <!-- Status chip for history table -->
        <template #body-cell-status_history="props">
          <q-td :props="props">
            <q-chip 
              v-if="props.row.status === 'checked_out'"
              color="grey" 
              text-color="white"
              dense
              size="sm"
            >
              Đã về
            </q-chip>
            <q-chip 
              v-else-if="props.row.status === 'checked_in'"
              color="blue" 
              text-color="white"
              dense
              size="sm"
            >
              Đã vào
            </q-chip>
          </q-td>
        </template>

        <!-- BẮT ĐẦU NÂNG CẤP: Định dạng ô Giờ dự kiến (cho bảng đã vào) -->
        <template #body-cell-estimated_datetime="props">
          <q-td :props="props">
            <q-chip 
              v-if="props.value" 
              icon="schedule" 
              :label="quasarDate.formatDate(quasarDate.addToDate(props.value, { hours: 7 }), 'DD/MM HH:mm')" 
              dense 
              outline 
              size="sm"
              color="grey-8"
            />
          </q-td>
        </template>
        <!-- KẾT THÚC NÂNG CẤP -->
      </q-table>
    </q-card>
  </q-page>
</template>

<script setup>
// BẮT ĐẦU NÂNG CẤP: Thêm 'quasarDate'
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useQuasar, date as quasarDate } from 'quasar' 
// KẾT THÚC NÂNG CẤP
import api from '../api'
import { useAuthStore } from '../stores/auth'
// === CHECKLIST 4.6 (Phần 1): Import thêm các hàm PWA cho Tài sản ===
// === KẾT THÚC CHECKLIST 4.6 (Phần 1) ===

// PWA Imports (giữ nguyên)

import { registerServiceWorker } from '../register-sw'
// SỬA LỖI: Gộp tất cả import PWA vào 1 khối duy nhất
import { 
  getGuestsSnapshot, 
  saveGuestsSnapshot, 
  enqueueConfirm,
  enqueueConfirmOut,  // NEW: Add offline support for check-out
  drainQueue, 
  enqueueAssetCheckOut,
  enqueueAssetReturn
} from '../pwa/db/guard-gate-db'

const $q = useQuasar()
const auth = useAuthStore()
const loading = ref(false)

// Refactored variable names for clarity
const activeGuests = ref([])  // Khách đang xử lý (pending + checked_in)
const historyGuests = ref([]) // Lịch sử đã ra về (checked_out)
// === CHECKLIST 3.2: Thêm 2 ref mới cho tài sản ===
const assetsPendingOut = ref([])
const assetsCheckedOut = ref([])
// === KẾT THÚC CHECKLIST 3.2 ===
const q = ref('')
let timer = null

// --- PWA State Refs (giữ nguyên) ---
const cachedAt = ref(null)
const offline = ref(false)

// --- Audio Notification Logic (giữ nguyên) ---
const audioEnabled = ref(localStorage.getItem('guard_audio_enabled') !== 'false');
const previousPendingCount = ref(0)
let notificationSound = null

function toggleAudio() {
  if (!notificationSound) {
    notificationSound = new Audio('/notification.mp3');
  }
  
  audioEnabled.value = !audioEnabled.value;
  localStorage.setItem('guard_audio_enabled', audioEnabled.value);

  const message = audioEnabled.value ? 'Đã bật thông báo âm thanh.' : 'Đã tắt thông báo âm thanh.';
  const icon = audioEnabled.value ? 'volume_up' : 'volume_off';

  // BẮT ĐẦU SỬA LỖI: Sửa $q-notify thành $q.notify
  $q.notify({ type: 'info', icon, message, position: 'top' });
  // KẾT THÚC SỬA LỖI

  if (audioEnabled.value) {
    notificationSound.play().catch(e => console.error("Audio play failed on toggle:", e));
  }
}

// --- BẮT ĐẦU NÂNG CẤP: Logic kiểm tra quá giờ dự kiến (dùng DateTime) ---
function isOverdue(row) {
    // Chỉ áp dụng cho khách 'pending' VÀ có 'estimated_datetime'
    if (!row.estimated_datetime || row.status !== 'pending') return false;
    
    try {
      const now = new Date();
      // estimated_datetime là chuỗi ISO (VD: "2025-10-30T17:00:00")
      // new Date() có thể phân tích trực tiếp chuỗi này
      // Fix timezone +7
      const estDate = quasarDate.addToDate(new Date(row.estimated_datetime), { hours: 7 });

      // So sánh: Giờ hiện tại > Giờ dự kiến
      return now > estDate;
    } catch (e) {
      console.error("Lỗi khi phân tích isOverdue:", e);
      return false;
    }
}
// --- KẾT THÚC NÂNG CẤP ---

// --- SỬA ĐỔI: Thêm cột estimated_datetime ---
const baseColumns = [
  { name: 'full_name', align: 'left', label: 'Họ tên', field: 'full_name', sortable: true },
  { name: 'id_card_number', align: 'left', label: 'CCCD', field: 'id_card_number', sortable: true },
  { name: 'supplier_name', align: 'left', label: 'Nhà cung cấp', field: 'supplier_name', sortable: true },
  { name: 'reason', align: 'left', label: 'Chi tiết', field: 'reason', sortable: true, style: 'max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;' },
  { name: 'license_plate', align: 'left', label: 'Biển số', field: 'license_plate', sortable: true },
  

  // --- BẮT ĐẦU NÂNG CẤP: Cột Ngày & Giờ dự kiến ---
  { 
    name: 'estimated_datetime', 
    align: 'left', 
    label: 'Dự kiến', 
    field: 'estimated_datetime', 
    sortable: true,
    style: 'width: 200px' // <-- THÊM DÒNG NÀY
  },
  // --- KẾT THÚC NÂNG CẤP ---


  { name: 'registered_by_name', align: 'left', label: 'Người đăng ký', field: 'registered_by_name', sortable: true },
  { name: 'created_at', align: 'left', label: 'Ngày đăng ký', field: 'created_at', sortable: true, format: val => val ? new Date(val).toLocaleString('vi-VN') : '' },
];
// --- KẾT THÚC SỬA ĐỔI ---

const activeGuestsColumns = [
  // Cột "actions" được đưa lên đầu tiên
  { name: 'actions', label: 'Hành động', field: 'actions', align: 'left' },
  // Add status chip column
  { name: 'status_chip', label: 'Trạng thái', field: 'status', align: 'left' },
  ...baseColumns
];

const historyGuestsColumns = [
    // Add status chip column at the beginning
    { name: 'status_history', label: 'Trạng thái', field: 'status', align: 'left' },
    ...baseColumns,
    // Thêm cột giờ vào và giờ ra cho bảng lịch sử
    { 
      name: 'check_in_time', 
      align: 'left', 
      label: 'Giờ vào', 
      field: 'check_in_time', 
      sortable: true, 
      format: (val) => {
        if (!val) return '';
        try {
          const dateStr = val.endsWith('Z') ? val : val + 'Z';
          const dbDate = new Date(dateStr);
          const adjustedDate = quasarDate.addToDate(dbDate, { hours: -7 });
          return adjustedDate.toLocaleString('vi-VN');
        } catch (e) {
          return val;
        }
      } 
    },
    { 
      name: 'check_out_time', 
      align: 'left', 
      label: 'Giờ ra', 
      field: 'check_out_time', 
      sortable: true, 
      format: (val) => {
        if (!val) return '';
        try {
          const dateStr = val.endsWith('Z') ? val : val + 'Z';
          const dbDate = new Date(dateStr);
          const adjustedDate = quasarDate.addToDate(dbDate, { hours: -7 });
          return adjustedDate.toLocaleString('vi-VN');
        } catch (e) {
          return val;
        }
      } 
    },
];
// === CHECKLIST 3.6, 3.7: Định nghĩa cột cho bảng Tài sản ===
const assetBaseColumns = [
  { name: 'full_name', label: 'Người ĐK', field: row => row.registered_by.full_name, align: 'left', sortable: true },
  { name: 'department', label: 'Bộ phận', field: 'department', align: 'left', sortable: true },
  { name: 'destination', label: 'Nơi đến', field: 'destination', align: 'left', sortable: true },
  // (Checklist 3.6) Sửa style để mô tả có thể xuống dòng
  { name: 'description_reason', label: 'Mô tả', field: 'description_reason', align: 'left', style: 'max-width: 200px; white-space: normal;' },
  { name: 'quantity', label: 'SL', field: 'quantity', align: 'center', sortable: true }, // (Checklist 3.7)
  { name: 'expected_return_date', label: 'Dự kiến về', field: 'expected_return_date', align: 'left', sortable: true, format: val => val ? quasarDate.formatDate(val, 'DD/MM/YYYY') : 'Không về' },
];
const assetsPendingColumns = [
  { name: 'actions', label: 'Hành động', align: 'left', style: 'width: 150px' },
  ...assetBaseColumns
];
const assetsCheckedInColumns = [
  { name: 'actions', label: 'Hành động', align: 'left', style: 'width: 150px' },
  ...assetBaseColumns,
  { 
    name: 'check_out_time', 
    label: 'Giờ ra', 
    field: 'check_out_time', 
    align: 'left', 
    sortable: true, 
    // Sửa lỗi +7 giờ (nếu cần) bằng cách dùng toLocaleString
    format: val => val ? new Date(val).toLocaleString('vi-VN') : '' 
  },
];
// === KẾT THÚC CHECKLIST 3.6, 3.7 ===


// Chỉ cần thêm đoạn code này vào hàm load() trong GuardGate.vue

async function load () {
  loading.value = true;
  const userId = auth.user?.id || 'anon'
  try {
    // 1. Load guests - BÂY GIỜ BAO GỒM CẢ checked_out
    const res = await api.get('/guests', { params: { q: q.value || undefined, status: 'pending,checked_in,checked_out' } })
    const rows = res.data || []
    
    const newPendingCount = rows.filter(r => r.status === 'pending').length;
    if (audioEnabled.value && notificationSound && newPendingCount > previousPendingCount.value) {
      notificationSound.play().catch(e => console.error("Audio play failed on new guest:", e));
    }
    previousPendingCount.value = newPendingCount;

    // Phân loại theo logic mới + Backward Compatibility
    // Xác định thời điểm bắt đầu ngày hôm nay
    const startOfToday = new Date();
    startOfToday.setHours(0, 0, 0, 0);
    
    // activeGuests: 
    // - pending (all)
    // - OR (checked_in AND has license_plate AND created_at >= today)
    activeGuests.value = rows.filter(r => {
      if (r.status === 'pending') return true;
      
      if (r.status === 'checked_in' && r.license_plate) {
        // Chỉ hiển thị khách checked_in có xe nếu đăng ký từ hôm nay
        const createdAt = new Date(r.created_at);
        return createdAt >= startOfToday;
      }
      
      return false;
    });
    
    // historyGuests:
    // - checked_out
    // - OR (checked_in AND no license_plate)
    // - OR (checked_in AND created_at < today) --> Old data
    historyGuests.value = rows.filter(r => {
      if (r.status === 'checked_out') return true;
      
      if (r.status === 'checked_in') {
        // Khách không xe hoặc dữ liệu cũ đều xuống bảng lịch sử
        if (!r.license_plate) return true;
        
        const createdAt = new Date(r.created_at);
        return createdAt < startOfToday; // Old data
      }
      
      return false;
    });

    // === FIX: THÊM LOGIC LOAD ASSETS ===
    // 2. Load assets từ endpoint guard-gate
    const assetsRes = await api.get('/assets/guard-gate', { params: { q: q.value || undefined } })
    const assetsRows = assetsRes.data || []
    
    assetsPendingOut.value = assetsRows.filter(r => r.status === 'pending_out')
    assetsCheckedOut.value = assetsRows.filter(r => r.status === 'checked_out')
    // === KẾT THÚC FIX ===

    // Lưu cache PWA
    const plainActive = JSON.parse(JSON.stringify(activeGuests.value));
    const plainHistory = JSON.parse(JSON.stringify(historyGuests.value));
    const plainAssetsPending = JSON.parse(JSON.stringify(assetsPendingOut.value));
    const plainAssetsChecked = JSON.parse(JSON.stringify(assetsCheckedOut.value));
    
    await saveGuestsSnapshot(userId, { 
      pending: plainActive,  // Keep 'pending' key for backward compatibility
      checkedIn: plainHistory,  // Keep 'checkedIn' key for backward compatibility
      assetsPending: plainAssetsPending,
      assetsChecked: plainAssetsChecked
    });

    cachedAt.value = new Date().toISOString()
    offline.value = false

  } catch (error) {
    if (error.name !== 'DexieError') {
      $q.notify({type: 'negative', message: 'Không tải được danh sách khách/tài sản.'})
    }
    console.error("Failed to load data", error)
    offline.value = true
  } finally {
    loading.value = false;
  }
}

async function confirmIn (row) {
  // Offline handling (giữ nguyên)
  if (!navigator.onLine) {
    await enqueueConfirm(row.id)
    $q.notify({ type:'warning', message: 'Đã xếp hàng xác nhận. Sẽ đồng bộ khi online.'})
    const index = activeGuests.value.findIndex(p => p.id === row.id);
    if (index > -1) {
        const [confirmedGuest] = activeGuests.value.splice(index, 1);
        confirmedGuest.status = 'checked_in'; // Update status optimistically
        activeGuests.value.unshift(confirmedGuest); // Keep in same table but update status
    }
    try { 
      const registration = await navigator.serviceWorker.ready;
      await registration.sync.register('sync-confirm') 
    } catch(e){
      console.error('Background Sync registration failed:', e);
    }
    return
  }
  
  // Online handling
  try {
    await api.post(`/guests/${row.id}/confirm-in`)
    $q.notify({type: 'positive', message: `${row.full_name} đã được xác nhận vào.`})
    load() // Tải lại dữ liệu sau khi xác nhận
  } catch(error) {
     $q.notify({type: 'negative', message: 'Xác nhận thất bại.'})
  }
}

// === NEW FUNCTION: confirmOut ===
async function confirmOut(row) {
  // Offline handling with PWA support
  if (!navigator.onLine) {
    try {
      await enqueueConfirmOut(row.id)
      $q.notify({ type:'warning', message: 'Đã xếp hàng xác nhận ra (offline). Sẽ đồng bộ khi online.'})
      
      // Optimistic update: move from activeGuests to historyGuests
      const index = activeGuests.value.findIndex(p => p.id === row.id);
      if (index > -1) {
        const [confirmedGuest] = activeGuests.value.splice(index, 1);
        confirmedGuest.status = 'checked_out';
        confirmedGuest.check_out_time = new Date().toISOString();
        historyGuests.value.unshift(confirmedGuest);
      }
      
      // Register background sync
      const registration = await navigator.serviceWorker.ready;
      await registration.sync.register('sync-confirm');
    } catch(e) {
      console.error('Failed to enqueue check-out:', e);
      $q.notify({ type: 'negative', message: 'Lỗi khi xếp hàng offline.' });
    }
    return
  }
  
  // Online handling
  try {
    await api.post(`/guests/${row.id}/confirm-out`)
    $q.notify({type: 'info', message: `${row.full_name} đã được xác nhận ra.`})
    load() // Reload data - guest will move to "Lịch sử" table
  } catch(error) {
    console.error('Check-out failed:', error)
    $q.notify({type: 'negative', message: error.response?.data?.detail || 'Xác nhận ra thất bại.'})
  }
}

// === CHECKLIST 3.10: Hàm Xác nhận Tài sản RA ===
async function confirmAssetCheckOut(row) {
  // === CHECKLIST 4.6 (Phần 2): Logic PWA Offline ===
  if (!navigator.onLine) {
    try {
      await enqueueAssetCheckOut(row.id); // <--- Gọi hàm PWA mới
      $q.notify({ type:'warning', message: 'Đã xếp hàng (offline) xác nhận TÀI SẢN RA.'});
      
      // Cập nhật UI (Optimistic Update)
      const index = assetsPendingOut.value.findIndex(p => p.id === row.id);
      if (index > -1) {
          const [confirmedAsset] = assetsPendingOut.value.splice(index, 1);
          confirmedAsset.status = 'checked_out'; // Cập nhật trạng thái
          assetsCheckedOut.value.unshift(confirmedAsset); // Thêm vào bảng "Chờ Về"
      }
      // Đăng ký Background Sync
      const registration = await navigator.serviceWorker.ready;
      await registration.sync.register('sync-confirm'); 
    } catch(e){
      console.error('Lỗi xếp hàng (enqueue) confirmAssetCheckOut:', e);
      $q.notify({ type: 'negative', message: 'Lỗi khi xếp hàng offline.' });
    }
    return;
  }
  // === KẾT THÚC CHECKLIST 4.6 (Phần 2) ===

  // === FIX (TASK 2): Xóa bỏ đoạn code offline lặp lại (dead code) ===
  // if (!navigator.onLine) {
  //   $q.notify({ type:'warning', message: 'Chức năng offline cho tài sản chưa được hỗ trợ. Vui lòng kết nối mạng.'})
  //   return;
  // }
  // === KẾT THÚC FIX ===

  try {
    // Gọi API đã tạo ở Giai đoạn 1 (Checklist 1.9)
    await api.post(`/assets/${row.id}/checkout`);
    $q.notify({ type: 'positive', message: `Đã xác nhận tài sản [${row.description_reason}] RA.` });
    load(); // Tải lại toàn bộ dữ liệu
  } catch (error) {
    $q.notify({ type: 'negative', message: error.response?.data?.detail || 'Xác nhận thất bại.' });
  }
}
// === KẾT THÚC CHECKLIST 3.10 ===

// === CHECKLIST 3.11 & 4.6 (Phần 3): Cập nhật hàm Xác nhận Tài sản VỀ (Hỗ trợ Offline) ===
async function confirmAssetReturn(row) {
  // === CHECKLIST 4.6 (Phần 3): Logic PWA Offline ===
  if (!navigator.onLine) {
    try {
      await enqueueAssetReturn(row.id); // <--- Gọi hàm PWA mới
      $q.notify({ type:'warning', message: 'Đã xếp hàng (offline) xác nhận TÀI SẢN VỀ.'});
      
      // Cập nhật UI (Optimistic Update)
      const index = assetsCheckedOut.value.findIndex(p => p.id === row.id);
      if (index > -1) {
          assetsCheckedOut.value.splice(index, 1); // Xóa khỏi bảng "Chờ Về"
      }
      // Đăng ký Background Sync
      const registration = await navigator.serviceWorker.ready;
      await registration.sync.register('sync-confirm'); 
    } catch(e){
      console.error('Lỗi xếp hàng (enqueue) confirmAssetReturn:', e);
      $q.notify({ type: 'negative', message: 'Lỗi khi xếp hàng offline.' });
    }
    return;
  }
  // === KẾT THÚC CHECKLIST 4.6 (Phần 3) ===
  
  // Logic Online (giữ nguyên)
  try {
    // Gọi API đã tạo ở Giai đoạn 1 (Checklist 1.10)
    await api.post(`/assets/${row.id}/checkin-back`);
    $q.notify({ type: 'info', message: `Đã xác nhận tài sản [${row.description_reason}] VỀ.` });
    load(); // Tải lại toàn bộ dữ liệu
  } catch (error) {
    $q.notify({ type: 'negative', message: error.response?.data?.detail || 'Xác nhận thất bại.' });
  }
}
// === KẾT THÚC CHECKLIST 3.11 & 4.6 (Phần 3) ===


// --- PWA Function ---
// === CHECKLIST 4.6 (Phần 4): Cập nhật flushQueue để xử lý Tài sản VÀ Khách ra ===
async function flushQueue() {
  await drainQueue(async (item) => {
    // Guest check-in
    if (item.type === 'confirmIn') {
      await api.post(`/guests/${item.payload.guestId}/confirm-in`);
    }
    // Guest check-out (NEW)
    if (item.type === 'confirmOut') {
      await api.post(`/guests/${item.payload.guestId}/confirm-out`);
    }
    // Asset checkout
    if (item.type === 'ASSET_CHECKOUT') {
      await api.post(`/assets/${item.payload.assetId}/checkout`);
    }
    // Asset return
    if (item.type === 'ASSET_RETURN') {
      await api.post(`/assets/${item.payload.assetId}/checkin-back`);
    }
  });
  
  // Chỉ load lại khi online để tránh lỗi
  if (navigator.onLine) {
    await load();
  }
}
// === KẾT THÚC CHECKLIST 4.6 (Phần 4) ===

// --- Lifecycle hooks (giữ nguyên) ---
onMounted(async () => {
  notificationSound = new Audio('/notification.mp3');
  
  registerServiceWorker()
  
  const userId = auth.user?.id || 'anon'
  const snap = await getGuestsSnapshot(userId)
  if (snap?.data) {
    activeGuests.value = snap.data.pending || []  // backward compatibility
    historyGuests.value = snap.data.checkedIn || []  // backward compatibility
    // === CHECKLIST 4.4: Tải assets từ PWA cache ===
    assetsPendingOut.value = snap.data.assetsPending || []
    assetsCheckedOut.value = snap.data.assetsChecked || []
    // === KẾT THÚC CHECKLIST 4.4 ===
    cachedAt.value = snap.cachedAt
    offline.value = !navigator.onLine
  }
  
  if (navigator.onLine) {
    await load()
  }
  previousPendingCount.value = activeGuests.value.filter(g => g.status === 'pending').length;
  
  navigator.serviceWorker?.addEventListener('message', async (e) => {
    const { type } = e.data || {}
    if (type === 'GUESTS_REFRESHED' || type === 'SYNC_CONFIRM') {
      await flushQueue()
    }
  })
  
  window.addEventListener('online', flushQueue)

  timer = setInterval(load, 15000) // Tăng thời gian polling lên 15 giây
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  window.removeEventListener('online', flushQueue);
})
</script>

<!-- BẮT ĐẦU NÂNG CẤP: Thêm CSS cho hiệu ứng nhấp nháy -->
<style lang="scss" scoped>
// Thêm một chút style để giao diện thoáng hơn
.q-page {
//  max-width: 1400px;
  margin: 0 auto;
}

// CSS Animation cho cảnh báo quá hạn
@keyframes blink-animation {
  0% { opacity: 1; }
  50% { opacity: 0.6; }
  100% { opacity: 1; }
}
.blink-warning {
  animation: blink-animation 1.5s infinite;
}
</style>
<!-- KẾT THÚC NÂNG CẤP -->