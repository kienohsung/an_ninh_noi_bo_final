<template>
  <div class="asset-form-paper" :class="{ 'mode-print': mode === 'print' }">
    <!-- Main Bordered Container -->
    <div class="main-container">
      
      <!-- Row 1: Header Top (no bottom border) -->
      <div class="grid-row flex">
        <!-- Logo Box (no right border) -->
         <div class="q-pa-xs flex flex-center" style="width: 150px;">
            <img src="/ohsung_logo_v2.jpg" alt="Logo" style="height: 100px; max-width: 200%; object-fit: contain;" />
         </div>
         <!-- Spacer -->
         <div class="col-grow"></div>
        <!-- Ticket Number only -->
        <div class="flex column" style="width: 250px; align-items: flex-end;">
          <div class="q-pa-xs flex flex-center">
             <span class="text-italic" style="font-size: 12px;">{{ ticketNumberLabel }}</span>
          </div>
        </div>
      </div>

      <!-- Row 2: Title (no bottom border) -->
      <div class="grid-row q-pa-sm text-center">
         <div class="text-h5 text-weight-bold">GIẤY MANG TÀI SẢN RA CỔNG</div>
         <div class="text-subtitle1 text-weight-bold">(PROPERTY GATE PASS)</div>
      </div>

      <!-- Row 3: Date below title -->
      <div class="grid-row q-pa-xs flex justify-end">
         <div class="text-italic" style="font-size: 12px;">{{ formattedDateLabel }}</div>
      </div>

      <!-- Row 3: Delivery To -->
      <div class="grid-row border-bottom" style="display: flex;">
         <div class="q-pa-xs flex items-center col-grow">
            <span class="q-mr-xs">Delivery to/ Chuyển đến:</span>
            <div class="bg-yellow-2 col-grow q-px-sm">
               <input 
                 v-if="mode === 'edit'" 
                 v-model="localData.destination" 
                 class="paper-input full-width" 
                 placeholder="Nhập tên Nhà cung cấp ở đây"
               />
               <span v-else class="q-pl-xs">{{ localData.destination }}</span>
            </div>
         </div>
      </div>

      <!-- Row 6: User Info 1 -->
      <div class="grid-row border-bottom flex">
         <div class="col-6 border-right flex items-center q-pa-xs">
            <span class="q-mr-sm" style="white-space: nowrap;">Họ tên người mang ra:</span>
            <div class="col-grow q-px-sm text-weight-bold">{{ localData.full_name }}</div>
         </div>
         <div class="col-6 flex items-center q-pa-xs">
            <span class="q-mr-sm" style="white-space: nowrap;">Mã nhân viên:</span>
            <div class="col-grow q-px-sm text-weight-bold">{{ localData.employee_code }}</div>
         </div>
      </div>

      <!-- Row 6: Department + Return Dates -->
      <div class="grid-row border-bottom flex">
         <div class="col-12 flex items-center q-pa-xs">
            <span class="q-mr-sm" style="white-space: nowrap;">Bộ phận/ Department:</span>
            <div class="bg-yellow-2 col-grow q-px-sm">
               <input 
                 v-if="mode === 'edit'" 
                 v-model="localData.department" 
                 class="paper-input full-width" 
                 placeholder="Nhập bộ phận ở đây ..."
               />
               <span v-else class="text-weight-bold">{{ localData.department }}</span>
            </div>
         </div>
      </div>

      <!-- Row 7: Return Dates -->
      <div class="grid-row border-bottom flex">
         <div class="border-right flex column q-pa-xs" style="width: 50%;">
            <div class="text-caption q-mb-xs">Expected Return Date/ Ngày dự kiến trả:</div>
            <div class="bg-yellow-2 q-px-sm q-py-xs flex items-center justify-center full-width">
                <template v-if="mode === 'edit'">
                  <q-input borderless dense v-model="localData.estimated_datetime" mask="date" class="full-width text-center" style="padding: 0;">
                    <template v-slot:append>
                      <q-icon name="event" class="cursor-pointer">
                        <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                          <q-date v-model="localData.estimated_datetime" @update:model-value="onDateChange">
                            <div class="row items-center justify-end">
                              <q-btn v-close-popup label="Close" color="primary" flat />
                            </div>
                          </q-date>
                        </q-popup-proxy>
                      </q-icon>
                    </template>
                  </q-input>
                </template>
               <span v-else>{{ formatDate(localData.estimated_datetime) }}</span>
            </div>
         </div>
         <div class="flex column q-pa-xs" style="width: 50%;">
            <div class="text-caption q-mb-xs">Actual Return Date/ Ngày trả thực tế:</div>
            <div class="bg-yellow-2 q-px-sm q-py-xs flex items-center justify-center full-width">
               <span class="text-weight-bold">{{ formatDate(localData.check_in_back_time) }}</span>
            </div>
         </div>
      </div>

      <!-- Asset Table -->
      <div class="grid-row border-bottom" style="min-height: 300px; display: flex; flex-direction: column;">
         <table class="w-full paper-table">
            <thead>
               <tr class="bg-yellow-2">
                  <th class="border-right border-bottom" style="width: 50px;">STT<br>(No)</th>
                  <th class="border-right border-bottom">Tên hàng hóa<br>(Asset name)</th>
                  <th class="border-right border-bottom" style="width: 80px;">Số lượng<br>(Quantity)</th>
                  <th class="border-right border-bottom">Lý do<br>(Reason)</th>
                  <th class="border-bottom">Ghi chú<br>(Remarks)</th>
                  <th v-if="mode === 'edit'" class="no-print border-bottom" style="width: 40px;"></th>
               </tr>
            </thead>
            <tbody>
               <tr v-for="(item, index) in items" :key="index">
                  <td class="text-center border-right border-bottom">{{ index + 1 }}</td>
                  <td class="border-right border-bottom bg-yellow-2">
                     <textarea 
                        v-if="mode === 'edit'" 
                        v-model="item.name" 
                        class="paper-textarea" 
                        rows="1"
                        placeholder="Tên hàng hóa..."
                        @input="updateLocalData"
                     ></textarea>
                     <div v-else class="text-pre-wrap">{{ item.name }}</div>
                  </td>
                  <td class="border-right border-bottom text-center bg-yellow-2">
                     <input 
                        v-if="mode === 'edit'" 
                        v-model.number="item.quantity" 
                        type="number" 
                        class="paper-input text-center"
                        @input="updateLocalData"
                     />
                     <span v-else>{{ item.quantity }}</span>
                  </td>
                  <td class="border-right border-bottom bg-yellow-2">
                     <textarea 
                        v-if="mode === 'edit'" 
                        v-model="item.reason" 
                        class="paper-textarea" 
                        rows="1"
                        placeholder="Lý do..."
                        @input="updateLocalData"
                     ></textarea>
                     <div v-else class="text-pre-wrap">{{ item.reason }}</div>
                  </td>
                  <td class="border-bottom bg-yellow-2">
                     <textarea 
                        v-if="mode === 'edit'" 
                        v-model="item.remarks" 
                        class="paper-textarea" 
                        rows="1"
                        placeholder="Ghi chú..."
                        @input="updateLocalData"
                     ></textarea>
                     <div v-else class="text-pre-wrap">{{ item.remarks }}</div>
                  </td>
                  <td v-if="mode === 'edit'" class="text-center border-bottom no-print">
                     <q-btn icon="delete" flat dense color="negative" size="sm" @click="removeItem(index)" v-if="items.length > 1" />
                  </td>
               </tr>
               <!-- Filler rows -->
               <tr v-if="items.length < 5 && mode === 'print'" v-for="i in (5 - items.length)" :key="`empty-${i}`">
                  <td class="border-right border-bottom" style="height: 30px;"></td>
                  <td class="border-right border-bottom"></td>
                  <td class="border-right border-bottom"></td>
                  <td class="border-right border-bottom"></td>
                  <td class="border-bottom"></td>
               </tr>
            </tbody>
         </table>
         
         <!-- Add Button Area -->
         <div v-if="mode === 'edit'" class="q-pa-sm text-right bg-yellow-2 no-print">
            <q-btn label="Thêm dòng" icon="add" color="secondary" size="sm" @click="addItem" />
         </div>
         
         <!-- Large Page 1 Watermark if needed, but skipping for cleanliness -->
      </div>

      <!-- Signatures -->
      <div class="grid-row border-bottom">
         <table class="w-full paper-table">
            <thead>
               <tr>
                  <th class="border-right border-bottom">Người đề nghị<br>Requested by</th>
                  <th class="border-right border-bottom">P. Hành chính<br>GA Dept.</th>
                  <th class="border-right border-bottom">Trưởng bộ phận<br>Dept Manager</th>
                  <th class="border-right border-bottom">GĐ người Hàn<br>Korean Manager</th>
                  <th class="border-bottom">Approved by<br>General Director</th>
               </tr>
            </thead>
            <tbody>
               <tr style="height: 100px;">
                  <td class="border-right"></td>
                  <td class="border-right"></td>
                  <td class="border-right"></td>
                  <td class="border-right"></td>
                  <td></td>
               </tr>
               <tr>
                  <td class="border-right text-center text-weight-bold q-pb-sm">{{ localData.full_name }}</td>
                  <td class="border-right"></td>
                   <td class="border-right bg-yellow-2 text-center relative-position q-pb-sm">
                      <input 
                        v-if="mode === 'edit'" 
                        v-model="localData.vietnamese_manager_name" 
                        @input="updateLocalData"
                        class="paper-input text-center text-weight-bold" 
                        style="font-size: 11px;"
                        placeholder="Nhập tên quản lý người Việt"
                      />
                      <span v-else class="text-weight-bold" style="font-size: 18px;">{{ localData.vietnamese_manager_name }}</span>
                      <div class="text-caption">Vietnamese manager</div>
                   </td>
                   <td class="border-right bg-yellow-2 text-center relative-position q-pb-sm">
                      <input 
                        v-if="mode === 'edit'" 
                        v-model="localData.korean_manager_name" 
                        @input="updateLocalData"
                        class="paper-input text-center text-weight-bold" 
                        style="font-size: 11px;"
                        placeholder="Nhập tên quản lý người Hàn"
                      />
                     <span v-else class="text-weight-bold" style="font-size: 18px;">{{ localData.korean_manager_name }}</span>
                     <div class="text-caption">Korean manager</div>
                  </td>
                  <td></td>
               </tr>
            </tbody>
         </table>
      </div>

      <!-- Footer -->
      <div class="grid-row flex">
         <div class="col-grow border-right q-pa-sm" style="flex: 1;">
            <div class="text-weight-bold q-mb-xs">LƯU Ý: Cần có đầy đủ chữ kí, ghi họ tên bằng tiếng anh của Trưởng bộ phận và Giám đốc người Hàn.</div>
            <div class="text-italic q-mt-md">Effective from 01 Dec 2025</div>
         </div>
         <div class="col-grow" style="flex: 1; display: flex; flex-direction: column;">
            <div class="border-bottom q-pa-xs text-center bg-grey-2">
               Xác nhận của Bảo vệ/ Confirmed by Security
            </div>
            <div class="col-grow" style="min-height: 80px;"></div>
            <div class="flex border-top">
               <div class="col-6 border-right q-pa-xs text-center">Date/Ngày:.............</div>
               <div class="col-6 q-pa-xs text-center">Time/Giờ:.......</div>
            </div>
         </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue';
