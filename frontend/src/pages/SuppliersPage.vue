<!-- File: security_mgmt_dev/frontend/src/pages/SuppliersPage.vue -->
<template>
  <q-page padding>
    <q-card>
      <q-card-section class="row items-center justify-between">
        <div class="text-subtitle1">Nhà cung cấp</div>
        <div class="row items-center q-gutter-sm">
          <q-btn label="Thêm" color="primary" @click="addSupplier"/>
          <q-btn 
            label="Chuẩn hóa tên NCC" 
            color="orange" 
            icon="sync" 
            @click="openNormalizationDialog"
            v-if="auth.user?.role === 'admin'"
          />
          <q-btn-dropdown color="secondary" label="Actions" v-if="auth.user?.role === 'admin'">
            <q-list>
              <q-item clickable v-close-popup @click="triggerImport"><q-item-section>Import Excel</q-item-section></q-item>
              <q-item clickable v-close-popup @click="exportSuppliers"><q-item-section>Export Excel</q-item-section></q-item>
            </q-list>
          </q-btn-dropdown>
          <q-btn color="red" label="Xóa dữ liệu" @click="clearData" v-if="auth.user?.role === 'admin'" />
          <input type="file" ref="fileInput" @change="handleImport" accept=".xlsx" hidden/>
        </div>
      </q-card-section>
      <q-separator/>
      
      <!-- STATS CARDS ROW - 2 COLUMNS -->
      <q-card-section class="q-pa-none">
        <div class="row q-col-gutter-md q-pa-md">
          <!-- LEFT: Activity Stats -->
          <div class="col-12 col-md-6">
            <div class="stats-card-wrapper">
              <q-card flat class="stats-card">
                <q-card-section>
                  <div class="row items-center justify-between q-mb-sm">
                    <div class="stats-title">
                      <q-icon name="bar_chart" size="24px" class="q-mr-sm" />
                      <span>Thống kê hoạt động</span>
                    </div>
                    <q-btn-group push>
                      <q-btn 
                        label="7 ngày" 
                        size="sm"
                        @click="setStatsPeriod(7)" 
                        :color="statsPeriod === 7 ? 'primary' : 'white'" 
                        :text-color="statsPeriod === 7 ? 'white' : 'black'"
                      />
                      <q-btn 
                        label="30 ngày" 
                        size="sm"
                        @click="setStatsPeriod(30)" 
                        :color="statsPeriod === 30 ? 'primary' : 'white'" 
                        :text-color="statsPeriod === 30 ? 'white' : 'black'"
                      />
                      <q-btn 
                        label="90 ngày" 
                        size="sm"
                        @click="setStatsPeriod(90)" 
                        :color="statsPeriod === 90 ? 'primary' : 'white'" 
                        :text-color="statsPeriod === 90 ? 'white' : 'black'"
                      />
                    </q-btn-group>
                  </div>
                </q-card-section>
                
                <q-separator />
                
                <q-card-section class="chart-section">
                  <div v-if="loadingStats" class="text-center q-py-xl">
                    <q-spinner-dots color="primary" size="40px" />
                    <div class="text-grey-6 q-mt-sm">Đang tải dữ liệu...</div>
                  </div>
                  <div v-else-if="statsData.labels.length === 0" class="text-center q-py-xl text-grey-6">
                    <q-icon name="info" size="48px" />
                    <div class="q-mt-sm">Không có dữ liệu trong khoảng thời gian này</div>
                  </div>
                  <BarChart 
                    v-else
                    :labels="statsData.labels" 
                    :series="statsData.series" 
                    title="Số khách"
                  />
                </q-card-section>
              </q-card>
            </div>
          </div>
          
          <!-- RIGHT: No-Show Stats -->
          <div class="col-12 col-md-6">
            <div class="stats-card-wrapper">
              <q-card flat class="stats-card no-show-card">
                <q-card-section>
                  <div class="row items-center justify-between q-mb-sm">
                    <div class="stats-title no-show-title">
                      <q-icon name="event_busy" size="24px" class="q-mr-sm" />
                      <span>Top NCC khách đăng ký nhưng không tới !</span>
                    </div>
                    <q-btn-group push>
                      <q-btn 
                        label="7 ngày" 
                        size="sm"
                        @click="setNoShowPeriod(7)" 
                        :color="noShowPeriod === 7 ? 'negative' : 'white'" 
                        :text-color="noShowPeriod === 7 ? 'white' : 'black'"
                      />
                      <q-btn 
                        label="30 ngày" 
                        size="sm"
                        @click="setNoShowPeriod(30)" 
                        :color="noShowPeriod === 30 ? 'negative' : 'white'" 
                        :text-color="noShowPeriod === 30 ? 'white' : 'black'"
                      />
                      <q-btn 
                        label="90 ngày" 
                        size="sm"
                        @click="setNoShowPeriod(90)" 
                        :color="noShowPeriod === 90 ? 'negative' : 'white'" 
                        :text-color="noShowPeriod === 90 ? 'white' : 'black'"
                      />
                    </q-btn-group>
                  </div>
                </q-card-section>
                
                <q-separator />
                
                <q-card-section class="q-pa-none">
                  <div v-if="loadingNoShow" class="text-center q-py-md">
                    <q-spinner-dots color="negative" size="40px" />
                    <div class="text-grey-6 q-mt-sm">Đang tải dữ liệu...</div>
                  </div>
                  <div v-else-if="noShowData.data.length === 0" class="text-center q-py-md text-grey-6">
                    <q-icon name="check_circle" size="48px" color="positive" />
                    <div class="q-mt-sm">Không có khách no-show trong khoảng thời gian này 🎉</div>
                  </div>
                  <q-table
                    v-else
                    :rows="noShowData.data"
                    :columns="noShowColumns"
                    row-key="supplier_name"
                    flat
                    dense
                    hide-pagination
                    :rows-per-page-options="[0]"
                  >
                    <template #body-cell-supplier_name="props">
                      <q-td :props="props">
                        <span 
                          class="text-primary cursor-pointer text-weight-medium"
                          @click="showNoShowDetails(props.row.supplier_name)"
                        >
                          {{ props.row.supplier_name }}
                          <q-icon name="arrow_forward" size="xs" />
                        </span>
                      </q-td>
                    </template>
                    <template #body-cell-no_show_count="props">
                      <q-td :props="props">
                        <q-badge color="negative" class="text-weight-bold">
                          {{ props.row.no_show_count }}
                        </q-badge>
                      </q-td>
                    </template>
                  </q-table>
                </q-card-section>
              </q-card>
            </div>
          </div>
        </div>
      </q-card-section>
      
      <q-separator/>
      <q-card-section>
        <q-table :rows="rows" :columns="columns" row-key="id" flat>
          <template #body-cell-actions="props">
            <q-td :props="props">
              <q-btn flat icon="edit" @click="editSupplier(props.row)"/>
              <q-btn flat icon="delete" color="negative" @click="delSupplier(props.row)"/>
              <q-btn flat icon="format_list_numbered" label="Biển số" @click="managePlates(props.row)"/>
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>

    <q-dialog v-model="dlgPlates">
      <q-card style="min-width:420px">
        <q-card-section><div class="text-subtitle1">Quản lý biển số — {{ activeSupplier?.name }}</div></q-card-section>
        <q-separator/>
        <q-card-section>
          <div class="row q-col-gutter-sm q-mb-sm">
            <div class="col"><q-input v-model="newPlate" label="Thêm biển số" dense outlined/></div>
            <div class="col-auto"><q-btn color="primary" label="Thêm" @click="addPlate"/></div>
          </div>
          <q-list bordered separator>
            <q-item v-for="p in plates" :key="p.id">
              <q-item-section>{{ p.plate }}</q-item-section>
              <q-item-section side>
                <q-btn flat icon="delete" color="negative" @click="delPlate(p)"/>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
        <q-separator/>
        <q-card-actions align="right"><q-btn flat label="Đóng" v-close-popup/></q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Normalization Dialog -->
    <q-dialog v-model="dlgNormalization" persistent>
      <q-card style="min-width: 800px; max-width: 90vw">
        <q-card-section class="row items-center">
          <div class="text-h6">Chuẩn hóa tên Nhà cung cấp</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>
        <q-separator />

        <q-card-section v-if="normalizationData" style="max-height: 60vh" class="scroll">
          <div v-if="normalizationData.total_groups === 0" class="text-center text-grey-6 q-pa-md">
            <q-icon name="check_circle" size="48px" color="positive" />
            <div class="text-subtitle1 q-mt-md">Không tìm thấy tên NCC trùng lặp</div>
            <div class="text-caption">Tất cả tên nhà cung cấp đã được chuẩn hóa</div>
          </div>

          <div v-else>
            <div class="text-subtitle2 q-mb-md">
              Tìm thấy <strong>{{ normalizationData.total_groups }}</strong> nhóm tên tương tự
            </div>

            <q-list class="q-gutter-sm">
              <q-expansion-item
                v-for="(group, idx) in normalizationData.groups"
                :key="idx"
                :label="`${group.suggested_name} (${group.total_records} bản ghi)`"
                :caption="`${group.variants.length} biến thể - Độ tương đồng: ${(group.similarity_score * 100).toFixed(0)}%`"
                expand-separator
                default-opened
                header-class="bg-orange-1"
              >
                <q-card flat bordered>
                  <q-card-section>
                    <!-- Bảng danh sách variants -->
                    <q-table
                      :rows="group.variants"
                      :columns="variantColumns"
                      row-key="name"
                      flat
                      dense
                      hide-pagination
                      :rows-per-page-options="[0]"
                    >
                      <template #body-cell-tables="props">
                        <q-td :props="props">
                          <q-chip 
                            v-for="table in props.row.tables" 
                            :key="table" 
                            dense 
                            size="sm"
                            :label="tableLabels[table] || table"
                          />
                        </q-td>
                      </template>
                    </q-table>

                    <!-- Chọn tên chuẩn -->
                    <div class="row items-center q-mt-md q-gutter-sm">
                      <div class="col-auto text-weight-medium">Tên chuẩn:</div>
                      <div class="col">
                        <q-select
                          v-model="groupSelections[idx]"
                          :options="group.variants.map(v => v.name)"
                          outlined
                          dense
                          emit-value
                          map-options
                        />
                      </div>
                      <div class="col-auto">
                        <q-checkbox 
                          v-model="groupEnabled[idx]" 
                          label="Áp dụng"
                          color="primary"
                        />
                      </div>
                      <div class="col-auto">
                        <q-btn 
                          color="orange" 
                          label="Chuẩn hóa ngay" 
                          icon="sync"
                          size="sm"
                          @click="executeGroupNormalization(idx)"
                          :disable="!groupEnabled[idx]"
                        />
                      </div>
                    </div>
                  </q-card-section>
                </q-card>
              </q-expansion-item>
            </q-list>
          </div>
        </q-card-section>

        <q-separator />
        <q-card-actions align="right" v-if="normalizationData && normalizationData.total_groups > 0">
          <q-btn flat label="Hủy" v-close-popup />
          <q-btn 
            label="Xác nhận tất cả" 
            color="primary" 
            @click="executeNormalization"
            :disable="!hasEnabledGroups"
          />
        </q-card-actions>
        <q-card-actions align="right" v-else>
          <q-btn flat label="Đóng" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- NO-SHOW DETAILS DIALOG -->
    <q-dialog v-model="dlgNoShowDetails">
      <q-card style="min-width: 900px; max-width: 95vw">
        <q-card-section class="bg-negative text-white">
          <div class="text-h6">Chi tiết khách không tới - {{ selectedSupplierNoShow }}</div>
        </q-card-section>
        
        <q-separator />
        
        <q-card-section>
          <div v-if="loadingNoShowDetails" class="text-center q-py-md">
            <q-spinner-dots color="negative" size="40px" />
            <div class="text-grey-6 q-mt-sm">Đang tải...</div>
          </div>
          <q-table
            v-else
            :rows="noShowDetailsData"
            :columns="noShowDetailsColumns"
            row-key="guest_name"
            flat
            dense
            hide-pagination
            :rows-per-page-options="[0]"
          >
            <template #body-cell-registered_at="props">
              <q-td :props="props">
                {{ new Date(props.row.registered_at).toLocaleString('vi-VN') }}
              </q-td>
            </template>
            <template #body-cell-visit_date="props">
              <q-td :props="props">
                {{ new Date(props.row.visit_date).toLocaleDateString('vi-VN') }}
              </q-td>
            </template>
            <template #body-cell-no_show_count="props">
              <q-td :props="props">
                <q-badge :color="props.row.no_show_count > 2 ? 'negative' : 'warning'" class="text-weight-bold">
                  {{ props.row.no_show_count }} lần
                </q-badge>
              </q-td>
            </template>
          </q-table>
          <div v-if="!loadingNoShowDetails && noShowDetailsData.length === 0" class="text-center text-grey-6 q-pa-md">
            Không có dữ liệu
          </div>
        </q-card-section>
        
        <q-separator />
        
        <q-card-actions align="right">
          <q-btn flat label="Đóng" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '../api'
