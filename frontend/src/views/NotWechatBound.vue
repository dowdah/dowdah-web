<template>
  <div v-if="wechatBinding && !wechatPoll.bound">
    <a-image
        :width="200"
        src="https://r2.dowdah.com/wechat_service_qr_code_min.png"
        :preview="{src: 'https://r2.dowdah.com/wechat_service_qr_code.png',
                title: '扫码关注服务号'}"/>
    <p style="margin: 10px 0 0 0;">关注微信服务号后，发送以下信息提交您的微信绑定申请：</p>
    <a-typography-paragraph copyable style="margin-bottom: 0; font-weight: bold; text-decoration: underline">
      /绑定 {{ user.email }}
    </a-typography-paragraph>
    <p style="margin-bottom: 0;">提交绑定申请后，需要等待绑定状态更新，等待时间通常是5秒。</p>
    <a-flex justify="space-between" align="center" style="margin-bottom: 10px;">
      <p>当前绑定状态: {{ wechatPoll.bound ? '已提交绑定申请' : '未提交绑定申请' }}</p>
      <a-button v-if="showManualBind" size="small" @click="handleCheckWechat" :disabled="wechatCooldown > 0">
        {{ wechatCooldown > 0 ? wechatCooldown + '秒后可重试' : '刷新绑定状态' }}
        <template #icon>
          <ReloadOutlined/>
        </template>
      </a-button>
    </a-flex>
  </div>

  <a-result v-if="!wechatBinding && !wechatPoll.bound" status="error"
            title="您必须绑定微信才能正常使用Dowdah账户" sub-title="请前往绑定页面进行微信绑定">
    <template #extra>
      <a-button type="primary" @click="handleStartBinding">前往绑定页面</a-button>
    </template>
  </a-result>

  <a-result
    status="success"
    title="微信绑定成功"
    sub-title="您已可以正常使用您的账户"
    v-if="wechatPoll.bound && !wechatBinding"
  >
    <template #extra>
      <a-button type="primary" @click="handleReturnHomePage">回到主页</a-button>
    </template>
  </a-result>
</template>

<script>
import {mapActions, mapState} from 'vuex';
import apiClient from "@/api";
import {ReloadOutlined} from '@ant-design/icons-vue';

export default {
  name: 'NotWechatBound',
  data() {
    return {
      wechatBinding: false,
      wechatPoll: {
        bound: false,
        count: 0,
        interval: null
      },
      wechatCooldown: 0,
      wechatTimer: null,
      showManualBind: false,
    };
  },
  computed: {
    ...mapState(['user']),
  },
  components: {
    ReloadOutlined
  },
  methods: {
    ...mapActions(["init"]),
    async checkWechatBind() {
      // 检查微信绑定状态
      let response;
      try {
        response = await apiClient.get("/auth/bind-wechat");
      } catch (error) {
        const response = error.response;
        if (response) {
          this.showManualBind = true;
          this.stopWechatPolling()
          this.$message.error(response.data.msg);
        }
        console.error('Check Wechat bind status error:', error);
        return;
      }
      if (response.data.success) {
        if (response.data.wechat_bound) {
          this.wechatPoll.bound = true;
          this.wechatBinding = false;
          this.stopWechatPolling();
          this.$message.success('微信绑定成功！');
        }
      }
      this.wechatPoll.count++;
      // 最大轮询次数为10次
      if (this.wechatPoll.count >= 10) {
        this.$message.error('未能自动取得微信绑定结果，请您发送绑定消息后手动查询。');
        this.stopWechatPolling();
        this.showManualBind = true;
      }
    },
    startWechatPolling() {
      // 开始微信绑定状态轮询
      this.wechatPoll.interval = setInterval(this.checkWechatBind, 5000);
    },
    stopWechatPolling() {
      // 停止微信绑定状态轮询
      clearInterval(this.wechatPoll.interval);
      this.wechatPoll.interval = null;
      this.wechatPoll.count = 0;
    },
    startWechatCooldown() {
      // 开始微信冷却
      this.wechatCooldown = 5;
      this.wechatTimer = setInterval(() => {
        this.wechatCooldown--;
        if (this.wechatCooldown <= 0) {
          clearInterval(this.wechatTimer);
          this.wechatTimer = null;
        }
      }, 1000);
    },
    async handleCheckWechat() {
      // 检查微信绑定状态
      if (this.wechatCooldown > 0) return;
      this.startWechatCooldown();
      let response;
      try {
        response = await apiClient.get("/auth/bind-wechat");
      } catch (error) {
        const response = error.response;
        if (response) {
          this.showManualBind = true;
          this.stopWechatPolling()
          this.$message.error(response.data.msg);
        }
        console.error('Check Wechat bind status error:', error);
        return;
      }
      if (response.data.success) {
        if (response.data.wechat_bound) {
          this.wechatPoll.bound = true;
          this.wechatBinding = false;
          this.showManualBind = false;
          if (this.wechatPoll.interval) {
            this.stopWechatPolling();
          }
          this.$message.success('微信绑定成功！');
        } else {
          this.$message.error('暂未收到您的微信绑定请求。');
        }
      } else {
        this.$message.error('检查微信绑定状态失败，请稍后重试。');
      }
    },
    handleStartBinding() {
      this.wechatBinding = true;
      this.startWechatPolling();
    },
    handleReturnHomePage() {
      if (this.$route.path === '/') {
        this.init()
      } else {
        this.$router.push('/');
      }
    }
  }
};
</script>
