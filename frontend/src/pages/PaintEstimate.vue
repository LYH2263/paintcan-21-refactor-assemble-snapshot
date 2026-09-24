<script setup>
import { ref } from 'vue'
import { postJSON } from '../api'
const room_id = ref(1)
const out = ref(null)
const run = async () => { out.value = await postJSON('/api/estimate', { room_id: room_id.value, persist: true }) }
</script>
<template><div class="page"><h1>估漆工作台</h1>
<label>房间ID <input v-model.number="room_id" /></label>
<button @click="run">估算</button>
<p v-if="out">净 {{ out.net_m2 }} m² · {{ out.liters }} 升 · {{ out.coats }} 遍</p></div></template>
