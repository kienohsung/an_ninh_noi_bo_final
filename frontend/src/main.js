// File: frontend/src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { Quasar, Dialog, Notify, Loading } from 'quasar'
import quasarLang from 'quasar/lang/vi'

// Import icon libraries
import '@quasar/extras/material-icons/material-icons.css'
// Import Quasar css
import 'quasar/dist/quasar.css'

// Import ApexCharts
import VueApexCharts from "vue3-apexcharts";

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)

app.use(createPinia())
app.use(Quasar, {
  plugins: { Dialog, Notify, Loading },
  lang: quasarLang,
})

// --- SỬA LỖI: Chỉ đăng ký ApexCharts một lần duy nhất tại đây ---
app.use(VueApexCharts);

app.use(router)

const auth = useAuthStore();
/* --- CLEAR CACHE ON STARTUP (Prevent White Screen) --- */
(async () => {
  try {
    console.log('[System] Cleaning up caches...');

    // 1. Backup critical keys
    const whitelist = ['token', 'refreshToken', 'guard_audio_enabled'];
    const backups = {};
    whitelist.forEach(key => {
      const val = localStorage.getItem(key);
      if (val) backups[key] = val;
    });

    // 2. Clear storages
    localStorage.clear();
    sessionStorage.clear();

    // 3. Restore backups
    Object.entries(backups).forEach(([key, val]) => {
      localStorage.setItem(key, val);
    });

    // 4. Unregister Service Workers (Force fresh load)
    if ('serviceWorker' in navigator) {
      const registrations = await navigator.serviceWorker.getRegistrations();
      for (const registration of registrations) {
        await registration.unregister();
      }
    }
    console.log('[System] Cache cleared. App ready.');
  } catch (e) {
    console.warn('[System] Cache clear warning:', e);
  }
})();
/* ---------------------------------------------------- */

// Bootstrap authentication
auth.bootstrap().then(() => {
  app.mount('#app')
})

