<template>
  <q-page padding>
    <q-card>
      <q-card-section class="row items-center justify-between">
        <div class="text-h6">Quản lý Lịch sử Tài sản</div>
        <q-btn 
          label="Xuất Excel" 
          color="positive" 
          @click="exportData" 
          icon="download"
          :loading="loading"
        />
      </q-card-section>
      <q-separator />

      <!-- Filters -->
      <q-card-section class="row q-col-gutter-md items-center">
         <div class="col-12 col-md-3">
            <q-input dense outlined v-model="filters.startDate" mask="date" label="Từ ngày">
              <template v-slot:append>
                <q-icon name="event" class="cursor-pointer">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <q-date v-model="filters.startDate"><div class="row items-center justify-end"><q-btn v-close-popup label="Đóng" color="primary" flat /></div></q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </div>
          <div class="col-12 col-md-3">
             <q-input dense outlined v-model="filters.endDate" mask="date" label="Đến ngày">
              <template v-slot:append>
                <q-icon name="event" class="cursor-pointer">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <q-date v-model="filters.endDate"><div class="row items-center justify-end"><q-btn v-close-popup label="Đóng" color="primary" flat /></div></q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </div>
         <div class="col-12 col-md-3">
          <q-select
            v-model="filters.status"
            :options="statusOptions"
            label="Trạng thái"
            dense
            outlined
            emit-value
            map-options
            clearable
          />
        </div>
        <div class="col-12 col-md-3">
          <q-input
            v-model="filters.department"
            label="Tìm theo bộ phận"
            dense
            outlined
            clearable
          />
        </div>
      </q-card-section>

      <!-- Table -->
      <q-table
        :rows="rows"
        :columns="columns"
        row-key="id"
        flat
        :loading="loading"
        :pagination="{ rowsPerPage: 15 }"
        @row-click="onRowClick"
        class="cursor-pointer"
      >
        <template #body-cell-status="props">
          <q-td :props="props">
            <q-chip 
              :color="getStatusColor(props.value)" 
              text-color="white" 
              dense
              :label="getStatusLabel(props.value, props.row)"
            />
          </q-td>
        </template>

        <template #body-cell-created_at="props">
          <q-td :props="props">{{ formatDateTime(props.value) }}</q-td>
        </template>
        <template #body-cell-estimated_datetime="props">
          <q-td :props="props">{{ formatDate(props.value) }}</q-td>
        </template>
         <template #body-cell-check_out_time="props">
          <q-td :props="props">{{ formatDateTime(props.value) }}</q-td>
        </template>
        <template #body-cell-check_in_back_time="props">
          <q-td :props="props">{{ formatDateTime(props.value) }}</q-td>
        </template>

        <template #body-cell-actions="props">
          <q-td :props="props">
            <q-btn flat dense icon="edit" color="primary" @click.stop="openEditAssetDialog(props.row)" :disable="auth.user?.role !== 'admin' && props.row.status !== 'pending_out'">
              <q-tooltip v-if="auth.user?.role === 'admin' || props.row.status === 'pending_out'">Sửa thông tin</q-tooltip>
              <q-tooltip v-else>Chỉ sửa được khi chờ ra</q-tooltip>
            </q-btn>
            <q-btn flat dense icon="delete" color="negative" @click.stop="deleteAsset(props.row.id)" :disable="auth.user?.role !== 'admin' && props.row.status !== 'pending_out'">
              <q-tooltip v-if="auth.user?.role === 'admin' || props.row.status === 'pending_out'">Xóa (Chỉ khi chưa ra cổng)</q-tooltip>
              <q-tooltip v-else>Chỉ xóa được khi chờ ra</q-tooltip>
            </q-btn>
          </q-td>
        </template>
      </q-table>
    </q-card>

    <!-- Detail Dialog -->
    <q-dialog v-model="showDetailDialog" position="right">
      <q-card style="width: 500px; max-width: 90vw;">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6">Chi tiết Tài sản</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section v-if="selectedAsset" class="q-pt-none">
          <!-- Image Carousel -->
          <div v-if="selectedAsset.images && selectedAsset.images.length > 0" class="q-mb-md">
            <q-carousel
              v-model="slide"
              animated
              arrows
              navigation
              infinite
              swipeable
              height="300px"
            >
              <q-carousel-slide 
                v-for="(image, index) in selectedAsset.images" 
                :key="index"
                :name="index"
                class="q-pa-none"
              >
                <q-img 
                  :src="getImageUrl(image.image_path)" 
                  fit="contain"
                  style="height: 300px;"
                />
              </q-carousel-slide>
            </q-carousel>
          </div>
          <div v-else class="q-mb-md text-center text-grey-6">
            Không có hình ảnh
          </div>

          <!-- Asset Details -->
          <q-list dense>
            <q-item>
              <q-item-section>
                <q-item-label caption>Trạng thái</q-item-label>
                <q-item-label>
                  <q-chip 
                    :color="getStatusColor(selectedAsset.status)" 
                    text-color="white" 
                    dense
                  >
                    {{ getStatusLabel(selectedAsset.status) }}
                  </q-chip>
                </q-item-label>
              </q-item-section>
            </q-item>

            <q-separator spaced />

            <q-item>
              <q-item-section>
                <q-item-label caption>Người đăng ký</q-item-label>
                <q-item-label>{{ selectedAsset.registered_by.full_name }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item>
              <q-item-section>
                <q-item-label caption>Bộ phận</q-item-label>
                <q-item-label>{{ selectedAsset.department }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item>
              <q-item-section>
                <q-item-label caption>Nơi đến</q-item-label>
                <q-item-label>{{ selectedAsset.destination }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item>
              <q-item-section>
                <q-item-label caption>Mô tả tài sản & lý do</q-item-label>
                <q-item-label class="text-pre-wrap">{{ selectedAsset.description_reason }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item>
              <q-item-section>
                <q-item-label caption>Số lượng</q-item-label>
                <q-item-label>{{ selectedAsset.quantity }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-separator spaced />

            <q-item>
              <q-item-section>
                <q-item-label caption>Ngày đăng ký</q-item-label>
                <q-item-label>{{ formatDateTime(selectedAsset.created_at) }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-item>
              <q-item-section>
                <q-item-label caption>Dự kiến về</q-item-label>
                <q-item-label>{{ formatDate(selectedAsset.estimated_datetime) || 'Không về' }}</q-item-label>
              </q-item-section>
            </q-item>

            <template v-if="selectedAsset.check_out_time">
              <q-separator spaced />
              <q-item>
                <q-item-section>
                  <q-item-label caption>Giờ ra</q-item-label>
                  <q-item-label>{{ formatDateTime(selectedAsset.check_out_time) }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item v-if="selectedAsset.check_out_by">
                <q-item-section>
                  <q-item-label caption>BV xác nhận ra</q-item-label>
                  <q-item-label>{{ selectedAsset.check_out_by.full_name }}</q-item-label>
                </q-item-section>
              </q-item>
            </template>

            <template v-if="selectedAsset.check_in_back_time">
              <q-separator spaced />
              <q-item>
                <q-item-section>
                  <q-item-label caption>Giờ về</q-item-label>
                  <q-item-label>{{ formatDateTime(selectedAsset.check_in_back_time) }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item v-if="selectedAsset.check_in_back_by">
                <q-item-section>
                  <q-item-label caption>BV xác nhận về</q-item-label>
                  <q-item-label>{{ selectedAsset.check_in_back_by.full_name }}</q-item-label>
                </q-item-section>
              </q-item>
            </template>
          </q-list>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Edit Dialog -->
    <q-dialog v-model="showEditAssetDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Cập nhật tài sản</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="submitEditAsset" class="q-gutter-md">
            <q-input v-model="editAssetForm.destination" label="Nơi đến" outlined dense required />
            <q-input v-model.number="editAssetForm.quantity" label="Số lượng" type="number" outlined dense required />
            
            <q-input 
                v-model="formattedEditAssetDatetime" 
                label="Ngày dự kiến *" 
                dense 
                outlined 
                readonly 
                required
                :rules="[val => !!val || 'Vui lòng chọn ngày dự kiến']"
              >
                <template v-slot:append>
                  <q-icon name="event" class="cursor-pointer" @click="openDateTimePickerProxy">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <div class="q-pa-md" style="min-width: 300px">
                        <div class="q-gutter-md">
                          <q-date v-model="proxyDate" mask="YYYY-MM-DD" />
                        </div>
                        <div class="row items-center justify-end q-mt-md q-gutter-sm">
                          <q-btn v-close-popup label="Bỏ qua" color="primary" flat />
                          <q-btn v-close-popup label="OK" color="primary" @click="setEstimatedDatetime" />
                        </div>
                      </div>
                    </q-popup-proxy>
                  </q-icon>
                </template>
            </q-input>

            <q-input v-model="editAssetForm.description_reason" label="Mô tả / Lý do" type="textarea" outlined dense required />
            
            <div class="row justify-end q-gutter-sm">
              <q-btn label="Hủy" flat v-close-popup />
              <q-btn label="Cập nhật" type="submit" color="primary" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

      <!-- Print Dialog -->
      <q-dialog v-model="showPrintDialog" class="print-dialog-custom">
        <q-card style="width: 50vw; max-width: 900px; height: 90vh; position: relative;">
          <q-card-section style="padding: 0; overflow-y: auto; height: 100%;" class="hide-scrollbar">
            <AssetFormPaper 
              v-if="printAssetData" 
              :model-value="printAssetData" 
              :asset-id="printAssetData.id"
              mode="print"
              :is-returnable="printAssetData.estimated_datetime !== null"
            />
          </q-card-section>
          
          <!-- Floating Action Buttons -->
          <q-btn 
            fab 
            icon="print" 
            color="primary" 
            @click="triggerPrint"
            class="no-print"
            style="position: absolute; bottom: 80px; right: 20px; z-index: 100;"
          >
            <q-tooltip>In phiếu</q-tooltip>
          </q-btn>
          
          <q-btn 
            fab 
            icon="close" 
            color="grey-7" 
            v-close-popup
            class="no-print"
            style="position: absolute; bottom: 20px; right: 20px; z-index: 100;"
          >
            <q-tooltip>Đóng</q-tooltip>
          </q-btn>
        </q-card>
      </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted, reactive, watch, computed } from 'vue';
import { useQuasar, date as quasarDate } from 'quasar';
import { useRoute, useRouter } from 'vue-router';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import api from '../api';
import { exportFile } from '../utils/export';
import { useAuthStore } from '../stores/auth';
import AssetFormPaper from '../components/AssetFormPaper.vue';

const $q = useQuasar();
const auth = useAuthStore();
const route = useRoute();
const router = useRouter();
const loading = ref(false);
const rows = ref([]);
const showDetailDialog = ref(false);
const selectedAsset = ref(null);
const slide = ref(0);

// Print dialog
const showPrintDialog = ref(false);
const printAssetData = ref(null);

function printAsset(row) {
  printAssetData.value = {
    ...row,
    full_name: row.registered_by.full_name,
    employee_code: row.registered_by.username,
    vietnamese_manager_name: row.vietnamese_manager_name || '',
    korean_manager_name: row.korean_manager_name || '',
    asset_description: row.asset_description || '',
    description_reason: row.description_reason || '',
  };
  showPrintDialog.value = true;
}

function triggerPrint() {
  // Increment print count trước khi in
  if (printAssetData.value?.id) {
    api.post(`/assets/${printAssetData.value.id}/increment-print-count`)
      .then(() => {
        exportToPDF();
      })
      .catch(error => {
        console.error('Failed to increment print count:', error);
        // Vẫn in ngay cả khi API fail
        exportToPDF();
      });
  } else {
    exportToPDF();
  }
}

// PDF Export Function
async function exportToPDF() {
  try {
    const element = document.querySelector('.asset-form-paper');
    if (!element) {
      $q.notify({ type: 'negative', message: 'Không tìm thấy form để xuất PDF' });
      return;
    }

    $q.loading.show({ message: 'Đang tạo PDF...' });

    // Temporarily remove yellow backgrounds by removing class completely
    const yellowElements = element.querySelectorAll('.bg-yellow-2');
    const originalYellowClasses = []; // To store if bg-yellow-2 was present

    yellowElements.forEach(el => {
      // Store if the class was present
      originalYellowClasses.push({
        element: el,
        hasClass: el.classList.contains('bg-yellow-2')
      });
      // Remove bg-yellow-2 class completely
      el.classList.remove('bg-yellow-2');
    });
    
    // Increase all font sizes
    const originalFontSize = element.style.fontSize;
    element.style.fontSize = '125%'; // Increase by 1 more size

    // Wait for styles to apply
    await new Promise(resolve => setTimeout(resolve, 100));

    // Capture form as canvas with high quality
    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff'
    });

    // Restore yellow class after capture
    yellowElements.forEach(el => {
      el.classList.add('bg-yellow-2');
    });
    element.style.fontSize = originalFontSize;

    // Calculate dimensions for A4 with 0.5cm margins
    const marginMM = 5; // 0.5cm = 5mm
    const imgWidth = 210 - (marginMM * 2); // A4 width minus left/right margins
    const pageHeight = 297; // A4 height in mm
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    
    // Create PDF
    const pdf = new jsPDF('p', 'mm', 'a4');
    const imgData = canvas.toDataURL('image/png');
    
    // Add image to PDF with margins
    const yOffset = imgHeight < pageHeight ? (pageHeight - imgHeight) / 2 : marginMM;
    pdf.addImage(imgData, 'PNG', marginMM, yOffset, imgWidth, imgHeight);
    
    // Generate filename with current date
    const assetId = printAssetData.value?.id || 'unknown';
    const date = new Date();
    const filename = `TaiSan_${assetId}_${date.getFullYear()}${String(date.getMonth()+1).padStart(2,'0')}${String(date.getDate()).padStart(2,'0')}.pdf`;
    
    // Tạo blob và mở PDF trong tab mới (UX liền mạch)
    const pdfBlob = pdf.output('blob');
    const blobUrl = URL.createObjectURL(pdfBlob);
    
    // Mở PDF trong tab mới
    window.open(blobUrl, '_blank');
    
    // Tùy chọn: vẫn download file nếu người dùng muốn
    // pdf.save(filename);
    
    $q.loading.hide();
    
    // Show prominent success notification
    $q.notify({
      type: 'positive',
      message: '✅ ĐÃ MỞ PDF THÀNH CÔNG!',
      caption: `File: ${filename} - Đã mở trong tab mới`,
      position: 'center',
      timeout: 2000,
      textColor: 'white',
      color: 'positive',
      classes: 'text-h6',
      attrs: {
        style: 'font-size: 1.5rem; padding: 20px;'
      }
    });
  } catch (error) {
    $q.loading.hide();
    console.error('PDF generation error:', error);
    $q.notify({ type: 'negative', message: 'Lỗi khi tạo PDF' });
  }
}
// Filters
const filters = reactive({
  status: null,
  department: '',
  startDate: null,
  endDate: null,
});

const statusOptions = [
  { label: 'Chờ ra', value: 'pending_out' },
  { label: 'Đã ra (chờ về)', value: 'checked_out' },
  { label: 'Đã hoàn trả', value: 'returned' }
];

// Columns
const columns = [
  { name: 'status', label: 'Trạng thái', field: 'status', align: 'left', sortable: true },
  { name: 'registered_by_name', label: 'Người đăng ký', field: row => row.registered_by.full_name, align: 'left' },
  { name: 'department', label: 'Bộ phận', field: 'department', align: 'left', sortable: true },
  { name: 'destination', label: 'Nơi đến', field: 'destination', align: 'left' },
  { name: 'description_reason', label: 'Mô tả', field: 'description_reason', align: 'left', style: 'max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;' },
  { name: 'quantity', label: 'SL', field: 'quantity', align: 'center', sortable: true },
  { name: 'created_at', label: 'Ngày ĐK', field: 'created_at', align: 'left', sortable: true },
  { name: 'estimated_datetime', label: 'Ngày dự kiến', field: 'estimated_datetime', align: 'left', sortable: true, format: val => formatDate(val) },
  { name: 'check_out_time', label: 'Giờ ra', field: 'check_out_time', align: 'left', sortable: true },
  { name: 'check_in_back_time', label: 'Giờ về', field: 'check_in_back_time', align: 'left', sortable: true },
  { name: 'check_out_by_name', label: 'BV xác nhận ra', field: row => row.check_out_by?.full_name, align: 'left' },
  { name: 'check_in_back_by_name', label: 'BV xác nhận về', field: row => row.check_in_back_by?.full_name, align: 'left' },
  { name: 'actions', label: 'Thao tác', field: 'actions', align: 'center' }
];

// Helpers
function getStatusColor(status) {
  if (status === 'pending_out') return 'warning';
  if (status === 'checked_out') return 'info';
  if (status === 'returned') return 'positive';
  return 'grey';
}
function getStatusLabel(status, row = null) {
  // Trường hợp đặc biệt: Tài sản KHÔNG hoàn lại đã ra cổng
  if (status === 'returned' && row && row.estimated_datetime === null) {
    return 'Đã ra - Không hoàn lại';
  }
  
  const option = statusOptions.find(opt => opt.value === status);
  return option ? option.label : status;
}
function formatDateTime(val) {
  if (!val) return '';
  return quasarDate.formatDate(val, 'YYYY/MM/DD HH:mm');
}
function formatDate(val) {
  if (!val) return '';
  return quasarDate.formatDate(val, 'YYYY/MM/DD');
}

// Load Data
async function loadData() {
  loading.value = true;
  try {
    const params = {
      status: filters.status || undefined,
      department: filters.department || undefined,
      start_date: filters.startDate ? quasarDate.formatDate(quasarDate.extractDate(filters.startDate, 'YYYY/MM/DD'), 'YYYY-MM-DD') : undefined,
      end_date: filters.endDate ? quasarDate.formatDate(quasarDate.extractDate(filters.endDate, 'YYYY/MM/DD'), 'YYYY-MM-DD') : undefined,
    };
    
    const response = await api.get('/assets', { params });
    rows.value = response.data;
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Không thể tải lịch sử tài sản.' });
  } finally {
    loading.value = false;
  }
}

// Row Click - show print dialog with AssetFormPaper
function onRowClick(evt, row) {
  printAsset(row);
}

// Image URL
function getImageUrl(imagePath) {
  if (!imagePath) return '';
  const apiBaseURL = api.defaults.baseURL || 'http://localhost:8000';
  return `${apiBaseURL}/uploads/${imagePath}`;
}

// Export
function exportData() {
  loading.value = true;
  try {
    const dataToExport = rows.value.map(row => ({
      'Trạng thái': getStatusLabel(row.status),
      'Người đăng ký': row.registered_by.full_name,
      'Bộ phận': row.department,
      'Nơi đến': row.destination,
      'Mô tả': row.description_reason,
      'Số lượng': row.quantity,
      'Ngày ĐK': formatDateTime(row.created_at),
      'Dự kiến về': formatDate(row.estimated_datetime),
      'Giờ ra': formatDateTime(row.check_out_time),
      'BV xác nhận ra': row.check_out_by?.full_name || '',
      'Giờ về': formatDateTime(row.check_in_back_time),
      'BV xác nhận về': row.check_in_back_by?.full_name || '',
    }));
    
    const columnsToExport = [
      'Trạng thái', 'Người đăng ký', 'Bộ phận', 'Nơi đến', 'Mô tả', 'Số lượng', 
      'Ngày ĐK', 'Dự kiến về', 'Giờ ra', 'BV xác nhận ra', 'Giờ về', 'BV xác nhận về'
    ];

    exportFile('LichSuTaiSan.xlsx', dataToExport, columnsToExport);
  } catch (error) {
     $q.notify({ type: 'negative', message: 'Lỗi khi tạo file Excel.' });
  } finally {
    loading.value = false;
  }
}

// Watch filters
watch(filters, loadData, { deep: true });

// Edit/Delete Logic
async function deleteAsset(id) {
  $q.dialog({
    title: 'Xác nhận',
    message: 'Bạn có chắc chắn muốn xóa tài sản này?',
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.delete(`/assets/${id}`)
      $q.notify({ type: 'positive', message: 'Đã xóa tài sản.' })
      loadData()
    } catch (error) {
       $q.notify({ type: 'negative', message: error.response?.data?.detail || 'Xóa thất bại.' })
    }
  })
}

const showEditAssetDialog = ref(false)
const editAssetForm = reactive({
  id: null,
  destination: '',
  quantity: 1,
  description_reason: '',
  estimated_datetime: null
})
const proxyDate = ref(null)

const formattedEditAssetDatetime = computed(() => {
  if (!editAssetForm.estimated_datetime) return null
  return quasarDate.formatDate(new Date(editAssetForm.estimated_datetime), 'DD/MM/YYYY')
})

function openEditAssetDialog(row) {
  editAssetForm.id = row.id
  editAssetForm.destination = row.destination
  editAssetForm.quantity = row.quantity
  editAssetForm.description_reason = row.description_reason
  editAssetForm.estimated_datetime = row.estimated_datetime 
  showEditAssetDialog.value = true
}

function openDateTimePickerProxy() {
  let d
  if (editAssetForm.estimated_datetime) {
    d = new Date(editAssetForm.estimated_datetime)
  } else {
    d = new Date()
  }
  proxyDate.value = quasarDate.formatDate(d, 'YYYY-MM-DD')
}

function setEstimatedDatetime() {
  if (proxyDate.value) {
    editAssetForm.estimated_datetime = `${proxyDate.value}T00:00:00`
  }
}

async function submitEditAsset() {
  try {
    const payload = { 
        destination: editAssetForm.destination,
        quantity: editAssetForm.quantity,
        description_reason: editAssetForm.description_reason,
        estimated_datetime: editAssetForm.estimated_datetime
    }
    
    await api.put(`/assets/${editAssetForm.id}`, payload)
    $q.notify({ type: 'positive', message: 'Cập nhật tài sản thành công!' })
    showEditAssetDialog.value = false
    loadData()
  } catch (error) {
    console.error('Update asset failed:', error)
    $q.notify({ type: 'negative', message: error.response?.data?.detail || 'Cập nhật thất bại.' })
  }
}

onMounted(async () => {
  console.log('[AssetManagementPage] onMounted, query params:', route.query);
  await loadData();
  
  // Auto-open print dialog if printId query param exists
  const printId = route.query.printId;
  console.log('[AssetManagementPage] printId from query:', printId);
  
  if (printId) {
    // Find the asset in loaded data
    const assetToPrint = rows.value.find(row => row.id === parseInt(printId));
    console.log('[AssetManagementPage] Found asset in rows:', assetToPrint);
    
    if (assetToPrint) {
      console.log('[AssetManagementPage] Opening print dialog for asset:', assetToPrint.id);
      printAsset(assetToPrint);
    } else {
      // If not in current page, fetch it specifically
      console.log('[AssetManagementPage] Asset not in current data, fetching all...');
      try {
        const response = await api.get(`/assets`);
        const asset = response.data.find(a => a.id === parseInt(printId));
        if (asset) {
          console.log('[AssetManagementPage] Found asset from API, opening print dialog');
          printAsset(asset);
        } else {
          console.log('[AssetManagementPage] Asset not found even in full list');
        }
      } catch (error) {
        console.error('Could not fetch asset for printing:', error);
      }
    }
    // Note: We keep the query param - it doesn't hurt anything
  }
});

</script>
<style scoped>
.hide-scrollbar {
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.hide-scrollbar::-webkit-scrollbar {
  display: none;
}
</style>
