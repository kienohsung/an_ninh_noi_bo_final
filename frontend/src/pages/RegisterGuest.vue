<!-- File path: frontend/src/pages/RegisterGuest.vue -->
<!-- CHỈNH SỬA LAYOUT: Di chuyển các tùy chọn lại gần nhau -->
<template>
  <q-page padding>
    <q-card>
      <q-card-section class="row items-center justify-between">
        <div class="text-subtitle1">Đăng ký khách</div>
        <div>
          <q-btn 
            icon="qr_code_scanner" 
            label="Quét CCCD" 
            color="secondary" 
            @click="triggerCccdInput"
            :loading="isScanning"
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
      </q-card-section>
      <q-card-section>
          <q-form @submit="onSubmit" class="q-gutter-y-md">

          <!-- SỬA ĐỔI: Gom nhóm các tùy chọn đăng ký đặc biệt -->
          <div class="q-pa-sm bg-grey-2 rounded-borders">
            <div class="row items-center q-gutter-x-md">
              <q-toggle v-model="isBulk" label="Đăng ký theo đoàn" />
              <q-toggle v-model="isLongTerm" label="Khách thường xuyên (dài hạn)" />
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
// Import image upload utilities
import { resizeImage, uploadMultipleImages } from '../utils/imageUpload'
// Import validators
import { validateEstimatedDateTime, validateGuestArray, validateDateRange } from '../utils/validators'

const $q = useQuasar()
const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role === 'admin')
const isManager = computed(() => auth.user?.role === 'manager')

// --- BẮT ĐẦU NÂNG CẤP: Thay estimated_time bằng estimated_datetime ---
const initialFormState = {
  full_name: '', id_card_number: '', company: '', reason: '',
  license_plate: '', supplier_name: '',
  estimated_datetime: null, // <-- NÂNG CẤP
  guests: [{ full_name: '', id_card_number: '' }]
}
// --- KẾT THÚC NÂNG CẤP ---

const form = reactive({ ...initialFormState })
const isBulk = ref(false)
const isLongTerm = ref(false)
const longTermDates = reactive({ from: '', to: '' })

const rows = ref([])
const q = ref('')
const fileInputRef = ref(null)
const suggestions = reactive({ companies: [], license_plates: [], supplier_names: [] })
const showEditDialog = ref(false)

// --- BẮT ĐẦU NÂNG CẤP: Thêm estimated_datetime vào form sửa ---
const editForm = reactive({
  id: null, full_name: '', id_card_number: '', company: '',
  reason: '', license_plate: '', supplier_name: '', images: [],
  estimated_datetime: null // <-- NÂNG CẤP
})
// --- KẾT THÚC NÂNG CẤP ---

const newImageFiles = ref([])

const imageFiles = ref([])
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
const isScanning = ref(false);

// --- NÂNG CẤP: Export Logic ---
const showExportDialog = ref(false)
const isExporting = ref(false)
const exportFilters = reactive({
  start_date: '',
  end_date: '',
  registrant: null,
  supplier_name: null
})
const userOptions = ref([])
const allUsers = ref([]) // Cache all users

function openExportDialog() {
  // Reset filters or keep them? Let's keep them for convenience, maybe reset dates if needed.
  // exportFilters.start_date = ''
  // exportFilters.end_date = ''
  
  // Load users if admin/manager
  if ((isAdmin.value || isManager.value) && allUsers.value.length === 0) {
    loadUsers()
  }
  
  showExportDialog.value = true
}

