<template>
  <div>
    <div class="dashboard">
      <template v-if="user">
        <div class="user-info">
          <h2>用户信息</h2>
          <div class="userinfo-row">
            <div class="info-label">用户名</div>
            <div class="info-value">{{ user.username }}</div>
          </div>
          <div class="userinfo-row">
            <div class="info-label">身份</div>
            <div class="info-value">{{ user.role.name }}</div>
          </div>
        </div>
        <div class="permissions-info" v-if="user.role.name !== '普通用户'">
          <h2>你拥有的权限</h2>
          <p class="hint">此栏仅管理员可见，方便确认自己的权能</p>
          <div class="permission-table">
            <div v-for="(permission_number, permission_name, index) in permissions" :key="permission_number"
                 class="permission-row">
              <input type="checkbox" :id="permission_number" :disabled="true" :checked="hasPermission(permission_name)">
              <label :for="permission_number">{{ permission_name }}</label>
            </div>
          </div>
        </div>
        <button @click="logoutHandler" class="logout-button" :disabled="isLoading">登出</button>
        <div class="webauthn-register">
          <h2>Passkey 注册</h2>
          <button @click="registerWebAuthn" :disabled="isLoading">注册新验证器</button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  align-items: stretch;
  max-width: 800px;
  margin: 0 auto;
}

.user-info, .card-info, .permissions-info, .webauthn-register {
  background-color: #ffffff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.hint {
  text-align: center;
  margin-top: 10px;
  font-size: 14px;
  color: #666;
}

h2 {
  margin-bottom: 10px;
  color: #333333;
}

.userinfo-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #e9ecef;
}

.info-label {
  font-weight: bold;
  color: #333333;
  text-align: left;
}

.info-value {
  color: #555555;
  text-align: right;
}

.logout-button, .webauthn-register button {
  padding: 10px 20px;
  background-color: #007bff;
  color: #ffffff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  align-self: stretch;
}

.logout-button:not(:disabled):hover, .webauthn-register button:not(:disabled):hover {
  background-color: #0056b3;
}

.logout-button:disabled, .webauthn-register button:disabled {
  background-color: #ccc;
  color: #666;
  cursor: default;
}

.permission-table {
  display: flex;
  flex-direction: row;
  gap: 10px;
  flex-wrap: wrap;
  padding: 10px;
  border: 1px solid #e9ecef;
  border-radius: 4px;
}

.permission-row {
  display: flex;
  align-items: center;
  background-color: #f1f3f5;
  padding: 5px;
  border-radius: 4px;
}

.permission-row:hover {
  background-color: #e9ecef;
}

.permission-row input {
  margin-right: 10px;
}

.permission-row label {
  color: #333333;
}
</style>

<script>
import {mapActions, mapState, mapGetters} from 'vuex';
import axios from 'axios';
import {BASE_API_URL} from '@/config/constants';

export default {
  name: 'Dashboard',
  computed: {
    ...mapState(['isLoading', 'user', 'permissions']),
    ...mapGetters(['hasPermission'])
  },
  methods: {
    ...mapActions(['logout', 'setLoading']),
    async logoutHandler() {
      const route = this.$route
      const requiresAuth = route.meta && route.meta.requiresAuth;
      await this.logout();
      if (requiresAuth || route.meta.requiresPermission !== undefined) {
        this.$router.push('/');
      }
      this.$message.success('登出成功');
    },
    async registerWebAuthn() {
      // TODO: 将弹窗提示的内容改为使用 AlertWindow 组件
      let errorOccurred = false;
      let response;
      let attestationResponse;
      this.setLoading(true)
      try {
        response = await axios.get(`${BASE_API_URL}/webauthn/register/begin`);
      } catch (error) {
        console.error('WebAuthn Register Begin error:', error);
        this.setLoading(false)
        alert('WebAuthn 注册失败');
        errorOccurred = true;
      }
      if (!errorOccurred) {
        try {
          let options = response.data.options;
          if (options.excludeCredentials) {
            options.excludeCredentials = options.excludeCredentials.map(credential => {
              credential.id = this.base64urlToArrayBuffer(credential.id);
              return credential;
            });
          }
          const publicKey = {
            ...options,
            challenge: this.base64urlToArrayBuffer(options.challenge),
            user: {
              ...options.user,
              id: this.base64urlToArrayBuffer(options.user.id)
            }
          };
          const credential = await navigator.credentials.create({publicKey});
          attestationResponse = {
            id: credential.id,
            rawId: this.arrayBufferToBase64url(credential.rawId),
            response: {
              clientDataJSON: this.arrayBufferToBase64url(credential.response.clientDataJSON),
              attestationObject: this.arrayBufferToBase64url(credential.response.attestationObject)
            },
            type: credential.type,
            challenge: options.challenge
          };
        } catch (error) {
          console.error('WebAuthn Register error:', error);
          this.setLoading(false)
          errorOccurred = true;
          alert('WebAuthn 注册失败')
        }
        if (!errorOccurred) {
          try {
            response = await axios.post(`${BASE_API_URL}/webauthn/register/complete`, attestationResponse);
          } catch (error) {
            console.error('WebAuthn Register Complete error:', error);
            errorOccurred = true;
          } finally {
            this.setLoading(false)
            // 在 finally 代码块中弹窗的原因是避免其阻塞 setLoading(false) 的执行
            if (errorOccurred) {
              alert('WebAuthn 注册失败');
            } else {
              alert('WebAuthn 注册成功');
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
};
</script>
