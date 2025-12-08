<script setup>
/**
 * PurchasingReceiveDialog.vue
 * Modal "Nhận hàng" cho module Mua bán
 */
import { ref, watch } from 'vue'
import { useQuasar } from 'quasar'
import api from '../../../api'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  item: { type: Object, required: true }
})

const emit = defineEmits(['update:modelValue', 'saved'])
const $q = useQuasar()

// State
const note = ref('')
const images = ref([])
const loading = ref(false)

// Reset form when opening
watch(() => props.modelValue, (val) => {
  if (val) {
    note.value = ''
    images.value = []
  }
})

// Submit
async function onSubmit() {
  if (images.value.length === 0) {
    $q.notify({ type: 'warning', message: 'Vui lòng đính kèm ít nhất 1 ảnh thực tế/biên bản!' })
    return
  }
  
  loading.value = true
  try {
    // 1. Confirm receive (change status)
    await api.post(`/purchasing/${props.item.id}/receive`, {
        note: note.value
    })
    
    // 2. Upload delivery images
    for (const file of images.value) {
      const formData = new FormData()
      formData.append('file', file)
      // Upload with type=delivery
      await api.post(`/purchasing/${props.item.id}/upload-image?type=delivery`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    }
    
    $q.notify({ type: 'positive', message: 'Đã xác nhận nhận hàng thành công!' })
    emit('saved')
    emit('update:modelValue', false)
    
  } catch (error) {
    console.error('Receive error:', error)
    $q.notify({ 
        type: 'negative', 
        message: error.response?.data?.detail || 'Lỗi khi xác nhận nhận hàng'
    })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <q-dialog :model-value="modelValue" @update:model-value="emit('update:modelValue', $event)" persistent>
    <q-card style="min-width: 500px">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6 text-primary">
            <q-icon name="inventory" class="q-mr-sm" />
            Nhận Bàn Giao Hàng Hóa
        </div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>
      
      <q-separator />
      
      <q-card-section>
        <div class="text-subtitle1 text-weight-bold q-mb-xs">
            Phiếu: {{ item.item_name }}
        </div>
        <div class="text-caption text-grey-7 q-mb-md">
            Người lập: {{ item.creator_name }}
        </div>
        
        <!-- Note -->
        <q-input
            v-model="note"
            label="Ghi chú nhận hàng / Tình trạng"
            outlined
            type="textarea"
            rows="3"
            class="q-mb-md"
            placeholder="Ví dụ: Đã nhận đủ số lượng, hàng nguyên vẹn..."
        />
        
        <!-- Images Upload -->
        <div>
            <div class="text-subtitle2 q-mb-sm text-red">
                Ảnh thực tế / Biên bản bàn giao *
            </div>
            <q-file
                v-model="images"
                label="Chọn ảnh đính kèm"
                outlined
                dense
                multiple
                accept="image/*"
                max-files="5"
                counter
                :max-file-size="5242880"
            >
                <template v-slot:prepend>
                    <q-icon name="cloud_upload" />
                </template>
            </q-file>
            <div class="text-caption text-grey-6 q-mt-xs">
                * Bắt buộc phải có ít nhất 1 ảnh minh chứng
            </div>
        </div>
      </q-card-section>
      
      <q-separator />
      
      <q-card-actions align="right" class="q-pa-md">
        <q-btn flat label="Hủy" color="grey" v-close-popup />
        <q-btn 
            label="Xác nhận Nhận Hàng" 
            color="primary" 
            unelevated
            :loading="loading"
            @click="onSubmit"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>
