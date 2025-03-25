<template>
  <a-modal v-model:open="open" title="输入你的凭据" @ok="handleOk" centered>
    <template #footer>
      <a-button key="back" @click="handleCancel">取消</a-button>
      <a-button key="submit" type="primary" :loading="loading" @click="handleOk" :disabled="disabled">登录</a-button>
    </template>
    <a-form
        :model="formState"
        :rules="rules"
        ref="loginForm"
        name="normal_login"
        class="login-form"
    >
      <a-form-item label="登录方式">
        <a-radio-group v-model:value="formState.loginMethod">
          <a-radio-button value="username">用户名</a-radio-button>
          <a-radio-button value="email">邮箱</a-radio-button>
          <a-radio-button value="passkey" :disabled="passkeyDisabled">
            通行密钥
            <a-tooltip title="您的设备不支持 WebAuthn，无法使用通行密钥登录" v-if="passkeyDisabled">
              <QuestionCircleOutlined/>
            </a-tooltip>
            <a-tooltip title="使用通行密钥登录，安全又便捷。" v-else>
              <QuestionCircleOutlined/>
            </a-tooltip>
          </a-radio-button>
        </a-radio-group>
      </a-form-item>
      <a-form-item
          name="username"
          v-if="formState.loginMethod === 'username'"
      >
        <a-input v-model:value="formState.username" placeholder="用户名" autocomplete="username">
          <template #prefix>
            <UserOutlined class="site-form-item-icon"/>
          </template>
        </a-input>
      </a-form-item>

      <a-form-item
          name="email"
          v-if="formState.loginMethod === 'email'"
          type="email"
      >
        <a-input v-model:value="formState.email" placeholder="邮箱" autocomplete="email">
          <template #prefix>
            <MailOutlined class="site-form-item-icon"/>
          </template>
        </a-input>
      </a-form-item>

      <a-form-item
          name="password"
          v-if="formState.loginMethod !== 'passkey'"
      >
        <a-input-password v-model:value="formState.password" placeholder="密码" autocomplete="password">
          <template #prefix>
            <LockOutlined class="site-form-item-icon"/>
          </template>
        </a-input-password>
      </a-form-item>
      <p v-if="formState.loginMethod === 'passkey'">您已选择使用通行密钥登录。注意，您必须已经注册
        WebAuthn 才能够使用其登录。</p>
      <a-form-item name="agreeToS">
        <a-checkbox v-model:checked="formState.agreeToS">我已阅读并同意<a href="https://r2.dowdah.com/Dowdah_ToS.txt"
                                                                          target="_blank">《服务条款》</a></a-checkbox>
      </a-form-item>
      <a-flex justify="center" align="center" v-if="open && formState.loginMethod !== 'passkey'">
        <Turnstile ref="turnstile" v-model:cf-token="token" action="login"/>
      </a-flex>
      <a-form-item v-if="failedResponseData.code === 401">
        <!--        <RouterLink to="/reset-pwd" style="float: right">忘记密码？</RouterLink>-->
        <a href="#" style="float: right">忘记密码？</a>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script>
import {UserOutlined, LockOutlined, MailOutlined, QuestionCircleOutlined} from '@ant-design/icons-vue';
import {mapActions, mapGetters, mapState} from 'vuex';
import {TURNSTILE_VERIFY_URL, EMAIL_REGEX, USERNAME_REGEX, PASSWORD_REGEX} from "../config/constants";
import apiClient from "@/api";
import Turnstile from "../components/Turnstile.vue";
import axios from 'axios';

