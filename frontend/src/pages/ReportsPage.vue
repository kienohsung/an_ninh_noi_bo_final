<template>
  <q-page padding>
    <!-- Header -->
    <div class="row items-center q-mb-md">
      <q-icon name="summarize" size="32px" color="primary" class="q-mr-sm"/>
      <div class="text-h5">Xuất Báo cáo</div>
    </div>

    <!-- Báo cáo Khách Export Feature -->
    <q-expansion-item
      ref="guestReportExpansion"
      v-model="expandedGuestReport"
      @before-show="onExpandGuestReport"
      class="q-mt-md"
      icon="description"
      label="Báo cáo Khách"
      header-class="bg-grey-2 text-weight-medium"
      dense
    >
      <q-card flat bordered>
        <q-card-section>
          <div class="text-body2 text-grey-8 q-mb-md">
            Xuất danh sách khách ra/vào công ty theo thời gian, nhà cung cấp, hoặc người đăng ký.
          </div>
          <q-btn 
            color="secondary" 
            icon="download" 
            label="Xuất Báo cáo Khách" 
            @click="openExportDialog"
            unelevated
          />
        </q-card-section>
      </q-card>
    </q-expansion-item>

    <!-- Báo cáo Tài sản Export Feature -->
    <q-expansion-item
      ref="assetReportExpansion"
      v-model="expandedAssetReport"
      @before-show="onExpandAssetReport"
      class="q-mt-sm"
      icon="inventory"
      label="Báo cáo Tài sản"
      header-class="bg-grey-2 text-weight-medium"
      dense
    >
      <q-card flat bordered>
        <q-card-section>
          <div class="text-body2 text-grey-8 q-mb-md">
            Xuất lịch sử tài sản ra/vào công ty theo thời gian, trạng thái, hoặc bộ phận.
          </div>
          <q-btn 
            color="secondary" 
            icon="download" 
            label="Xuất Báo cáo Tài sản" 
            @click="openAssetExportDialog"
            unelevated
          />
        </q-card-section>
      </q-card>
    </q-expansion-item>

    <!-- Sự kiện An ninh -->
    <q-expansion-item
      ref="securityEventExpansion"
      v-model="expandedSecurityEvent"
      class="q-mt-sm"
      icon="report_problem"
      label="Sự kiện An ninh"
      header-class="bg-orange-2 text-weight-medium"
      dense
    >
      <q-card flat bordered>
        <q-card-section>
          <SecurityEventTable />
        </q-card-section>
      </q-card>
    </q-expansion-item>

    <!-- Guest Export Dialog -->
    <q-dialog v-model="showExportDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Xuất Báo cáo Khách</div>
        </q-card-section>
        <q-separator />
        <q-card-section class="q-gutter-md">
          <!-- Quick Date Range Buttons -->
          <div class="row items-center q-mb-sm">
            <div class="text-caption text-grey-7 q-mr-sm">Khoảng thời gian:</div>
            <q-btn-group push>
              <q-btn 
                label="Hôm nay" 
                @click="setExportRange('today')" 
                :color="exportFilters.range === 'today' ? 'primary' : 'white'" 
                :text-color="exportFilters.range === 'today' ? 'white' : 'black'"
                size="sm"
              />
              <q-btn 
                label="3 ngày" 
                @click="setExportRange('last3days')" 
                :color="exportFilters.range === 'last3days' ? 'primary' : 'white'" 
                :text-color="exportFilters.range === 'last3days' ? 'white' : 'black'"
                size="sm"
              />
              <q-btn 
                label="1 tuần" 
                @click="setExportRange('last7days')" 
                :color="exportFilters.range === 'last7days' ? 'primary' : 'white'" 
                :text-color="exportFilters.range === 'last7days' ? 'white' : 'black'"
                size="sm"
              />
              <q-btn 
                label="1 tháng" 
                @click="setExportRange('last1month')" 
                :color="exportFilters.range === 'last1month' ? 'primary' : 'white'" 
                :text-color="exportFilters.range === 'last1month' ? 'white' : 'black'"
                size="sm"
              />
            </q-btn-group>
          </div>

          <!-- Status Filter Buttons -->
          <div class="row items-center q-mb-md">
            <div class="text-caption text-grey-7 q-mr-sm">Trạng thái:</div>
            <q-btn-group push>
              <q-btn 
                label="Tất cả" 
                @click="exportFilters.status = null" 
                :color="exportFilters.status === null ? 'primary' : 'white'" 
                :text-color="exportFilters.status === null ? 'white' : 'black'"
                size="sm"
              />
              <q-btn 
                label="Đã vào" 
                @click="exportFilters.status = 'checked_in'" 
                :color="exportFilters.status === 'checked_in' ? 'positive' : 'white'" 
                :text-color="exportFilters.status === 'checked_in' ? 'white' : 'black'"
                size="sm"
              />
              <q-btn 
                label="Chờ vào" 
                @click="exportFilters.status = 'pending'" 
                :color="exportFilters.status === 'pending' ? 'orange' : 'white'" 
                :text-color="exportFilters.status === 'pending' ? 'white' : 'black'"
                size="sm"
              />
              <q-btn 
                label="Đã ra" 
                @click="exportFilters.status = 'checked_out'" 
                :color="exportFilters.status === 'checked_out' ? 'grey' : 'white'" 
                :text-color="exportFilters.status === 'checked_out' ? 'white' : 'black'"
                size="sm"
              />
            </q-btn-group>
          </div>

          <div class="row q-col-gutter-sm">
            <div class="col-12 col-sm-6">
              <q-input dense outlined v-model="exportFilters.start_date" mask="date" label="Từ ngày">
                <template v-slot:append>
                  <q-icon name="event" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date v-model="exportFilters.start_date" @update:model-value="exportFilters.range = ''">
                        <div class="row items-center justify-end"><q-btn v-close-popup label="Đóng" color="primary" flat /></div>
                      </q-date>
                    </q-popup-proxy>
                  </q-icon>
                </template>
              </q-input>
            </div>
            <div class="col-12 col-sm-6">
              <q-input dense outlined v-model="exportFilters.end_date" mask="date" label="Đến ngày">
                <template v-slot:append>
                  <q-icon name="event" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date v-model="exportFilters.end_date" @update:model-value="exportFilters.range = ''">
                        <div class="row items-center justify-end"><q-btn v-close-popup label="Đóng" color="primary" flat /></div>
                      </q-date>
                    </q-popup-proxy>
                  </q-icon>
                </template>
              </q-input>
            </div>
          </div>

          <q-select
            v-if="isAdmin || isManager"
            dense
            outlined
            v-model="exportFilters.registrant"
            :options="userOptions"
            option-label="full_name"
            option-value="id"
            label="Người đăng ký"
            clearable
            emit-value
            map-options
            use-input
            @filter="filterUsers"
          />

          <q-select
            dense
            outlined
            v-model="exportFilters.supplier_name"
            :options="filteredSupplierOptions"
            label="Nhà cung cấp"
            clearable
            use-input
            @filter="filterSuppliers"
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Hủy" color="primary" v-close-popup />
          <q-btn label="Export" color="secondary" @click="executeExport" :loading="isExporting" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Asset Export Dialog -->
    <q-dialog v-model="showAssetExportDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Xuất Báo cáo Tài sản</div>
        </q-card-section>
        <q-separator />
        <q-card-section class="q-gutter-md">
          <!-- Quick Date Range Buttons -->
          <div class="row items-center q-mb-sm">
            <div class="text-caption text-grey-7 q-mr-sm">Khoảng thời gian:</div>
            <q-btn-group push>
              <q-btn 
                label="Hôm nay" 
                @click="setAssetExportRange('today')" 
                :color="assetExportFilters.range === 'today' ? 'primary' : 'white'" 
                :text-color="assetExportFilters.range === 'today' ? 'white' : 'black'"
                size="sm"
              />
              <q-btn 
                label="3 ngày" 
                @click="setAssetExportRange('last3days')" 
                :color="assetExportFilters.range === 'last3days' ? 'primary' : 'white'" 
                :text-color="assetExportFilters.range === 'last3days' ? 'white' : 'black'"
                size="sm"
              />
              <q-btn 
                label="1 tuần" 
                @click="setAssetExportRange('last7days')" 
                :color="assetExportFilters.range === 'last7days' ? 'primary' : 'white'" 
                :text-color="assetExportFilters.range === 'last7days' ? 'white' : 'black'"
                size="sm"
              />
              <q-btn 
                label="1 tháng" 
                @click="setAssetExportRange('last1month')" 
                :color="assetExportFilters.range === 'last1month' ? 'primary' : 'white'" 
                :text-color="assetExportFilters.range === 'last1month' ? 'white' : 'black'"
                size="sm"
              />
            </q-btn-group>
          </div>

          <!-- Status Filter Buttons -->
          <div class="row items-center q-mb-md">
            <div class="text-caption text-grey-7 q-mr-sm">Trạng thái:</div>
            <q-btn-group push>
              <q-btn 
                label="Tất cả" 
                @click="assetExportFilters.status = null" 
                :color="assetExportFilters.status === null ? 'primary' : 'white'" 
                :text-color="assetExportFilters.status === null ? 'white' : 'black'"
                size="sm"
              />
              <q-btn 
                label="Chờ ra" 
                @click="assetExportFilters.status = 'pending_out'" 
                :color="assetExportFilters.status === 'pending_out' ? 'warning' : 'white'" 
                :text-color="assetExportFilters.status === 'pending_out' ? 'white' : 'black'"
                size="sm"
              />
              <q-btn 
                label="Đã ra" 
                @click="assetExportFilters.status = 'checked_out'" 
                :color="assetExportFilters.status === 'checked_out' ? 'info' : 'white'" 
                :text-color="assetExportFilters.status === 'checked_out' ? 'white' : 'black'"
                size="sm"
              />
              <q-btn 
                label="Đã hoàn trả" 
                @click="assetExportFilters.status = 'returned'" 
                :color="assetExportFilters.status === 'returned' ? 'positive' : 'white'" 
                :text-color="assetExportFilters.status === 'returned' ? 'white' : 'black'"
                size="sm"
              />
            </q-btn-group>
          </div>

          <div class="row q-col-gutter-sm">
            <div class="col-12 col-sm-6">
              <q-input dense outlined v-model="assetExportFilters.start_date" mask="date" label="Từ ngày">
                <template v-slot:append>
                  <q-icon name="event" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date v-model="assetExportFilters.start_date" @update:model-value="assetExportFilters.range = ''">
                        <div class="row items-center justify-end"><q-btn v-close-popup label="Đóng" color="primary" flat /></div>
                      </q-date>
                    </q-popup-proxy>
                  </q-icon>
                </template>
              </q-input>
            </div>
            <div class="col-12 col-sm-6">
              <q-input dense outlined v-model="assetExportFilters.end_date" mask="date" label="Đến ngày">
                <template v-slot:append>
                  <q-icon name="event" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date v-model="assetExportFilters.end_date" @update:model-value="assetExportFilters.range = ''">
                        <div class="row items-center justify-end"><q-btn v-close-popup label="Đóng" color="primary" flat /></div>
                      </q-date>
                    </q-popup-proxy>
                  </q-icon>
                </template>
              </q-input>
            </div>
          </div>

          <q-input
            dense
            outlined
            v-model="assetExportFilters.department"
            label="Bộ phận"
            clearable
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Hủy" color="primary" v-close-popup />
          <q-btn label="Export" color="secondary" @click="executeAssetExport" :loading="isAssetExporting" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { useQuasar, date } from 'quasar'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import SecurityEventTable from '../components/SecurityEventTable.vue'