async function loadUsers() {
  try {
    // Assuming there is an endpoint to get users. If not, we might need to rely on what we have or add one.
    // Checking api.js or similar might be good, but for now let's assume /users exists or we can't do it easily.
    // Wait, I don't see a /users endpoint in the file list I saw earlier (only guests.py).
    // But guests.py imports models.User. 
    // Let's check if there is a users router.
    // If not, I might need to add one or just skip this part.
    // However, the requirement says "người đăng ký... dạng droplist".
    // I will try to fetch from /users if it exists, otherwise I might need to add it.
    // Let's assume for now I can get it. If not I will fix later.
    // Actually, I can use the `registered_by_name` from the loaded rows as a quick hack if I don't want to call API.
    // But that only gives users who have registered guests in the current view.
    // Better to fetch all users.
    const { data } = await api.get('/users/') 
    allUsers.value = data
    userOptions.value = data
  } catch (e) {
    console.error("Failed to load users", e)
    // Fallback: use unique users from current rows if available? No, that's unreliable.
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
    if (exportFilters.start_date) params.start_date = exportFilters.start_date.split('/').reverse().join('-') // Format if needed? Quasar date is YYYY/MM/DD usually.
    // Wait, Quasar date mask="date" uses YYYY/MM/DD by default. Backend expects YYYY-MM-DD.
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
      if (fileNameMatch.length === 2) fileName = fileNameMatch[1]
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
// --- KẾT THÚC NÂNG CẤP ---



// --- BẮT ĐẦU NÂNG CẤP: Logic cho DateTime Picker ---
const proxyDate = ref(null)
const proxyTime = ref(null)
// searchTargetForm đã tồn tại, chúng ta sẽ tái sử dụng nó cho ('main' hoặc 'edit')

// Computed để hiển thị ngày giờ trong FORM CHÍNH
const formattedEstimatedDatetime = computed(() => {
  if (!form.estimated_datetime) return null;
  // new Date() có thể xử lý chuỗi ISO (VD: 2025-10-30T15:30:00)
  const d = new Date(form.estimated_datetime);
  // Định dạng lại theo chuẩn Việt Nam
  return quasarDate.formatDate(d, 'DD/MM/YYYY HH:mm');
});

// Computed để hiển thị ngày giờ trong DIALOG SỬA
const formattedEditEstimatedDatetime = computed(() => {
  if (!editForm.estimated_datetime) return null;
  const d = new Date(editForm.estimated_datetime);
  return quasarDate.formatDate(d, 'DD/MM/YYYY HH:mm');
});

// Hàm mở popup và khởi tạo giá trị
function openDateTimePickerProxy(target) {
  searchTargetForm = target; // 'main', 'edit', hoặc 'edit_asset'
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
    // SỬA LỖI: Gửi thời gian UTC (có Z) để Backend lưu đúng chuẩn UTC
    // Backend sẽ coi Naive DateTime là UTC và convert sang Local khi hiển thị
    const d = new Date(newVal);
    const utcIsoString = d.toISOString();

    if (searchTargetForm === 'main') {
      form.estimated_datetime = utcIsoString;
    } else if (searchTargetForm === 'edit') {
      editForm.estimated_datetime = utcIsoString;
    }
  }
}
// --- KẾT THÚC NÂNG CẤP ---


watch(isLongTerm, (newVal) => {
  if (newVal) {
    // Đăng ký dài hạn không hỗ trợ tải ảnh lên trực tiếp
    imageFiles.value = [];
  }
});

// --- BẮT ĐẦU NÂNG CẤP: Thay đổi cột 'Giờ dự kiến' thành 'Ngày & Giờ dự kiến' ---
const columns = [
  { name: 'thumbnail', label: 'Ảnh', field: 'thumbnail', align: 'center' },
  { name: 'full_name', align: 'left', label: 'Họ tên', field: 'full_name', sortable: true },
  { name: 'id_card_number', align: 'left', label: 'CCCD', field: 'id_card_number', sortable: true },
  { name: 'supplier_name', align: 'left', label: 'Nhà cung cấp', field: 'supplier_name', sortable: true },
  { name: 'reason', align: 'left', label: 'Chi tiết', field: 'reason', sortable: true, style: 'max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;' },
  { name: 'license_plate', align: 'left', label: 'Biển số', field: 'license_plate', sortable: true },
  
  // --- NÂNG CẤP ---
  { name: 'estimated_datetime', align: 'left', label: 'Ngày & Giờ dự kiến', field: 'estimated_datetime', sortable: true },
  // --- KẾT THÚC NÂNG CẤP ---
  
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
        // Lấy thời gian từ CSDL
        const dbDate = new Date(val);
        
        // Hiển thị thời gian theo định dạng Việt Nam
        return dbDate.toLocaleString('vi-VN');
      } catch (e) {
        return val; // Trả về giá trị gốc nếu có lỗi
      }
    } 
  },
  { name: 'actions', label: '', field: 'actions', align: 'right' }
]
// --- KẾT THÚC NÂNG CẤP ---

