import http from "../utils/http"
import {reactive, ref} from "vue"

const nav = reactive({
    header_nav_list: [],    // 头部导航列表
    footer_nav_list: [],    // 底部导航列表
    get_header_nav(){
        // 获取头部导航
        return http.get("/home/nav/header")
    },
    get_footer_nav(){
        // 获取底部导航
        return http.get("/home/nav/footer")
    },
})

export default nav;