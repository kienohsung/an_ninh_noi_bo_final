import { ref, reactive } from 'vue'
import api from '../api'
import { useQuasar } from 'quasar'

export function useDashboardData() {
  const $q = useQuasar()
  const loading = ref(false)
  const errors = ref([])

  // State for all dashboard sections
  const guestsDaily = reactive({ labels: [], series: [] })
  const assetsDaily = reactive({
    labels: [],
    outSeries: [],
    inSeries: [],
    cumulativeSeries: []
  })
  const guestsByPlate = reactive({ labels: [], series: [] })
  const systemOverview = ref({
    total_users: 0,
    total_guests_all_time: 0,
    total_assets_all_time: 0,
    active_guests_today: 0,
    active_assets_today: 0,
    avg_processing_time_minutes: null
  })
  const assetControl = ref({
    total_assets_out: 0,
    total_assets_returned: 0,
    return_rate_percentage: 0,
    overdue_assets: [],
    overdue_count: 0,
    high_risk_count: 0
  })
  const visitorSecurity = ref({
    total_guests_current_month: 0,
    total_guests_last_month: 0,
    growth_percentage: 0,
    monthly_data: [],
    top_suppliers: [],
    status_breakdown: { pending: 0, checked_in: 0, checked_out: 0 }
  })
  const userActivity = ref({ users: [], date_range: 'All time' })

  // Helper: Get section name by index
  function getSectionName(index) {
    const names = [
      'Khách theo ngày',
      'Tài sản theo ngày',
      'Top xe',
      'Tổng quan',
      'Kiểm soát TS',
      'An ninh khách'
    ]
    return names[index]
  }

  // Helper: API with timeout protection (15s)
  function apiWithTimeout(url, options, timeout = 15000) {
    return Promise.race([
      api.get(url, options),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout after 15s')), timeout)
      )
    ])
  }

  // Critical sections that need prominent error display
  const criticalSections = [3, 4] // System Overview, Asset Control

  // Main data loading function with Promise.allSettled
  async function loadDashboardData(params) {
    loading.value = true
    errors.value = []

    try {
      const results = await Promise.allSettled([
        apiWithTimeout('/reports/guests_daily', { params }),
        apiWithTimeout('/reports/assets_daily', { params }),
        apiWithTimeout('/reports/guests_by_plate', { params }),
        apiWithTimeout('/reports/system-overview', { params }),
        apiWithTimeout('/reports/asset-control', { params }),
        apiWithTimeout('/reports/visitor-security-index', { params })
      ])

      // Handle each result independently
      results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          switch (index) {
            case 0:
              Object.assign(guestsDaily, result.value.data)
              break
            case 1:
              console.log('🔧 [DEBUG] Assets Daily API Response:', result.value.data)
              const apiData = result.value.data; assetsDaily.labels = apiData.labels || []; assetsDaily.outSeries = apiData.out_series || []; assetsDaily.inSeries = apiData.in_series || []; assetsDaily.cumulativeSeries = apiData.cumulative_series || []
              break
            case 2:
              Object.assign(guestsByPlate, result.value.data)
              break
            case 3:
              systemOverview.value = result.value.data
              break
            case 4:
              assetControl.value = result.value.data
              break
            case 5:
              visitorSecurity.value = result.value.data
              break
          }
        } else {
          // Log error but don't block UI
          console.error(`API ${getSectionName(index)} failed:`, result.reason)

          const isCritical = criticalSections.includes(index)
          errors.value.push({
            section: getSectionName(index),
            error: result.reason,
            critical: isCritical
          })
        }
      })

      // Show notification if there are errors
      if (errors.value.length > 0) {
        const criticalCount = errors.value.filter(e => e.critical).length
        $q.notify({
          type: criticalCount > 0 ? 'warning' : 'info',
          message: `Một số dữ liệu không tải được (${errors.value.length} section)`,
          caption: 'Dashboard vẫn có thể sử dụng bình thường',
          timeout: 5000,
          actions: [{ label: 'Đóng', color: 'white' }]
        })
      }

    } catch (error) {
      console.error('Dashboard data load error:', error)
      $q.notify({
        type: 'negative',
        message: 'Không thể tải dữ liệu dashboard',
        caption: error.message
      })
    } finally {
      loading.value = false
    }
  }

  // Lazy load user activity (only when expanded)
  const loadingUsers = ref(false)
  async function loadUserActivity() {
    if (userActivity.value.users.length > 0) {
      return // Already loaded
    }

    loadingUsers.value = true
    try {
      const response = await apiWithTimeout('/reports/user-activity', {})
      userActivity.value = response.data
    } catch (error) {
      console.error('User activity load error:', error)
      $q.notify({
        type: 'negative',
        message: 'Không thể tải dữ liệu hoạt động người dùng'
      })
    } finally {
      loadingUsers.value = false
    }
  }

  return {
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
  }
}
