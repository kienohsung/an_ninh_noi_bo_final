import { ref } from 'vue'
import { Notify, Loading } from 'quasar'
import api from '../api'

export function useCCCDScanner() {
    const isScanning = ref(false)

    const extractInfo = async (files) => {
        if (!files || files.length === 0) return null

        isScanning.value = true
        Loading.show({ message: `Đang xử lý ${files.length} ảnh CCCD...` })

        try {
            if (files.length === 1) {
                const formData = new FormData()
                formData.append('file', files[0])
                const { data } = await api.post('/gemini/extract-cccd-info', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                })

                Notify.create({ type: 'positive', message: 'Đã điền thông tin từ 1 CCCD.' })
                return { single: true, data }

            } else {
                const promises = Array.from(files).map(file => {
                    const formData = new FormData()
                    formData.append('file', file)
                    return api.post('/gemini/extract-cccd-info', formData, {
                        headers: { 'Content-Type': 'multipart/form-data' }
                    })
                })

                const results = await Promise.all(promises)
                const extractedData = []

                results.forEach(res => {
                    if (res.data && (res.data.ho_ten || res.data.so_cccd)) {
                        extractedData.push({
                            full_name: res.data.ho_ten || '',
                            id_card_number: res.data.so_cccd || ''
                        })
                    }
                })

                Notify.create({ type: 'positive', message: `Đã điền thông tin từ ${extractedData.length} CCCD vào form đăng ký đoàn.` })
                return { single: false, data: extractedData }
            }
        } catch (error) {
            console.error("Lỗi khi quét CCCD:", error)
            const detail = error.response?.data?.detail || 'Quét CCCD thất bại.'
            Notify.create({ type: 'negative', message: detail })
            return null
        } finally {
            isScanning.value = false
            Loading.hide()
        }
    }

    return {
        isScanning,
        extractInfo
    }
}
