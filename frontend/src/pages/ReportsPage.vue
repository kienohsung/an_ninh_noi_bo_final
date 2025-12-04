<template>
  <q-page padding>
    <!-- Header -->
    <div class="row items-center q-mb-md">
      <q-icon name="assessment" size="32px" color="primary" class="q-mr-sm"/>
      <div class="text-h5">Báo cáo & Phân tích</div>
    </div>

    <!-- Tabs -->
    <q-tabs
      v-model="activeTab"
      dense
      class="text-grey"
      active-color="primary"
      indicator-color="primary"
      align="justify"
      narrow-indicator
    >
      <q-tab name="visitor" icon="people" label="Chỉ số An ninh Khách" />
      <q-tab name="asset" icon="inventory" label="Kiểm soát Tài sản" />
      <q-tab name="overview" icon="dashboard" label="Tổng quan" />
      <q-tab name="activity" icon="leaderboard" label="Hoạt động NV" />
    </q-tabs>

    <q-separator />

    <!-- Tab Panels -->
    <q-tab-panels v-model="activeTab" animated class="q-mt-md">
      <!-- Visitor Security Index Tab -->
      <q-tab-panel name="visitor">
        <VisitorSecurityChart />
      </q-tab-panel>

      <!-- Asset Control Tab -->
      <q-tab-panel name="asset">
        <AssetControlDashboard />
      </q-tab-panel>

      <!-- System Overview Tab -->
      <q-tab-panel name="overview">
        <SystemOverviewCards />
      </q-tab-panel>

      <!-- User Activity Tab -->
      <q-tab-panel name="activity">
        <UserActivityTable />
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import VisitorSecurityChart from '../components/reports/VisitorSecurityChart.vue'
import AssetControlDashboard from '../components/reports/AssetControlDashboard.vue'
import SystemOverviewCards from '../components/reports/SystemOverviewCards.vue'
import UserActivityTable from '../components/reports/UserActivityTable.vue'

const activeTab = ref('visitor')
</script>

<style scoped>
/* Add any custom styles here */
</style>
