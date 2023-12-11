import {createStore} from "vuex"
import createPersistedState from "vuex-persistedstate"

// 实例化一个vuex存储库
export default createStore({
    // 调用永久存储vuex数据的插件，localstorage里会多一个名叫vuex的Key，里面就是vuex的数据
    plugins: [createPersistedState()],
    state() {                      // 数据存储位置，相当于组件中的data
        return {
            user: {}
        }
    },
    getters: {
        getUserInfo(state) {
            // 从jwt的载荷中提取用户信息
            let now = parseInt((new Date() - 0) / 1000);
            if (state.user.exp === undefined) {
                // 没登录
                state.user = {}
                localStorage.token = null;
                sessionStorage.token = null;
                return null
            }

            if (parseInt(state.user.exp) < now) {
                // 过期处理
                state.user = {}
                localStorage.token = null;
                sessionStorage.token = null;
                return null
            }
            return state.user;
        }
    },
    mutations: {                    // 操作数据的方法，相当于methods
        login(state, user) {       // state 就是上面的state,mutations中每一个方法都默认第一个参数是它   state.user 就是上面的数据
            state.user = user
        },
        logout(state) {             // 退出登录
            state.user = {}
            localStorage.token = null;
            sessionStorage.token = null;
        }
    }
})