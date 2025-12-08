import { reactive, ref } from 'vue'
import { Notify } from 'quasar'
import { validateEstimatedDateTime } from '../utils/validators'

export function useGuestForm() {
    const initialFormState = {
        full_name: '',
        id_card_number: '',
        company: '',
        reason: '',
        license_plate: '',
        supplier_name: '',
        estimated_datetime: null,
        guests: [{ full_name: '', id_card_number: '' }]
    }

    const form = reactive({ ...initialFormState })
    const isBulk = ref(false)
    const isLongTerm = ref(false)
    const longTermDates = reactive({ from: '', to: '' })
    const imageFiles = ref([])

    const resetForm = () => {
        // Reset form fields
        Object.assign(form, JSON.parse(JSON.stringify(initialFormState)))

        // Reset other states
        isBulk.value = false
        isLongTerm.value = false
        longTermDates.from = ''
        longTermDates.to = ''
        imageFiles.value = []
    }

    const addGuestToBulk = () => {
        form.guests.push({ full_name: '', id_card_number: '' })
    }

    const removeGuestFromBulk = (index) => {
        if (form.guests.length > 1) {
            form.guests.splice(index, 1)
        }
    }

    const validateForm = () => {
        // Validate estimated datetime
        if (!validateEstimatedDateTime(form.estimated_datetime)) {
            Notify.create({
                type: 'negative',
                message: 'Vui lòng nhập "Ngày & Giờ dự kiến" để tiếp tục đăng ký.'
            })
            return false
        }

        if (isLongTerm.value) {
            if (!longTermDates.from || !longTermDates.to) {
                Notify.create({ type: 'negative', message: 'Vui lòng chọn đầy đủ ngày bắt đầu và kết thúc.' })
                return false
            }

            const guestsToRegister = isBulk.value
                ? form.guests
                : [{ full_name: form.full_name, id_card_number: form.id_card_number }]

            if (guestsToRegister.some(g => !g.full_name || !g.full_name.trim())) {
                Notify.create({ type: 'negative', message: 'Vui lòng nhập đầy đủ họ tên cho tất cả khách.' })
                return false
            }
        }

        return true
    }

    return {
        form,
        isBulk,
        isLongTerm,
        longTermDates,
        imageFiles,
        resetForm,
        addGuestToBulk,
        removeGuestFromBulk,
        validateForm
    }
}