import { useQuasar } from 'quasar'
import { useAuthStore } from '../stores/auth'
import BarChart from '../components/charts/BarChart.vue'

const rows = ref([])
const $q = useQuasar()
const auth = useAuthStore()
const fileInput = ref(null)

const columns = [
  { name: 'name', label: 'Tên NCC', field: 'name', align: 'left' },
  { name: 'actions', label: '', field: 'actions', align: 'right' }
]

const dlgPlates = ref(false)
const activeSupplier = ref(null)
const plates = ref([])
const newPlate = ref('')

// Stats state
const statsData = ref({ labels: [], series: [], total_suppliers: 0 })
const statsPeriod = ref(30)
const loadingStats = ref(false)

// No-show stats state
const noShowData = ref({ data: [], total: 0 })
const noShowPeriod = ref(30)
const loadingNoShow = ref(false)

const noShowColumns = [
  { name: 'supplier_name', label: 'Nhà cung cấp', field: 'supplier_name', align: 'left', sortable: true },
  { name: 'no_show_count', label: 'Số khách No-show', field: 'no_show_count', align: 'center', sortable: true }
]

// No-show details dialog state
const dlgNoShowDetails = ref(false)
const selectedSupplierNoShow = ref('')
const noShowDetailsData = ref([])
const loadingNoShowDetails = ref(false)

