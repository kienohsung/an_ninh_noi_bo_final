<!-- File path: frontend/src/pages/RegisterGuest.vue -->
<!-- CHỈNH SỬA LAYOUT: Di chuyển các tùy chọn lại gần nhau -->
<template>
  <q-page padding>
    <q-card>
      <!-- REMOVED HEADER SECTION -->
      <q-card-section>
          <!-- WARNING BANNER -->
           <div class="q-mb-md text-center">
               <div class="blinking-warning text-h6 text-red text-weight-bold q-pa-md" style="border: 2px dashed red; border-radius: 8px; background-color: #fff0f0;">
                   CHÚ Ý: KHÁCH MANG LAPTOP VÀO PHẢI THÔNG BÁO VỚI IT, HOẶC GHI CHÚ VÀO MỤC CHI TIẾT.<br>
                   KHÔNG THÔNG BÁO SẼ BỊ LIÊN ĐỚI KHI CÓ KHIẾU NẠI XẢY RA!
               </div>
           </div>

          <q-form @submit="onSubmit" class="q-gutter-y-md">

          <!-- SỬA ĐỔI: Gom nhóm các tùy chọn đăng ký đặc biệt -->
          <div class="q-pa-sm bg-grey-2 rounded-borders">
            <div class="row items-center q-gutter-x-md">
              <q-toggle v-model="isBulk" label="Đăng ký theo đoàn" />
              <q-toggle v-model="isLongTerm" label="Khách thường xuyên (dài hạn)" />
              <q-toggle v-model="hasLaptop" color="red" label="Khách mang Laptop" />
              <q-space />
              <div>
                  <q-btn 
                    icon="qr_code_scanner" 
                    label="Quét CCCD" 
                    color="secondary" 
                    @click="triggerCccdInput"
                    :loading="isScanning"
                    dense
                  >
                    <q-tooltip>Tải ảnh CCCD để điền thông tin tự động</q-tooltip>
                  </q-btn>
                  <input 
                    type="file" 
                    ref="cccdInputRef" 
                    @change="handleCccdUpload" 
                    accept="image/*" 
                    multiple 
                    hidden 
                  />
              </div>
            </div>

            <q-slide-transition>
              <div v-if="isLongTerm" class="q-mt-md">
                <div class="row q-col-gutter-md">
                    <div class="col-12 col-sm-6">
                        <q-input dense outlined v-model="longTermDates.from" mask="date" label="Từ ngày">
                            <template v-slot:append>
                                <q-icon name="event" class="cursor-pointer">
                                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                                        <q-date v-model="longTermDates.from">
                                            <div class="row items-center justify-end"><q-btn v-close-popup label="Đóng" color="primary" flat /></div>
                                        </q-date>
                                    </q-popup-proxy>
                                </q-icon>
                            </template>
                        </q-input>
                    </div>
                    <div class="col-12 col-sm-6">
                        <q-input dense outlined v-model="longTermDates.to" mask="date" label="Đến ngày">
                            <template v-slot:append>
                                <q-icon name="event" class="cursor-pointer">
                                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                                        <q-date v-model="longTermDates.to">
                                            <div class="row items-center justify-end"><q-btn v-close-popup label="Đóng" color="primary" flat /></div>
                                        </q-date>
                                    </q-popup-proxy>
                                </q-icon>
                            </template>
                        </q-input>
                    </div>
                </div>
              </div>
            </q-slide-transition>
          </div>
          <!-- KẾT THÚC SỬA ĐỔI -->


          <!-- Form đăng ký theo đoàn -->
          <div v-if="isBulk">
            <div class="text-caption q-mb-sm">Nhập thông tin chung cho đoàn:</div>
            <!-- THÊM MỚI: Bổ sung estimated_time, thay đổi grid thành md-4 -->
            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <q-input 
                  v-model="form.supplier_name" 
                  label="Nhà cung cấp *" 
                  dense 
                  outlined
                  required
                  :rules="[val => !!val || 'Vui lòng nhập nhà cung cấp']"
                >
                  <template v-slot:append>
                    <q-btn round dense flat icon="search" @click="openSearchDialog('supplier', 'main')" />
                  </template>
                </q-input>
              </div>
              <div class="col-12 col-md-6">
                 <q-input v-model="form.license_plate" label="Biển số" dense outlined>
                  <template v-slot:append>
                    <q-btn round dense flat icon="search" @click="openSearchDialog('plate', 'main')" />
                  </template>
                </q-input>
              </div>
              
              <!-- BẮT ĐẦU NÂNG CẤP: Thay thế input time bằng DateTime Picker (Form Đoàn) -->
              <!-- === CẢI TIẾN 3: Làm datetime bắt buộc === -->
              <div class="col-12 col-md-6">
                <q-input 
                  v-model="formattedEstimatedDatetime" 
                  label="Ngày & Giờ dự kiến *" 
                  dense 
                  outlined 
                  readonly 
                  required
                  :rules="[val => !!val || 'Vui lòng chọn ngày giờ dự kiến']"
                  hint="Bắt buộc"
                >
                  <template v-slot:append>
                    <!-- Thay đổi @click để gọi hàm chuẩn bị proxy -->
                    <q-icon name="event" class="cursor-pointer" @click="openDateTimePickerProxy('main')">
                      <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                        <div class="q-pa-md" style="min-width: 300px">
                          <div class="q-gutter-md">
                            <q-date v-model="proxyDate" mask="YYYY-MM-DD" />
                            <q-time v-model="proxyTime" mask="HH:mm" format24h />
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
              </div>
              <!-- KẾT THÚC NÂNG CẤP -->

              <div class="col-12 col-md-6">
                <q-input 
                  type="textarea" 
                  v-model="form.reason" 
                  label="Chi tiết / Lý do *" 
                  outlined 
                  dense 
                  rows="1"
                  required
                  :rules="[val => !!val || 'Vui lòng nhập nội dung công việc']"
                />
              </div>
            </div>
            <q-separator class="q-my-md" />
            <div class="text-caption q-mb-sm">Thêm từng người trong đoàn:</div>
            <div v-for="(person, index) in form.guests" :key="index" class="row items-center q-col-gutter-sm q-mb-sm">
              <div class="col-12 col-md-6"><q-input v-model="person.full_name" :label="`Họ tên người ${index + 1}`" dense outlined required /></div>
              <div class="col-12 col-md-5"><q-input v-model="person.id_card_number" :label="`CCCD người ${index + 1}`" dense outlined /></div>
              <div class="col-12 col-md-1 text-center"><q-btn flat dense icon="remove_circle" color="negative" @click="removePerson(index)" v-if="form.guests.length > 1" /></div>
            </div>
            <q-btn flat icon="add" label="Thêm người" @click="addPerson" />
          </div>

          <!-- Form đăng ký 1 người -->
          <!-- THÊM MỚI: Bổ sung estimated_time, thay đổi grid thành md-4 -->
          <div v-else class="row q-col-gutter-md">
            <div class="col-12 col-md-6"><q-input v-model="form.full_name" label="Họ tên *" dense outlined required /></div>
            <div class="col-12 col-md-6"><q-input v-model="form.id_card_number" label="CCCD" dense outlined /></div>
            
            <!-- <div class="col-12 col-md-6"><q-input v-model="form.company" label="Công ty / Phòng ban" dense outlined /></div> -->
            <div class="col-12 col-md-6">
                 <q-input v-model="form.license_plate" label="Biển số" dense outlined>
                  <template v-slot:append>
                    <q-btn round dense flat icon="search" @click="openSearchDialog('plate', 'main')" />
                  </template>
                </q-input>
            </div>

            <div class="col-12 col-md-6">
              <q-input 
                v-model="form.supplier_name" 
                label="Nhà cung cấp *" 
                dense 
                outlined
                required
                :rules="[val => !!val || 'Vui lòng nhập nhà cung cấp']"
              >
                <template v-slot:append>
                  <q-btn round dense flat icon="search" @click="openSearchDialog('supplier', 'main')" />
                </template>
              </q-input>
            </div>
            
            <!-- BẮT ĐẦU NÂNG CẤP: Thay thế input time bằng DateTime Picker (Form 1 người) -->
            <!-- === CẢI TIẾN 3: Làm datetime bắt buộc === -->
            <div class="col-12 col-md-6">
               <q-input 
                v-model="formattedEstimatedDatetime" 
                label="Ngày & Giờ dự kiến *" 
                dense 
                outlined 
                readonly 
                required
                :rules="[val => !!val || 'Vui lòng chọn ngày giờ dự kiến']"
                hint="Bắt buộc"
              >
                <template v-slot:append>
                  <!-- Thay đổi @click để gọi hàm chuẩn bị proxy -->
                  <q-icon name="event" class="cursor-pointer" @click="openDateTimePickerProxy('main')">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <div class="q-pa-md" style="min-width: 300px">
                        <div class="q-gutter-md">
                          <q-date v-model="proxyDate" mask="YYYY-MM-DD" />
                          <q-time v-model="proxyTime" mask="HH:mm" format24h />
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
            </div>
            <!-- KẾT THÚC NÂNG CẤP -->

            <div class="col-12">
                <q-input 
                  v-model="form.reason" 
                  label="Lý do / Chi tiết *" 
                  dense 
                  outlined
                  required
                  :rules="[val => !!val || 'Vui lòng nhập nội dung công việc']"
                />
            </div>

            <div class="col-12">
              <q-file
                v-model="imageFiles"
                label="Chọn hình ảnh chân dung (tối đa 5 ảnh)"
                multiple
                accept="image/*"
                dense
                outlined
                use-chips
                clearable
                @rejected="onFileRejected"
                :max-files="5"
                :disable="isLongTerm"
              >
                <template v-slot:prepend>
                  <q-icon name="attach_file" />
                </template>
              </q-file>
            </div>
          </div>

          <div class="col-12 q-mt-md">
            <q-btn type="submit" label="Đăng ký" color="primary" :loading="isSubmitting" class="full-width" size="md"/>
          </div>
        </q-form>
      </q-card-section>
    </q-card>

    <!-- PHẦN LỊCH SỬ GIỮ NGUYÊN -->
    <q-card class="q-mt-md">
      <q-card-section class="row items-center justify-between q-gutter-sm">
        <div class="text-subtitle1">Lịch sử khách đã đăng ký</div>
        <div class="row items-center q-gutter-sm">
          <q-input dense outlined v-model="q" placeholder="Tìm kiếm..." style="min-width: 280px" clearable @clear="load" @keyup.enter="load">
            <template #append><q-icon name="search" class="cursor-pointer" @click="load" /></template>
          </q-input>
          
          <!-- NÂNG CẤP: Nút Export riêng biệt -->
          <q-btn 
            color="secondary" 
            icon="download" 
            label="Export" 
            @click="openExportDialog"
          />
          <!-- KẾT THÚC NÂNG CẤP -->

          <q-btn-dropdown color="primary" label="Actions" v-if="isAdmin || isManager">
            <q-list>
              <q-item clickable v-close-popup @click="() => fileInputRef.click()">
                <q-item-section avatar><q-icon name="upload_file" /></q-item-section>
                <q-item-section>Import Excel</q-item-section>
              </q-item>
              <q-item clickable v-close-popup @click="deleteOldData" v-if="isAdmin">
                <q-item-section avatar><q-icon name="delete_sweep" /></q-item-section>
                <q-item-section>Xóa dữ liệu cũ</q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
          <q-btn label="Xóa dữ liệu" color="negative" @click="clearData" v-if="isAdmin" />
          <input type="file" ref="fileInputRef" @change="handleImport" accept=".xlsx, .xls" style="display:none" />
        </div>
      </q-card-section>
      <q-separator />
      <q-card-section>
         <q-table :rows="rows" :columns="columns" row-key="id" flat dense @row-click="onRowClick">
          <template #body-cell-thumbnail="props">
            <q-td :props="props">
              <q-img
                v-if="props.row.images && props.row.images.length > 0"
                :src="getImgUrl(props.row.images[0].image_path)"
                style="width: 50px; height: 50px; border-radius: 4px; cursor: pointer;"
                fit="cover"
                @click.stop="openFullImageViewer(props.row.images[0].image_path)"
              />
            </q-td>
          </template>
           <template #body-cell-status="props">
            <q-td :props="props">
              <q-chip 
                :color="props.row.status === 'checked_in' ? 'positive' : props.row.status === 'checked_out' ? 'grey' : 'orange'" 
                text-color="white" 
                dense
              >
                {{ props.row.status === 'checked_in' ? 'ĐÃ VÀO' : props.row.status === 'checked_out' ? 'ĐÃ RA' : 'CHƯA VÀO' }}
              </q-chip>
            </q-td>
          </template>
          
          <!-- BẮT ĐẦU NÂNG CẤP: Định dạng ô Ngày & Giờ dự kiến -->
          <template #body-cell-estimated_datetime="props">
            <q-td :props="props">
              <q-chip 
                v-if="props.value" 
                icon="schedule" 
                :label="quasarDate.formatDate(quasarDate.addToDate(props.value, { hours: 7 }), 'DD/MM HH:mm')" 
                dense 
                outline 
                size="sm"
                color="blue-grey" 
              />
            </q-td>
          </template>
          <!-- KẾT THÚC NÂNG CẤP -->

          <template #body-cell-actions="props">
            <q-td :props="props">
              <q-btn flat dense icon="edit" @click.stop="editRow(props.row)" :disable="auth.user?.role === 'staff' && props.row.status !== 'pending'">
                <q-tooltip v-if="auth.user?.role === 'staff' && props.row.status !== 'pending'">Không thể sửa khi khách đã vào</q-tooltip>
              </q-btn>
              <!-- RE-REGISTER BUTTON -->
              <q-btn flat dense icon="history" color="info" @click.stop="reRegister(props.row)">
                <q-tooltip>Đăng ký lại (sử dụng thông tin cũ)</q-tooltip>
              </q-btn>
              <q-btn flat dense icon="delete" color="negative" @click.stop="delRow(props.row)" :disable="auth.user?.role === 'staff' && props.row.status !== 'pending'">
                <q-tooltip v-if="auth.user?.role === 'staff' && props.row.status !== 'pending'">Không thể xóa khi khách đã vào</q-tooltip>
              </q-btn>
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>

    <!-- CÁC DIALOG GIỮ NGUYÊN -->
    <q-dialog v-model="showEditDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Sửa thông tin khách</div>
        </q-card-section>
        <q-separator/>
        <q-card-section>
          <q-form @submit="onUpdateSubmit" class="q-gutter-md">
            <q-input v-model="editForm.full_name" label="Họ tên" dense outlined required />
            <q-input v-model="editForm.id_card_number" label="CCCD" dense outlined />
            
            <!-- BẮT ĐẦU NÂNG CẤP: Thêm DateTime Picker vào Dialog Sửa -->
            <q-input 
              v-model="formattedEditEstimatedDatetime" 
              label="Ngày & Giờ dự kiến" 
              dense 
              outlined 
              readonly 
              clearable 
              @clear="editForm.estimated_datetime = null"
              hint="Tùy chọn"
            >
              <template v-slot:append>
                <!-- Thay đổi @click để gọi hàm chuẩn bị proxy (target 'edit') -->
                <q-icon name="event" class="cursor-pointer" @click="openDateTimePickerProxy('edit')">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <div class="q-pa-md" style="min-width: 300px">
                      <div class="q-gutter-md">
                        <q-date v-model="proxyDate" mask="YYYY-MM-DD" />
                        <q-time v-model="proxyTime" mask="HH:mm" format24h />
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
            <!-- KẾT THÚC NÂNG CẤP -->

             <q-input v-model="editForm.supplier_name" label="Nhà cung cấp" dense outlined>
                <template v-slot:append>
                  <q-btn round dense flat icon="search" @click="openSearchDialog('supplier', 'edit')" />
                </template>
              </q-input>
              <q-input v-model="editForm.license_plate" label="Biển số" dense outlined>
                <template v-slot:append>
                  <q-btn round dense flat icon="search" @click="openSearchDialog('plate', 'edit')" />
                </template>
              </q-input>
            <q-input type="textarea" v-model="editForm.reason" label="Chi tiết" outlined dense/>

            <div class="q-mt-md">
              <div class="text-subtitle2">Quản lý hình ảnh</div>
              <div v-if="editForm.images && editForm.images.length > 0" class="q-gutter-sm row items-start">
                <div v-for="image in editForm.images" :key="image.id" class="q-pa-xs" style="position: relative;">
                  <q-img :src="getImgUrl(image.image_path)" style="width: 100px; height: 100px; border-radius: 4px;" />
                  <q-btn
                    round
                    dense
                    color="negative"
                    icon="delete"
                    size="sm"
                    @click="deleteImage(image)"
                    style="position: absolute; top: 0; right: 0;"
                  />
                </div>
              </div>
              <div v-else class="text-grey">Không có hình ảnh.</div>
              <q-file
                v-model="newImageFiles"
                label="Thêm ảnh mới"
                multiple
                accept="image/*"
                dense
                outlined
                use-chips
                clearable
                class="q-mt-md"
                :max-files="5 - (editForm.images ? editForm.images.length : 0)"
              >
                <template v-slot:prepend>
                  <q-icon name="add_a_photo" />
                </template>
              </q-file>
            </div>

            <div class="row justify-end q-gutter-sm q-mt-lg">
                <q-btn label="Hủy" flat v-close-popup />
                <q-btn type="submit" label="Cập nhật" color="primary" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>



    <q-dialog v-model="showDetailsDialog">
      <q-card style="min-width: 60vw; max-width: 800px;">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6">Chi tiết khách</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>
        <q-separator/>

        <q-card-section v-if="activeGuest">
            <div class="row q-col-gutter-md">
                <div class="col-12 col-md-6">
                    <q-list bordered separator>
                        <q-item><q-item-section><q-item-label overline>Họ tên</q-item-label><q-item-label>{{ activeGuest.full_name }}</q-item-label></q-item-section></q-item>
                        <q-item><q-item-section><q-item-label overline>CCCD</q-item-label><q-item-label>{{ activeGuest.id_card_number }}</q-item-label></q-item-section></q-item>
                        
                        <!-- BẮT ĐẦU NÂNG CẤP: Hiển thị Ngày & Giờ dự kiến trong chi tiết -->
                        <q-item v-if="activeGuest.estimated_datetime">
                          <q-item-section>
                            <q-item-label overline>Ngày & Giờ dự kiến</q-item-label>
                            <!-- Định dạng lại cho đẹp -->
                            <q-item-label>{{ quasarDate.formatDate(activeGuest.estimated_datetime, 'HH:mm - DD/MM/YYYY') }}</q-item-label>
                          </q-item-section>
                        </q-item>
                        <!-- KẾT THÚC NÂNG CẤP -->

                        <q-item><q-item-section><q-item-label overline>Nhà cung cấp</q-item-label><q-item-label>{{ activeGuest.supplier_name }}</q-item-label></q-item-section></q-item>
                        <q-item><q-item-section><q-item-label overline>Biển số</q-item-label><q-item-label>{{ activeGuest.license_plate }}</q-item-label></q-item-section></q-item>
                        <q-item><q-item-section><q-item-label overline>Người đăng ký</q-item-label><q-item-label>{{ activeGuest.registered_by_name }}</q-item-label></q-item-section></q-item>
                        <q-item><q-item-section><q-item-label overline>Chi tiết</q-item-label><q-item-label style="white-space: pre-wrap;">{{ activeGuest.reason }}</q-item-label></q-item-section></q-item>
                    </q-list>
                </div>
                <div class="col-12 col-md-6">
                    <div class="text-overline q-mb-sm">Hình ảnh</div>
                     <q-carousel
                        v-if="activeGuest.images && activeGuest.images.length > 0"
                        swipeable
                        animated
                        v-model="slide"
                        thumbnails
                        infinite
                        arrows
                        navigation
                        height="400px"
                        class="bg-grey-2 rounded-borders"
                        >
                        <q-carousel-slide
                           v-for="(image, index) in activeGuest.images"
                           :key="image.id"
                           :name="index"
                           :img-src="getImgUrl(image.image_path)"
                           @click="openFullImageViewer(image.image_path)"
                           class="cursor-pointer"
                        />
                    </q-carousel>
                    <div v-else class="text-grey-7">Không có hình ảnh.</div>
                </div>
            </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <q-dialog v-model="showFullImageDialog">
      <q-card style="width: 90vw; max-width: 90vw;">
        <q-card-section class="q-pa-none">
          <q-img :src="fullImageUrl" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Đóng" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="showSupplierSearch">
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">Chọn nhà cung cấp</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-list bordered separator>
            <q-item clickable v-ripple v-for="name in suggestions.supplier_names" :key="name" @click="selectValue('supplier', name)">
              <q-item-section>{{ name }}</q-item-section>
            </q-item>
            <q-item v-if="!suggestions.supplier_names.length">
              <q-item-section class="text-grey">Không có gợi ý.</q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Đóng" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="showPlateSearch">
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">Chọn biển số</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-list bordered separator>
             <q-item clickable v-ripple v-for="plate in suggestions.license_plates" :key="plate" @click="selectValue('plate', plate)">
              <q-item-section>{{ plate }}</q-item-section>
            </q-item>
            <q-item v-if="!suggestions.license_plates.length">
              <q-item-section class="text-grey">Không có gợi ý.</q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Đóng" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- NÂNG CẤP: Dialog Export -->
    <q-dialog v-model="showExportDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Xuất dữ liệu</div>
        </q-card-section>
        <q-separator />
        <q-card-section class="q-gutter-md">
          <div class="row q-col-gutter-sm">
            <div class="col-12 col-sm-6">
              <q-input dense outlined v-model="exportFilters.start_date" mask="date" label="Từ ngày">
                <template v-slot:append>
                  <q-icon name="event" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date v-model="exportFilters.start_date">
                        <div class="row items-center justify-end"><q-btn v-close-popup label="Đóng" color="primary" flat /></div>
                      </q-date>
                    </q-popup-proxy>
                  </q-icon>
                </template>
              </q-input>
            </div>
            <div class="col-12 col-sm-6">
              <q-input dense outlined v-model="exportFilters.end_date" mask="date" label="Đến ngày">
                <template v-slot:append>
                  <q-icon name="event" class="cursor-pointer">
                    <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                      <q-date v-model="exportFilters.end_date">
                        <div class="row items-center justify-end"><q-btn v-close-popup label="Đóng" color="primary" flat /></div>
                      </q-date>
                    </q-popup-proxy>
                  </q-icon>
                </template>
              </q-input>
            </div>
          </div>

          <q-select
            v-if="isAdmin || isManager"
            dense
            outlined
            v-model="exportFilters.registrant"
            :options="userOptions"
            option-label="full_name"
            option-value="id"
            label="Người đăng ký"
            clearable
            emit-value
            map-options
            use-input
            @filter="filterUsers"
          />

          <q-select
            dense
            outlined
            v-model="exportFilters.supplier_name"
            :options="filteredSupplierOptions"
            label="Nhà cung cấp"
            clearable
            use-input
            @filter="filterSuppliers"
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Hủy" color="primary" v-close-popup />
          <q-btn label="Export" color="secondary" @click="executeExport" :loading="isExporting" />
        </q-card-actions>
      </q-card>
    </q-dialog>
    <!-- KẾT THÚC NÂNG CẤP -->

  </q-page>
