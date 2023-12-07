<template>
  <div class="home">
    <Header></Header>

    <Footer></Footer>
  </div>
</template>

<script setup>
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

// 测试CORS的跨域配置是否有问题
import http from "@/utils/http";

http.get("/home/regi").then(response => {
  console.log(response.data);
})

</script>


<style scoped>

</style>