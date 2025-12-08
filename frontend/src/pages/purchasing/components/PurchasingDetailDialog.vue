<script setup>
/**
 * PurchasingDetailDialog.vue
 * Popup xem chi tiết phiếu mua bán (Style: Security Event Table)
 */
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  item: { type: Object, default: null } // Purchasing object
})

const emit = defineEmits(['update:modelValue'])

const carouselSlide = ref(0)
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Status helpers
const statusMap = {
  new: { label: 'Mới', color: 'blue', icon: 'fiber_new' },
  pending: { label: 'Chờ duyệt', color: 'orange', icon: 'hourglass_empty' },
  approved: { label: 'Đã duyệt', color: 'green', icon: 'check_circle' },
  rejected: { label: 'Từ chối', color: 'red', icon: 'cancel' },
  completed: { label: 'Đã nhận', color: 'purple', icon: 'inventory' }
}

const statusInfo = computed(() => {
  const s = props.item?.status || 'new'
  return statusMap[s] || { label: s, color: 'grey', icon: 'help' }
})

const requestImages = computed(() => {
    return props.item?.images?.filter(img => !img.image_type || img.image_type === 'request') || []
})

const deliveryImages = computed(() => {
    return props.item?.images?.filter(img => img.image_type === 'delivery') || []
})

const hasRequestImages = computed(() => requestImages.value.length > 0)
const hasDeliveryImages = computed(() => deliveryImages.value.length > 0)

