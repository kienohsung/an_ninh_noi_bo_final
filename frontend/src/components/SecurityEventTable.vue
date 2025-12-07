<template>
  <div class="security-event-table">
    <!-- Header với nút thêm mới -->
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="text-body2 text-grey-8">
          Ghi nhận các sự kiện an ninh quan trọng trong công ty.
        </div>
      </div>
      <div class="col-auto" v-if="canCreate">
        <q-btn 
          color="primary" 
          icon="add" 
          label="Thêm sự kiện" 
          @click="openCreateDialog"
          unelevated
        />
      </div>
    </div>

    <!-- Bảng danh sách sự kiện -->
    <q-table
      :rows="events"
      :columns="columns"
      row-key="id"
      :loading="loading"
      flat
      bordered
      @row-click="onRowClick"
      :pagination="{ rowsPerPage: 10 }"
      class="cursor-pointer"
    >
      <template v-slot:body-cell-occurred_at="props">
        <q-td :props="props">
          {{ formatDateTime(props.row.occurred_at) }}
        </q-td>
      </template>

      <!-- Actions Slot -->
      <template v-slot:body-cell-actions="props">
        <q-td :props="props" @click.stop>
          <q-btn flat round dense color="primary" icon="edit" size="sm" @click.stop="openEditDialog(props.row)">
            <q-tooltip>Sửa</q-tooltip>
          </q-btn>
          <q-btn flat round dense color="negative" icon="delete" size="sm" @click.stop="confirmDeleteEvent(props.row)" v-if="canDelete">
            <q-tooltip>Xóa</q-tooltip>
          </q-btn>
        </q-td>
      </template>

      <template v-slot:loading>
        <q-inner-loading showing color="primary" />
      </template>

      <template v-slot:no-data>
        <div class="full-width row flex-center text-grey-6 q-gutter-sm q-pa-lg">
          <q-icon size="2em" name="sentiment_dissatisfied" />
          <span>Chưa có sự kiện nào được ghi nhận</span>
        </div>
      </template>
    </q-table>

    <!-- Dialog Thêm mới -->
    <q-dialog v-model="showCreateDialog" persistent>
      <q-card style="min-width: 500px; max-width: 700px">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6">
            <q-icon name="report_problem" color="warning" class="q-mr-sm" />
            {{ isEditing ? 'Cập Nhật Sự Kiện' : 'Thêm Sự Kiện An Ninh' }}
          </div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-separator />

        <q-card-section class="q-gutter-md">
          <q-input
            v-model="eventForm.title"
            label="Tiêu đề sự kiện *"
            outlined
            dense
            :rules="[val => !!val || 'Tiêu đề là bắt buộc', val => val.length >= 5 || 'Tối thiểu 5 ký tự']"
          />

          <div class="row q-col-gutter-md">
            <div class="col-12 col-sm-6">
              <q-input
                v-model="eventForm.occurred_date"
                label="Ngày xảy ra *"
                outlined
                dense
                mask="date"
                :rules="[val => !!val || 'Ngày là bắt buộc']"
              >
                <template v-slot:append>
                  <q-icon name="event" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date v-model="eventForm.occurred_date">
                        <div class="row items-center justify-end">
                          <q-btn v-close-popup label="Đóng" color="primary" flat />
                        </div>
                      </q-date>
                    </q-popup-proxy>
                  </q-icon>
                </template>
              </q-input>
            </div>
            <div class="col-12 col-sm-6">
              <q-input
                v-model="eventForm.occurred_time"
                label="Giờ xảy ra *"
                outlined
                dense
                mask="time"
                :rules="[val => !!val || 'Giờ là bắt buộc']"
              >
                <template v-slot:append>
                  <q-icon name="access_time" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-time v-model="eventForm.occurred_time" format24h>
                        <div class="row items-center justify-end">
                          <q-btn v-close-popup label="Đóng" color="primary" flat />
                        </div>
                      </q-time>
                    </q-popup-proxy>
                  </q-icon>
                </template>
              </q-input>
            </div>
          </div>

          <q-input
            v-model="eventForm.location"
            label="Địa điểm *"
            outlined
            dense
            :rules="[val => !!val || 'Địa điểm là bắt buộc']"
          />

          <q-input
            v-model="eventForm.involved_parties"
            label="Các bên liên quan"
            outlined
            dense
            placeholder="VD: Bảo vệ, Quản lý, Nhân viên A..."
          />

          <q-input
            v-model="eventForm.detail"
            label="Nội dung chi tiết"
            outlined
            dense
            type="textarea"
            rows="3"
          />

          <q-input
            v-model="eventForm.resolution"
            label="Hướng giải quyết"
            outlined
            dense
            type="textarea"
            rows="2"
          />

          <!-- Upload ảnh -->
          <div>
            <div class="text-caption text-grey-7 q-mb-sm">Ảnh đính kèm (tối đa 5 ảnh)</div>
            <q-file
              v-model="selectedImages"
              outlined
              dense
              multiple
              accept="image/*"
              max-files="5"
              counter
              :max-file-size="10485760"
              @rejected="onImageRejected"
            >
              <template v-slot:prepend>
                <q-icon name="attach_file" />
              </template>
              <template v-slot:append>
                <q-icon name="close" @click.stop.prevent="selectedImages = []" class="cursor-pointer" />
              </template>
            </q-file>
          </div>
        </q-card-section>

        <q-separator />

        <q-card-actions align="right" class="q-pa-md">
          <q-btn flat label="Hủy" color="grey" v-close-popup />
          <q-btn 
            :label="isEditing ? 'Lưu thay đổi' : 'Tạo sự kiện'" 
            color="primary" 
            unelevated
            :loading="saving"
            @click="handleSaveEvent"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Dialog Xem chi tiết (Read-only) - Redesigned -->
    <q-dialog v-model="showDetailDialog" full-width>
      <q-card class="bg-white" style="width: 90vw; max-width: 1400px; display: flex; flex-direction: column; max-height: 90vh">
        <!-- Report Header -->
        <q-card-section class="q-pa-lg text-center bg-grey-2 border-bottom flex-none">
          <div class="text-h5 text-weight-bold text-uppercase text-primary q-mb-xs">Báo Cáo Sự Kiện An Ninh</div>
          <div class="text-caption text-grey-8">Mã sự kiện: <span class="text-weight-bold">#SE-{{ selectedEvent?.id }}</span></div>
          <div class="text-caption text-grey-8">Ngày báo cáo: {{ selectedEvent ? formatDateTime(selectedEvent.created_at) : '' }}</div>
          <q-btn icon="close" flat round dense v-close-popup class="absolute-top-right q-ma-sm" />
        </q-card-section>

        <q-separator />

        <q-card-section class="q-pa-lg scroll" style="flex: 1" v-if="selectedEvent">
          <div class="row q-col-gutter-xl full-height">
            <!-- LEFT COLUMN: Information -->
            <div class="col-12 col-md-7 flex column">
               <!-- 1. General Info -->
               <div class="row items-center q-mb-md">
                 <q-icon name="info" color="primary" size="sm" class="q-mr-sm" />
                 <div class="text-subtitle1 text-weight-bold text-uppercase text-primary">1. Thông tin chung</div>
               </div>
               
               <div class="row q-col-gutter-y-md q-col-gutter-x-xl q-mb-lg">
                  <!-- Row 1: Title -->
                  <div class="col-12">
                     <div class="text-caption text-grey-7 text-uppercase" style="letter-spacing: 0.5px">Tiêu đề sự kiện</div>
                     <div class="text-h6 text-weight-medium text-blue-grey-10">{{ selectedEvent.title }}</div>
                  </div>

                  <!-- Row 2: Time & Location -->
                  <div class="col-12 col-sm-6">
                     <div class="text-caption text-grey-7 text-uppercase" style="letter-spacing: 0.5px">Thời gian xảy ra</div>
                     <div class="text-body1 flex items-center">
                       <q-icon name="event" size="xs" class="q-mr-xs text-grey-6" />
                       {{ formatDateTime(selectedEvent.occurred_at) }}
                     </div>
                  </div>
                  <div class="col-12 col-sm-6">
                     <div class="text-caption text-grey-7 text-uppercase" style="letter-spacing: 0.5px">Địa điểm</div>
                     <div class="text-body1 flex items-center">
                       <q-icon name="place" size="xs" class="q-mr-xs text-grey-6" />
                       {{ selectedEvent.location }}
                     </div>
                  </div>
                  
                  <!-- Row 3: Reporter & Involved Parties -->
                  <div class="col-12 col-sm-6">
                     <div class="text-caption text-grey-7 text-uppercase" style="letter-spacing: 0.5px">Người báo cáo</div>
                     <div class="text-body1 flex items-center">
                         <q-icon name="person" size="xs" class="q-mr-xs text-grey-6" />
                         <span class="text-weight-medium">{{ selectedEvent.reported_by_name }}</span>
                     </div>
                  </div>
                  <div class="col-12 col-sm-6">
                     <div class="text-caption text-grey-7 text-uppercase" style="letter-spacing: 0.5px">Các bên liên quan</div>
                     <div class="text-body1 flex items-center">
                         <q-icon name="groups" size="xs" class="q-mr-xs text-grey-6" />
                         {{ selectedEvent.involved_parties || 'Không có' }}
                     </div>
                  </div>
               </div>
               
               <q-separator class="q-my-lg" />

               <!-- 2. Details -->
               <div class="row items-center q-mb-md">
                 <q-icon name="description" color="primary" size="sm" class="q-mr-sm" />
                 <div class="text-subtitle1 text-weight-bold text-uppercase text-primary">2. Nội dung chi tiết</div>
               </div>
               <div class="bg-grey-1 q-pa-md rounded-borders text-body1 text-justify q-mb-lg" style="white-space: pre-wrap; line-height: 1.6">
                 {{ selectedEvent.detail || 'Chưa cập nhật nội dung' }}
               </div>

               <!-- 3. Resolution -->
               <div class="row items-center q-mb-md">
                 <q-icon name="assignment_turned_in" color="positive" size="sm" class="q-mr-sm" />
                 <div class="text-subtitle1 text-weight-bold text-uppercase text-positive">3. Hướng giải quyết</div>
               </div>
               <div class="bg-green-1 q-pa-md rounded-borders text-body1 text-justify" style="white-space: pre-wrap; line-height: 1.6; border-left: 4px solid #21ba45">
                 {{ selectedEvent.resolution || 'Chưa có hướng giải quyết' }}
               </div>
            </div>

            <!-- RIGHT COLUMN: Images -->
            <div class="col-12 col-md-5">
              <div class="column full-height">
                <div class="row items-center q-mb-md">
                  <q-icon name="photo_library" color="primary" size="sm" class="q-mr-sm" />
                  <div class="text-subtitle1 text-weight-bold text-uppercase text-primary">4. Hình ảnh ({{ selectedEvent.images ? selectedEvent.images.length : 0 }})</div>
                </div>

                <div v-if="!selectedEvent.images || selectedEvent.images.length === 0" class="col flex flex-center bg-grey-2 rounded-borders text-grey-6">
                  <div class="text-center">
                    <q-icon name="no_photography" size="4em" />
                    <div class="q-mt-sm">Không có hình ảnh đính kèm</div>
                  </div>
                </div>

                <div v-else class="col relative-position">
                   <q-carousel
                    v-model="carouselSlide"
                    animated
                    arrows
                    navigation
                    infinite
                    class="bg-grey-9 text-white rounded-borders shadow-2 full-height"
                  >
                    <q-carousel-slide 
                      v-for="(img, idx) in selectedEvent.images" 
                      :key="img.id" 
                      :name="idx"
                      class="flex flex-center q-pa-none"
                    >
                      <q-img
                        :src="getImageUrl(img.image_path)"
                        fit="contain"
                        class="full-height full-width cursor-pointer"
                        @click="openImageFullscreen(img)"
                      >
                        <template v-slot:loading>
                          <q-spinner-gears color="primary" />
                        </template>
                      </q-img>
                    </q-carousel-slide>
                  </q-carousel>
                  
                  <div class="text-caption text-center text-grey-6 q-mt-sm">
                    * Nhấn vào ảnh để xem kích thước đầy đủ
                  </div>
                </div>
              </div>
            </div>
          </div>
        </q-card-section>

        
        <q-separator />

        <q-card-actions align="right" class="q-pa-md bg-grey-1" v-if="canDelete">
          <q-btn 
            flat 
            label="Xóa báo cáo này" 
            color="negative" 
            icon="delete"
            @click="confirmDeleteEvent(selectedEvent)"
            :loading="deleting"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const $q = useQuasar()