const $q = useQuasar()
const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role === 'admin')
const isManager = computed(() => auth.user?.role === 'manager')

// UI State
const expandedGuestReport = ref(false)
const guestReportExpansion = ref(null)
const showExportDialog = ref(false)
const isExporting = ref(false)

// Asset Report UI State
const expandedAssetReport = ref(false)
const assetReportExpansion = ref(null)
const showAssetExportDialog = ref(false)
const isAssetExporting = ref(false)

// Security Event UI State
const expandedSecurityEvent = ref(false)
const securityEventExpansion = ref(null)

// Export filters
const exportFilters = ref({
  start_date: '',
  end_date: '',
  registrant: null,
  supplier_name: null,
  range: '',
  status: null  // null = all, 'checked_in' = đã vào, 'pending' = chờ vào
})

// Asset Export filters
const assetExportFilters = ref({
  start_date: '',
  end_date: '',
  status: null,  // null = all, 'pending_out', 'checked_out', 'returned'
  department: '',
  range: ''
})

// User options for registrant filter
const userOptions = ref([])
const allUsers = ref([])

// Supplier options
const allSuppliers = ref([])
const filteredSupplierOptions = ref([])

// Auto-scroll on expansion
function onExpandGuestReport() {
  nextTick(() => {
    if (guestReportExpansion.value?.$el) {
      guestReportExpansion.value.$el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  })
}

// Open export dialog
function openExportDialog() {
  // Load users if admin/manager and not loaded yet
  if ((isAdmin.value || isManager.value) && allUsers.value.length === 0) {
    loadUsers()
  }
  
  // Load suppliers if not loaded yet
  if (allSuppliers.value.length === 0) {
    loadSuppliers()
  }
  
  showExportDialog.value = true
}

// Load users for registrant filter
async function loadUsers() {
  try {
    const { data } = await api.get('/users/')
    allUsers.value = data
    userOptions.value = data
  } catch (e) {
    console.error("Failed to load users", e)
    $q.notify({ type: 'warning', message: 'Không thể tải danh sách người dùng' })
  }
}

// Filter users
function filterUsers(val, update) {
  if (val === '') {
    update(() => {
      userOptions.value = allUsers.value
    })
    return
  }

  update(() => {
    const needle = val.toLowerCase()
    userOptions.value = allUsers.value.filter(v => v.full_name.toLowerCase().indexOf(needle) > -1)
  })
}

// Load suppliers
async function loadSuppliers() {
  try {
    const res = await api.get('/guests/suggestions')
    allSuppliers.value = res.data.supplier_names || []
    filteredSupplierOptions.value = res.data.supplier_names || []
  } catch (error) {
    console.error("Could not load suppliers", error)
    $q.notify({ type: 'warning', message: 'Không thể tải danh sách nhà cung cấp' })
  }
}

// Filter suppliers
function filterSuppliers(val, update) {
  update(() => {
    const needle = val.toLowerCase()
    filteredSupplierOptions.value = allSuppliers.value.filter(v => v.toLowerCase().indexOf(needle) > -1)
  })
}

// Initialize filtered options
watch(allSuppliers, (newVal) => {
  filteredSupplierOptions.value = newVal
}, { immediate: true })

// Set quick date range for export
function setExportRange(period) {
  exportFilters.value.range = period
  const today = new Date()
  
  if (period === 'today') {
    exportFilters.value.start_date = date.formatDate(today, 'YYYY/MM/DD')
    exportFilters.value.end_date = date.formatDate(today, 'YYYY/MM/DD')
  } else if (period === 'last3days') {
    const startDate = date.subtractFromDate(today, { days: 2 })
    exportFilters.value.start_date = date.formatDate(startDate, 'YYYY/MM/DD')
    exportFilters.value.end_date = date.formatDate(today, 'YYYY/MM/DD')
  } else if (period === 'last7days') {
    const startDate = date.subtractFromDate(today, { days: 6 })
    exportFilters.value.start_date = date.formatDate(startDate, 'YYYY/MM/DD')
    exportFilters.value.end_date = date.formatDate(today, 'YYYY/MM/DD')
  } else if (period === 'last1month') {
    const startDate = date.subtractFromDate(today, { months: 1 })
    exportFilters.value.start_date = date.formatDate(startDate, 'YYYY/MM/DD')
    exportFilters.value.end_date = date.formatDate(today, 'YYYY/MM/DD')
  }
}

// Execute export
async function executeExport() {
  isExporting.value = true
  try {
    const params = {}
    if (exportFilters.value.start_date) params.start_date = exportFilters.value.start_date.replace(/\//g, '-')
    if (exportFilters.value.end_date) params.end_date = exportFilters.value.end_date.replace(/\//g, '-')
    if (exportFilters.value.registrant) params.registrant_id = exportFilters.value.registrant
    if (exportFilters.value.supplier_name) params.supplier_name = exportFilters.value.supplier_name
    if (exportFilters.value.status) params.status = exportFilters.value.status

    const response = await api.get('/guests/export/xlsx', {
      params,
      responseType: 'blob'
    })

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    const contentDisposition = response.headers['content-disposition']
    let fileName = 'bao_cao_khach.xlsx'
    if (contentDisposition) {
      const fileNameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
      if (fileNameMatch && fileNameMatch.length === 2) fileName = fileNameMatch[1]
    }
    link.setAttribute('download', fileName)
    document.body.appendChild(link)
    link.click()
    link.remove()
    
    showExportDialog.value = false
    $q.notify({ type: 'positive', message: 'Xuất báo cáo thành công!' })
  } catch (error) {
    console.error("Export failed", error)
    $q.notify({ type: 'negative', message: 'Xuất báo cáo thất bại. Vui lòng thử lại.' })
  } finally {
    isExporting.value = false
  }
}

// === ASSET REPORT FUNCTIONS ===

// Auto-scroll on asset expansion
function onExpandAssetReport() {
  nextTick(() => {
    if (assetReportExpansion.value?.$el) {
      assetReportExpansion.value.$el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  })
}

// Open asset export dialog
function openAssetExportDialog() {
  showAssetExportDialog.value = true
}

// Set quick date range for asset export
function setAssetExportRange(period) {
  assetExportFilters.value.range = period
  const today = new Date()
  
  if (period === 'today') {
    assetExportFilters.value.start_date = date.formatDate(today, 'YYYY/MM/DD')
    assetExportFilters.value.end_date = date.formatDate(today, 'YYYY/MM/DD')
  } else if (period === 'last3days') {
    const startDate = date.subtractFromDate(today, { days: 2 })
    assetExportFilters.value.start_date = date.formatDate(startDate, 'YYYY/MM/DD')
    assetExportFilters.value.end_date = date.formatDate(today, 'YYYY/MM/DD')
  } else if (period === 'last7days') {
    const startDate = date.subtractFromDate(today, { days: 6 })
    assetExportFilters.value.start_date = date.formatDate(startDate, 'YYYY/MM/DD')
    assetExportFilters.value.end_date = date.formatDate(today, 'YYYY/MM/DD')
  } else if (period === 'last1month') {
    const startDate = date.subtractFromDate(today, { months: 1 })
    assetExportFilters.value.start_date = date.formatDate(startDate, 'YYYY/MM/DD')
    assetExportFilters.value.end_date = date.formatDate(today, 'YYYY/MM/DD')
  }
}

// Execute asset export
async function executeAssetExport() {
  isAssetExporting.value = true
  try {
    const params = {}
    if (assetExportFilters.value.start_date) params.start_date = assetExportFilters.value.start_date.replace(/\//g, '-')
    if (assetExportFilters.value.end_date) params.end_date = assetExportFilters.value.end_date.replace(/\//g, '-')
    if (assetExportFilters.value.status) params.status = assetExportFilters.value.status
    if (assetExportFilters.value.department) params.department = assetExportFilters.value.department

    const response = await api.get('/assets/export/xlsx', {
      params,
      responseType: 'blob'
    })

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    const contentDisposition = response.headers['content-disposition']
    let fileName = 'bao_cao_tai_san.xlsx'
    if (contentDisposition) {
      const fileNameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
      if (fileNameMatch && fileNameMatch.length === 2) fileName = fileNameMatch[1]
    }
    link.setAttribute('download', fileName)
    document.body.appendChild(link)
    link.click()
    link.remove()
    
    showAssetExportDialog.value = false
    $q.notify({ type: 'positive', message: 'Xuất báo cáo thành công!' })
  } catch (error) {
    console.error("Asset export failed", error)
    $q.notify({ type: 'negative', message: 'Xuất báo cáo thất bại. Vui lòng thử lại.' })
  } finally {
    isAssetExporting.value = false
  }
}
</script>

<style scoped>
/* Add any custom styles here */
</style>
