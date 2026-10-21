<script setup>
// Control de un atributo según su tipo de dato. Lo arma el esquema del registro
// (app/atributos/esquema.py): ninguna pantalla conoce los atributos de un rubro.
import { computed } from 'vue'
import Icono from './Icono.vue'
import SelectorReferencia from './SelectorReferencia.vue'

const props = defineProps({
  campo: { type: Object, required: true }, // {atributo, obligatorio, es_eje, heredado_de…}
  modelValue: { type: [String, Number, Boolean, Array, Object], default: null },
  unidades: { type: Array, default: () => [] },
  error: { type: String, default: '' },
  idBase: { type: String, default: 'attr' },
  etiqueta: { type: String, default: '' }, // en lugar del nombre del atributo
})
const emit = defineEmits(['update:modelValue'])
const a = computed(() => props.campo.atributo)
const id = computed(() => `${props.idBase}-${a.value.codigo}`)
const opciones = computed(() => (a.value.opciones || []).filter((o) => o.activa || [].concat(props.modelValue).includes(o.codigo)))
const unidadesMagnitud = computed(() => props.unidades.filter((u) => u.magnitud_id === a.value.magnitud_id && u.activa))
const conUnidad = computed(() => ['entero', 'decimal'].includes(a.value.tipo_dato) && a.value.magnitud_id)
const requerido = computed(() => props.campo.obligatorio || props.campo.es_eje)

const ayuda = computed(() => {
  const r = a.value.reglas || {}
  const partes = []
  if (a.value.descripcion) partes.push(a.value.descripcion)
  if (r.minimo !== undefined && r.maximo !== undefined) partes.push(`Entre ${r.minimo} y ${r.maximo}${a.value.unidad_defecto ? ` ${a.value.unidad_defecto}` : ''}`)
  else if (r.minimo !== undefined) partes.push(`Mínimo ${r.minimo}`)
  else if (r.maximo !== undefined) partes.push(`Máximo ${r.maximo}`)
  if (r.decimales !== undefined) partes.push(`hasta ${r.decimales} decimales`)
  if (r.patron) partes.push(`formato ${r.patron}`)
  return partes.join(' · ')
})

const valorNumero = computed(() => (conUnidad.value ? props.modelValue?.valor ?? '' : props.modelValue ?? ''))
const unidad = computed(() => props.modelValue?.unidad || a.value.unidad_defecto || unidadesMagnitud.value[0]?.codigo || '')

function numero(v) {
  const limpio = v === '' ? null : v
  if (conUnidad.value) emit('update:modelValue', limpio === null ? null : { valor: limpio, unidad: unidad.value })
  else emit('update:modelValue', limpio)
}
function cambiarUnidad(u) {
  emit('update:modelValue', valorNumero.value === '' ? null : { valor: valorNumero.value, unidad: u })
}
function alternar(codigo) {
  const actual = [...(props.modelValue || [])]
  const i = actual.indexOf(codigo)
  if (i >= 0) actual.splice(i, 1)
  else actual.push(codigo)
  emit('update:modelValue', actual.length ? actual : null)
}
</script>

<template>
  <div class="campo" :class="{ 'con-error': error }">
    <label :for="id" class="campo-titulo">
      <span :class="{ req: requerido }">{{ etiqueta || a.nombre }}</span>
      <span v-if="campo.heredado_de" class="heredado" :title="`Heredado del tipo ${campo.heredado_de}`"><Icono nombre="heredado" :tam="13" /></span>
    </label>

    <input v-if="a.tipo_dato === 'texto'" :id="id" class="entrada" type="text" :value="modelValue ?? ''"
           :maxlength="a.reglas?.longitud_max || 1000" :aria-invalid="!!error" @input="emit('update:modelValue', $event.target.value || null)" />

    <span v-else-if="['entero', 'decimal'].includes(a.tipo_dato)" class="con-unidad">
      <input :id="id" class="entrada num" type="number" inputmode="decimal" :step="a.tipo_dato === 'entero' ? 1 : 'any'"
             :value="valorNumero" :aria-invalid="!!error" @input="numero($event.target.value)" />
      <select v-if="conUnidad" class="entrada unidad" :value="unidad" :aria-label="`Unidad de ${a.nombre}`" @change="cambiarUnidad($event.target.value)">
        <option v-for="u in unidadesMagnitud" :key="u.id" :value="u.codigo">{{ u.simbolo || u.codigo }}</option>
      </select>
    </span>

    <label v-else-if="a.tipo_dato === 'booleano'" class="check si-no">
      <input :id="id" type="checkbox" :checked="!!modelValue" @change="emit('update:modelValue', $event.target.checked)" />{{ modelValue ? 'Sí' : 'No' }}
    </label>

    <input v-else-if="a.tipo_dato === 'fecha'" :id="id" class="entrada" type="date" :value="modelValue ?? ''" :min="a.reglas?.minimo"
           :max="a.reglas?.maximo" :aria-invalid="!!error" @input="emit('update:modelValue', $event.target.value || null)" />

    <select v-else-if="a.tipo_dato === 'opcion' && opciones.length > 6" :id="id" class="entrada" :value="modelValue ?? ''"
            :aria-invalid="!!error" @change="emit('update:modelValue', $event.target.value || null)">
      <option value="">Sin elegir</option>
      <option v-for="o in opciones" :key="o.codigo" :value="o.codigo">{{ o.nombre }}</option>
    </select>
    <div v-else-if="a.tipo_dato === 'opcion'" :id="id" class="opciones-chips" role="radiogroup" :aria-label="a.nombre">
      <button v-for="o in opciones" :key="o.codigo" type="button" role="radio" class="opcion-chip" :aria-checked="modelValue === o.codigo"
              @click="emit('update:modelValue', modelValue === o.codigo ? null : o.codigo)">{{ o.nombre }}</button>
    </div>

    <div v-else-if="a.tipo_dato === 'opciones'" :id="id" class="opciones-chips" role="group" :aria-label="a.nombre">
      <button v-for="o in opciones" :key="o.codigo" type="button" class="opcion-chip" :aria-pressed="(modelValue || []).includes(o.codigo)"
              @click="alternar(o.codigo)"><Icono v-if="(modelValue || []).includes(o.codigo)" nombre="check" :tam="13" />{{ o.nombre }}</button>
    </div>

    <SelectorReferencia v-else-if="a.tipo_dato === 'referencia'" :id="id" :entidad="a.entidad_referencia"
                        :model-value="modelValue" :invalido="!!error" @update:model-value="emit('update:modelValue', $event)" />

    <small v-if="error" class="campo-error" role="alert">{{ error }}</small>
    <small v-else-if="ayuda" class="ayuda">{{ ayuda }}</small>
  </div>
</template>

<style scoped>
.campo-titulo { display: inline-flex; align-items: center; gap: 4px; font-weight: 580; }
.heredado { color: var(--tinta-3); display: inline-flex; }
.con-unidad { display: flex; gap: 6px; }
.con-unidad .num { flex: 1; min-width: 0; text-align: end; }
.con-unidad .unidad { width: 86px; flex: none; }
.si-no { min-height: 36px; }
</style>
