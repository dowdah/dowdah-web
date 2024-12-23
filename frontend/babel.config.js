module.exports = {
  plugins: [
    ['import', {
      libraryName: '@ant-design/icons-vue',
      libraryDirectory: 'es', // 使用 'es' 目录
      camel2DashComponentName: false // 禁用驼峰命名转换
    }, '@ant-design/icons-vue']
  ]
};