import { date } from 'quasar';

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  mode: {
    type: String,
    default: 'edit' // 'edit' or 'print'
  },
  assetId: {
    type: [Number, String],
    default: null
  }
});

const emit = defineEmits(['update:modelValue']);

const localData = ref({ ...props.modelValue });
const items = ref([]);

function initItems() {
  if (props.modelValue.asset_description && props.modelValue.asset_description.includes('\n')) {
    const names = props.modelValue.asset_description.split('\n');
    const reasons = (props.modelValue.description_reason || '').split('\n');
    // Distribute quantity? For now assume total quantity is for the batch, or 1 per item.
    // The backend only has one quantity field. This is a limitation.
    // We will display the total quantity in the first row or try to split it?
    // Let's assume quantity is 1 for each extra row if not specified.
    // Actually, to keep it simple and safe, we put the first item with the total quantity, others 0 or 1?
    // Let's just put the name/reason in rows. Quantity is tricky.
    // We'll just put the total quantity in the first row for now, and let user edit.
    
    items.value = names.map((name, index) => ({
      name: name,
      quantity: index === 0 ? props.modelValue.quantity : 1,
      reason: reasons[index] || '',
      remarks: ''
    }));
  } else {
     items.value = [{
       name: props.modelValue.asset_description || '',
       quantity: props.modelValue.quantity || 1,
       reason: props.modelValue.description_reason || '',
       remarks: ''
    }];
  }
}