</template>

<script setup>
import { reactive, ref, onMounted, computed, watch } from 'vue'
import { useQuasar, exportFile as qExportFile, date as quasarDate } from 'quasar'
import api from '../api'
import { useAuthStore } from '../stores/auth'
import { uploadMultipleImages } from '../utils/imageUpload'
import { useCCCDScanner } from '../composables/useCCCDScanner'
import { useGuestForm } from '../composables/useGuestForm'

const $q = useQuasar()
const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role === 'admin')
const isManager = computed(() => auth.user?.role === 'manager')

// --- Composables ---
const { isScanning, extractInfo } = useCCCDScanner()
const { 
  form, 
  isBulk, 
  isLongTerm, 
  longTermDates, 
  imageFiles, 
  resetForm, 
  addGuestToBulk: addPerson, 
  removeGuestFromBulk: removePerson, 
  validateForm 
} = useGuestForm()

// --- Local State ---
const rows = ref([])
const q = ref('')
const fileInputRef = ref(null)
const suggestions = reactive({ companies: [], license_plates: [], supplier_names: [] })
const showEditDialog = ref(false)
const isSubmitting = ref(false)
const showDetailsDialog = ref(false)
const activeGuest = ref(null)
const slide = ref(0)
const showFullImageDialog = ref(false)
const fullImageUrl = ref('')
const showSupplierSearch = ref(false)
const showPlateSearch = ref(false)
let searchTargetForm = 'main'; 
const cccdInputRef = ref(null);

