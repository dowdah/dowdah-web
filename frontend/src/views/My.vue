<template>
  <div class="personal-center" v-if="user">
    <!-- 选项卡示例 -->
    <a-card style="margin-top: 16px;">
      <a-tabs default-active-key="1">
        <a-tab-pane key="1" tab="基本信息">
          <a-tooltip>
            <template #title>点击头像框上传新头像(文件大小须小于 5 MB)</template>
            <a-upload
                accept="image/jpg, image/jpeg, image/png, image/gif"
                name="avatar"
                list-type="picture-card"
                class="avatar-uploader"
                :show-upload-list="false"
                :custom-request="avatarUpload"
            >
              <img v-if="userHasAvatar" :src="user.avatar_url" alt="avatar" class="avatar-img"/>
              <a-avatar class="default-avatar" v-else shape="square" size="large">
                {{ user.username[0].toUpperCase() }}
              </a-avatar>
            </a-upload>
          </a-tooltip>
          <a-descriptions
              bordered
              :column="{ xxl: 4, xl: 3, lg: 3, md: 3, sm: 2, xs: 1 }"
          >
            <a-descriptions-item label="UID">
              <a-typography-paragraph class="no-margin-bottom" :copyable="{ tooltip: false }">1</a-typography-paragraph>
            </a-descriptions-item>
            <a-descriptions-item label="用户名">
              <a-typography-paragraph
                  class="no-margin-bottom"
                  v-model:content="formData.username"
                  :editable="{maxlength: 20, tooltip: false}"
              />
            </a-descriptions-item>
            <a-descriptions-item label="邮箱">
              <a-typography-paragraph
                  class="no-margin-bottom"
                  v-model:content="formData.email"
                  :editable="{maxlength: 50, tooltip: false}"
              />
            </a-descriptions-item>
            <a-descriptions-item label="角色">
              {{ user.role.name }}
            </a-descriptions-item>
            <a-descriptions-item label="注册时间">
              {{ user.created_at }}
            </a-descriptions-item>
          </a-descriptions>
        </a-tab-pane>
        ‘
        <a-tab-pane key="2" tab="设置">
          <!-- 在此处放置个人设置的内容骨架 -->
          <p>这里展示个人的设置内容。</p>
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>
</template>

<script>
import {LoadingOutlined, PlusOutlined} from '@ant-design/icons-vue';
import {mapActions, mapState, mapGetters} from 'vuex';
import axios from 'axios';
import {BASE_API_URL, AVATAR_PROXY} from '@/config/constants';

export default {
  name: 'My',
  data() {
    return {
      formData: {
        username: '',
        email: ''
      }
    };
  },
  components: {
    LoadingOutlined,
    PlusOutlined
  },
  computed: {
    ...mapState(['isLoading', 'user', 'permissions']),
    ...mapGetters(['hasPermission']),
    userHasAvatar() {
      return this.user.avatar_url !== null;
    }
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
    },
    async avatarUpload({ file, onSuccess, onError }) {
      const maxSize = 5 * 1024 * 1024; // 5MB
      if (file.size >= maxSize) {
          this.$message.error('文件大小不能超过5MB');
          return onError(new Error('文件大小超出限制'));
        }
      try {
        this.setLoading(true)
        // 1. 获取预签名URL
        const fileExt = file.name.split('.').pop();
        const { data } = await axios.get(`${BASE_API_URL}/s3/get-avatar-upload-presigned-put?ext=${fileExt}`);

        // 2. 上传文件到R2
        let form = new FormData();
        form.append("presigned", data.presigned);
        form.append("avatar", file);
        await axios.post(AVATAR_PROXY, form, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        this.user.avatar_url = data.avatar_url;
        this.$message.success('头像上传成功');
        this.setLoading(false)
        onSuccess();
      } catch (err) {
        this.$message.error(err.response.data.msg);
        this.setLoading(false)
        onError(err);
      }
    }
  },
  created() {
    this.formData.username = this.user.username;
    this.formData.email = this.user.email;
  }
};
</script>
<style>
.no-margin-bottom {
  margin-bottom: 0 !important;
}

.avatar-uploader {
  display: flex !important;
  justify-content: center;
  align-items: center;
  width: 100% !important;
}

.default-avatar {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
}

.avatar-img {
  width: 90%;
  height: 90%;
  object-fit: cover;
}
</style>
