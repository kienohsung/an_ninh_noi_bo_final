<template>
  <q-card flat bordered>
    <q-card-section>
      <div class="text-body2 text-grey-8 q-mb-md">
        Xuất danh sách phiếu mua sắm vật tư/thiết bị theo thời gian, bộ phận, hoặc trạng thái.
      </div>

      <div class="row q-col-gutter-sm q-mb-md">
        <!-- Date Filters -->
        <div class="col-12 col-md-6">
          <q-input dense outlined v-model="filters.start_date" mask="date" label="Từ ngày">
            <template v-slot:append>
              <q-icon name="event" class="cursor-pointer">
                <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                  <q-date v-model="filters.start_date">
                    <div class="row items-center justify-end"><q-btn v-close-popup label="Đóng" color="primary" flat /></div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>
        <div class="col-12 col-md-6">
          <q-input dense outlined v-model="filters.end_date" mask="date" label="Đến ngày">
            <template v-slot:append>
              <q-icon name="event" class="cursor-pointer">
                <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                  <q-date v-model="filters.end_date">
                    <div class="row items-center justify-end"><q-btn v-close-popup label="Đóng" color="primary" flat /></div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>

        <!-- Quick Ranges -->
        <div class="col-12">
            <q-btn-group push class="full-width justify-center">
              <q-btn label="Hôm nay" size="sm" @click="setRange('today')" />
              <q-btn label="Tuần này" size="sm" @click="setRange('week')" />
              <q-btn label="Tháng này" size="sm" @click="setRange('month')" />
            </q-btn-group>
        </div>
      </div>

      <div class="row q-col-gutter-sm">
        <!-- Other Filters -->
         <div class="col-12 col-sm-6">
            <q-select
                dense outlined
                v-model="filters.status"
                :options="statusOptions"
                label="Trạng thái"
                emit-value map-options
                clearable
            />
         </div>
         <div class="col-12 col-sm-6">
            <q-input dense outlined v-model="filters.department" label="Bộ phận đề xuất" clearable />
         </div>
      </div>

      <div class="row justify-end q-mt-md">
        <q-btn 
            color="secondary" 
            icon="download" 
            label="Xuất Excel" 
            @click="exportExcel"
            :loading="isExporting"
            unelevated
            class="full-width"
        />
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup>
import { ref } from 'vue'
import { date, useQuasar } from 'quasar'
import api from '../../api'

const $q = useQuasar()
const isExporting = ref(false)

const filters = ref({
  start_date: '',
  end_date: '',
  status: null,
  department: ''
})

const statusOptions = [
  { label: 'Mới tạo', value: 'new' },
  { label: 'Chờ duyệt', value: 'pending' },
  { label: 'Đã duyệt', value: 'approved' },
  { label: 'Từ chối', value: 'rejected' },
  { label: 'Hoàn thành', value: 'completed' }
]

function setRange(range) {
    const today = new Date()
    if (range === 'today') {
        filters.value.start_date = date.formatDate(today, 'YYYY/MM/DD')
        filters.value.end_date = date.formatDate(today, 'YYYY/MM/DD')
    } else if (range === 'week') {
        // Tuần này (T2 - CN)
        const dayOfWeek = today.getDay()
        const diff = today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1) // adjust when day is sunday
        const monday = new Date(today.setDate(diff))
        filters.value.start_date = date.formatDate(monday, 'YYYY/MM/DD')
        filters.value.end_date = date.formatDate(new Date(), 'YYYY/MM/DD')
    } else if (range === 'month') {
        const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
        filters.value.start_date = date.formatDate(startOfMonth, 'YYYY/MM/DD')
        filters.value.end_date = date.formatDate(new Date(), 'YYYY/MM/DD')
    }
}

async function exportExcel() {
    isExporting.value = true
    try {
        const params = { ...filters.value }
        if (params.start_date) params.start_date = params.start_date.replace(/\//g, '-')
        if (params.end_date) params.end_date = params.end_date.replace(/\//g, '-')
        
        // Remove empty keys
        Object.keys(params).forEach(key => {
            if (params[key] === null || params[key] === '') delete params[key]
        })

        const response = await api.get('/purchasing/export/xlsx', {
             params,
             responseType: 'blob'
        })

        // Download logic
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        const contentDisposition = response.headers['content-disposition']
        let fileName = 'bao_cao_mua_sam.xlsx'
        if (contentDisposition) {
            const match = contentDisposition.match(/filename="?([^"]+)"?/)
            if (match && match[1]) fileName = match[1]
        }
        link.setAttribute('download', fileName)
        document.body.appendChild(link)
        link.click()
        link.remove()
        
        $q.notify({ type: 'positive', message: 'Xuất file thành công' })

    } catch (error) {
        console.error(error)
        $q.notify({ type: 'negative', message: 'Lỗi khi xuất báo cáo' })
    } finally {
        isExporting.value = false
    }
}
</script>