// Edit Form State (Local)
const editForm = reactive({
  id: null, full_name: '', id_card_number: '', company: '',
  reason: '', license_plate: '', supplier_name: '', images: [],
  estimated_datetime: null
})
const newImageFiles = ref([])

// --- Export Logic ---
const showExportDialog = ref(false)
const isExporting = ref(false)
const exportFilters = reactive({
  start_date: '',
  end_date: '',
  registrant: null,
  supplier_name: null
})
const userOptions = ref([])
const allUsers = ref([]) 
const filteredSupplierOptions = ref([])

// --- DateTime Picker Logic ---
const proxyDate = ref(null)
const proxyTime = ref(null)

const formattedEstimatedDatetime = computed(() => {
  if (!form.estimated_datetime) return null;
  const d = new Date(form.estimated_datetime);
  return quasarDate.formatDate(d, 'DD/MM/YYYY HH:mm');
});

const formattedEditEstimatedDatetime = computed(() => {
  if (!editForm.estimated_datetime) return null;
  const d = new Date(editForm.estimated_datetime);
  return quasarDate.formatDate(d, 'DD/MM/YYYY HH:mm');
});

function openDateTimePickerProxy(target) {
  searchTargetForm = target;
  let dStr = null;

  if (target === 'main') {
    dStr = form.estimated_datetime;
  } else if (target === 'edit') {
    dStr = editForm.estimated_datetime;
  }

  let d;
  if (dStr) {
    d = new Date(dStr);
  } else {
    d = new Date();
  }
  proxyDate.value = quasarDate.formatDate(d, 'YYYY-MM-DD');
  proxyTime.value = quasarDate.formatDate(d, 'HH:mm');
}

