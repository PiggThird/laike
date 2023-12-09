import {reactive, ref} from "vue"
import http from '../utils/http'

const user = reactive({
    login_type: 0,  // 登陆方式 0：密码登录 1：短信登陆
    username: "",    // 登录账号/手机号/邮箱
    password: "",   // 登录密码
    remember: false,    // 是否记住登录状态
    mobile:"",          // 登录手机号码
    code:"",            // 短信验证码
    login(){
        // 用户登录
        return http.post("/users/login/",{
            "username": this.username,
            "password": this.password
        })
    }
})

export default user;