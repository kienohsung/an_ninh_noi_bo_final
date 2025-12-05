<!-- File: security_mgmt_dev/frontend/src/pages/DashboardPage.vue -->
<template>
  <q-page padding>
    <!-- BỘ LỌC THỜI GIAN -->
    <q-card class="q-mb-md">
      <q-card-section>
        <div class="row items-center q-col-gutter-md">
          <div class="col-auto">
            <q-btn-group push>
              <q-btn label="1 tuần" @click="setRange('last7days')" :color="filters.range === 'last7days' ? 'primary' : 'white'" :text-color="filters.range === 'last7days' ? 'white' : 'black'"/>
              <q-btn label="1 tháng" @click="setRange('last1month')" :color="filters.range === 'last1month' ? 'primary' : 'white'" :text-color="filters.range === 'last1month' ? 'white' : 'black'"/>
              <q-btn label="3 tháng" @click="setRange('last3months')" :color="filters.range === 'last3months' ? 'primary' : 'white'" :text-color="filters.range === 'last3months' ? 'white' : 'black'"/>
              <q-btn label="Tất cả" @click="setRange('all')" :color="filters.range === 'all' ? 'primary' : 'white'" :text-color="filters.range === 'all' ? 'white' : 'black'"/>
            </q-btn-group>
          </div>
          <div class="col-12 col-sm-3">
            <q-input dense outlined v-model="filters.start" mask="date" label="Từ ngày">
              <template v-slot:append>
                <q-icon name="event" class="cursor-pointer">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <q-date v-model="filters.start" @update:model-value="filters.range = ''">
                      <div class="row items-center justify-end">
                        <q-btn v-close-popup label="Đóng" color="primary" flat />
                      </div>
                    </q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </div>
          <div class="col-12 col-sm-3">
             <q-input dense outlined v-model="filters.end" mask="date" label="Đến ngày">
              <template v-slot:append>
                <q-icon name="event" class="cursor-pointer">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <q-date v-model="filters.end" @update:model-value="filters.range = ''">
                      <div class="row items-center justify-end">
                        <q-btn v-close-popup label="Đóng" color="primary" flat />
                      </div>
                    </q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </div>
          <!-- Visual indicator for filter status -->
          <div class="col-auto">
            <q-spinner v-if="loading" color="primary" size="20px" />
            <q-icon v-else-if="isPending" name="schedule" color="orange" size="20px">
              <q-tooltip>Đang chờ input ổn định...</q-tooltip>
            </q-icon>
            <q-icon v-else name="check_circle" color="positive" size="20px">
              <q-tooltip>Dữ liệu đã tải xong</q-tooltip>
            </q-icon>
          </div>
        </div>
      </q-card-section>
    </q-card>

    <!-- === SECTION 2: KPI OVERVIEW CARDS (5 cards x 20%) === -->
    <DashboardSkeletonLoader v-if="loading" type="kpi-cards" :count="5" />
    <div v-else class="row q-col-gutter-sm q-mb-sm">
      <div class="col-6 col-sm-20pc">
        <DashboardKPICard
          label="Tổng Users"
          :value="systemOverview.total_users"
          icon="group"
          :gradient="1"
        />
      </div>
      <div class="col-6 col-sm-20pc">
        <DashboardKPICard
          :label="`Tổng Khách · Hôm nay: ${systemOverview.active_guests_today}`"
          :value="systemOverview.total_guests_all_time"
          icon="people"
          :gradient="2"
        />
      </div>
      <div class="col-6 col-sm-20pc">
        <DashboardKPICard
          :label="`Tổng Tài sản · Đang ra: ${systemOverview.active_assets_today}`"
          :value="systemOverview.total_assets_all_time"
          icon="inventory"
          :gradient="3"
        />
      </div>
      <div class="col-6 col-sm-20pc">
        <DashboardKPICard
          label="Đã hoàn trả"
          :value="assetControl.total_assets_returned"
          icon="check_circle"
          :gradient="4"
        />
      </div>
      <div class="col-6 col-sm-20pc">
        <DashboardKPICard
          :label="`⚠️ Quá hạn · Rủi ro cao: ${assetControl.high_risk_count}`"
          :value="assetControl.overdue_count"
          icon="warning"
          :gradient="1"
        />
      </div>
    </div>
    <!-- === END SECTION 2 === -->

    <!-- === SECTION 3: MAIN CHARTS (3 Charts Only) === -->
    <div class="row q-col-gutter-md">
      <!-- 1. Lượt khách vào theo ngày -->
      <div class="col-12 col-lg-4">
        <q-card>
          <q-card-section>
             <div class="text-subtitle1">Lượt khách vào theo ngày</div>
          </q-card-section>
          <q-separator />
          <q-card-section class="q-pa-sm">
            <DashboardSkeletonLoader v-if="loading" type="chart" height="220px" />
            <BarChart v-else :labels="guestsDaily.labels" :series="guestsDaily.series" title="Số khách" height="220"/>
          </q-card-section>
        </q-card>
      </div>
      
      <!-- 2. Tài sản ra/vào theo ngày -->
      <div class="col-12 col-lg-4">
        <q-card>
          <q-card-section>
            <div class="text-subtitle1">Tài sản ra/vào theo ngày</div>
          </q-card-section>
          <q-separator />
          <q-card-section class="q-pa-sm">
            <DashboardSkeletonLoader v-if="loading" type="chart" height="220px" />
            <MixedChart 
              v-else
              :labels="assetsDaily.labels" 
              :out-series="assetsDaily.outSeries" 
              :in-series="assetsDaily.inSeries"
              :cumulative-series="assetsDaily.cumulativeSeries"
              height="220"
            />
          </q-card-section>
        </q-card>
      </div>
      
      <!-- 3. Top 10 xe vào nhiều nhất -->
      <div class="col-12 col-lg-4">
        <q-card>
          <q-card-section>
            <div class="text-subtitle1">Top 10 xe vào nhiều nhất</div>
          </q-card-section>
          <q-separator />
          <q-card-section class="q-pa-sm">
            <DashboardSkeletonLoader v-if="loading" type="chart" height="220px" />
            <BarChart v-else :labels="guestsByPlate.labels" :series="guestsByPlate.series" title="Số lượt" height="220"/>
          </q-card-section>
        </q-card>
      </div>
    </div>
    <!-- === END SECTION 3 === -->

    <!-- === SECTION 4: ASSET CONTROL ALERT TABLE === -->
    <div class="q-mt-sm">
      <!-- Alert Table - Conditional -->
      <q-card v-if="!loading && assetControl.overdue_count > 0" class="bg-red-1">
        <q-card-section>
          <div class="row items-center">
            <q-icon name="warning" color="negative" size="24px" />
            <div class="text-h6 text-negative q-ml-sm">
              ⚠️ {{ assetControl.overdue_count }} Tài sản quá hạn
            </div>
            <q-space />
            <q-btn 
              flat 
              dense 
              :label="showOverdueTable ? 'Thu gọn' : 'Xem chi tiết'" 
              @click="showOverdueTable = !showOverdueTable"
            />
          </div>
        </q-card-section>
        
        <q-slide-transition>
          <q-card-section v-show="showOverdueTable" class="q-pa-none">
            <q-table
              dense
              flat
              :rows="assetControl.overdue_assets"
              :columns="overdueColumns"
              row-key="id"
              :rows-per-page="5"
              :pagination="{ rowsPerPage: 5 }"
            >
              <template v-slot:body-cell-risk_level="props">
                <q-td :props="props">
                  <q-badge :color="getRiskColor(props.row.risk_level)">
                    {{ getRiskLabel(props.row.risk_level) }}
                  </q-badge>
                </q-td>
              </template>
              <template v-slot:body-cell-days_overdue="props">
                <q-td :props="props">
                  <span class="text-negative text-weight-bold">{{ props.row.days_overdue }} ngày</span>
                </q-td>
              </template>
            </q-table>
          </q-card-section>
        </q-slide-transition>
      </q-card>
    </div>
    <!-- === END SECTION 4 === -->

    <!-- === SECTION 6: TOP PERFORMERS (Lazy Loaded) === -->
    <q-expansion-item
      ref="topPerformersExpansion"
      v-model="expandedPerformers"
      @before-show="onExpandTopPerformers"
      class="q-mt-md"
      icon="leaderboard"
      label="Top 5 Nhân viên hiệu suất cao"
      header-class="bg-grey-2 text-weight-medium"
      dense
    >
      <q-card flat bordered>
        <q-inner-loading :showing="loadingUsers">
          <q-spinner-gears size="40px" color="primary" />
        </q-inner-loading>
        <q-list v-if="userActivity.users.length > 0" separator dense>
          <q-item v-for="(user, index) in userActivity.users.slice(0, 5)" :key="user.user_id" class="q-py-sm">
            <q-item-section avatar>
              <q-avatar :color="index < 3 ? 'primary' : 'grey'" text-color="white" size="32px">
                <span class="text-weight-bold">{{ index + 1 }}</span>
              </q-avatar>
            </q-item-section>
            <q-item-section>
              <q-item-label class="text-weight-medium">{{ user.full_name }}</q-item-label>
              <q-item-label caption>{{ user.department || 'N/A' }}</q-item-label>
            </q-item-section>
            <q-item-section side>
              <div class="row items-center q-gutter-sm">
                <q-badge color="primary" class="text-weight-bold">
                  {{ user.performance_score }} điểm
                </q-badge>
                <div style="width: 100px">
                  <q-linear-progress 
                    :value="user.performance_score / 100" 
                    color="primary" 
                    size="8px"
                    rounded
                  />
                </div>
              </div>
            </q-item-section>
          </q-item>
        </q-list>
        <q-card-section v-else-if="!loadingUsers" class="text-center text-grey-7">
          <q-icon name="info" size="24px" />
          <div>Không có dữ liệu</div>
        </q-card-section>
      </q-card>
    </q-expansion-item>
    <!-- === END SECTION 6 === -->

    <!-- === SECTION 7: TOP SUPPLIERS === -->
    <q-expansion-item
      ref="topSuppliersExpansion"
      v-model="expandedSuppliers"
      @before-show="onExpandTopSuppliers"
      class="q-mt-sm"
      icon="business"
      label="Top 5 Nhà cung cấp"
      header-class="bg-grey-2 text-weight-medium"
      dense
    >
      <q-card flat bordered>
        <q-inner-loading :showing="loadingSuppliers">
          <q-spinner-gears size="40px" color="primary" />
        </q-inner-loading>
        <q-list v-if="topSuppliers.length > 0" separator dense>
          <q-item v-for="(supplier, index) in topSuppliers.slice(0, 5)" :key="index" class="q-py-sm">
            <q-item-section avatar>
              <q-avatar :color="index < 3 ? 'secondary' : 'grey'" text-color="white" size="32px">
                <span class="text-weight-bold">{{ index + 1 }}</span>
              </q-avatar>
            </q-item-section>
            <q-item-section>
              <q-item-label class="text-weight-medium">{{ supplier.supplier_name || 'N/A' }}</q-item-label>
              <q-item-label caption>Nhà cung cấp</q-item-label>
            </q-item-section>
            <q-item-section side>
              <div class="row items-center q-gutter-sm">
                <q-badge color="secondary" class="text-weight-bold">
                  {{ supplier.count }} khách
                </q-badge>
                <div style="width: 100px">
                  <q-linear-progress 
                    :value="supplier.count / maxSupplierCount" 
                    color="secondary" 
                    size="8px"
                    rounded
                  />
                </div>
              </div>
            </q-item-section>
          </q-item>
        </q-list>
        <q-card-section v-else-if="!loadingSuppliers" class="text-center text-grey-7">
          <q-icon name="info" size="24px" />
          <div>Không có dữ liệu</div>
        </q-card-section>
      </q-card>
    </q-expansion-item>
    <!-- === END SECTION 7 === -->
  </q-page>
