<template>
  <q-page padding>
    <!-- Header -->
    <div class="row items-center q-mb-md">
      <q-icon name="assessment" size="32px" color="primary" class="q-mr-sm"/>
      <div class="text-h5">Báo cáo An ninh Khách</div>
    </div>

    <!-- Visitor Security Chart Only -->
    <VisitorSecurityChart />
    
    <q-separator class="q-my-md" />
    
    <div class="text-caption text-grey-7">
      💡 Tip: Các báo cáo "Kiểm soát Tài sản", "Tổng quan", và "Hoạt động NV" đã được tích hợp vào trang Dashboard
    </div>
  </q-page>
</template>

<script setup>
import VisitorSecurityChart from '../components/reports/VisitorSecurityChart.vue'
</script>

<style scoped>
/* Add any custom styles here */
</style>