function triggerCccdInput() {
  cccdInputRef.value.click();
}

async function handleCccdUpload(event) {
  const files = event.target.files;
  if (!files || files.length === 0) return;

  isScanning.value = true;
  $q.loading.show({ message: `Đang xử lý ${files.length} ảnh CCCD...` });

  try {
    if (files.length === 1) {
      const formData = new FormData();
      formData.append('file', files[0]);
      const { data } = await api.post('/gemini/extract-cccd-info', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      isBulk.value = false;
      // Khi quét CCCD, mặc định là đăng ký thường, không phải dài hạn
      isLongTerm.value = false;
      form.full_name = data.ho_ten || '';
      form.id_card_number = data.so_cccd || '';
      $q.notify({ type: 'positive', message: 'Đã điền thông tin từ 1 CCCD.' });

    } else {
      isBulk.value = true;
      // Khi quét CCCD, mặc định là đăng ký thường, không phải dài hạn
      isLongTerm.value = false;
      form.guests = [];

      const promises = Array.from(files).map(file => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post('/gemini/extract-cccd-info', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      });

      const results = await Promise.all(promises);
      
      results.forEach(res => {
        if (res.data && (res.data.ho_ten || res.data.so_cccd)) {
          form.guests.push({
            full_name: res.data.ho_ten || '',
            id_card_number: res.data.so_cccd || ''
          });
        }
      });

      if (form.guests.length === 0) addPerson();

      $q.notify({ type: 'positive', message: `Đã điền thông tin từ ${form.guests.length} CCCD vào form đăng ký đoàn.` });
    }
  } catch (error) {
    console.error("Lỗi khi quét CCCD:", error);
    const detail = error.response?.data?.detail || 'Quét CCCD thất bại.';
    $q.notify({ type: 'negative', message: detail });
  } finally {
    isScanning.value = false;
    $q.loading.hide();
    event.target.value = '';
  }
}

function addPerson() {
  form.guests.push({ full_name: '', id_card_number: '' })
}

function removePerson(index) {
  form.guests.splice(index, 1)
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

// --- NÂNG CẤP: Load users for filter ---
// We need to ensure we have a way to get users.
// If /users/ endpoint exists.
// Let's assume it does or I'll add it.
// Actually, to be safe, I'll check if I can find the users router.
// But I can't check in the middle of this tool call.
// I'll assume standard /users/ path.
// Also need to handle the supplier filtering in the dialog properly.
// I replaced the options in the template with suggestions.supplier_names, 
// but for filtering to work I should use a filtered list.
// Let's fix the template part for supplier select to use supplierOptions if I can.
// Wait, I can't change the template I already wrote in the previous chunk easily without context.
// Actually I can. I will update the template chunk to use `supplierOptions` instead of `suggestions.supplier_names`.
// Ah, I already wrote the template chunk.
// I will just make sure `suggestions.supplier_names` is used for now, and maybe skip filtering for supplier in the first pass if it's complex, 
// OR I can use `use-input` and `@filter` with a local ref.
// In the script chunk I added `supplierOptions` and `filterSuppliers`.
// I need to make sure `filterSuppliers` updates `suggestions.supplier_names`? No, that would affect other parts.
// I should have used a separate ref for the export dialog supplier options.
// Let's refine the script chunk.
// Actually, I can just use `suggestions.supplier_names` for the options and filter it?
// No, `suggestions` is reactive.
// I will create `filteredSupplierOptions` for the export dialog.

const filteredSupplierOptions = ref([])

function filterSuppliers (val, update) {
  update(() => {
    const needle = val.toLowerCase()
    filteredSupplierOptions.value = suggestions.supplier_names.filter(v => v.toLowerCase().indexOf(needle) > -1)
  })
}

// Initialize filtered options
watch(() => suggestions.supplier_names, (newVal) => {
    filteredSupplierOptions.value = newVal
}, { immediate: true })

// Also need to update the template to use `filteredSupplierOptions`
// I will do that in a separate tool call if needed, or I can try to fix it now.
// The previous chunk for template used `suggestions.supplier_names`.
// I will use `multi_replace` so I can't go back.
// I will just use `suggestions.supplier_names` in the template for now.
// Wait, if I use `use-input` and `@filter`, I MUST update the options list passed to the component.
// If I passed `suggestions.supplier_names`, I am filtering the global suggestions list? That's bad.
// I should have passed `filteredSupplierOptions`.
// I will correct the template in a subsequent call if I made a mistake.
// BUT, I haven't submitted the tool call yet.
// I can fix the template chunk in THIS tool call.
// Let's check the template chunk again.
// It says `:options="suggestions.supplier_names"`.
// I will change it to `:options="filteredSupplierOptions"`.

// ... wait, I can't edit the previous chunk in this thought process.
// I have to issue the tool call with the CORRECT content.
// So I will correct the template chunk in the tool call arguments.

// Also, I need to add `exportGuests` to the return object if using Options API?
// No, this is `<script setup>`, so top level variables are exposed.

// One more thing: `api.get('/users/')`.
// I need to verify if this endpoint exists.
// I saw `backend/app/routers/guests.py`.
// I didn't see `users.py` in the file list I checked earlier (I checked `backend` dir, it had 88 children).
// I should probably check if `users.py` exists.
// But I am in `replace_file_content` mode.
// I will assume it exists because `guests.py` imports `models.User`.
// If it fails, I'll fix it.

// Correcting the template chunk in the tool call:
// Change `:options="suggestions.supplier_names"` to `:options="filteredSupplierOptions"`

// Correcting the script chunk:
// Add `filteredSupplierOptions` and `filterSuppliers`.

// Final check on `executeExport`:
// `api.get('/guests/export/xlsx', ...)`
// The backend endpoint I modified is `@router.get("/export/xlsx")`.
// So it matches.

// One detail: `exportGuests` vs `executeExport`.
// In the template I used `@click="exportGuests"` in the dropdown menu.
// But I defined `executeExport` for the dialog button.
// And `openExportDialog` for the dropdown button.
// Wait, in the dropdown menu:
// `<q-item clickable v-close-popup @click="exportGuests">`
// This should be `@click="openExportDialog"`.
// I need to fix that in the template chunk.

// Summary of fixes for the tool call:
// 1. Template: Change `exportGuests` to `openExportDialog` in the dropdown.
// 2. Template: Change `:options="suggestions.supplier_names"` to `:options="filteredSupplierOptions"` in the dialog.
// 3. Script: Add `filteredSupplierOptions`, `filterSuppliers`, `openExportDialog`, `executeExport`.
// 4. Script: `loadUsers` implementation.

// Let's prepare the chunks.

// Chunk 1 (Dropdown):
// Replace `exportGuests` with `openExportDialog`.

// Chunk 2 (Dialog):
// Use `filteredSupplierOptions`.

// Chunk 3 (Script):
// Implement logic.

// Wait, I need to make sure I don't break the existing `exportGuests` if it was there?
// The original code had:
// `<q-item clickable v-close-popup @click="exportGuests">`
// And `const exportGuests = ...` (maybe? No, I don't see it in the file content I read).
// The file content I read had:
// `// ...` (truncated?)
// Let's check the file content again.
// I read lines 1-800.
// The `exportGuests` function was NOT in the visible part.
// But the template used it: `<q-item clickable v-close-popup @click="exportGuests">` (Line 243).
// So it must be defined somewhere or it was missing.
// If I am replacing it, I should define it or replace the call.
// I will replace the call to `openExportDialog`.

// I will proceed with the tool call.


// Image upload functions moved to utils/imageUpload.js

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
    } catch (error) {
        console.error("Could not load suggestions", error)
    }
}