const noShowDetailsColumns = [
  { name: 'guest_name', label: 'Tên khách', field: 'guest_name', align: 'left' },
  { name: 'registered_by', label: 'Họ tên nhân viên', field: 'registered_by', align: 'left' },
  { name: 'registered_at', label: 'Ngày đăng ký', field: 'registered_at', align: 'left' },
  { name: 'visit_date', label: 'Ngày hẹn', field: 'visit_date', align: 'left' },
  { name: 'no_show_count', label: 'Số lần nhỡ hẹn', field: 'no_show_count', align: 'center' }
]

// Normalization state
const dlgNormalization = ref(false)
const normalizationData = ref(null)
const groupSelections = ref({}) // {index: selected_name}
const groupEnabled = ref({}) // {index: boolean}

const variantColumns = [
  { name: 'name', label: 'Tên', field: 'name', align: 'left' },
  { name: 'count', label: 'Số lượng', field: 'count', align: 'center' },
  { name: 'tables', label: 'Bảng dữ liệu', field: 'tables', align: 'left' }
]

const tableLabels = {
  'guests': 'Khách',
  'long_term_guests': 'Khách dài hạn',
  'purchasing_log': 'Mua hàng'
}

const hasEnabledGroups = computed(() => {
  return Object.values(groupEnabled.value).some(v => v === true)
})

