<template>
  <div class="asset-control-dashboard">
    <q-card flat bordered class="q-mb-md">
      <q-card-section>
        <div class="text-h6">Kiểm soát Tài sản</div>
        <div class="text-caption text-grey-7">Theo dõi tỷ lệ hoàn trả và cảnh báo rủi ro</div>
      </q-card-section>
    </q-card>

    <!-- KPI Cards -->
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col-12 col-sm-6 col-md-3">
        <q-card flat class="kpi-card">
          <q-card-section>
            <div class="text-overline text-grey-7">Đang ra ngoài</div>
            <div class="text-h4 text-warning">{{ control.total_assets_out }}</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-sm-6 col-md-3">
        <q-card flat class="kpi-card">
          <q-card-section>
            <div class="text-overline text-grey-7">Đã hoàn trả</div>
            <div class="text-h4 text-positive">{{ control.total_assets_returned }}</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-sm-6 col-md-3">
        <q-card flat class="kpi-card" :class="returnRateClass">
          <q-card-section>
            <div class="text-overline text-grey-7">Tỷ lệ hoàn trả</div>
            <div class="text-h4">{{ control.return_rate_percentage }}%</div>
            <q-linear-progress :value="control.return_rate_percentage / 100" :color="returnRateColor" class="q-mt-sm"/>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-sm-6 col-md-3">
        <q-card flat class="kpi-card bg-negative text-white">
          <q-card-section>
            <div class="text-overline">⚠️ Quá hạn</div>
            <div class="text-h4">{{ control.overdue_count }}</div>
            <div class="text-caption">Rủi ro cao: {{ control.high_risk_count }}</div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- CRITICAL: Overdue Assets Table -->
    <q-card flat bordered class="q-mb-md" v-if="control.overdue_count > 0">
      <q-card-section>
        <div class="row items-center">
          <q-icon name="warning" color="negative" size="24px" class="q-mr-sm"/>
          <div class="text-h6 text-negative">Cảnh báo Rủi ro - Tài sản Quá hạn</div>
          <q-space/>
          <q-btn flat dense icon="file_download" label="Export Excel" color="primary" @click="exportOverdueAssets"/>
        </div>
      </q-card-section>

      <q-separator/>

      <q-card-section class="q-pa-none">
        <q-table
          :rows="control.overdue_assets"
          :columns="overdueColumns"
          row-key="id"
          flat
          :pagination="{ rowsPerPage: 10 }"
          :rows-per-page-options="[10, 20, 50]"
        >
          <template v-slot:body-cell-risk_level="props">
            <q-td :props="props">
              <q-badge
                :color="getRiskColor(props.row.risk_level)"
                :label="getRiskLabel(props.row.risk_level)"
              />
            </q-td>
          </template>

          <template v-slot:body-cell-days_overdue="props">
            <q-td :props="props">
              <span class="text-negative text-bold">{{ props.row.days_overdue }} ngày</span>
            </q-td>
          </template>

          <template v-slot:body-cell-expected_return_date="props">
            <q-td :props="props">
              {{ formatDate(props.row.expected_return_date) }}
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>

    <!-- Empty State -->
    <q-card flat bordered v-else class="q-mb-md">
      <q-card-section class="text-center q-pa-lg">
        <q-icon name="check_circle" color="positive" size="64px"/>
        <div class="text-h6 text-positive q-mt-md">Tuyệt vời! Không có tài sản quá hạn</div>
        <div class="text-caption text-grey-7">Tất cả tài sản đều được hoàn trả đúng hạn</div>
      </q-card-section>
    </q-card>

    <!-- Loading -->
    <q-inner-loading :showing="loading">
      <q-spinner-gears size="50px" color="primary" />
    </q-inner-loading>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../../api'
import { useQuasar, exportFile } from 'quasar'

const $q = useQuasar()
const loading = ref(false)
const control = ref({
  total_assets_out: 0,
  total_assets_returned: 0,
  return_rate_percentage: 0,
  overdue_assets: [],
  overdue_count: 0,
  high_risk_count: 0
})

const overdueColumns = [
  { name: 'asset_description', label: 'Mô tả tài sản', field: 'asset_description', align: 'left', sortable: true },
  { name: 'full_name', label: 'Người mang ra', field: 'full_name', align: 'left', sortable: true },
  { name: 'employee_code', label: 'Mã NV', field: 'employee_code', align: 'left' },
  { name: 'department', label: 'Bộ phận', field: 'department', align: 'left' },
  { name: 'destination', label: 'Nơi đến', field: 'destination', align: 'left' },
  { name: 'expected_return_date', label: 'Ngày dự kiến về', field: 'expected_return_date', align: 'left', sortable: true },
  { name: 'days_overdue', label: 'Số ngày quá hạn', field: 'days_overdue', align: 'center', sortable: true },
  { name: 'risk_level', label: 'Mức độ rủi ro', field: 'risk_level', align: 'center', sortable: true }
]

const returnRateColor = computed(() => {
  const rate = control.value.return_rate_percentage
  if (rate >= 90) return 'positive'
  if (rate >= 70) return 'warning'
  return 'negative'
})

const returnRateClass = computed(() => {
  const rate = control.value.return_rate_percentage
  if (rate < 70) return 'border-negative'
  return ''
})

function getRiskColor(level) {
  const colors = {
    high: 'negative',
    medium: 'warning',
    low: 'info'
  }
  return colors[level] || 'grey'
}

function getRiskLabel(level) {
  const labels = {
    high: 'Cao',
    medium: 'Trung bình',
    low: 'Thấp'
  }
  return labels[level] || level
}

function formatDate(dateString) {
  if (!dateString) return ''
  try {
    const date = new Date(dateString)
    const day = String(date.getDate()).padStart(2, '0')
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const year = date.getFullYear()
    return `${day}/${month}/${year}`
  } catch {
    return dateString
  }
}

function exportOverdueAssets() {
  const headers = ['Mã tài sản', 'Mô tả', 'Người mang', 'Mã NV', 'Bộ phận', 'Ngày dự kiến về', 'Số ngày quá hạn', 'Rủi ro']
  const rows = control.value.overdue_assets.map(asset => [
    asset.id,
    asset.asset_description,
    asset.full_name,
    asset.employee_code,
    asset.department,
    formatDate(asset.expected_return_date),
    asset.days_overdue,
    getRiskLabel(asset.risk_level)
  ])

  const csv = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\r\n')

  const status = exportFile('tai-san-qua-han.csv', csv, 'text/csv')
  
  if (status) {
    $q.notify({
      type: 'positive',
      message: 'Đã export thành công'
    })
  }
}

async function fetchData() {
  loading.value = true
  try {
    const response = await api.get('/reports/asset-control')
    control.value = response.data
  } catch (error) {
    console.error('Error fetching asset control:', error)
    $q.notify({
      type: 'negative',
      message: 'Không thể tải dữ liệu kiểm soát tài sản',
      caption: error.response?.data?.detail || error.message
    })
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.kpi-card {
  border-left: 4px solid var(--q-primary);
  transition: all 0.3s ease;
}

.kpi-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.border-negative {
  border-left-color: var(--q-negative);
}
</style>
