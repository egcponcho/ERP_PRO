<script setup>
// Buscador de registros de una entidad referenciable (combobox): se escribe y se elige.
// v-model = id del registro. Las entidades las registra cada módulo en el backend
// (app/core/referencias.py) y se consultan en /api/referencias/{entidad}.
import { onMounted, ref, watch } from 'vue'
import { api } from '@/nucleo/api.js'

const props = defineProps({ modelValue: { type: Number, default: null }, id: { type: String, required: true },
                            entidad: { type: String, required: true }, excluir: { type: Number, default: null },
                            invalido: { type: Boolean, default: false } })
const emit = defineEmits(['update:modelValue', 'elegido'])
const texto = ref('')
const opciones = ref([])
const abierto = ref(false)
const activo = ref(0)
let espera = null

const etiqueta = (r) => (r.codigo ? `${r.codigo} · ${r.nombre}` : r.nombre)

onMounted(async () => {
  if (props.modelValue) {
    try { texto.value = etiqueta(await api.get(`/referencias/${props.entidad}/${props.modelValue}`)) } catch { /* sin nombre */ }
  }
})

async function buscar() {
  try {
    const r = await api.get(`/referencias/${props.entidad}`, { q: texto.value.includes(' · ') ? '' : texto.value, tamano: 8 })
    opciones.value = r.filter((x) => x.id !== props.excluir)
    activo.value = 0
  } catch { opciones.value = [] }
}
watch(texto, () => { clearTimeout(espera); espera = setTimeout(buscar, 200) })

function alEntrar() {
  abierto.value = true
  if (!opciones.value.length) buscar()
}
function alSalir() {
  setTimeout(() => (abierto.value = false), 150)
}
function elegir(r) {
  emit('update:modelValue', r.id)
  emit('elegido', r)
  texto.value = etiqueta(r)
  abierto.value = false
}
function teclas(e) {
  if (e.key === 'ArrowDown') { e.preventDefault(); abierto.value = true; activo.value = Math.min(activo.value + 1, opciones.value.length - 1) }
  else if (e.key === 'ArrowUp') { e.preventDefault(); activo.value = Math.max(activo.value - 1, 0) }
  else if (e.key === 'Enter' && abierto.value && opciones.value[activo.value]) { e.preventDefault(); elegir(opciones.value[activo.value]) }
  else if (e.key === 'Escape') abierto.value = false
}
</script>

<template>
  <div class="selector-referencia">
    <input :id="id" v-model="texto" class="entrada" :aria-invalid="invalido" type="text" role="combobox" autocomplete="off"
           :aria-expanded="abierto" :aria-controls="`${id}-lista`" placeholder="Buscar…"
           @focus="alEntrar" @input="abierto = true; emit('update:modelValue', null)" @blur="alSalir" @keydown="teclas" />
    <ul v-if="abierto && opciones.length" :id="`${id}-lista`" class="sr-lista" role="listbox">
      <li v-for="(r, i) in opciones" :key="r.id" role="option" :aria-selected="i === activo" :class="{ activo: i === activo }"
          @mousedown.prevent="elegir(r)" @mouseenter="activo = i">
        <span v-if="r.codigo" class="mono">{{ r.codigo }}</span><span class="crece">{{ r.nombre }}</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.selector-referencia { position: relative; }
.selector-referencia .entrada { width: 100%; }
.sr-lista { position: absolute; z-index: 30; top: calc(100% + 4px); inset-inline: 0; margin: 0; padding: 4px; list-style: none; background: var(--superficie);
  border: 1px solid var(--linea); border-radius: var(--radio); box-shadow: var(--sombra-media); max-height: 260px; overflow-y: auto; }
.sr-lista li { display: flex; gap: 10px; align-items: center; padding: 8px 10px; border-radius: 6px; cursor: pointer; font-size: 0.9rem; }
.sr-lista li.activo { background: var(--acento-claro); }
</style>