async function load () {
  const res = await api.get('/suppliers')
  rows.value = res.data
}

// ========== STATS FUNCTIONS ==========
function calculateDateRange(days) {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - days)
  
  return {
    start: start.toISOString(),
    end: end.toISOString()
  }
}

async function loadStats() {
  loadingStats.value = true
  try {
    const { start, end } = calculateDateRange(statsPeriod.value)
    const res = await api.get('/suppliers/stats/activity', {
      params: { start_date: start, end_date: end }
    })
    statsData.value = res.data
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Không thể tải thống kê: ' + (error.response?.data?.detail || error.message)
    })
  } finally {
    loadingStats.value = false
  }
}

function setStatsPeriod(days) {
  statsPeriod.value = days
  loadStats()
}

// ========== NO-SHOW STATS FUNCTIONS ==========
async function loadNoShow() {
  loadingNoShow.value = true
  try {
    const { start, end } = calculateDateRange(noShowPeriod.value)
    const res = await api.get('/suppliers/stats/no-show', {
      params: { start_date: start, end_date: end }
    })
    noShowData.value = res.data
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Không thể tải thống kê no-show: ' + (error.response?.data?.detail || error.message)
    })
  } finally {
    loadingNoShow.value = false
  }
}

function setNoShowPeriod(days) {
  noShowPeriod.value = days
  loadNoShow()
}

