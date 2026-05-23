<template>
  <div id="app">
    <router-view style="flex: 1;" />
    <footer class="site-footer">
      <a href="http://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">赣ICP备2026010457号-1</a>
    </footer>
  </div>
</template>

<script setup>
// 主应用组件
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  color-scheme: light;
}

body {
  font-family: Inter, 'Helvetica Neue', Helvetica, 'PingFang SC',
    'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  line-height: 1.5;
}

#app {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.site-footer {
  flex-shrink: 0;
  text-align: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-top: 1px solid #e9ecef;
  color: #666;
  font-size: 13px;
}

.site-footer a {
  color: #666;
  text-decoration: none;
  transition: color 0.2s;
}

.site-footer a:hover {
  color: #333;
  text-decoration: underline;
}
</style>
