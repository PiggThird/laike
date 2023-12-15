const {defineConfig} = require('@vue/cli-service')
module.exports = defineConfig({
    transpileDependencies: true,
    lintOnSave: false,   /*关闭语法检查*/
    devServer:{
        client:{
            overlay:{
                warnings: false,
                errors: true,
                runtimeErrors: false
            }
        }
    }
})