function setEstimatedDatetime() {
  if (proxyDate.value) {
    const timeStr = proxyTime.value || '00:00';
    const newVal = `${proxyDate.value}T${timeStr}:00`;
    const d = new Date(newVal);
    const utcIsoString = d.toISOString();

    if (searchTargetForm === 'main') {
      form.estimated_datetime = utcIsoString;
    } else if (searchTargetForm === 'edit') {
      editForm.estimated_datetime = utcIsoString;
    }
  }
}


const hasLaptop = ref(false);

watch(hasLaptop, (val) => {
  const laptopText = " - Khách mang Laptop";
  if (val) {
    if (!form.reason.includes(laptopText)) {
      form.reason += laptopText;
    }
  } else {
    form.reason = form.reason.replace(laptopText, "");
  }
});

watch(isLongTerm, (newVal) => {
  if (newVal) {
    imageFiles.value = [];
  }
});

const columns = [
  { name: 'thumbnail', label: 'Ảnh', field: 'thumbnail', align: 'center' },
  { name: 'full_name', align: 'left', label: 'Họ tên', field: 'full_name', sortable: true },
  { name: 'id_card_number', align: 'left', label: 'CCCD', field: 'id_card_number', sortable: true },
  { name: 'supplier_name', align: 'left', label: 'Nhà cung cấp', field: 'supplier_name', sortable: true },
  { name: 'reason', align: 'left', label: 'Chi tiết', field: 'reason', sortable: true, style: 'max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;' },
  { name: 'license_plate', align: 'left', label: 'Biển số', field: 'license_plate', sortable: true },
  { name: 'estimated_datetime', align: 'left', label: 'Ngày & Giờ dự kiến', field: 'estimated_datetime', sortable: true },
  { name: 'registered_by_name', align: 'left', label: 'Người đăng ký', field: 'registered_by_name', sortable: true },
  { name: 'created_at', align: 'left', label: 'Ngày đăng ký', field: 'created_at', sortable: true, format: val => val ? new Date(val).toLocaleString('vi-VN') : '' },
  { name: 'status', align: 'center', label: 'Trạng thái', field: 'status', sortable: true },
  { 
    name: 'check_in_time', 
    align: 'left', 
    label: 'Giờ vào', 
    field: 'check_in_time', 
    sortable: true, 
    format: (val) => {
      if (!val) return '';
      try {
        const dbDate = new Date(val);
        return dbDate.toLocaleString('vi-VN');
      } catch (e) {
        return val;
      }
    } 
  },
  { name: 'actions', label: '', field: 'actions', align: 'right' }
]