watch(() => props.modelValue, (newVal) => {
  if (newVal && props.mode === 'print') {
    // Only update in print mode (for viewing existing records)
    localData.value = { ...newVal };
    initItems();
  }
  // In edit mode, don't auto-reset to avoid losing user input
});

function updateLocalData() {
  const names = items.value.map(i => i.name).join('\n');
  const reasons = items.value.map(i => i.reason).join('\n');
  // Sum quantity? Or just take the first? 
  // If we want to support multiple quantities, we need to change backend or sum them up.
  const totalQuantity = items.value.reduce((sum, i) => sum + (Number(i.quantity) || 0), 0);

  localData.value.asset_description = names;
  localData.value.description_reason = reasons;
  localData.value.quantity = totalQuantity;

  emit('update:modelValue', localData.value);
}

function addItem() {
  items.value.push({ name: '', quantity: 1, reason: '', remarks: '' });
  updateLocalData();
}

function removeItem(index) {
  items.value.splice(index, 1);
  updateLocalData();
}

// Removed deep watch - updates are handled by onDateChange and updateLocalData
// to avoid race conditions and circular updates

function onDateChange(newDate) {
  localData.value.estimated_datetime = newDate;
  emit('update:modelValue', { ...localData.value });
}

onMounted(() => {
  initItems();
});

