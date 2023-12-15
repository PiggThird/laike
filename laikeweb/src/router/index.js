import {createRouter, createWebHistory} from 'vue-router'
import store from "@/store";

// 路由列表
const routes = [
    {
        meta: {
            title: "Laike-站点首页",
            keepAlive: true
        },
        path: '/',         // uri访问地址
        name: "Home",
        component: () => import("../views/Home.vue")
    },
    {
        meta: {
            title: "Laike-用户登录",
            keepAlive: true
        },
        path: '/login',      // uri访问地址
        name: "Login",
        component: () => import("../views/Login.vue")
    },
    {
        meta: {
            title: "Laike-注册",
            keepAlive: true,
        },
        path: '/register',
        name: "Register",
        component: () => import("../views/Register.vue"),
    },
    {
        meta: {
            title: "Laike-个人中心",
            keepAlive: true,
            authorization: true,
        },
        path: '/user',
        name: "User",
        component: () => import("../views/User.vue"),
    },
    {
        meta: {
            title: "Laike-课程信息",
            keepAlive: true,
        },
        path: '/project',
        name: "Course",
        component: () => import("../views/Course.vue"),
    },
    {
        meta: {
            title: "Laike-课程详情",
            keepAlive: true
        },
        path: '/project/:id',     // :id vue的路径参数，代表了课程的ID
        name: "Info",
        component: () => import("../views/Info.vue"),
    },
    {
        meta: {
            title: "Laike-购物车",
            keepAlive: true
        },
        path: '/cart',
        name: "Cart",
        component: () => import("../views/Cart.vue"),
    },
    {
        meta: {
            title: "确认下单",
            keepAlive: true
        },
        path: '/order',
        name: "Order",
        component: () => import("../views/Order.vue"),
    },
    {
        meta: {
            title: "支付成功",
            keepAlive: true
        },
        path: '/alipay',
        name: "PaySuccess",
        component: () => import("../views/AliPaySuccess.vue"),
    },

]

// 路由对象实例化
const router = createRouter({
    // history, 指定路由的模式
    history: createWebHistory(),
    // 路由列表
    routes,
});

// 导航守卫
router.beforeEach((to, from, next) => {
    document.title = to.meta.title
    // 登录状态验证
    if (to.meta.authorization && !store.getters.getUserInfo) {
        next({"name": "Login"})
    } else {
        next()
    }
})

// 暴露路由对象
export default router