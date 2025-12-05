<template>
  <q-card flat class="kpi-compact-card" :class="gradientClass">
    <q-card-section class="q-pa-sm" :class="textClass">
      <div class="row items-center">
        <q-icon 
          :name="icon" 
          :size="iconSize" 
          class="q-mr-sm"
        />
        <div class="flex-1">
          <div class="text-overline">{{ label }}</div>
          <div :class="valueClass">{{ formattedValue }}</div>
          <div v-if="subtitle" class="text-caption">{{ subtitle }}</div>
        </div>
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: [Number, String],
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  },
  icon: {
    type: String,
    default: 'analytics'
  },
  iconSize: {
    type: String,
    default: '24px'
  },
  gradient: {
    type: Number,
    default: 1,
    validator: (value) => value >= 1 && value <= 4
  },
  textWhite: {
    type: Boolean,
    default: true
  }
})

const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    return props.value.toLocaleString()
  }
  return props.value
})

const gradientClass = computed(() => `bg-gradient-${props.gradient}`)
const textClass = computed(() => props.textWhite ? 'text-white' : '')
const valueClass = computed(() => {
  const classes = ['text-h6', 'text-weight-bold']
  if (props.textWhite) classes.push('text-white')
  return classes.join(' ')
})
</script>

<style scoped>
.kpi-compact-card {
  transition: all 0.3s ease;
  border-radius: 8px;
  overflow: hidden;
  min-height: 80px;
}

.kpi-compact-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.bg-gradient-1 {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.bg-gradient-2 {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.bg-gradient-3 {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.bg-gradient-4 {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}
</style>