const formattedDate = computed(() => {
  return date.formatDate(new Date(), 'DD/MM/YYYY');
});

const ticketNumber = computed(() => {
  const year = new Date().getFullYear();
  if (!props.assetId) {
    return `TS/${year}/...`;
  }
  const idStr = String(props.assetId).padStart(3, '0');
  return `TS/${year}/${idStr}.0`;
});

const ticketNumberLabel = computed(() => {
  return `Số phiếu: ${ticketNumber.value}`;
});

const formattedDateLabel = computed(() => {
  const now = new Date();
  const day = now.getDate();
  const month = now.getMonth() + 1;
  const year = now.getFullYear();
  return `Ohsung vina Hải phòng, ngày ${day} tháng ${month} năm ${year}`;
});

const hasReturn = computed(() => {
  return !!localData.value.estimated_datetime;
});

function formatDate(val) {
  if (!val) return '';
  return date.formatDate(val, 'YYYY/MM/DD');
}
</script>

<style scoped>
.asset-form-paper {
  width: 210mm;
  min-height: 297mm;
  background: white;
  padding: 10mm;
  margin: 0 auto;
  box-sizing: border-box;
  font-family: 'Times New Roman', serif;
  color: black;
  font-size: 14px;
}

.main-container {
  border: 3px solid black;
  width: 100%;
  height: 100%;
}

.mode-print.asset-form-paper {
  border: none;
  margin: 0;
  padding: 0;
  width: 100%;
}

/* Grid & Utils */
.grid-row { width: 100%; }
.border-bottom { border-bottom: 1px solid black; }
.border-top { border-top: 1px solid black; }
.border-left { border-left: 1px solid black; }
.border-right { border-right: 1px solid black; }
.bg-yellow-2 { background-color: #ffff00 !important; } /* Bright yellow as in image */
.col-grow { flex-grow: 1; }
.w-full { width: 100%; }

/* Tables */
.paper-table { border-collapse: collapse; width: 100%; }
.paper-table th, .paper-table td { padding: 5px; vertical-align: middle; }

/* Inputs */
.paper-input {
  width: 100%;
  border: none;
  background: transparent;
  outline: none;
  font-family: inherit;
  font-size: inherit;
}
.paper-textarea {
  width: 100%;
  border: none;
  background: transparent;
  outline: none;
  resize: none;
  font-family: inherit;
  font-size: inherit;
  overflow: hidden;
}

/* Print Specifics */
@media print {
  @page { 
    size: A4 portrait; 
    margin: 0; /* Remove browser default margins */
  }
  
  /* Reset everything */
  * {
    overflow: visible !important;
  }
  
  /* Hide page layout */
  #q-app > *:not(.q-dialog),
  body > *:not(#q-app),
  .q-layout,
  .q-drawer,
  .q-header,
  .q-page-container > *:not(.asset-print-dialog) {
    display: none !important;
    visibility: hidden !important;
  }
  
  /* Hide dialog chrome */
  .q-dialog__backdrop,
  .q-card-section.row.items-center,
  .no-print,
  button,
  .q-btn,
  .q-icon,
  .q-space,
  h6,
  .text-h6,
  div[class*="row items-center"] {
    display: none !important;
  }
  
  /* Hide scrollbars */
  ::-webkit-scrollbar,
  * {
    scrollbar-width: none !important;
  }
  
  /* Show print dialog */
  .asset-print-dialog,
  .asset-print-dialog .q-dialog__inner,
  .asset-print-dialog .print-card {
    display: block !important;
    visibility: visible !important;
    position: static !important;
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    box-shadow: none !important;
  }
  
  /* Form for PDF export - simple and clean */
  .asset-form-paper {
    display: block !important;
    visibility: visible !important;
    width: 100% !important;
    max-width: 210mm !important;
    margin: 0 !important;
    padding: 0 5mm !important; /* 0.5cm left/right margins */
    box-shadow: none !important;
    font-size: 110% !important; /* Increase all fonts by ~1 size */
  }
  
  .main-container {
    border: 2px solid black !important;
    width: 100% !important;
  }

  
  /* Remove yellow backgrounds for PDF */
  .bg-yellow-2,
  td.bg-yellow-2,
  th.bg-yellow-2 { 
    background-color: white !important;
    print-color-adjust: exact;
    -webkit-print-color-adjust: exact;
  }
  
  /* Show input values */
  input {
    border: none !important;
    background: transparent !important;
    color: black !important;
    font-weight: bold !important;
  }
  
  /* Force borders */
  .border-bottom { border-bottom: 1px solid black !important; }
  .border-top { border-top: 1px solid black !important; }
  .border-left { border-left: 1px solid black !important; }
  .border-right { border-right: 1px solid black !important; }
}
</style>