async function showNoShowDetails(supplierName) {
  selectedSupplierNoShow.value = supplierName
  dlgNoShowDetails.value = true
  loadingNoShowDetails.value = true
  
  try {
    const { start, end } = calculateDateRange(noShowPeriod.value)
    const res = await api.get(`/suppliers/stats/no-show/${encodeURIComponent(supplierName)}/details`, {
      params: { start_date: start, end_date: end }
    })
    noShowDetailsData.value = res.data.guests || []
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Không thể tải chi tiết: ' + (error.response?.data?.detail || error.message)
    })
  } finally {
    loadingNoShowDetails.value = false
  }
}

async function addSupplier () {
  const name = prompt('Tên nhà cung cấp')
  if (name) { await api.post('/suppliers', { name }); load() }
}

async function editSupplier (row) {
  const name = prompt('Sửa tên nhà cung cấp', row.name)
  if (name) { await api.put(`/suppliers/${row.id}`, { name }); load() }
}

async function delSupplier (row) {
  if (confirm('Xóa nhà cung cấp này?')) { await api.delete(`/suppliers/${row.id}`); load() }
}

async function managePlates (row) {
  activeSupplier.value = row
  const res = await api.get(`/suppliers/${row.id}/plates`)
  plates.value = res.data; newPlate.value = ''; dlgPlates.value = true
}

async function addPlate () {
  if (!newPlate.value) return
  await api.post(`/suppliers/${activeSupplier.value.id}/plates`, { plate: newPlate.value.toUpperCase() })
  const res = await api.get(`/suppliers/${activeSupplier.value.id}/plates`)
  plates.value = res.data; newPlate.value = ''
}

async function delPlate (p) {
  await api.delete(`/suppliers/${activeSupplier.value.id}/plates/${p.id}`)
  const res = await api.get(`/suppliers/${activeSupplier.value.id}/plates`)
  plates.value = res.data
}

function triggerImport() { fileInput.value.click() }

async function handleImport(event) {
  const file = event.target.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append('file', file);
  try {
    $q.loading.show({ message: 'Đang xử lý file...' });
    await api.post('/suppliers/import/xlsx', formData);
    $q.notify({ type: 'positive', message: 'Import thành công!' });
    load();
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Import thất bại.' });
  } finally {
    $q.loading.hide();
    event.target.value = '';
  }
}