const auth = useAuthStore()

// Permissions
const canCreate = computed(() => ['admin', 'manager', 'guard'].includes(auth.user?.role))
const canDelete = computed(() => auth.user?.role === 'admin')

// Data
const events = ref([])
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)

// Dialogs
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const selectedEvent = ref(null)
const carouselSlide = ref(0)
const isEditing = ref(false)
const editingId = ref(null)

// Form
const eventForm = ref({
  title: '',
  occurred_date: '',
  occurred_time: '',
  location: '',
  involved_parties: '',
  detail: '',
  resolution: ''
})
const selectedImages = ref([])

// Table columns
const columns = [
  { 
    name: 'occurred_at', 
    label: 'Thời gian', 
    field: 'occurred_at', 
    sortable: true,
    align: 'left',
    style: 'width: 150px'
  },
  { 
    name: 'title', 
    label: 'Tiêu đề', 
    field: 'title',
    align: 'left'
  },
  { 
    name: 'location', 
    label: 'Địa điểm', 
    field: 'location',
    align: 'left',
    style: 'width: 150px'
  },
  { 
    name: 'reported_by_name', 
    label: 'Người báo cáo', 
    field: 'reported_by_name',
    align: 'left',
    style: 'width: 150px'
  },
  {
    name: 'actions',
    label: 'Thao tác',
    field: 'actions',
    align: 'center',
    style: 'width: 100px'
  }
]

