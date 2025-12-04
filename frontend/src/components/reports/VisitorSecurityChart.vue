<template>
  <div class="visitor-security-chart">
    <q-card flat bordered class="q-mb-md">
      <q-card-section>
        <div class="text-h6">Chỉ số An ninh Khách</div>
        <div class="text-caption text-grey-7">Phân tích xu hướng khách đăng ký</div>
      </q-card-section>
    </q-card>

    <!-- KPI Cards -->
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col-12 col-sm-6 col-md-3">
        <q-card flat class="kpi-card">
          <q-card-section>
            <div class="text-overline text-grey-7">Tháng này</div>
            <div class="text-h4 text-primary">{{ stats.total_guests_current_month }}</div>
            <div class="text-caption">
              <q-badge :color="stats.growth_percentage >= 0 ? 'positive' : 'negative'" :label="`${stats.growth_percentage >= 0 ? '+' : ''}${stats.growth_percentage}%`"/>
              <span class="q-ml-xs text-grey-7">so với tháng trước</span>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-sm-6 col-md-3">
        <q-card flat class="kpi-card">
          <q-card-section>
            <div class="text-overline text-grey-7">Tháng trước</div>
            <div class="text-h4">{{ stats.total_guests_last_month }}</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-sm-6 col-md-3">
        <q-card flat class="kpi-card">
          <q-card-section>
            <div class="text-overline text-grey-7">Pending</div>
            <div class="text-h4 text-orange">{{ stats.status_breakdown.pending }}</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-sm-6 col-md-3">
        <q-card flat class="kpi-card">
          <q-card-section>
            <div class="text-overline text-grey-7">Checked In</div>
            <div class="text-h4 text-positive">{{ stats.status_breakdown.checked_in }}</div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Charts -->
    <div class="row q-col-gutter-md">
      <!-- Monthly Trend -->
      <div class="col-12 col-md-8">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1">Xu hướng theo tháng (12 tháng)</div>
            <apexchart v-if="chartOptionsMonthly" type="area" height="350" :options="chartOptionsMonthly" :series="chartSeriesMonthly"></apexchart>
          </q-card-section>
        </q-card>
      </div>

      <!-- Status Breakdown -->
      <div class="col-12 col-md-4">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1">Phân bố trạng thái</div>
            <apexchart v-if="chartOptionsDonut" type="donut" height="350" :options="chartOptionsDonut" :series="chartSeriesDonut"></apexchart>
          </q-card-section>
        </q-card>
      </div>

      <!-- Top Suppliers -->
      <div class="col-12">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1">Top 5 Nhà cung cấp</div>
            <apexchart v-if="chartOptionsBar" type="bar" height="300" :options="chartOptionsBar" :series="chartSeriesBar"></apexchart>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Loading -->
    <q-inner-loading :showing="loading">
      <q-spinner-gears size="50px" color="primary" />
    </q-inner-loading>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../../api'
import VueApexCharts from 'vue3-apexcharts'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const loading = ref(false)
const stats = ref({
  total_guests_current_month: 0,
  total_guests_last_month: 0,
  growth_percentage: 0,
  monthly_data: [],
  daily_trend: [],
  top_suppliers: [],
  status_breakdown: { pending: 0, checked_in: 0, checked_out: 0 }
})

// Monthly Chart
const chartSeriesMonthly = computed(() => [{
  name: 'Khách đăng ký',
  data: stats.value.monthly_data.map(d => d.count)
}])

const chartOptionsMonthly = computed(() => ({
  chart: {
    type: 'area',
    height: 350,
    zoom: { enabled: true },
    toolbar: { show: true }
  },
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 2 },
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.7,
      opacityTo: 0.3,
      stops: [0, 90, 100]
    }
  },
  xaxis: {
    categories: stats.value.monthly_data.map(d => d.month),
    title: { text: 'Tháng' }
  },
  yaxis: {
    title: { text: 'Số lượng khách' }
  },
  colors: ['#1976D2']
}))

// Donut Chart
const chartSeriesDonut = computed(() => [
  stats.value.status_breakdown.pending,
  stats.value.status_breakdown.checked_in,
  stats.value.status_breakdown.checked_out
])

const chartOptionsDonut = computed(() => ({
  chart: { type: 'donut' },
  labels: ['Chờ vào', 'Đã vào', 'Đã ra'],
  colors: ['#FF9800', '#4CAF50', '#2196F3'],
  legend: { position: 'bottom' },
  responsive: [{
    breakpoint: 480,
    options: {
      chart: { width: 300 },
      legend: { position: 'bottom' }
    }
  }]
}))

// Bar Chart
const chartSeriesBar = computed(() => [{
  name: 'Số khách',
  data: stats.value.top_suppliers.map(s => s.count)
}])

const chartOptionsBar = computed(() => ({
  chart: {
    type: 'bar',
    height: 300
  },
  plotOptions: {
    bar: {
      horizontal: true,
      borderRadius: 4
    }
  },
  dataLabels: { enabled: true },
  xaxis: {
    categories: stats.value.top_suppliers.map(s => s.supplier_name || 'N/A'),
    title: { text: 'Số lượng khách' }
  },
  colors: ['#9C27B0']
}))

async function fetchData() {
  loading.value = true
  try {
    const response = await api.get('/reports/visitor-security-index')
    stats.value = response.data
    console.log('[VisitorSecurityChart] Data loaded successfully:', stats.value)
  } catch (error) {
    console.error('[VisitorSecurityChart] Error details:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      url: error.config?.url
    })
    $q.notify({
      type: 'negative',
      message: 'Không thể tải dữ liệu báo cáo khách',
      caption: error.response?.data?.detail || error.message,
      timeout: 5000,
      actions: [{ label: 'Đóng', color: 'white' }]
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  background: white;
}

.kpi-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
}
</style>
