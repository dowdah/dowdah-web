<template>
  <div>
    <div class="login-container">
      <h2>登录</h2>
      <form @submit.prevent="loginHandler" class="login-form">
        <div class="form-group">
          <label for="login_choice">登录方式</label>
          <select v-model="login_choice" required>
            <option value="username">用户名</option>
            <option value="email">邮箱</option>
            <option value="passkey">Passkey</option>
          </select>
        </div>
        <div class="form-group" v-if="login_choice === 'username'">
          <label for="username">用户名</label>
          <input type="text" v-model="username" required/>
        </div>
        <div class="form-group" v-if="login_choice === 'email'">
          <label for="email">邮箱</label>
          <input type="email" v-model="email" required/>
        </div>
        <div class="form-group" v-if="login_choice !== 'passkey'">
          <label for="password">密码</label>
          <input type="password" v-model="password" required/>
        </div>
        <button type="submit" class="login-button" :disabled="isLoading">确认</button>
      </form>
      <div v-if="failed_login" class="error-message">
        <span class="error-icon">❎</span>{{ failed_response_data.msg }}
        <template v-if="failed_response_data.code === 401">
          <RouterLink to="/reset-pwd">忘记密码？</RouterLink>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  max-width: 400px;
  margin: auto;
  padding: 2rem;
  background-color: #f9f9f9;
  border-radius: 8px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  text-align: center;
}

h2 {
  margin-bottom: 1.5rem;
  color: #333;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  width: 100%;
}

label {
  margin-bottom: 0.5rem;
  color: #555;
}

select, input, .login-button {
  width: 100%;
  box-sizing: border-box;
}

input, select {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

input:focus, select:focus {
  border-color: #007bff;
  outline: none;
}

.login-button {
  padding: 0.75rem;
  border: none;
  border-radius: 4px;
  background-color: #007bff;
  color: #fff;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.login-button:not(:disabled):hover {
  background-color: #0056b3;
}

.login-button:disabled {
  background-color: #ccc;
  color: #666;
  cursor: default;
}

.error-message {
  margin-top: 1rem;
  padding: 0.75rem;
  border: 1px solid #ff4d4f;
  background-color: #fff1f0;
  color: #ff4d4f;
  border-radius: 4px;
  text-align: left;
  font-size: 0.875rem;
}

.error-icon {
  margin-right: 0.5rem;
}
</style>

<script>
import {mapActions, mapState} from 'vuex';
import axios from 'axios';
import {BASE_API_URL} from '@/config/constants';

export default {
  name: 'Login',
  data() {
    return {
      login_choice: 'username',
      username: '',
      email: '',
      password: '',
      failed_login: false,
      failed_response_data: {},
    };
  },
  computed: {
    ...mapState(['isLoading']),
    credentials() {
      return this.login_choice === 'username'
          ? {username: this.username, password: this.password}
          : {email: this.email, password: this.password};
    }
  },
  methods: {
    ...mapActions(['login', 'setLoading', 'webauthnLoginComplete']),
    async loginHandler() {
      this.setLoading(true);
      if (this.login_choice === 'passkey') {
        await this.handleWebAuthnLogin();
      } else {
        try {
          await this.login(this.credentials);
        } catch (error) {
          this.failed_login = true;
          this.failed_response_data = error.response.data;
        }
      }
      this.setLoading(false);
    },
    async handleWebAuthnLogin() {
      let errorOccurred = false;
      let response;
      try {
        response = await axios.get(`${BASE_API_URL}/webauthn/login/begin`);
      } catch (error) {
        console.error('WebAuthn Login Begin error:', error);
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
          throw error;
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
  }
};
</script>
