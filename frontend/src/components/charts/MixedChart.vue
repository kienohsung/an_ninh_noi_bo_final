<!-- File: frontend/src/components/charts/MixedChart.vue -->
<template>
  <div style="height:360px"><canvas ref="canvas"></canvas></div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { Chart } from 'chart.js/auto'

const props = defineProps({
  labels: { type: Array, default: () => [] },
  outSeries: { type: Array, default: () => [] },      // Tài sản ra
  inSeries: { type: Array, default: () => [] },       // Tài sản vào
  cumulativeSeries: { type: Array, default: () => [] } // Tổng tích luỹ
})

const canvas = ref(null)
let chart

function render() {
  if (!canvas.value) return
  if (chart) { 
    chart.destroy()
    chart = null 
  }

  const ctx = canvas.value.getContext('2d')
  
  // Gradients for bars
  const gradientOut = ctx.createLinearGradient(0, 0, 0, 360)
  gradientOut.addColorStop(0, 'rgba(255, 99, 132, 0.8)')
  gradientOut.addColorStop(1, 'rgba(255, 99, 132, 0.2)')
  
  const gradientIn = ctx.createLinearGradient(0, 0, 0, 360)
  gradientIn.addColorStop(0, 'rgba(75, 192, 192, 0.8)')
  gradientIn.addColorStop(1, 'rgba(75, 192, 192, 0.2)')

  // Convert outSeries to negative values (hiển thị cột hướng xuống)
  const negativeOutSeries = props.outSeries.map(val => -Math.abs(val))

  chart = new Chart(canvas.value, {
    type: 'bar',
    data: {
      labels: props.labels,
      datasets: [
        {
          type: 'bar',
          label: 'Tài sản ra',
          data: negativeOutSeries,
          backgroundColor: gradientOut,
          borderColor: 'rgba(255, 99, 132, 1)',
          borderWidth: 1,
          borderRadius: 4,
          yAxisID: 'y',
          order: 2
        },
        {
          type: 'bar',
          label: 'Tài sản vào',
          data: props.inSeries,
          backgroundColor: gradientIn,
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1,
          borderRadius: 4,
          yAxisID: 'y',
          order: 3
        },
        {
          type: 'line',
          label: 'Tổng tích luỹ tài sản ra',
          data: props.cumulativeSeries,
          borderColor: 'rgba(54, 162, 235, 1)',
          backgroundColor: 'rgba(54, 162, 235, 0.1)',
          borderWidth: 3,
          fill: false,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: 'rgba(54, 162, 235, 1)',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          yAxisID: 'y1',
          order: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            usePointStyle: true,
            padding: 15,
            font: {
              size: 12
            }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleFont: { size: 14, weight: 'bold' },
          bodyFont: { size: 13 },
          padding: 12,
          cornerRadius: 6,
          displayColors: true,
          callbacks: {
            label: function(context) {
              let label = context.dataset.label || ''
              if (label) {
                label += ': '
              }
              if (context.parsed.y !== null) {
                // Hiển thị giá trị tuyệt đối cho số âm (tài sản ra)
                const value = Math.abs(context.parsed.y)
                label += value + ' tài sản'
              }
              return label
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          },
          ticks: {
            maxRotation: 45,
            minRotation: 0,
            font: {
              size: 11
            }
          }
        },
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          grid: {
            color: 'rgba(0, 0, 0, 0.05)',
            drawTicks: true
          },
          ticks: {
            font: {
              size: 11
            },
            callback: function(value) {
              // Hiển thị giá trị tuyệt đối trên trục Y
              return Math.abs(value)
            }
          },
          title: {
            display: true,
            text: 'Số lượng (↓ Ra | Vào ↑)',
            font: {
              size: 12,
              weight: 'bold'
            }
          }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          beginAtZero: true,
          grid: {
            drawOnChartArea: false
          },
          ticks: {
            font: {
              size: 11
            }
          },
          title: {
            display: true,
            text: 'Tổng tích luỹ',
            font: {
              size: 12,
              weight: 'bold'
            }
          }
        }
      }
    }
  })
}

onMounted(render)
onBeforeUnmount(() => { 
  if (chart) chart.destroy() 
})

watch(() => [props.labels, props.outSeries, props.inSeries, props.cumulativeSeries], render)
</script>
