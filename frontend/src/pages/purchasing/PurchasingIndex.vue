<script setup>
/**
 * PurchasingIndex.vue
 * Trang danh sách Quản lý Mua bán
 */
import { ref, onMounted, computed } from 'vue'
import { useQuasar, date as qdate } from 'quasar'
import api from '../../api'
import PurchasingFormDialog from './components/PurchasingFormDialog.vue'
import PurchasingDetailDialog from './components/PurchasingDetailDialog.vue'
import PurchasingReceiveDialog from './components/PurchasingReceiveDialog.vue'

const $q = useQuasar()

// Data
const purchasingList = ref([])
const loading = ref(false)

// Filters
const filterStartDate = ref('')
const filterEndDate = ref('')
const filterCategory = ref(null)

// Dialog
const showFormDialog = ref(false)
const editItem = ref(null)

// Image viewer
const showImageDialog = ref(false)
const currentImages = ref([])
const currentImageIndex = ref(0)
const showDetailDialog = ref(false)
const showReceiveDialog = ref(false)
const selectedItem = ref(null)
const receiveItem = ref(null)

// Table columns
const columns = [
  { name: 'created_at', label: 'Ngày tạo', field: 'created_at', align: 'left', sortable: true },
  { name: 'creator_name', label: 'Người lập', field: 'creator_name', align: 'left' },
  { name: 'department', label: 'Bộ phận', field: 'department', align: 'left' },
  { name: 'category', label: 'Loại hàng', field: 'category', align: 'left' },
  { name: 'item_name', label: 'Tên hàng', field: 'item_name', align: 'left' },
  { name: 'supplier_name', label: 'Nhà cung cấp', field: 'supplier_name', align: 'left' },
  { name: 'approved_price', label: 'Giá duyệt', field: 'approved_price', align: 'right' },
  { name: 'status', label: 'Trạng thái', field: 'status', align: 'center' },
  { name: 'images', label: 'Ảnh', field: 'images', align: 'center' },
  { name: 'actions', label: 'Thao tác', field: 'actions', align: 'center' }
]

const categoryOptions = [
  { label: 'Tất cả', value: null },
  { label: 'PC', value: 'PC' },
  { label: 'Laptop', value: 'Laptop' },
  { label: 'Linh kiện', value: 'Linh kiện' },
  { label: 'Mực in', value: 'Mực in' },
  { label: 'Khác', value: 'Khác' }
]

// Status mapping
const statusMap = {
  new: { label: 'Mới', color: 'blue' },
  pending: { label: 'Chờ duyệt', color: 'orange' },
  approved: { label: 'Đã duyệt', color: 'green' },
  rejected: { label: 'Từ chối', color: 'red' },
  completed: { label: 'Đã nhận', color: 'purple' }
}

// Computed
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Format helpers
function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString('vi-VN')
}

function formatPrice(price) {
  if (!price) return '0 ₫'
  return price.toLocaleString('vi-VN') + ' ₫'
}

function getStatusInfo(status) {
  return statusMap[status] || { label: status, color: 'grey' }
}

function getImageUrl(imagePath) {
  return `${API_URL}/uploads/${imagePath}`
}

// Fetch data
async function fetchData() {
  loading.value = true
  try {
    const params = {}
    if (filterStartDate.value) params.start_date = filterStartDate.value
    if (filterEndDate.value) params.end_date = filterEndDate.value
    if (filterCategory.value) params.category = filterCategory.value

    const res = await api.get('/purchasing', { params })
    purchasingList.value = res.data
  } catch (e) {
    console.error('Fetch error:', e)
    $q.notify({ type: 'negative', message: 'Không thể tải dữ liệu' })
  } finally {
    loading.value = false
  }
}

// Open form for new
function openNewForm() {
  editItem.value = null
  showFormDialog.value = true
}

// Open form for edit
function openEditForm(item) {
  editItem.value = item
  showFormDialog.value = true
}

// Refresh after save
function onSaved() {
  fetchData()
}