function triggerCccdInput() {
  cccdInputRef.value.click();
}

async function handleCccdUpload(event) {
  const files = event.target.files;
  const result = await extractInfo(files);
  
  if (result) {
    if (result.single) {
      isBulk.value = false;
      isLongTerm.value = false;
      form.full_name = result.data.ho_ten || '';
      form.id_card_number = result.data.so_cccd || '';
    } else {
      isBulk.value = true;
      isLongTerm.value = false;
      form.guests = result.data;
      if (form.guests.length === 0) addPerson(); // uses alias
    }
  }
  event.target.value = '';
}

const getImgUrl = (path) => `${api.defaults.baseURL}/uploads/${path}`

function onRowClick(evt, row) {
    activeGuest.value = row
    slide.value = 0
    showDetailsDialog.value = true
}

function openFullImageViewer(path) {
  fullImageUrl.value = getImgUrl(path)
  showFullImageDialog.value = true
}

function onFileRejected(rejectedEntries) {
    $q.notify({
        type: 'negative',
        message: `${rejectedEntries.length} file(s) did not pass validation checks.`
    })
}

function openSearchDialog(type, target) {
  searchTargetForm = target;
    if (type === 'supplier') {
        showSupplierSearch.value = true;
    } else if (type === 'plate') {
        showPlateSearch.value = true;
    }
}