</template>

<script setup>
import { reactive, onMounted, watch, ref, computed, nextTick } from 'vue';
import { date } from 'quasar'; // Import Quasar date utility
import BarChart from '../components/charts/BarChart.vue';
import MixedChart from '../components/charts/MixedChart.vue';
import DashboardSkeletonLoader from '../components/DashboardSkeletonLoader.vue';
import DashboardKPICard from '../components/DashboardKPICard.vue';
import { useDashboardData } from '../composables/useDashboardData';

// Use composable for data management
const {
  loading,
  loadingUsers,
  errors,
  guestsDaily,
  assetsDaily,
  guestsByPlate,
  systemOverview,
  assetControl,
  visitorSecurity,
  userActivity,
  loadDashboardData,
  loadUserActivity
} = useDashboardData();

// Debounce state
const isPending = ref(false);

// Asset Control UI state
const showOverdueTable = ref(false);

// Top Performers UI state
const expandedPerformers = ref(false);
const topPerformersExpansion = ref(null);

// Top Suppliers UI state
const expandedSuppliers = ref(false);
const topSuppliersExpansion = ref(null);

// Auto-scroll handlers
function onExpandTopPerformers() {
  loadUserActivity();
  nextTick(() => {
    if (topPerformersExpansion.value?.$el) {
      topPerformersExpansion.value.$el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
}

function onExpandTopSuppliers() {
  nextTick(() => {
    if (topSuppliersExpansion.value?.$el) {
      topSuppliersExpansion.value.$el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
}

// Computed: use data from visitorSecurity
const topSuppliers = computed(() => visitorSecurity.value.top_suppliers || []);
const loadingSuppliers = computed(() => loading.value);

// Computed: max supplier count for progress bar scaling
const maxSupplierCount = computed(() => {
  if (topSuppliers.value.length === 0) return 1;
  return Math.max(...topSuppliers.value.map(s => s.count));
});

const overdueColumns = [
  { name: 'asset_description', label: 'Mô tả tài sản', field: 'asset_description', align: 'left', sortable: true },
  { name: 'employee_name', label: 'Người mang ra', field: 'employee_name', align: 'left', sortable: true },
  { name: 'employee_code', label: 'Mã NV', field: 'employee_code', align: 'left' },
  { name: 'expected_return_date', label: 'Ngày dự kiến về', field: 'expected_return_date', align: 'left', sortable: true },
  { name: 'days_overdue', label: 'Số ngày quá hạn', field: 'days_overdue', align: 'center', sortable: true },
  { name: 'risk_level', label: 'Mức độ rủi ro', field: 'risk_level', align: 'center', sortable: true }
];

// Computed
const returnRateColor = computed(() => {
  const rate = assetControl.value.return_rate_percentage || 0;
  if (rate >= 90) return 'positive';
  if (rate >= 70) return 'warning';
  return 'negative';
});

const returnRateClass = computed(() => {
  const rate = assetControl.value.return_rate_percentage || 0;
  if (rate >= 90) return 'bg-positive text-white';
  if (rate >= 70) return 'bg-warning text-white';
  return 'bg-negative text-white';
});

// Helper functions
function getRiskColor(level) {
  const colors = {
    HIGH: 'negative',
    MEDIUM: 'warning',
    LOW: 'info'
  };
  return colors[level] || 'grey';
}

function getRiskLabel(level) {
  const labels = {
    HIGH: 'Cao',
    MEDIUM: 'Trung bình',
    LOW: 'Thấp'
  };
  return labels[level] || level;
}

const filters = reactive({
  start: '',
  end: '',
  range: 'last1month', // default
});

// Format date to YYYY/MM/DD for q-date component
const formatDateForInput = (d) => date.formatDate(d, 'YYYY/MM/DD');

// Function to set quick date ranges
function setRange(period) {
  filters.range = period;
  const today = new Date();
  
  if (period === 'last7days') {
    const startDate = date.subtractFromDate(today, { days: 6 });
    filters.start = formatDateForInput(startDate);
    filters.end = formatDateForInput(today);
  } else if (period === 'last1month') {
    const startDate = date.subtractFromDate(today, { months: 1 });
    filters.start = formatDateForInput(startDate);
    filters.end = formatDateForInput(today);
  } else if (period === 'last3months') {
    const startDate = date.subtractFromDate(today, { months: 3 });
    filters.start = formatDateForInput(startDate);
    filters.end = formatDateForInput(today);
  } else if (period === 'all') {
    // Setting to empty will clear the filters and fetch all data
    filters.start = '';
    filters.end = '';
  }
}

// Build API params from filters
function buildParams() {
  const params = {}
  if (filters.start) {
    const startDate = new Date(filters.start)
    startDate.setHours(0, 0, 0, 0)
    params.start = startDate.toISOString()
  }
  if (filters.end) {
    const endDate = new Date(filters.end)
    endDate.setHours(23, 59, 59, 999)
    params.end = endDate.toISOString()
  }
  return params
}

// Load data using composable
async function load() {
  const params = buildParams()
  await loadDashboardData(params)
}

// Watch for filter changes with debounce (500ms)
let debounceTimer = null
watch(filters, () => {
  isPending.value = true
  
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    isPending.value = false
    load()
  }, 500)
}, { deep: true, immediate: false }); 

onMounted(() => {
  setRange('last1month'); // This will trigger the watch and load initial data
});
</script>

<style scoped>
.kpi-compact-card {
  transition: all 0.3s ease;
  border-radius: 8px;
  overflow: hidden;
  min-height: 80px;
}

.kpi-compact-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

/* Custom class for 5 columns (20% each) on desktop */
@media (min-width: 600px) {
  .col-sm-20pc {
    width: 20%;
    flex: 0 0 20%;
    max-width: 20%;
  }
}
</style>