// Delete item
async function deleteItem(item) {
  $q.dialog({
    title: 'Xác nhận xóa',
    message: `Bạn có chắc muốn xóa phiếu "${item.item_name}"?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.delete(`/purchasing/${item.id}`)
      $q.notify({ type: 'positive', message: 'Đã xóa thành công!' })
      fetchData()
    } catch (e) {
      console.error('Delete error:', e)
      $q.notify({ type: 'negative', message: 'Không thể xóa!' })
    }
  })
}

// View images
function viewImages(images) {
  if (!images || images.length === 0) return
  currentImages.value = images
  currentImageIndex.value = 0
  showImageDialog.value = true
}

const openDetail = (evt, row) => {
  selectedItem.value = row
  showDetailDialog.value = true
}

const openReceive = (item) => {
  receiveItem.value = item
  showReceiveDialog.value = true
}

onMounted(fetchData)
</script>

<template>
  <q-page padding>
    <!-- Header -->
    <div class="row items-center q-mb-md">
      <div class="text-h5 text-weight-bold">
        <q-icon name="shopping_cart" class="q-mr-sm" />
        Quản lý Mua bán
      </div>
      <q-space />
      <q-btn color="primary" icon="add" label="Thêm mới" @click="openNewForm" />
    </div>

    <!-- Filters -->
    <q-card flat bordered class="q-mb-md">
      <q-card-section class="row q-gutter-md items-end">
        <q-input
          v-model="filterStartDate"
          label="Từ ngày"
          type="date"
          dense
          outlined
          style="width: 150px"
        />
        <q-input
          v-model="filterEndDate"
          label="Đến ngày"
          type="date"
          dense
          outlined
          style="width: 150px"
        />
        <q-select
          v-model="filterCategory"
          :options="categoryOptions"
          option-value="value"
          option-label="label"
          emit-value
          map-options
          label="Loại hàng"
          dense
          outlined
          style="width: 150px"
        />
        <q-btn color="primary" icon="search" label="Lọc" @click="fetchData" />
        <q-btn flat icon="refresh" @click="fetchData" />
      </q-card-section>
    </q-card>

    <!-- Table -->
    <q-table
      :rows="purchasingList"
      :columns="columns"
      row-key="id"
      :loading="loading"
      flat
      bordered
      :rows-per-page-options="[10, 25, 50]"
      @row-click="openDetail"
      class="cursor-pointer"
    >
      <!-- Date column -->
      <template v-slot:body-cell-created_at="props">
        <q-td :props="props">
          {{ formatDate(props.row.created_at) }}
        </q-td>
      </template>

      <!-- Price column -->
      <template v-slot:body-cell-approved_price="props">
        <q-td :props="props" class="text-weight-medium">
          {{ formatPrice(props.row.approved_price) }}
        </q-td>
      </template>

      <!-- Status column -->
      <template v-slot:body-cell-status="props">
        <q-td :props="props">
          <q-chip
            :color="getStatusInfo(props.row.status).color"
            text-color="white"
            dense
            size="sm"
          >
            {{ getStatusInfo(props.row.status).label }}
          </q-chip>
        </q-td>
      </template>

      <!-- Images column -->
      <template v-slot:body-cell-images="props">
        <q-td :props="props">
          <template v-if="props.row.images && props.row.images.length > 0">
            <q-avatar
              v-for="(img, idx) in props.row.images.slice(0, 2)"
              :key="img.id"
              size="32px"
              class="cursor-pointer q-mr-xs"
              @click="viewImages(props.row.images)"
            >
              <img :src="getImageUrl(img.image_path)" />
            </q-avatar>
            <q-badge v-if="props.row.images.length > 2" color="grey">
              +{{ props.row.images.length - 2 }}
            </q-badge>
          </template>
          <span v-else class="text-grey-5">--</span>
        </q-td>
      </template>

      <!-- Actions column -->
      <template v-slot:body-cell-actions="props">
        <q-td :props="props">
          <q-btn flat round dense icon="edit" color="primary" @click.stop="openEditForm(props.row)">
            <q-tooltip>Sửa</q-tooltip>
          </q-btn>
          <!-- Nút Nhận hàng: Chỉ hiện khi chưa hoàn thành và chưa từ chối -->
          <q-btn 
            v-if="!['completed', 'rejected'].includes(props.row.status)"
            flat round dense icon="inventory" color="deep-purple" 
            @click.stop="openReceive(props.row)"
          >
            <q-tooltip>Nhận hàng</q-tooltip>
          </q-btn>
          <q-btn flat round dense icon="delete" color="negative" @click.stop="deleteItem(props.row)">
            <q-tooltip>Xóa</q-tooltip>
          </q-btn>
        </q-td>
      </template>
    </q-table>

    <!-- Detail Dialog -->
    <PurchasingDetailDialog
      v-model="showDetailDialog"
      :item="selectedItem"
    />

    <!-- Form Dialog -->
    <PurchasingFormDialog
      v-model="showFormDialog"
      :edit-item="editItem"
      @saved="onSaved"
    />

    <!-- Receive Dialog -->
    <PurchasingReceiveDialog
      v-if="receiveItem"
      v-model="showReceiveDialog"
      :item="receiveItem"
      @saved="onSaved"
    />

    <!-- Image Viewer Dialog -->
    <q-dialog v-model="showImageDialog" maximized>
      <q-card class="bg-black">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-white">
            Ảnh {{ currentImageIndex + 1 }} / {{ currentImages.length }}
          </div>
          <q-space />
          <q-btn icon="close" flat round dense color="white" v-close-popup />
        </q-card-section>
        <q-card-section class="flex flex-center" style="height: calc(100vh - 80px)">
          <q-carousel
            v-model="currentImageIndex"
            animated
            arrows
            navigation
            infinite
            class="full-width full-height"
          >
            <q-carousel-slide
              v-for="(img, idx) in currentImages"
              :key="img.id"
              :name="idx"
              class="flex flex-center"
            >
              <img
                :src="getImageUrl(img.image_path)"
                style="max-width: 90vw; max-height: 80vh; object-fit: contain"
              />
            </q-carousel-slide>
          </q-carousel>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>
