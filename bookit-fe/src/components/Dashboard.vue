<script setup>
import { ref } from 'vue'

const resData = ref([])
const showModal = ref(false)

const fetchData = () => {
  fetch('http://127.0.0.1:5000/api')
    .then((res) => res.json())
    .then((data) => {
      resData.value = data.data
      console.log(data)
    })
}
fetchData()
</script>

<template>
  <div class="container text-center">
    <h2 class="text-danger fw-bold mb-3 col">All Movies</h2>
    <button
      class="btn btn-danger mb-3 col"
      :on-click="
        () => {
          showModal.value = !showModal.value
        }
      "
    >
      Create a movie
    </button>
    <div class="row">
      <div class="card mx-3 my-1" style="width: 18rem" v-for="item in resData">
        <div class="card-body">
          <h5 class="card-title">{{ item.name }}</h5>
          <p>{{ item.rating ? item.rating : 0 }}</p>
          <p>Tags: {{ item.tags }}</p>
          <p>Price: Rs.{{ item.ticketPrice }}</p>
          <a href="#" class="btn btn-danger w-100">Buy Now</a>
        </div>
      </div>
    </div>
  </div>
</template>
