import { createApp } from 'vue'
import '@fontsource-variable/plus-jakarta-sans'
import './styles.css'
import App from './App.vue'
import router from './router.js'
import { vFiltros, vFlotante } from './nucleo/directivas.js'

createApp(App).use(router).directive('filtros', vFiltros).directive('flotante', vFlotante).mount('#app')