function selectValue(type, value) {
  const formToUpdate = searchTargetForm === 'edit' ? editForm : form;
  if (type === 'supplier') {
    formToUpdate.supplier_name = value;
    showSupplierSearch.value = false;
  } else if (type === 'plate') {
    formToUpdate.license_plate = value;
    showPlateSearch.value = false;
  }
}

async function load () {
  try {
    const res = await api.get('/guests', { params: { q: q.value || undefined, include_all_my_history: true } })
    rows.value = res.data
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Không tải được lịch sử khách.' })
  }
}

async function loadSuggestions() {
    try {
        const res = await api.get('/guests/suggestions')
        Object.assign(suggestions, res.data)
        filteredSupplierOptions.value = suggestions.supplier_names || []
    } catch (error) {
        console.error("Could not load suggestions", error)
    }
}

function filterSuppliers (val, update) {
  update(() => {
    const needle = val.toLowerCase()
    const options = suggestions.supplier_names || []
    filteredSupplierOptions.value = options.filter(v => v.toLowerCase().indexOf(needle) > -1)
  })
}

watch(() => suggestions.supplier_names, (newVal) => {
    filteredSupplierOptions.value = newVal || []
}, { immediate: true })


async function onSubmit() {
    isSubmitting.value = true;

    try {
        if (!validateForm()) {
             isSubmitting.value = false;
             return;
        }
        
        let successMessage = 'Đăng ký thành công!';
        
        if (isLongTerm.value) {
            // Logic checked by validateForm, safe to proceed
            const guestsToRegister = isBulk.value 
                ? form.guests 
                : [{ full_name: form.full_name, id_card_number: form.id_card_number }];

            const registrationPromises = guestsToRegister.map(guest => {
                const payload = {
                    company: form.company,
                    reason: form.reason,
                    license_plate: form.license_plate,
                    supplier_name: form.supplier_name,
                    full_name: guest.full_name,
                    id_card_number: guest.id_card_number,
                    estimated_datetime: form.estimated_datetime || null,
                    start_date: quasarDate.formatDate(quasarDate.extractDate(longTermDates.from, 'YYYY/MM/DD'), 'YYYY-MM-DD'),
                    end_date: quasarDate.formatDate(quasarDate.extractDate(longTermDates.to, 'YYYY/MM/DD'), 'YYYY-MM-DD'),
                };
                delete payload.guests;
                return api.post('/long-term-guests', payload);
            });

            await Promise.all(registrationPromises);
            successMessage = `Đăng ký dài hạn cho ${guestsToRegister.length} khách thành công!`;

        } else {
            if (isBulk.value) {
                const bulkResponse = await api.post('/guests/bulk', form);
                const createdGuests = bulkResponse.data;
                if (!createdGuests || createdGuests.length === 0) throw new Error("Không tạo được bản ghi khách.");
                await uploadImagesForGuests(createdGuests);
            } else {
                const payload = { ...form };
                delete payload.guests;
                const guestResponse = await api.post('/guests', payload);
                await uploadImagesForGuests([guestResponse.data]);
            }
        }
        
        $q.notify({ type: 'positive', message: successMessage });
        resetForm();
        load();

    } catch (error) {
        console.error("Registration failed:", error);
        $q.notify({ type: 'negative', message: error.response?.data?.detail || 'Đăng ký thất bại.' })
    } finally {
        isSubmitting.value = false
    }
}