export default {
  name: 'LoginModal',
  props: ['mOpen'],
  emits: ['update:mOpen'],
  components: {
    UserOutlined,
    LockOutlined,
    MailOutlined,
    QuestionCircleOutlined,
    Turnstile
  },
  data() {
    return {
      loading: false,
      failedLogin: false,
      failedResponseData: {},
      formState: {
        username: '',
        password: '',
        email: '',
        loginMethod: 'username',
        agreeToS: false,
      },
      rules: {
        username: [
          {validator: this.validateUsername, trigger: 'change'}
        ],
        email: [
          {validator: this.validateEmail, trigger: 'change'}
        ],
        password: [
          {validator: this.validatePassword, trigger: 'change'}
        ],
        agreeToS: [
          {validator: this.validateAgreeToS, trigger: ['change', 'blur']}
        ]
      },
      passkeyDisabled: false,
      token: '',
      turnstileVerifyResponse: null,
      turnstileVerified: false,
    };
  },
  methods: {
    ...mapActions(['login', 'webauthnLoginComplete']),
    async handleOk() {
      this.loading = true;
      const route = this.$route;
      const blockedForAuthenticated = route.meta && route.meta.blockedForAuthenticated;
      if (this.formState.loginMethod === 'passkey') {
        await this.handleWebAuthnLogin();
      } else {
        try {
          await this.login(this.credentials);
        } catch (error) {
          this.failedLogin = true;
          this.failedResponseData = error.response.data;
        }
      }
      this.loading = false;
      if (this.isAuthenticated) {
        this.open = false;
        this.$message.success('登录成功');
        if (blockedForAuthenticated) {
          this.$router.push('/');
        }
      } else {
        this.resetTurnstile()
        this.$message.error(this.failedResponseData.msg);
      }
    },
    handleCancel() {
      this.open = false;
    },
    async validateUsername(_rule, value) {
      if (this.formState.loginMethod === 'username') {
        if (!value) {
          return Promise.reject('请输入用户名');
        } else if (!USERNAME_REGEX.test(value)) {
          return Promise.reject('用户名格式不正确');
        } else {
          return Promise.resolve();
        }
      } else {
        return Promise.resolve();
      }
    },
    async validateEmail(_rule, value) {
      if (this.formState.loginMethod === 'email') {
        if (!value) {
          return Promise.reject('请输入邮箱');
        } else if (!EMAIL_REGEX.test(value)) {
          return Promise.reject('邮箱格式不正确');
        } else {
          return Promise.resolve();
        }
      } else {
        return Promise.resolve();
      }
    },
    async validatePassword(_rule, value) {
      if (this.formState.loginMethod !== 'passkey') {
        if (!value) {
          return Promise.reject('请输入密码');
        } else if (!PASSWORD_REGEX.test(value)) {
          return Promise.reject('密码格式不正确');
        } else {
          return Promise.resolve();
        }
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
    async handleWebAuthnLogin() {
      let errorOccurred = false;
      let response;
      try {
        response = await apiClient.get('/webauthn/login/begin');
      } catch (error) {
        console.error('WebAuthn Login Begin error:', error);
        this.failedLogin = true;
        this.failedResponseData = error.response.data;
        errorOccurred = true;
      }
      if (!errorOccurred) {
        try {
          const options = response.data.options;
          const publicKey = {
            ...options,
            challenge: this.base64urlToArrayBuffer(options.challenge),
            allowCredentials: options.allowCredentials.map(cred => ({
              ...cred,
              id: this.base64urlToArrayBuffer(cred.id)
            }))
          };
          const assertion = await navigator.credentials.get({publicKey});
          const assertionResponse = {
            id: assertion.id,
            rawId: this.arrayBufferToBase64url(assertion.rawId),
            response: {
              clientDataJSON: this.arrayBufferToBase64url(assertion.response.clientDataJSON),
              authenticatorData: this.arrayBufferToBase64url(assertion.response.authenticatorData),
              signature: this.arrayBufferToBase64url(assertion.response.signature),
              userHandle: assertion.response.userHandle ? this.arrayBufferToBase64url(assertion.response.userHandle) : null
            },
            type: assertion.type,
            challenge: options.challenge
          };
          await this.webauthnLoginComplete(assertionResponse);
        } catch (error) {
          console.error('WebAuthn login error:', error);
          this.failedLogin = true;
          if (error.response) {
            this.failedResponseData = error.response.data;
          } else {
            switch (error.name) {
              case 'NotAllowedError':
                this.failedResponseData = {msg: '您拒绝了登录请求'};
                break;
              case 'InvalidStateError':
                this.failedResponseData = {msg: '登录请求已过期，请重试'};
                break;
              default:
                this.failedResponseData = {msg: '未知错误'};
            }
          }
        }
      }
    },
    base64urlToArrayBuffer(base64url) {
      return Uint8Array.from(atob(base64url.replace(/-/g, '+').replace(/_/g, '/')), c => c.charCodeAt(0));
    },
    arrayBufferToBase64url(buffer) {
      return btoa(String.fromCharCode(...new Uint8Array(buffer)))
          .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
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
    resetTurnstile() {
      if (this.open) {
        this.turnstileVerifyResponse = null;
        this.turnstileVerified = false;
        this.$refs.turnstile.reset();
      }
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
    disabled() {
      if (!this.formState.agreeToS) {
        return true;
      }
      switch (this.formState.loginMethod) {
        case 'username':
          return !USERNAME_REGEX.test(this.formState.username)
              || !PASSWORD_REGEX.test(this.formState.password) || !this.turnstileVerified;
        case 'email':
          return !EMAIL_REGEX.test(this.formState.email)
              || !PASSWORD_REGEX.test(this.formState.password) || !this.turnstileVerified;
        case 'passkey':
          return this.passkeyDisabled
      }
    },
    credentials() {
      return this.formState.loginMethod === 'username'
          ? {
            username: this.formState.username,
            password: this.formState.password,
            turnstile: this.turnstileVerifyResponse,
            fingerprint: this.fingerprint
          }
          : {
            email: this.formState.email,
            password: this.formState.password,
            turnstile: this.turnstileVerifyResponse,
            fingerprint: this.fingerprint
          };
    }
  },
  watch: {
    'formState.loginMethod'(value) {
      this.failedLogin = false;
      this.failedResponseData = {};
    },
    token(val) {
      if (val) {
        this.verifyTurnstile(val);
      }
    },
    open(val) {
      if (val) {
        this.failedLogin = false;
        this.failedResponseData = {};
        this.turnstileVerified = false;
        this.turnstileVerifyResponse = null;
        this.formState = {
          username: '',
          password: '',
          email: '',
          loginMethod: 'username'
        }
      }
    }
  },
  created() {
    if (!window.PublicKeyCredential) {
      this.passkeyDisabled = true;
    }
  }
};
</script>

<style>
.site-form-item-icon {
  margin-right: 8px;
}
</style>
