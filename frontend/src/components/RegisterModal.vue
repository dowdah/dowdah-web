<template>
  <a-modal v-model:open="open" title="注册" centered>
    <template #footer>
    </template>
    <div>
      <a-steps :current="currentStep" :items="steps" style="margin-bottom: 20px"></a-steps>
      <div class="step-1" v-if="currentStep === 0">
        <a-form
            :model="formState"
            :rules="rules"
            ref="registerForm"
            name="normal_register"
            class="register-form"
            @validate="handleValidate"
        >
          <a-form-item
              name="username"
          >
            <a-input v-model:value="formState.username" placeholder="用户名" autocomplete="off">
              <template #prefix>
                <UserOutlined class="site-form-item-icon"/>
              </template>
              <template #suffix>
                <a-tooltip class="username-hint"
                           title="用户名的长度应在三到二十个字符之间，仅允许使用英文字母、数字、下划线和点。用户名不能以下划线或点开头或结尾，也不能包含连续的下划线或点，同时禁止使用空格及其他特殊符号。">
                  <QuestionCircleOutlined />
                </a-tooltip>
              </template>
            </a-input>
          </a-form-item>
          <a-form-item
              name="email"
              type="email"
          >
            <a-input v-model:value="formState.email" placeholder="邮箱" autocomplete="off">
              <template #prefix>
                <MailOutlined class="site-form-item-icon"/>
              </template>
            </a-input>
          </a-form-item>
          <a-form-item
              name="password"
          >
            <a-input-password v-model:value="formState.password" placeholder="密码" autocomplete="off"
                              @pressEnter="nextStep">
              <template #prefix>
                <LockOutlined class="site-form-item-icon"/>
              </template>
            </a-input-password>
          </a-form-item>
          <a-form-item name="agreeToS">
            <a-checkbox v-model:checked="formState.agreeToS">我已阅读并同意<a href="https://r2.dowdah.com/Dowdah_ToS.txt"
                                                        target="_blank">《服务条款》</a></a-checkbox>
          </a-form-item>
        </a-form>
      </div>
      <div class="step-2" v-if="currentStep === 1">
        <p>确认您的邮箱为：{{ formState.email }}</p>
        <a-flex justify="space-around" align="center">
          <Turnstile ref="turnstile" v-model:cf-token="cfToken" action="send_email_code_and_register"/>
          <a-button type="primary" @click="sendEmailCode" :loading="sendCodeLoading || sendCodeCooldown > 0"
                    :disabled="!turnstileVerified || sendCodeCooldown > 0">
            {{ sendCodeCooldown > 0 ? sendCodeCooldown + '秒后可重发' : '发送验证码' }}
          </a-button>
        </a-flex>
        <a-input v-model:value="emailCode" placeholder="请输入6位数字验证码" autocomplete="off"
                 @change="validateCode" ref="emailCodeInput" style="margin-top: 10px;"
                 @pressEnter="nextStep" :status="codeStatus">
          <template #prefix>
            <SecurityScanOutlined class="site-form-item-icon"/>
          </template>
        </a-input>
        <p :style="{color: 'red', 'margin-bottom': '20px', opacity: codeStatus === '' ? '0':'1'}">请输入6位数字验证码</p>
      </div>
      <div class="step-3" v-if="currentStep === 2">
        <p>注册成功！</p>
      </div>
      <a-flex justify="space-around" align="center">
        <a-button v-if="currentStep === 1" @click="previousStep" shape="circle">
          <caret-left-outlined/>
        </a-button>
        <a-button v-if="currentStep < steps.length - 1" type="primary" @click="nextStep" shape="circle"
                  :disabled="nextStepDisabled">
          <caret-right-outlined/>
        </a-button>
        <a-button
            v-if="currentStep === steps.length - 1"
            type="primary"
            @click="this.open = false"
            shape="circle"
        >
          <CheckOutlined/>
        </a-button>
      </a-flex>
    </div>
  </a-modal>
</template>

<script>
import {
  UserOutlined, LockOutlined, MailOutlined, QuestionCircleOutlined, SendOutlined,
  SolutionOutlined, FileDoneOutlined, CaretRightOutlined, CaretLeftOutlined,
  CheckOutlined, SecurityScanOutlined
} from '@ant-design/icons-vue';
import {mapActions, mapGetters, mapState} from 'vuex';
import {TURNSTILE_VERIFY_URL, EMAIL_REGEX, USERNAME_REGEX, PASSWORD_REGEX} from "../config/constants";
import apiClient from "@/api";
import Turnstile from "../components/Turnstile.vue";
import axios from 'axios';
import {h} from 'vue';

