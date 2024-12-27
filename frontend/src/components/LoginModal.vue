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
        @validate="handleValidate"
    >
      <a-form-item label="登录方式">
        <a-radio-group v-model:value="formState.loginMethod">
          <a-radio-button value="username">用户名</a-radio-button>
          <a-radio-button value="email">邮箱</a-radio-button>
          <a-radio-button value="passkey" :disabled="passkeyDisabled">
            通行密钥
            <a-tooltip title="您的设备不支持 WebAuthn，无法使用通行密钥登录" v-if="passkeyDisabled">
              <QuestionCircleOutlined />
            </a-tooltip>
            <a-tooltip title="使用通行密钥登录，免去使用键盘的烦恼！" v-else>
              <QuestionCircleOutlined />
            </a-tooltip>
          </a-radio-button>
        </a-radio-group>
      </a-form-item>
      <a-form-item
          label="昵称"
          name="username"
          v-if="formState.loginMethod === 'username'"
      >
        <a-input v-model:value="formState.username">
          <template #prefix>
            <UserOutlined class="site-form-item-icon"/>
          </template>
        </a-input>
      </a-form-item>

      <a-form-item
          label="邮箱"
          name="email"
          v-if="formState.loginMethod === 'email'"
          type="email"
      >
        <a-input v-model:value="formState.email">
          <template #prefix>
            <MailOutlined class="site-form-item-icon"/>
          </template>
        </a-input>
      </a-form-item>

      <a-form-item
          label="密码"
          name="password"
          v-if="formState.loginMethod !== 'passkey'"
      >
        <a-input-password v-model:value="formState.password">
          <template #prefix>
            <LockOutlined class="site-form-item-icon"/>
          </template>
        </a-input-password>
      </a-form-item>

      <a-form-item v-if="formState.loginMethod === 'passkey'">
        <p>您已选择使用通行密钥登录，直接点击“登录”按钮即可。注意，您必须已经注册 WebAuthn 才能够使用其登录。</p>
      </a-form-item>

      <a-form-item v-if="failed_response_data.code === 401">
        <!--        <RouterLink to="/reset-pwd" style="float: right">忘记密码？</RouterLink>-->
        <a href="#" style="float: right">忘记密码？</a>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script>
import {UserOutlined, LockOutlined, MailOutlined, QuestionCircleOutlined} from '@ant-design/icons-vue';
import {mapActions, mapGetters} from 'vuex';
import axios from 'axios';
import {BASE_API_URL} from '@/config/constants';

export default {
  name: 'LoginModal',
  props: ['mOpen'],
  emits: ['update:mOpen'],
  components: {
    UserOutlined,
    LockOutlined,
    MailOutlined,
    QuestionCircleOutlined
  },
  data() {
    return {
      loading: false,
      failed_login: false,
      failed_response_data: {},
      formRef: this.$refs.loginForm,
      formState: {
        username: '',
        password: '',
        email: '',
        loginMethod: 'username'
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
        ]
      },
      passkeyDisabled: false
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
          this.failed_login = true;
          this.failed_response_data = error.response.data;
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
        this.$message.error(this.failed_response_data.msg);
      }
    },
    handleCancel() {
      this.open = false;
    },
    handleValidate(...args) {
      console.log('validate', args);
    },
    async validateUsername(_rule, value) {
      if (this.formState.loginMethod === 'username' && !value) {
        return Promise.reject('请输入用户名');
      } else {
        return Promise.resolve();
      }
    },
    async validateEmail(_rule, value) {
      if (this.formState.loginMethod === 'email') {
        if (!value) {
          return Promise.reject('请输入邮箱');
        } else if (!/^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/.test(value)) {
          return Promise.reject('请输入正确的邮箱格式');
        } else {
          return Promise.resolve();
        }
      } else {
        return Promise.resolve();
      }
    },
    async validatePassword(_rule, value) {
      if (this.formState.loginMethod !== 'passkey' && !value) {
        return Promise.reject('请输入密码');
      } else {
        return Promise.resolve();
      }
    },
    async handleWebAuthnLogin() {
      let errorOccurred = false;
      let response;
      try {
        response = await axios.get(`${BASE_API_URL}/webauthn/login/begin`);
      } catch (error) {
        console.error('WebAuthn Login Begin error:', error);
        this.failed_login = true;
        this.failed_response_data = error.response.data;
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
          this.failed_login = true;
          if (error.response) {
            this.failed_response_data = error.response.data;
          } else {
            switch (error.name) {
              case 'NotAllowedError':
                this.failed_response_data = {msg: '您拒绝了登录请求'};
                break;
              case 'InvalidStateError':
                this.failed_response_data = {msg: '登录请求已过期，请重试'};
                break;
              default:
                this.failed_response_data = {msg: '未知错误'};
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
    }
  },
  computed: {
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
      switch (this.formState.loginMethod) {
        case 'username':
          return !this.formState.username || !this.formState.password;
        case 'email':
          return !/^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/.test(this.formState.email)
              || !this.formState.password;
        case 'passkey':
          return this.passkeyDisabled
      }
    },
    credentials() {
      return this.formState.loginMethod === 'username'
          ? {username: this.formState.username, password: this.formState.password}
          : {email: this.formState.email, password: this.formState.password};
    }
  },
  watch: {
    'formState.loginMethod'(value) {
      this.failed_login = false;
      this.failed_response_data = {};
    }
  },
  created() {
    if (!window.PublicKeyCredential) {
      this.passkeyDisabled = true;
    }
  }
};
</script>