async function uploadImagesForGuests(guests) {
    if (imageFiles.value && imageFiles.value.length > 0) {
        for (const guest of guests) {
            await uploadMultipleImages(guest.id, imageFiles.value, (file, error) => {
                $q.notify({ type: 'warning', message: `Lỗi upload ảnh ${file.name} cho khách ${guest.full_name}` });
            });
        }
    }
}

function editRow(row) {
    Object.assign(editForm, JSON.parse(JSON.stringify(row)));
    newImageFiles.value = [];
    showEditDialog.value = true;
}

async function deleteImage(image) {
  $q.dialog({
    title: 'Xác nhận',
    message: 'Bạn có chắc chắn muốn xóa ảnh này?',
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.delete(`/guests/images/${image.id}`);
      $q.notify({ type: 'positive', message: 'Đã xóa ảnh.' });
      const index = editForm.images.findIndex(img => img.id === image.id);
      if (index > -1) {
        editForm.images.splice(index, 1);
      }
    } catch (error) {
      $q.notify({ type: 'negative', message: 'Xóa ảnh thất bại.' });
    }
  });
}

async function onUpdateSubmit() {
    if (!editForm.id) return;
    $q.loading.show({ message: 'Đang cập nhật...' });
    try {
        editForm.supplier_name = editForm.supplier_name || editForm.company;
        await api.put(`/guests/${editForm.id}`, editForm);

        if (newImageFiles.value && newImageFiles.value.length > 0) {
            await uploadMultipleImages(editForm.id, newImageFiles.value, (file, error) => {
                $q.notify({ type: 'warning', message: `Lỗi upload ảnh ${file.name}` });
            });
        }

        $q.notify({ type: 'positive', message: 'Cập nhật thành công!' });
        showEditDialog.value = false;
        load();
    } catch (error) {
        $q.notify({ type: 'negative', message: 'Cập nhật thất bại.' });
    } finally {
       $q.loading.hide();
       newImageFiles.value = [];
    }
}

async function delRow (row) {
    $q.dialog({
        title: 'Xác nhận',
        message: 'Bạn có chắc chắn muốn xóa bản ghi này (bao gồm cả hình ảnh)?',
        cancel: true,
        persistent: true
    }).onOk(async () => {
        try {
            await api.delete(`/guests/${row.id}`)
            $q.notify({ type: 'positive', message: 'Đã xóa thành công.' })
            load()
        } catch (error) {
            $q.notify({ type: 'negative', message: 'Xóa thất bại.' })
        }
    })
}

async function handleImport(event) {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)
  $q.loading.show({ message: 'Đang xử lý file...' })
  try {
    await api.post('/guests/import/xlsx', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    $q.notify({ type: 'positive', message: 'Import thành công!' })
    load()
  } catch (error) {
    const detail = error.response?.data?.detail || 'Import thất bại. Vui lòng kiểm tra file.'
    $q.notify({ type: 'negative', message: detail })
  } finally {
    $q.loading.hide()
    event.target.value = ''
  }
}