// Helpers
function formatDateTime(dt) {
  if (!dt) return 'N/A'
  return new Date(dt).toLocaleString('vi-VN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getImageUrl(path) {
  if (!path) return ''
  // Handle absolute URLs
  if (path.startsWith('http')) return path
  
  // Build URL with /uploads prefix (backend mounts static files at /uploads because UPLOAD_DIR is "uploads")
  const baseUrl = api.defaults.baseURL.replace('/api', '')
  
  // If path already has uploads prefix, don't add again
  if (path.startsWith('uploads/')) {
    return `${baseUrl}/${path.replace(/\\/g, '/')}`
  }
  
  // Add uploads prefix for relative paths
  return `${baseUrl}/uploads/${path.replace(/\\/g, '/')}`
}

function resetForm() {
  eventForm.value = {
    title: '',
    occurred_date: '',
    occurred_time: '',
    location: '',
    involved_parties: '',
    detail: '',
    resolution: ''
  }
  selectedImages.value = []
  isEditing.value = false
  editingId.value = null
}

function openCreateDialog() {
  resetForm()
  showCreateDialog.value = true
}

function openEditDialog(row) {
  const dt = new Date(row.occurred_at)
  // Fix date format for input QDate: YYYY/MM/DD
  const yyyy = dt.getFullYear()
  const mm = String(dt.getMonth() + 1).padStart(2, '0')
  const dd = String(dt.getDate()).padStart(2, '0')
  const hh = String(dt.getHours()).padStart(2, '0')
  const min = String(dt.getMinutes()).padStart(2, '0')

  eventForm.value = {
    title: row.title,
    occurred_date: `${yyyy}/${mm}/${dd}`,
    occurred_time: `${hh}:${min}`,
    location: row.location,
    involved_parties: row.involved_parties,
    detail: row.detail,
    resolution: row.resolution
  }
  selectedImages.value = [] // Reset images
  
  isEditing.value = true
  editingId.value = row.id
  showCreateDialog.value = true
}

// API calls
async function fetchEvents() {
  loading.value = true
  try {
    const { data } = await api.get('/security-events/', { params: { limit: 20 } })
    events.value = data
  } catch (error) {
    console.error('Error fetching events:', error)
    // Không báo lỗi nếu là 403 (Guard không có quyền xem)
    if (error.response?.status !== 403) {
      $q.notify({ type: 'negative', message: 'Không thể tải danh sách sự kiện' })
    }
  } finally {
    loading.value = false
  }
}

async function handleSaveEvent() {
  // Common validation
  if (!eventForm.value.title || eventForm.value.title.length < 5) {
    $q.notify({ type: 'warning', message: 'Tiêu đề phải có ít nhất 5 ký tự' })
    return
  }
  if (!eventForm.value.occurred_date || !eventForm.value.occurred_time) {
    $q.notify({ type: 'warning', message: 'Vui lòng chọn ngày và giờ xảy ra' })
    return
  }
  if (!eventForm.value.location) {
    $q.notify({ type: 'warning', message: 'Địa điểm là bắt buộc' })
    return
  }

  saving.value = true
  try {
    // Combine date and time
    const dateStr = eventForm.value.occurred_date.replace(/\//g, '-')
    const timeStr = eventForm.value.occurred_time
    const occurred_at = `${dateStr}T${timeStr}:00`

    const payload = {
      title: eventForm.value.title,
      occurred_at: occurred_at,
      location: eventForm.value.location,
      involved_parties: eventForm.value.involved_parties || '',
      detail: eventForm.value.detail || '',
      resolution: eventForm.value.resolution || ''
    }

    let eventId = editingId.value

    if (isEditing.value) {
      // UPDATE
      await api.put(`/security-events/${eventId}`, payload)
      $q.notify({ type: 'positive', message: 'Đã cập nhật sự kiện' })
    } else {
      // CREATE
      const { data } = await api.post('/security-events/', payload)
      eventId = data.id
      $q.notify({ type: 'positive', message: 'Đã tạo sự kiện thành công' })
    }

    // Upload images if any
    if (selectedImages.value.length > 0) {
      for (const file of selectedImages.value) {
        const formData = new FormData()
        formData.append('file', file)
        try {
          await api.post(`/security-events/${eventId}/upload-image`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          })
        } catch (imgError) {
          console.error('Error uploading image:', imgError)
        }
      }
    }

    showCreateDialog.value = false
    resetForm()
    
    // Reload danh sách
    await fetchEvents()
    
    // Nếu tạo mới và có ảnh -> mở detail
    if (!isEditing.value && selectedImages.value.length > 0) {
      try {
        const { data: eventWithImages } = await api.get(`/security-events/${eventId}`)
        selectedEvent.value = eventWithImages
        carouselSlide.value = 0
        showDetailDialog.value = true
      } catch (error) {
        console.error('Error fetching event detail:', error)
      }
    }
  } catch (error) {
    console.error('Error saving event:', error)
    $q.notify({ 
      type: 'negative', 
      message: error.response?.data?.detail || 'Không thể lưu sự kiện' 
    })
  } finally {
    saving.value = false
  }
}



function onImageRejected(rejectedEntries) {
  let msg = 'Một số file bị từ chối: '
  if (rejectedEntries.some(e => e.failedPropValidation === 'max-file-size')) {
    msg += 'Kích thước file vượt quá 10MB'
  } else if (rejectedEntries.some(e => e.failedPropValidation === 'max-files')) {
    msg += 'Đã đạt giới hạn 5 file'
  } else {
    msg += 'File không hợp lệ'
  }
  $q.notify({ type: 'warning', message: msg })
}

function openImageFullscreen(img) {
  // Mở ảnh fullscreen đơn giản hơn - dùng window.open hoặc q-dialog khác
  const imgUrl = getImageUrl(img.image_path)
  window.open(imgUrl, '_blank')
}

function onRowClick(evt, row) {
  // Prevent opening detail if clicking action buttons (handled by @click.stop in template, but safety check)
  if (evt.target.closest('.q-btn')) return
  
  selectedEvent.value = row
  carouselSlide.value = 0
  showDetailDialog.value = true
}

async function confirmDeleteEvent(event) {
  // Support both direct call (from table) and detail dialog (using selectedEvent)
  const targetEvent = event || selectedEvent.value
  if (!targetEvent) return
  
  $q.dialog({
    title: 'Xác nhận xóa',
    message: `Bạn có chắc chắn muốn xóa sự kiện "${targetEvent.title}"?`,
    cancel: true,
    persistent: true,
    color: 'negative'
  }).onOk(async () => {
    deleting.value = true
    try {
      await api.delete(`/security-events/${targetEvent.id}`)
      $q.notify({ type: 'positive', message: 'Đã xóa sự kiện' })
      showDetailDialog.value = false
      selectedEvent.value = null
      fetchEvents()
    } catch (error) {
      console.error('Error deleting event:', error)
      $q.notify({ 
        type: 'negative', 
        message: error.response?.data?.detail || 'Không thể xóa sự kiện' 
      })
    } finally {
      deleting.value = false
    }
  })
}

// Lifecycle
onMounted(() => {
  // Chỉ fetch nếu có quyền xem (admin/manager)
  if (['admin', 'manager'].includes(auth.user?.role)) {
    fetchEvents()
  }
})

</script>

<style scoped>
.security-event-table {
  min-height: 200px;
}
</style>
