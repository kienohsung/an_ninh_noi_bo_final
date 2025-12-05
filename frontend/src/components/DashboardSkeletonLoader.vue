<template>
  <div class="dashboard-skeleton">
    <!-- KPI Cards Skeleton -->
    <div v-if="type === 'kpi-cards'" class="row q-col-gutter-sm">
      <div v-for="i in count" :key="i" class="col-6 col-sm-3">
        <q-skeleton height="80px" />
      </div>
    </div>

    <!-- Chart Skeleton -->
    <q-skeleton 
      v-else-if="type === 'chart'" 
      type="rect" 
      :height="height || '300px'" 
    />

    <!-- Table Skeleton -->
    <div v-else-if="type === 'table'">
      <q-skeleton type="text" width="30%" class="q-mb-md" />
      <q-skeleton type="rect" height="200px" />
    </div>

    <!-- Card Skeleton -->
    <q-skeleton 
      v-else-if="type === 'card'" 
      height="120px"
    />
  </div>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    default: 'chart',
    validator: (value) => ['chart', 'kpi-cards', 'table', 'card'].includes(value)
  },
  height: {
    type: String,
    default: '300px'
  },
  count: {
    type: Number,
    default: 4
  }
})
</script>

<style scoped>
.dashboard-skeleton {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}
</style>