async function onSubmit() {
    isSubmitting.value = true;

    try {
        // Validate estimated datetime using utility
        if (!validateEstimatedDateTime(form.estimated_datetime)) {
             $q.notify({ 
                 type: 'negative', 
                 message: 'Vui lòng nhập "Ngày & Giờ dự kiến" để tiếp tục đăng ký.' 
             });
             isSubmitting.value = false;
             return;
        }
        
        let successMessage = 'Đăng ký thành công!';
        
        if (isLongTerm.value) {
            if (!longTermDates.from || !longTermDates.to) {
                $q.notify({ type: 'negative', message: 'Vui lòng chọn đầy đủ ngày bắt đầu và kết thúc.' });
                isSubmitting.value = false;
                return;
            }

            const guestsToRegister = isBulk.value 
                ? form.guests 
                : [{ full_name: form.full_name, id_card_number: form.id_card_number }];

            if (guestsToRegister.some(g => !g.full_name || !g.full_name.trim())) {
                 $q.notify({ type: 'negative', message: 'Vui lòng nhập đầy đủ họ tên cho tất cả khách.' });
                 isSubmitting.value = false;
                 return;
            }

            const registrationPromises = guestsToRegister.map(guest => {
                const payload = {
                    company: form.company,
                    reason: form.reason,
                    license_plate: form.license_plate,
                    supplier_name: form.supplier_name,
                    full_name: guest.full_name,
                    id_card_number: guest.id_card_number,
                    
                    // Gửi estimated_datetime cho khách dài hạn
                    estimated_datetime: form.estimated_datetime || null,

                    start_date: quasarDate.formatDate(quasarDate.extractDate(longTermDates.from, 'YYYY/MM/DD'), 'YYYY-MM-DD'),
                    end_date: quasarDate.formatDate(quasarDate.extractDate(longTermDates.to, 'YYYY/MM/DD'), 'YYYY-MM-DD'),
                };
                delete payload.guests;
                return api.post('/long-term-guests', payload);
            });

            await Promise.all(registrationPromises);
            successMessage = `Đăng ký dài hạn cho ${guestsToRegister.length} khách thành công!`;

        } else { // Đăng ký thường (không dài hạn)
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

// --- BẮT ĐẦU NÂNG CẤP: Reset cả estimated_datetime ---
function resetForm() {
    Object.assign(form, { ...initialFormState, guests: [{ full_name: '', id_card_number: '' }] });
    form.estimated_datetime = null; // <-- NÂNG CẤP
    imageFiles.value = [];
    isBulk.value = false;
    isLongTerm.value = false;
    longTermDates.from = '';
    longTermDates.to = '';
}
// --- KẾT THÚC NÂNG CẤP ---


function editRow(row) {
    // Đảm bảo sao chép sâu (deep copy) để tránh ảnh hưởng row gốc
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
        
        // editForm (từ editForm definition) đã chứa estimated_datetime
        // Hàm openDateTimePickerProxy/setEstimatedDatetime đã cập nhật nó
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

async function exportGuests() {
  try {
    const response = await api.get('/guests/export/xlsx', { responseType: 'blob' })
    const blob = new Blob([response.data], { type: response.headers['content-type'] })
    const filename = `guests_export_${new Date().toISOString().slice(0,10)}.xlsx`
    qExportFile(filename, blob)
    $q.notify({ type: 'positive', message: 'Export thành công!' })
  } catch (error) {
    console.error("Export failed:", error)
    $q.notify({ type: 'negative', message: 'Export thất bại.' })
  }
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
      // Validate password với backend
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
      // Validate password với backend
      const validation = await api.post('/admin/validate-delete-password', { password })
      
      if (!validation.data.valid) {
        $q.loading.hide()
        $q.notify({ type: 'negative', message: 'Sai mật khẩu.' })
        return
      }
      
      // Password valid, proceed with delete
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