// Export Logic
function openExportDialog() {
  if ((isAdmin.value || isManager.value) && allUsers.value.length === 0) {
    loadUsers()
  }
  showExportDialog.value = true
}

async function loadUsers() {
  try {
    const { data } = await api.get('/users/') 
    allUsers.value = data
    userOptions.value = data
  } catch (e) {
    console.error("Failed to load users", e)
  }
}

function filterUsers (val, update) {
  if (val === '') {
    update(() => {
      userOptions.value = allUsers.value
    })
    return
  }

  update(() => {
    const needle = val.toLowerCase()
    userOptions.value = allUsers.value.filter(v => v.full_name.toLowerCase().indexOf(needle) > -1)
  })
}


async function executeExport() {
  isExporting.value = true
  try {
    const params = {}
    if (exportFilters.start_date) params.start_date = exportFilters.start_date.replace(/\//g, '-')
    if (exportFilters.end_date) params.end_date = exportFilters.end_date.replace(/\//g, '-')
    if (exportFilters.registrant) params.registrant_id = exportFilters.registrant
    if (exportFilters.supplier_name) params.supplier_name = exportFilters.supplier_name

    const response = await api.get('/guests/export/xlsx', {
      params,
      responseType: 'blob'
    })

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    const contentDisposition = response.headers['content-disposition']
    let fileName = 'guests_export.xlsx'
    if (contentDisposition) {
      const fileNameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
      if (fileNameMatch && fileNameMatch.length === 2) fileName = fileNameMatch[1] // Sửa lỗi check length
    }
    link.setAttribute('download', fileName)
    document.body.appendChild(link)
    link.click()
    link.remove()
    
    showExportDialog.value = false
    $q.notify({ type: 'positive', message: 'Xuất dữ liệu thành công' })
  } catch (error) {
    console.error("Export failed", error)
    $q.notify({ type: 'negative', message: 'Xuất dữ liệu thất bại' })
  } finally {
    isExporting.value = false
  }
}

function reRegister(row) {
  // Reset form first
  resetForm();
  
  // Populate form with row data
  form.full_name = row.full_name;
  form.id_card_number = row.id_card_number;
  form.supplier_name = row.supplier_name;
  form.license_plate = row.license_plate;
  form.reason = row.reason;
  form.company = row.company;
  
  // Set estimated_datetime to now
  const now = new Date();
  form.estimated_datetime = now.toISOString();
  
  // Ensure single guest mode
  isBulk.value = false;
  isLongTerm.value = false;
  
  // Validates user feedback
  $q.notify({
     type: 'info',
     message: `Đã nạp thông tin của ${row.full_name}. Vui lòng kiểm tra và bấm Đăng ký.` 
  });
  
  // Scroll to top
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function clearData() {
  $q.dialog({
    title: 'Xác nhận xóa TOÀN BỘ DỮ LIỆU',
    message: 'Hành động này không thể hoàn tác. Vui lòng nhập mật khẩu để xác nhận:',
    prompt: {
      model: '',
      type: 'password'
    },
    cancel: true,
    persistent: true
  }).onOk(async (password) => {
    try {
      const validation = await api.post('/admin/validate-delete-password', { password })
      
      if (validation.data.valid) {
        await api.post('/guests/clear')
        $q.notify({ type: 'positive', message: 'Đã xóa toàn bộ dữ liệu khách.' })
        load()
      } else {
        $q.notify({ type: 'negative', message: 'Sai mật khẩu.' })
      }
    } catch (error) {
      const message = error.response?.status === 401 ? 'Sai mật khẩu.' : 'Xóa dữ liệu thất bại.'
      $q.notify({ type: 'negative', message })
    }
  })
}

function deleteOldData() {
  $q.dialog({
    title: 'Xác nhận xóa DỮ LIỆU CŨ',
    message: 'Xóa các khách đăng ký cũ (pending, đã đăng ký và dự kiến vào trước hôm nay). Vui lòng nhập mật khẩu để xác nhận:',
    prompt: {
      model: '',
      type: 'password'
    },
    cancel: true,
    persistent: true
  }).onOk(async (password) => {
    $q.loading.show({ message: 'Đang xác thực...' })
    
    try {
      const validation = await api.post('/admin/validate-delete-password', { password })
      
      if (!validation.data.valid) {
        $q.loading.hide()
        $q.notify({ type: 'negative', message: 'Sai mật khẩu.' })
        return
      }
      
      $q.loading.show({ message: 'Đang xóa dữ liệu cũ...' })
      const response = await api.post('/guests/delete-old')
      const deletedCount = response.data?.deleted_count || 0
      $q.notify({ 
        type: 'positive', 
        message: response.data?.message || `Đã xóa ${deletedCount} khách đăng ký cũ.` 
      })
      load()
    } catch (error) {
      const detail = error.response?.data?.detail || 'Xóa dữ liệu thất bại.'
      $q.notify({ type: 'negative', message: detail })
    } finally {
      $q.loading.hide()
    }
  })
}

onMounted(() => {
  load()
  loadSuggestions()
})
</script>

<style scoped>
@keyframes blink {
  0% { opacity: 1; }
  50% { opacity: 0.4; }
  100% { opacity: 1; }
}

.blinking-warning {
  animation: blink 1s infinite;
}
</style>

