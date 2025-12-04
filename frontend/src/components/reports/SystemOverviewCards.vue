<template>
  <div class="system-overview-cards">
    <q-card flat bordered class="q-mb-md">
      <q-card-section>
        <div class="text-h6">Tổng quan Hệ thống</div>
        <div class="text-caption text-grey-7">Các chỉ số tổng hợp và hiệu suất</div>
      </q-card-section>
    </q-card>

    <!-- KPI Cards Grid -->
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col-12 col-sm-6 col-md-3">
        <q-card flat class="overview-card bg-gradient-1">
          <q-card-section class="text-white">
            <q-icon name="group" size="48px" class="q-mb-sm"/>
            <div class="text-overline">Tổng người dùng</div>
            <div class="text-h3">{{ overview.total_users }}</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-sm-6 col-md-3">
        <q-card flat class="overview-card bg-gradient-2">
          <q-card-section class="text-white">
            <q-icon name="people" size="48px" class="q-mb-sm"/>
            <div class="text-overline">Tổng khách</div>
            <div class="text-h3">{{ overview.total_guests_all_time }}</div>
            <div class="text-caption">Hôm nay: {{ overview.active_guests_today }}</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-sm-6 col-md-3">
        <q-card flat class="overview-card bg-gradient-3">
          <q-card-section class="text-white">
            <q-icon name="inventory" size="48px" class="q-mb-sm"/>
            <div class="text-overline">Tổng tài sản</div>
            <div class="text-h3">{{ overview.total_assets_all_time }}</div>
            <div class="text-caption">Đang ra: {{ overview.active_assets_today }}</div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-sm-6 col-md-3">
        <q-card flat class="overview-card bg-gradient-4">
          <q-card-section class="text-white">
            <q-icon name="speed" size="48px" class="q-mb-sm"/>
            <div class="text-overline">Thời gian xử lý TB</div>
            <div class="text-h3">{{ overview.avg_processing_time_minutes?.toFixed(1) || 'N/A' }}</div>
            <div class="text-caption">phút</div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="row q-col-gutter-md">
      <div class="col-12">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1">Hoạt động 7 ngày gần nhất</div>
            <apexchart v-if="chartOptions" type="line" height="300" :options="chartOptions" :series="chartSeries"></apexchart>
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
import { useQuasar } from 'quasar'

const $q = useQuasar()
const loading = ref(false)
const overview = ref({
  total_users: 0,
  total_guests_all_time: 0,
  total_assets_all_time: 0,
  active_guests_today: 0,
  active_assets_today: 0,
  avg_processing_time_minutes: null
})

// Sample data for 7-day activity (would come from a separate endpoint in real implementation)
const chartSeries = ref([
  {
    name: 'Khách',
    data: [30, 40, 35, 50, 49, 60, 70]
  },
  {
    name: 'Tài sản',
    data: [10, 20, 15, 25, 20, 30, 35]
  }
])

const chartOptions = ref({
  chart: {
    type: 'line',
    height: 300,
    zoom: { enabled: true },
    toolbar: { show: true }
  },
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 3 },
  xaxis: {
    categories: getLast7Days(),
    title: { text: 'Ngày' }
  },
  yaxis: {
    title: { text: 'Số lượng' }
  },
  colors: ['#2196F3', '#FF9800'],
  legend: {
    position: 'top'
  }
})

function getLast7Days() {
  const days = []
  const today = new Date()
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    days.push(d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' }))
  }
  return days
}

async function fetchData() {
  loading.value = true
  try {
    const response = await api.get('/reports/system-overview')
    overview.value = response.data
  } catch (error) {
    console.error('Error fetching system overview:', error)
    $q.notify({
      type: 'negative',
      message: 'Không thể tải dữ liệu tổng quan',
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
.overview-card {
  transition: all 0.3s ease;
  border-radius: 12px;
  overflow: hidden;
}

.overview-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}

.bg-gradient-1 {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.bg-gradient-2 {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.bg-gradient-3 {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.bg-gradient-4 {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}
</style>