export default {
  name: 'RegisterModal',
  props: ['mOpen'],
  emits: ['update:mOpen'],
  components: {
    UserOutlined,
    LockOutlined,
    MailOutlined,
    QuestionCircleOutlined,
    SendOutlined,
    SolutionOutlined,
    FileDoneOutlined,
    CaretRightOutlined,
    CaretLeftOutlined,
    CheckOutlined,
    SecurityScanOutlined,
    Turnstile
  },
  data() {
    return {
      formState: {
        username: '',
        email: '',
        password: '',
        agreeToS: false
      },
      rules: {
        username: [
          {validator: this.validateUsername, trigger: 'blur'}
        ],
        email: [
          {validator: this.validateEmail, trigger: 'blur'}
        ],
        password: [
          {validator: this.validatePassword, trigger: 'blur'}
        ],
        agreeToS: [
          {validator: this.validateAgreeToS, trigger: ['change', 'blur']}
        ]
      },
      cfToken: '',
      turnstileVerifyResponse: null,
      turnstileVerified: false,
      steps: [
        {
          title: '填写信息',
          icon: h(SolutionOutlined)
        },
        {
          title: '验证邮箱',
          icon: h(SendOutlined)
        },
        {
          title: '完成注册',
          icon: h(FileDoneOutlined)
        }
      ],
      currentStep: 0,
      nextStepDisabled: false,
      sendCodeLoading: false,
      emailCode: '',
      sendCodeCooldown: 0,
      sendCodeTimer: null,
      taskId: '',
      pollCount: 0,
      pollInterval: null,
      codeStatus: ''
    };
  },
  methods: {
    ...mapActions(['register', 'webauthnLoginComplete']),
    handleValidate(...args) {
      console.log('validate', args);
    },
    async validateUsername(_rule, value) {
      if (!value) {
        return Promise.reject('请输入用户名');
      } else if (!USERNAME_REGEX.test(value)) {
        return Promise.reject('用户名格式不正确');
      } else {
        const response = await this.userExists('username');
        if (response.success) {
          if (response.exists) {
            return Promise.reject('用户名已被注册');
          } else {
            return Promise.resolve();
          }
        } else {
          return Promise.reject(response.msg);
        }
      }
    },
    async validateEmail(_rule, value) {
      if (!value) {
        return Promise.reject('请输入邮箱');
      } else if (!EMAIL_REGEX.test(value)) {
        return Promise.reject('邮箱格式不正确');
      } else {
        const response = await this.userExists('email');
        if (response.success) {
          if (response.exists) {
            return Promise.reject('邮箱已被注册');
          } else {
            return Promise.resolve();
          }
        } else {
          return Promise.reject(response.msg);
        }
      }
    },
    async validatePassword(_rule, value) {
      if (!value) {
        return Promise.reject('请输入密码');
      } else if (!PASSWORD_REGEX.test(value)) {
        return Promise.reject('密码至少包含一个大写字母、一个小写字母、一个数字和一个特殊字符，长度至少为8个字符');
      } else {
        return Promise.resolve();
      }
    },
    async validateAgreeToS(_rule, value) {
      if (value) {
        return Promise.resolve();
      } else {
        return Promise.reject('请阅读并同意服务条款');
      }
    },
    async verifyTurnstile(cfToken) {
      let formData = new FormData();
      let response
      formData.append('token', cfToken);
      try {
        response = await axios.post(TURNSTILE_VERIFY_URL, formData);
      } catch (error) {
        this.$message.error('Turnstile 服务器端校验出错，请刷新页面重试');
        console.error('Turnstile verify error:', error);
        this.turnstileVerifyResponse = null;
        this.turnstileVerified = false;
        return;
      }
      if (response && response.status === 200) {
        this.turnstileVerifyResponse = response.data.cfResponse;
        this.turnstileVerified = true;
      } else {
        this.$message.error('Turnstile 服务器端校验超时，请刷新页面重试');
        this.turnstileVerifyResponse = null;
        this.turnstileVerified = false;
      }
    },
    validateCode() {
      this.emailCode = this.emailCode.replace(/\s/g, '');
      if (!/^[0-9]{6}$/.test(this.emailCode)) {
        this.codeStatus = 'error';
        return false;
      } else {
        this.codeStatus = '';
        return true;
      }
    },
    resetTurnstile() {
      if (this.open) {
        this.turnstileVerifyResponse = null;
        this.turnstileVerified = false;
        this.$refs.turnstile.reset();
      }
    },
    async userExists(field) {
      let response;
      try {
        if (field === 'username') {
          response = await apiClient.post('/user/exists', {username: this.formState.username});
        } else if (field === 'email') {
          response = await apiClient.post('/user/exists', {email: this.formState.email});
        }
      } catch (error) {
        return {
          success: false,
          msg: '网络错误'
        }
      }
      return response.data
    },
    async nextStep() {
      if (this.currentStep === 0) {
        if (!this.formState.agreeToS) {
          this.$message.error('请阅读并同意服务条款');
          return;
        }
        this.nextStepDisabled = true;
        try {
          await this.$refs.registerForm.validate();
          this.currentStep++;
        } catch (e) {
          this.$message.error('请检查输入信息是否正确');
        } finally {
          this.nextStepDisabled = false;
        }
      } else if (this.currentStep === 1) {
        if (this.turnstileVerified) {
          if (this.validateCode()) {
            this.nextStepDisabled = true;
            const responseData = await this.register(this.payload);
            if (responseData.success) {
              this.currentStep++;
              const route = this.$route;
              const blockedForAuthenticated = route.meta && route.meta.blockedForAuthenticated;
              if (blockedForAuthenticated) {
                this.$router.push('/');
              }
            } else {
              this.$message.error(responseData.msg);
              this.resetTurnstile();
            }
            this.nextStepDisabled = false;
          } else {
            this.$message.error('请输入6位数字验证码');
          }
        } else {
          this.$message.error('请完成 Turnstile 验证');
        }
      }
    },
    async sendEmailCode() {
      if (this.sendCodeCooldown > 0) return;
      if (this.turnstileVerified) {
        let response;
        this.sendCodeLoading = true;
        try {
          response = await apiClient.post('/auth/send-email-code', {
            email: this.formState.email,
            turnstile: this.turnstileVerifyResponse,
            fingerprint: this.fingerprint
          });
        } catch (error) {
          this.$message.error('发送邮件失败');
          this.sendCodeLoading = false;
          return;
        }
        if (response.data.success) {
          this.startCooldown();
          this.taskId = response.data.task_id;
          this.startPolling();
        } else {
          this.$message.error(response.data.msg);
        }
        this.sendCodeLoading = false;
        this.resetTurnstile();
      } else {
        this.$message.error('请完成 Turnstile 验证');
      }
    },
    previousStep() {
      this.currentStep--;
    },
    startCooldown() {
      this.sendCodeCooldown = 60;
      this.timer = setInterval(() => {
        this.sendCodeCooldown--;
        if (this.sendCodeCooldown <= 0) {
          clearInterval(this.timer);
          this.timer = null;
        }
      }, 1000);
    },
    async checkTaskStatus() {
      if (!this.taskId) return
      let response;
      try {
        response = await apiClient.get(`/task/${this.taskId}`)
      } catch (error) {
        console.error('Check task status error:', error)
      }
      if (response.data.success) {
        if (response.data.task_result) {
          if (response.data.task_result.success) {
            this.$message.success(`验证码已发送至${response.data.task_result.to}`)
          } else {
            this.$message.error('验证码发送失败，这可能是由于您的邮箱地址无效或者服务器网络出现问题。')
            // 确认服务器邮件发送出错，取消发送邮件冷却，方便用户重新申请验证码
            clearInterval(this.timer);
            this.timer = null;
            this.sendCodeCooldown = 0;
          }
          this.stopPolling();
        }
      }
      this.pollCount++;
      // 最大轮询次数为4次
      if (this.pollCount >= 4) {
        this.$message.error('未取得验证码发送结果，请自行检查您是否收到验证码邮件。');
        this.stopPolling();
      }
    },
    startPolling() {
      this.pollInterval = setInterval(this.checkTaskStatus, 1750);
    },
    stopPolling() {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
      this.pollCount = 0;
      this.taskId = '';
    }
  },
  computed: {
    ...mapState(['fingerprint']),
    ...mapGetters(['isAuthenticated']),
    open: {
      get() {
        return this.mOpen;
      },
      set(value) {
        this.$emit('update:mOpen', value);
      },
    },
    payload() {
      return {
        username: this.formState.username,
        email: this.formState.email,
        code: this.emailCode.replace(/ /g, ""),
        password: this.formState.password,
        turnstile: this.turnstileVerifyResponse,
        fingerprint: this.fingerprint
      }
    }
  },
  watch: {
    cfToken(val) {
      if (val) {
        this.verifyTurnstile(val);
      }
    },
    open(val) {
      if (val) {
        this.turnstileVerified = false;
        this.turnstileVerifyResponse = null;
        this.currentStep = 0;
        this.formState = {
          username: '',
          email: '',
          password: ''
        }
        this.emailCode = '';
      }
    }
  }
};
</script>

<style>
.site-form-item-icon {
  margin-right: 8px;
}
.username-hint {
  opacity: 0.45;
  transition: opacity 0.3s;
}
.username-hint:hover {
  opacity: 1;
}
</style>
