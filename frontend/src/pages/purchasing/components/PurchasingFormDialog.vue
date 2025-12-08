<script setup>
/**
 * PurchasingFormDialog.vue
 * Modal tạo mới/chỉnh sửa phiếu mua bán
 */
import { ref, computed, watch } from 'vue'
import { useQuasar } from 'quasar'
import { useAuthStore } from '../../../stores/auth'
import api from '../../../api'

const $q = useQuasar()
const authStore = useAuthStore()

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  editItem: { type: Object, default: null }
})

const emit = defineEmits(['update:modelValue', 'saved'])

// Form data
const form = ref({
  creator_name: '',
  department: '',
  using_department: '', // V2
  category: '',
  item_name: '',
  supplier_name: '',
  approved_price: 0
})

const imageFiles = ref([])
const loading = ref(false)

// Computed
const isEdit = computed(() => !!props.editItem)
const dialogTitle = computed(() => isEdit.value ? 'Chỉnh sửa Phiếu' : 'Thêm mới Phiếu Mua bán')

const categoryOptions = [
  { label: 'PC', value: 'PC' },
  { label: 'Laptop', value: 'Laptop' },
  { label: 'Linh kiện', value: 'Linh kiện' },
  { label: 'Mực in', value: 'Mực in' },
  { label: 'Khác', value: 'Khác' }
]

// Currency display (from integer to formatted string)
const priceDisplay = computed({
  get: () => {
    if (!form.value.approved_price) return ''
    return form.value.approved_price.toLocaleString('vi-VN')
  },
  set: (val) => {
    // Unmask: remove dots and convert to integer
    const numStr = val.replace(/\./g, '').replace(/,/g, '')
    form.value.approved_price = parseInt(numStr, 10) || 0
  }
})

// Reset form when dialog opens
watch(() => props.modelValue, (val) => {
  if (val) {
    if (props.editItem) {
      form.value = {
        creator_name: props.editItem.creator_name || '',
        department: props.editItem.department || '',
        using_department: props.editItem.using_department || '', // V2
        category: props.editItem.category || '',
        item_name: props.editItem.item_name || '',
        supplier_name: props.editItem.supplier_name || '',
        approved_price: props.editItem.approved_price || 0
      }
    } else {
      // Pre-fill from current user
      form.value = {
        creator_name: authStore.user?.full_name || '',
        department: authStore.user?.department || '',
        using_department: '', // V2
        category: '',
        item_name: '',
        supplier_name: '',
        approved_price: 0
      }
    }
    imageFiles.value = []
  }
})

// Close dialog
function closeDialog() {
  emit('update:modelValue', false)
}

// Submit form with atomic rollback
async function onSubmit() {
  // Validation (only for new records)
  if (!isEdit.value && imageFiles.value.length === 0) {
    $q.notify({ type: 'negative', message: 'Vui lòng chọn ảnh chứng từ/hóa đơn!' })
    return
  }

  if (!form.value.category || !form.value.item_name) {
    $q.notify({ type: 'negative', message: 'Vui lòng điền đầy đủ thông tin bắt buộc!' })
    return
  }

  loading.value = true
  let newId = null

  try {
    if (isEdit.value) {
      // Update existing record
      await api.put(`/purchasing/${props.editItem.id}`, form.value)
      
      // Upload new images if any
      if (imageFiles.value.length > 0) {
        for (const file of imageFiles.value) {
          const formData = new FormData()
          formData.append('file', file)
          await api.post(`/purchasing/${props.editItem.id}/upload-image`, formData)
        }
      }
      
      $q.notify({ type: 'positive', message: 'Cập nhật phiếu thành công!' })
    } else {
      // Step 1: Create record
      const res = await api.post('/purchasing', form.value)
      newId = res.data.id

      // Step 2: Upload images
      try {
        for (const file of imageFiles.value) {
          const formData = new FormData()
          formData.append('file', file)
          await api.post(`/purchasing/${newId}/upload-image`, formData)
        }
        $q.notify({ type: 'positive', message: 'Tạo phiếu thành công!' })
      } catch (uploadError) {
        // Step 3: Rollback on upload failure
        console.error('Upload failed, rolling back...', uploadError)
        await api.delete(`/purchasing/${newId}`)
        throw new Error('Upload ảnh thất bại, đã hủy phiếu. Vui lòng thử lại.')
      }
    }

    emit('saved')
    closeDialog()
  } catch (e) {
    console.error('Submit error:', e)
    $q.notify({ type: 'negative', message: e.message || 'Có lỗi xảy ra!' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <q-dialog :model-value="modelValue" @update:model-value="emit('update:modelValue', $event)" persistent>
    <q-card style="min-width: 500px; max-width: 600px">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">{{ dialogTitle }}</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section>
        <q-form @submit.prevent="onSubmit" class="q-gutter-sm">
          <!-- Creator Name -->
          <q-input
            v-model="form.creator_name"
            label="Người lập phiếu *"
            outlined
            dense
            :rules="[val => !!val || 'Bắt buộc']"
          />

          <!-- Department -->
          <div class="row q-col-gutter-sm">
            <div class="col-6">
              <q-input
                v-model="form.department"
                label="Bộ phận đề xuất"
                outlined
                dense
              />
            </div>
            <div class="col-6">
              <q-input
                v-model="form.using_department"
                label="Bộ phận sử dụng"
                placeholder="Nhập tên bộ phận"
                outlined
                dense
              />
            </div>
          </div>

          <!-- Category -->
          <q-select
            v-model="form.category"
            :options="categoryOptions"
            option-value="value"
            option-label="label"
            emit-value
            map-options
            label="Loại hàng *"
            outlined
            dense
            :rules="[val => !!val || 'Bắt buộc']"
          />

          <!-- Item Name -->
          <q-input
            v-model="form.item_name"
            label="Tên hàng/Mô tả *"
            outlined
            dense
            :rules="[val => !!val || 'Bắt buộc']"
          />

          <!-- Supplier Name -->
          <q-input
            v-model="form.supplier_name"
            label="Nhà cung cấp"
            outlined
            dense
          />

          <!-- Approved Price -->
          <q-input
            v-model="priceDisplay"
            label="Giá được duyệt (VNĐ)"
            outlined
            dense
            type="text"
            hint="Nhập số, tự động format"
          >
            <template v-slot:append>
              <span class="text-grey-7">₫</span>
            </template>
          </q-input>

          <!-- Image Upload -->
          <q-file
            v-model="imageFiles"
            label="Ảnh chứng từ/Hóa đơn *"
            outlined
            dense
            multiple
            accept="image/*,.pdf"
            :max-file-size="5242880"
            @rejected="() => $q.notify({ type: 'warning', message: 'File vượt quá 5MB hoặc không hợp lệ' })"
          >
            <template v-slot:prepend>
              <q-icon name="attach_file" />
            </template>
            <template v-slot:hint>
              <span>Bắt buộc. Tối đa 5MB/file. Hỗ trợ: JPG, PNG, PDF</span>
            </template>
          </q-file>

          <!-- Info -->
          <q-banner class="bg-grey-2 text-caption q-mt-sm" rounded>
            <q-icon name="info" class="q-mr-xs" />
            Ngày giờ tạo phiếu sẽ được ghi nhận tự động từ server.
          </q-banner>
        </q-form>
      </q-card-section>

      <q-card-actions align="right" class="q-pt-none">
        <q-btn flat label="Hủy" v-close-popup :disable="loading" />
        <q-btn
          color="primary"
          :label="isEdit ? 'Cập nhật' : 'Tạo phiếu'"
          :loading="loading"
          @click="onSubmit"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>
