<template>
  <div class="user-activity-table">
    <q-card flat bordered class="q-mb-md">
      <q-card-section>
        <div class="text-h6">Hoạt động Người dùng</div>
        <div class="text-caption text-grey-7">Thống kê hiệu suất nhân viên - {{ activity.date_range }}</div>
      </q-card-section>
    </q-card>

    <!-- Table -->
    <q-card flat bordered>
      <q-card-section>
        <q-table
          :rows="activity.users"
          :columns="columns"
          row-key="user_id"
          :pagination="tablePagination"
          :filter="filter"
          flat
        >
          <template v-slot:top-right>
            <q-input dense debounce="300" v-model="filter" placeholder="Tìm kiếm">
              <template v-slot:append>
                <q-icon name="search" />
              </template>
            </q-input>
          </template>

          <template v-slot:body-cell-performance_score="props">
            <q-td :props="props">
              <q-badge :color="getScoreColor(props.row.performance_score)" :label="props.row.performance_score"/>
            </q-td>
          </template>

          <template v-slot:body-cell-full_name="props">
            <q-td :props="props">
              <div class="text-bold">{{ props.row.full_name }}</div>
              <div class="text-caption text-grey-7">{{ props.row.department || 'N/A' }}</div>
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>

    <!-- Top Performers Chart -->
    <q-card flat bordered class="q-mt-md">
      <q-card-section>
        <div class="text-subtitle1">Top 10 nhân viên</div>
        <apexchart v-if="chartOptions" type="bar" height="400" :options="chartOptions" :series="chartSeries"></apexchart>
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
import { useQuasar } from 'quasar'

const $q = useQuasar()
const loading = ref(false)
const filter = ref('')
const activity = ref({
  users: [],
  date_range: 'All time'
})

const tablePagination = ref({
  rowsPerPage: 20,
  sortBy: 'performance_score',
  descending: true
})

const columns = [
  { name: 'full_name', label: 'Nhân viên', field: 'full_name', align: 'left', sortable: true },
  { name: 'guests_registered', label: 'Khách đăng ký', field: 'guests_registered', align: 'center', sortable: true },
  { name: 'assets_registered', label: 'Tài sản đăng ký', field: 'assets_registered', align: 'center', sortable: true },
  { name: 'performance_score', label: 'Điểm hiệu suất', field: 'performance_score', align: 'center', sortable: true }
]

const top10Users = computed(() => {
  return activity.value.users.slice(0, 10)
})

const chartSeries = computed(() => [{
  name: 'Tổng đăng ký',
  data: top10Users.value.map(u => u.performance_score)
}])

const chartOptions = computed(() => ({
  chart: {
    type: 'bar',
    height: 400
  },
  plotOptions: {
    bar: {
      horizontal: true,
      borderRadius: 4,
      dataLabels: {
        position: 'top'
      }
    }
  },
  dataLabels: {
    enabled: true,
    offsetX: 30,
    style: {
      fontSize: '12px',
      colors: ['#000']
    }
  },
  xaxis: {
    categories: top10Users.value.map(u => u.full_name),
    title: { text: 'Số lượng đăng ký' }
  },
  colors: ['#00897B'],
  fill: {
    type: 'gradient',
    gradient: {
      shade: 'light',
      type: 'horizontal',
      shadeIntensity: 0.5,
      inverseColors: false,
      opacityFrom: 0.85,
      opacityTo: 0.85
    }
  }
}))

function getScoreColor(score) {
  if (score >= 50) return 'positive'
  if (score >= 20) return 'info'
  if (score >= 10) return 'warning'
  return 'grey'
}

async function fetchData() {
  loading.value = true
  try {
    const response = await api.get('/reports/user-activity')
    activity.value = response.data
  } catch (error) {
    console.error('Error fetching user activity:', error)
    $q.notify({
      type: 'negative',
      message: 'Không thể tải dữ liệu hoạt động người dùng',
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
/* Custom styles if needed */
</style>