function getImageUrl(path) {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${API_URL}/uploads/${path.replace(/\\/g, '/')}`
}

function formatDate(dt) {
  if (!dt) return 'N/A'
  return new Date(dt).toLocaleString('vi-VN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

function formatPrice(p) {
  if (!p) return '0 ₫'
  return p.toLocaleString('vi-VN') + ' ₫'
}

function openImageFullscreen(img) {
  const imgUrl = getImageUrl(img.image_path)
  window.open(imgUrl, '_blank')
}
</script>

<template>
  <q-dialog :model-value="modelValue" @update:model-value="emit('update:modelValue', $event)" full-width>
    <q-card class="bg-white" style="width: 90vw; max-width: 1400px; display: flex; flex-direction: column; max-height: 90vh">
      
      <!-- HEADER -->
      <q-card-section class="q-pa-lg text-center bg-grey-2 border-bottom flex-none">
        <div class="text-h5 text-weight-bold text-uppercase text-primary q-mb-xs">Phiếu Yêu Cầu Mua Sắm</div>
        <div class="text-caption text-grey-8">Mã phiếu: <span class="text-weight-bold">#PUR-{{ item?.id }}</span></div>
        <div class="text-caption text-grey-8">Ngày tạo: {{ formatDate(item?.created_at) }}</div>
        <q-btn icon="close" flat round dense v-close-popup class="absolute-top-right q-ma-sm" />
      </q-card-section>

      <q-separator />

      <q-card-section class="q-pa-lg scroll" style="flex: 1" v-if="item">
        <div class="row q-col-gutter-xl full-height">
          
          <!-- LEFT COLUMN: Information (md-7) -->
          <div class="col-12 col-md-7 flex column">
            
            <!-- 1. General Info -->
            <div class="row items-center q-mb-md">
              <q-icon name="info" color="primary" size="sm" class="q-mr-sm" />
              <div class="text-subtitle1 text-weight-bold text-uppercase text-primary">1. Thông tin chung</div>
            </div>

            <div class="row q-col-gutter-y-md q-col-gutter-x-xl q-mb-lg">
              <!-- Creator -->
              <div class="col-12 col-sm-6">
                <div class="text-caption text-grey-7 text-uppercase" style="letter-spacing: 0.5px">Người đề xuất</div>
                <div class="text-body1 flex items-center">
                  <q-icon name="person" size="xs" class="q-mr-xs text-grey-6" />
                  <span class="text-weight-medium">{{ item.creator_name }}</span>
                </div>
              </div>
              
              <!-- Status -->
              <div class="col-12 col-sm-6">
                <div class="text-caption text-grey-7 text-uppercase" style="letter-spacing: 0.5px">Trạng thái</div>
                <div class="text-body1 flex items-center">
                  <q-chip :color="statusInfo.color" text-color="white" :icon="statusInfo.icon" dense size="sm">
                    {{ statusInfo.label }}
                  </q-chip>
                </div>
              </div>

              <!-- Departments -->
              <div class="col-12 col-sm-6">
                <div class="text-caption text-grey-7 text-uppercase" style="letter-spacing: 0.5px">Bộ phận đề xuất</div>
                <div class="text-body1 text-weight-medium">{{ item.department || '--' }}</div>
              </div>
              <div class="col-12 col-sm-6">
                 <div class="text-caption text-grey-7 text-uppercase" style="letter-spacing: 0.5px">Bộ phận sử dụng</div>
                 <div class="text-body1 text-weight-bold text-deep-purple">{{ item.using_department || '--' }}</div>
              </div>
            </div>

            <q-separator class="q-my-lg" />

            <!-- 2. Item Details -->
            <div class="row items-center q-mb-md">
               <q-icon name="shopping_bag" color="primary" size="sm" class="q-mr-sm" />
               <div class="text-subtitle1 text-weight-bold text-uppercase text-primary">2. Chi tiết hàng hóa</div>
            </div>

            <div class="bg-grey-1 q-pa-md rounded-borders q-mb-lg">
               <div class="row q-col-gutter-md">
                 <div class="col-12">
                   <div class="text-caption text-grey-7 text-uppercase">Tên hàng / Mô tả chi tiết</div>
                   <div class="text-h6 text-blue-grey-10">{{ item.item_name }}</div>
                 </div>
                 
                 <div class="col-12 col-sm-4">
                   <div class="text-caption text-grey-7 text-uppercase">Loại hàng</div>
                   <div class="text-body1 text-weight-medium">{{ item.category }}</div>
                 </div>
                 
                 <div class="col-12 col-sm-4">
                   <div class="text-caption text-grey-7 text-uppercase">Nhà cung cấp</div>
                   <div class="text-body1">{{ item.supplier_name || '--' }}</div>
                 </div>

                 <div class="col-12 col-sm-4">
                   <div class="text-caption text-grey-7 text-uppercase">Giá được duyệt</div>
                   <div class="text-h6 text-primary text-weight-bold">{{ formatPrice(item.approved_price) }}</div>
                 </div>
               </div>
            </div>

            <!-- 2b. Received Info (Visual Highlight) -->
            <div v-if="item.status === 'completed'" class="q-mb-lg bg-deep-purple-1 q-pa-md rounded-borders" style="border-left: 5px solid #673ab7">
                <div class="row items-center q-mb-sm">
                    <q-icon name="inventory" color="deep-purple" size="sm" class="q-mr-sm" />
                    <div class="text-subtitle1 text-weight-bold text-uppercase text-deep-purple">Thông tin nhận hàng</div>
                </div>
                <div class="text-caption text-grey-7">Thời gian nhận: {{ formatDate(item.received_at) }}</div>
                <div class="text-body1 q-mt-xs" style="white-space: pre-wrap;">{{ item.received_note || 'Không có ghi chú' }}</div>
            </div>

          </div>

          <!-- RIGHT COLUMN: Images (md-5) -->
          <div class="col-12 col-md-5 scroll" style="height: 100%; max-height: 80vh;">
            <div class="column q-gutter-y-lg">
                <!-- SECTION: REQUEST IMAGES -->
                <div>
                   <div class="row items-center q-mb-sm">
                        <q-icon name="description" color="primary" size="sm" class="q-mr-sm" />
                        <div class="text-subtitle2 text-weight-bold text-uppercase text-primary">Chứng từ yêu cầu ({{ requestImages.length }})</div>
                    </div>
                     <div v-if="!hasRequestImages" class="bg-grey-2 rounded-borders text-grey-6 flex flex-center q-pa-md">
                        <small>Không có ảnh chứng từ</small>
                    </div>
                    <q-carousel
                      v-else
                      animated
                      arrows
                      navigation
                      infinite
                      thumbnails
                      height="300px"
                      class="bg-grey-9 text-white rounded-borders shadow-2"
                      v-model="carouselSlide"
                    >
                      <q-carousel-slide 
                        v-for="(img, idx) in requestImages" 
                        :key="img.id" 
                        :name="idx"
                        class="flex flex-center q-pa-none"
                      >
                        <q-img
                          :src="getImageUrl(img.image_path)"
                          fit="contain"
                          class="full-height full-width cursor-pointer"
                          @click="openImageFullscreen(img)"
                        />
                      </q-carousel-slide>
                    </q-carousel>
                </div>

                <!-- SECTION: DELIVERY IMAGES -->
                <div v-if="hasDeliveryImages">
                   <div class="row items-center q-mb-sm">
                        <q-icon name="local_shipping" color="deep-purple" size="sm" class="q-mr-sm" />
                        <div class="text-subtitle2 text-weight-bold text-uppercase text-deep-purple">Ảnh thực tế / Bàn giao ({{ deliveryImages.length }})</div>
                    </div>
                    <div class="row q-col-gutter-sm">
                        <div v-for="img in deliveryImages" :key="img.id" class="col-4">
                            <q-img 
                                :src="getImageUrl(img.image_path)" 
                                ratio="1" 
                                class="rounded-borders cursor-pointer shadow-1"
                                @click="openImageFullscreen(img)"
                            >
                                <div class="absolute-bottom text-center text-caption q-pa-none" style="background: rgba(0,0,0,0.5)">
                                    Click xem
                                </div>
                            </q-img>
                        </div>
                    </div>
                </div>
            </div>
          </div>

        </div>
      </q-card-section>
      
      <q-separator />
      
      <q-card-actions align="right" class="q-pa-md bg-grey-1">
         <q-btn flat label="Đóng" color="grey-8" v-close-popup />
      </q-card-actions>

    </q-card>
  </q-dialog>
</template>
