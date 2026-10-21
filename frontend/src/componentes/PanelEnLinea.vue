<script setup>
// Formulario en la página (en lugar de una ventana emergente): aparece donde se
// trabaja, con su título, cerrar y las acciones al pie. Al abrirse se desplaza a
// la vista y enfoca el primer campo.
import { nextTick, onMounted, ref } from 'vue'
import Icono from './Icono.vue'

defineProps({ titulo: { type: String, required: true }, descripcion: { type: String, default: '' } })
const emit = defineEmits(['cerrar'])
const raiz = ref(null)

onMounted(async () => {
  await nextTick()
  raiz.value?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  raiz.value?.querySelector('[autofocus], input:not([type=hidden]):not([type=checkbox]), select, textarea')?.focus({ preventScroll: true })
})
</script>

<template>
  <section ref="raiz" class="panel en-linea" :aria-label="titulo" @keydown.esc="emit('cerrar')">
    <div class="en-linea-cabeza">
      <div><h3>{{ titulo }}</h3><p v-if="descripcion" class="ayuda">{{ descripcion }}</p></div>
      <button type="button" class="btn-icono" aria-label="Cerrar" @click="emit('cerrar')"><Icono nombre="cerrar" :tam="18" /></button>
    </div>
    <slot />
    <div v-if="$slots.pie" class="en-linea-pie"><slot name="pie" /></div>
  </section>
</template>