async function exportSuppliers() {
  try {
    const response = await api.get('/suppliers/export/xlsx', { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `suppliers_${new Date().toISOString().split('T')[0]}.xlsx`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Export thất bại.' });
  }
}

function clearData() {
  $q.dialog({
    title: 'Xác nhận xóa',
    message: 'Hành động này sẽ xóa tất cả nhà cung cấp và biển số liên quan. Vui lòng nhập mật khẩu để xác nhận:',
    prompt: { model: '', type: 'password' },
    cancel: true,
    persistent: true
  }).onOk(async (password) => {
    if (password === 'Kienhp@@123') {
      try {
        await api.post('/suppliers/clear');
        $q.notify({ type: 'positive', message: 'Đã xóa dữ liệu nhà cung cấp.' });
        load();
      } catch (error) {
        $q.notify({ type: 'negative', message: 'Xóa dữ liệu thất bại.' });
      }
    } else {
      $q.notify({ type: 'negative', message: 'Sai mật khẩu.' });
    }
  });
}

// Normalization functions
async function openNormalizationDialog() {
  try {
    $q.loading.show({ message: 'Đang phân tích dữ liệu...' })
    const res = await api.get('/suppliers/normalization/analyze')
    normalizationData.value = res.data
    
    // Initialize selections and enabled state
    groupSelections.value = {}
    groupEnabled.value = {}
    
    if (res.data.groups) {
      res.data.groups.forEach((group, idx) => {
        groupSelections.value[idx] = group.suggested_name
        groupEnabled.value[idx] = true
      })
    }
    
    dlgNormalization.value = true
  } catch (error) {
    $q.notify({ 
      type: 'negative', 
      message: 'Không thể phân tích dữ liệu: ' + (error.response?.data?.detail || error.message)
    })
  } finally {
    $q.loading.hide()
  }
}

// Execute normalization for a single group
async function executeGroupNormalization(groupIndex) {
  try {
    const group = normalizationData.value.groups[groupIndex]
    const targetName = groupSelections.value[groupIndex]
    
    // Build mappings for this group only
    const mappings = {}
    group.variants.forEach(variant => {
      if (variant.name !== targetName) {
        mappings[variant.name] = targetName
      }
    })
    
    if (Object.keys(mappings).length === 0) {
      $q.notify({ type: 'warning', message: 'Không có thay đổi nào cho nhóm này' })
      return
    }
    
    // Preview first
    $q.loading.show({ message: 'Đang tính toán...' })
    const previewRes = await api.post('/suppliers/normalization/preview', { mappings })
    $q.loading.hide()
    
    const preview = previewRes.data
    
    // Confirm with user
    $q.dialog({
      title: `Chuẩn hóa nhóm: ${targetName}`,
      message: `
        Các tên sẽ được đổi thành "${targetName}":
        ${Object.keys(mappings).map(old => `  • "${old}"`).join('\n')}
        
        Số bản ghi sẽ được cập nhật:
        • Khách: ${preview.guests}
        • Khách dài hạn: ${preview.long_term_guests}
        • Mua hàng: ${preview.purchasing_log}
        ───────────────────
        Tổng cộng: ${preview.total} bản ghi
        
        Bạn có chắc chắn muốn tiếp tục?
      `,
      cancel: true,
      persistent: true,
      html: true
    }).onOk(async () => {
      try {
        $q.loading.show({ message: 'Đang chuẩn hóa dữ liệu...' })
        const result = await api.post('/suppliers/normalization/execute', { mappings })
        
        if (result.data.success) {
          $q.notify({ 
            type: 'positive', 
            message: `Chuẩn hóa thành công nhóm "${targetName}"! Đã cập nhật ${preview.total} bản ghi.`
          })
          
          // Disable this group after successful normalization
          groupEnabled.value[groupIndex] = false
          
          // Reload analysis to show updated data
          await openNormalizationDialog()
        } else {
          throw new Error(result.data.errors.join(', '))
        }
      } catch (error) {
        $q.notify({ 
          type: 'negative', 
          message: 'Chuẩn hóa thất bại: ' + (error.response?.data?.detail || error.message)
        })
      } finally {
        $q.loading.hide()
      }
    })
  } catch (error) {
    $q.notify({ 
      type: 'negative', 
      message: 'Lỗi: ' + (error.response?.data?.detail || error.message)
    })
    $q.loading.hide()
  }
}

async function executeNormalization() {
  try {
    // Build mappings from enabled groups
    const mappings = {}
    
    normalizationData.value.groups.forEach((group, idx) => {
      if (!groupEnabled.value[idx]) return
      
      const targetName = groupSelections.value[idx]
      group.variants.forEach(variant => {
        if (variant.name !== targetName) {
          mappings[variant.name] = targetName
        }
      })
    })
    
    if (Object.keys(mappings).length === 0) {
      $q.notify({ type: 'warning', message: 'Không có thay đổi nào để thực hiện' })
      return
    }
    
    // Preview first
    $q.loading.show({ message: 'Đang tính toán...' })
    const previewRes = await api.post('/suppliers/normalization/preview', { mappings })
    $q.loading.hide()
    
    const preview = previewRes.data
    
    // Confirm with user
    $q.dialog({
      title: 'Xác nhận chuẩn hóa',
      message: `
        Số bản ghi sẽ được cập nhật:
        • Khách: ${preview.guests}
        • Khách dài hạn: ${preview.long_term_guests}
        • Mua hàng: ${preview.purchasing_log}
        ───────────────────
        Tổng cộng: ${preview.total} bản ghi
        
        Bạn có chắc chắn muốn tiếp tục?
      `,
      cancel: true,
      persistent: true,
      html: true
    }).onOk(async () => {
      try {
        $q.loading.show({ message: 'Đang chuẩn hóa dữ liệu...' })
        const result = await api.post('/suppliers/normalization/execute', { mappings })
        
        if (result.data.success) {
          $q.notify({ 
            type: 'positive', 
            message: `Chuẩn hóa thành công! Đã cập nhật ${preview.total} bản ghi.`
          })
          dlgNormalization.value = false
          load()
        } else {
          throw new Error(result.data.errors.join(', '))
        }
      } catch (error) {
        $q.notify({ 
          type: 'negative', 
          message: 'Chuẩn hóa thất bại: ' + (error.response?.data?.detail || error.message)
        })
      } finally {
        $q.loading.hide()
      }
    })
  } catch (error) {
    $q.notify({ 
      type: 'negative', 
      message: 'Lỗi: ' + (error.response?.data?.detail || error.message)
    })
    $q.loading.hide()
  }
}

load()
loadStats()
loadNoShow()
</script>

<style scoped>
/* Stats Card Wrapper */
.stats-card-wrapper {
  padding: 16px;
  background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
}

/* Glass Morphism Card */
.stats-card {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.9) 0%, 
    rgba(255, 255, 255, 0.7) 100%);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 
    0 8px 32px rgba(31, 38, 135, 0.15),
    0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.stats-card:hover {
  transform: translateY(-4px);
  box-shadow: 
    0 16px 48px rgba(31, 38, 135, 0.2),
    0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
}

/* Stats Title */
.stats-title {
  font-size: 1.25rem;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  display: flex;
  align-items: center;
}

/* Chart Section */
.chart-section {
  min-height: 360px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 8px;
}

/* No-show Card Specific Styles */
.no-show-card {
  background: linear-gradient(135deg, 
    rgba(255, 240, 240, 0.9) 0%, 
    rgba(255, 235, 235, 0.7) 100%);
  border: 1px solid rgba(255, 0, 0, 0.1);
}

.no-show-card:hover {
  border-color: rgba(255, 0, 0, 0.2);
}

.no-show-title {
  background: linear-gradient(135deg, #f44336 0%, #e91e63 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Responsive adjustments */
@media (max-width: 600px) {
  .stats-card-wrapper {
    padding: 8px;
  }
  
  .stats-title {
    font-size: 1rem;
  }
  
  .chart-section {
    min-height: 280px;
  }
}
</style>
