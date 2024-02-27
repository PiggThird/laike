<template>
  <div class="footer">
    <ul>
      <li v-for="nav in nav.footer_nav_list">
        <a :href="nav.link" v-if="nav.is_http">{{ nav.name }}</a>
        <router-link :to="nav.link" v-else>{{ nav.name }}</router-link>
      </li>
    </ul>
    <p>Copyright © Laike.com版权所有 | 京ICP备88888888号-1</p>
  </div>
</template>

<script setup>
import nav from "@/api/nav";

nav.get_footer_nav().then(response => {
  nav.footer_nav_list = response.data
})

</script>

<style scoped>
.footer {
  width: 100%;
  height: 128px;
  color: #545C63;
  background: #25292e;
  position: absolute;
  bottom: 0;
}

.footer ul {
  margin: 0 auto 16px;
  padding-top: 38px;
  width: 930px;
}

.footer ul li {
  float: left;
  width: 112px;
  margin: 0 10px;
  text-align: center;
  font-size: 14px;
}

.footer ul li a {
  text-decoration: none;
  color: white;
  cursor: pointer;
}

.footer ul::after {
  content: "";
  display: block;
  clear: both;
}

.footer p {
  text-align: center;
  font-size: 12px;
}
</style>