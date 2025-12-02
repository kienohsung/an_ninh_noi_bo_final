<template>
  <q-page padding>
    <div class="row justify-center">
      <div class="col-12" style="max-width: 230mm"> <!-- Slightly wider than A4 to allow padding -->
        <q-card class="q-mb-md">
          <q-card-section class="row items-center justify-between">
            <div class="text-subtitle1">Đăng ký Tài sản Ra/Vào</div>
          </q-card-section>
        </q-card>

        <!-- WYSIWYG Form -->
        <AssetFormPaper 
          :model-value="form"
          @update:model-value="handleFormUpdate"
          mode="edit" 
        />

        <!-- Image Upload Section (Keep outside the paper form) -->
        <q-card class="q-mt-md">
          <q-card-section>
            <div class="text-subtitle2 q-mb-sm">Hình ảnh đính kèm (Bắt buộc)</div>
            <q-file 
              v-model="selectedImages" 
              label="Chọn hình ảnh" 
              outlined 
              dense
              multiple
              accept="image/*"
              max-files="5"
              counter
              :rules="[val => (val && val.length > 0) || 'Vui lòng chọn ít nhất 1 ảnh']"
            >
              <template v-slot:prepend>
                <q-icon name="attach_file" />
              </template>
            </q-file>

            <!-- Image Preview -->
            <div v-if="imagePreviews.length > 0" class="row q-col-gutter-sm q-mt-sm">
              <div v-for="(preview, index) in imagePreviews" :key="index" class="col-6 col-sm-4 col-md-3">
                <q-card flat bordered>
                  <q-img :src="preview" ratio="1" />
                </q-card>
              </div>
            </div>
          </q-card-section>
        </q-card>

        <!-- Submit and Print Buttons at Bottom -->
        <q-card class="q-mt-md">
          <q-card-section class="text-center">
            <q-btn 
              label="In phiếu" 
              color="secondary" 
              icon="print"
              @click="handlePrint"
              size="lg"
              class="q-px-xl q-mr-md"
            />
            <q-btn 
              label="Gửi đăng ký" 
              color="primary" 
              icon="send"
              @click="onSubmit"
              :loading="isSubmitting"
              :disable="isSubmitting"
              size="lg"
              class="q-px-xl"
            />
          </q-card-section>
        </q-card>

      </div>
    </div>
  </q-page>
</template>

<script setup>
import { reactive, ref, computed, watch, onMounted } from 'vue'
import { useQuasar, date as quasarDate } from 'quasar'
import { useRouter } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import AssetFormPaper from '../components/AssetFormPaper.vue'

const $q = useQuasar()
const router = useRouter()
const auth = useAuthStore()

const departmentDisplay = computed(() => {
  if (auth.user?.department) return auth.user.department;
  if (auth.user?.full_name && auth.user.full_name.includes('-')) {
    return auth.user.full_name.split('-')[0].trim();
  }
  return '';
})

const initialFormState = {
  destination: '',
  description_reason: '',
  asset_description: '', // New field
  quantity: 1,
  department: '',
  estimated_datetime: null,
  vietnamese_manager_name: '',
  korean_manager_name: '',
  full_name: '',
  employee_code: ''
}

const form = reactive({ ...initialFormState })
const isSubmitting = ref(false)
const selectedImages = ref(null)
const imagePreviews = ref([])
const lastCreatedAssetId = ref(null); // Track last created asset ID

// Initialize user data when auth is ready
watch(() => auth.user, (user) => {
  if (user) {
    form.full_name = user.full_name;
    form.employee_code = user.username;
    form.department = departmentDisplay.value;
  }
}, { immediate: true });

// Watch for image selection
watch(selectedImages, (newFiles) => {
  imagePreviews.value = []
  if (newFiles && newFiles.length > 0) {
    for (const file of newFiles) {
      const reader = new FileReader()
      reader.onload = (e) => {
        imagePreviews.value.push(e.target.result)
      }
      reader.readAsDataURL(file)
    }
  }
})

function handleFormUpdate(newFormData) {
  Object.assign(form, newFormData);
}

function handlePrint() {
  // Navigate to AssetManagementPage with printId query param
  if (lastCreatedAssetId.value) {
    console.log('[RegisterAssetPage] Navigating with printId:', lastCreatedAssetId.value);
    router.push({ 
      path: '/asset-management', 
      query: { printId: lastCreatedAssetId.value } 
    });
  } else {
    $q.notify({ 
      type: 'warning', 
      message: 'Vui lòng đăng ký phiếu trước khi in' 
    });
  }
}

async function onSubmit() {
  isSubmitting.value = true;
  try {
    if (!form.quantity || form.quantity <= 0) {
        $q.notify({ type: 'negative', message: 'Số lượng phải lớn hơn 0.' });
        isSubmitting.value = false;
        return;
    }

    // Check date
    const dateValue = form.estimated_datetime;
    if (!dateValue || (typeof dateValue === 'string' && dateValue.trim() === '')) {
        $q.notify({ type: 'negative', message: 'Vui lòng chọn ngày dự kiến.' });
        isSubmitting.value = false;
        return;
    }

    if (!selectedImages.value || selectedImages.value.length === 0) {
        $q.notify({ type: 'negative', message: 'Vui lòng chọn ít nhất 1 ảnh.' });
        isSubmitting.value = false;
        return;
    }

    // Convert date from YYYY/MM/DD to YYYY-MM-DD format
    const estimatedDatetime = form.estimated_datetime ? 
      form.estimated_datetime.replace(/\//g, '-') : null;
    
    const payload = {
      destination: form.destination,
      description_reason: form.description_reason,
      asset_description: form.asset_description,
      quantity: form.quantity,
      department: form.department,
      estimated_datetime: estimatedDatetime,
      vietnamese_manager_name: form.vietnamese_manager_name || '',
      korean_manager_name: form.korean_manager_name || '',
    };
    
    const response = await api.post('/assets', payload); 
    const assetId = response.data.id;
    
    // Save the created asset ID for printing
    lastCreatedAssetId.value = assetId;
    
    const uploadPromises = []
    for (const file of selectedImages.value) {
      const formData = new FormData()
      formData.append('file', file)
      uploadPromises.push(
        api.post(`/assets/${assetId}/upload-image`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      )
    }
    
    await Promise.all(uploadPromises)
    
    $q.notify({ 
      type: 'positive', 
      message: 'Đăng ký tài sản và tải ảnh thành công! Bạn có thể in phiếu ngay bây giờ.' 
    });
    // Do NOT reset form - keep it for printing
    // resetForm();

  } catch (error) {
    console.error("Asset registration error:", error.response?.data?.detail || error.message);
    $q.notify({ type: 'negative', message: error.response?.data?.detail || 'Đăng ký thất bại.' })
  } finally {
    isSubmitting.value = false
  }
}

function resetForm() {
  Object.assign(form, initialFormState);
  form.quantity = 1;
  form.estimated_datetime = null;
  form.department = departmentDisplay.value;
  selectedImages.value = null
  imagePreviews.value = []
}
</script>
