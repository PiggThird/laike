import {reactive, ref} from "vue"
import http from '../utils/http'

const user = reactive({
    login_type: 0,      // 登陆方式 0：密码登录 1：短信登陆
    username: "",       // 登录账号/手机号/邮箱
    password: "",       // 登录密码
    re_password: "",    // 确认密码
    remember: false,    // 是否记住登录状态
    mobile:"",          // 登录手机号码
    code:"",            // 短信验证码
    is_send: false,     // 短信发送的标记
    sms_btn_text: "点击获取验证码", // 短信按钮提示
    sms_interval: 60,   // 间隔时间
    interval: null,     // 定时器的标记
    login(){
        // 用户登录
        return http.post("/users/login/",{
            "username": this.username,
            "password": this.password
        })
    },
    login_sms(){
        // 用户登录
        return http.post("/users/code_login/",{
            "mobile": this.mobile,
            "code": this.code
        })
    },
    check_mobile(){
        // 验证手机号
        return http.get(`/users/mobile/${this.mobile}/`)
    },
    register(data){
        data.mobile = this.mobile
        data.re_password = this.re_password
        data.password = this.password
        data.sms_code = this.code
        // 用户注册请求
        return http.post("/users/register/", data)
    },
    get_sms_code(){
        return http.get(`/users/sms/${this.mobile}/`)
    }
})

export default user;