<template>
</template>

<script>
import {mapState} from 'vuex';
export default {
  computed: {
    ...mapState(['fingerprint'])
  },
  mounted() {
    if (!this.fingerprint) {
      this.generateFingerprint().then(fingerprint => {
        this.$store.commit('setFingerprint', fingerprint);
        console.log(fingerprint);
      });
    }
  },
  methods: {
    // 获取基本浏览器信息
    getBrowserFingerprint() {
      return {
        userAgent: navigator.userAgent,
        language: navigator.language,
        platform: navigator.platform,
        screen: {
          width: screen.width,
          height: screen.height,
          colorDepth: screen.colorDepth
        },
        timezoneOffset: new Date().getTimezoneOffset(),
        plugins: Array.from(navigator.plugins).map(p => p.name),
      };
    },

    // 生成 Canvas 指纹
    getCanvasFingerprint() {
      let canvas = document.createElement("canvas");
      let ctx = canvas.getContext("2d");
      ctx.textBaseline = "top";
      ctx.font = "14px 'Arial'";
      ctx.fillStyle = "#f60";
      ctx.fillText("Hello, Browser Fingerprint!", 10, 10);
      return canvas.toDataURL();
    },

    // 获取 WebGL 指纹
    getWebGLFingerprint() {
      let canvas = document.createElement("canvas");
      let gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
      if (!gl) return "WebGL Not Supported";

      let debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
      return {
        vendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : "Unknown",
        renderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : "Unknown",
      };
    },

    // 计算 SHA-256 哈希
    async generateFingerprint() {
      const data = JSON.stringify({
        browser: this.getBrowserFingerprint(),
        canvas: this.getCanvasFingerprint(),
        webgl: this.getWebGLFingerprint(),
      });

      const encoder = new TextEncoder();
      const hashBuffer = await crypto.subtle.digest("SHA-256", encoder.encode(data));
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
    },
  },
};
</script>