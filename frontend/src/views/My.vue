<template>
  <div class="personal-center" v-if="user">
    <!-- 选项卡示例 -->
    <a-card style="margin-top: 16px;">
      <a-tabs default-active-key="1" size="large">
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
        <a-tab-pane key="2" tab="设置">
          <a-divider style="margin-top: 0">
            我的通行密钥
            <a-tooltip placement="topLeft">
              <template #title>
                <span>通行密钥 (Passkey) 是一种基于公钥加密的无密码身份验证技术，提供更安全便捷的登录体验，替代传统密码。</span>
              </template>
              <QuestionCircleOutlined style="width: 0.8em; height: 0.8em;"/>
            </a-tooltip>
          </a-divider>
          <a-flex justify="space-between" gap="large" align="center">
            <a-progress
                :percent="authenticatorPercentage"
                status="active"
                :steps="maxAuthenticators"
                :size="[20 * maxAuthenticators, 10]"
            >
              <template #format="percent">
                <span>({{ webAuthenticators.length }} / {{ maxAuthenticators }})</span>
              </template>
            </a-progress>
            <a-button
                class="editable-add-btn" style="margin-bottom: 8px"
                @click="registerWebAuthn" :disabled="!hasMoreAuthenticators">
              注册新的通行密钥
            </a-button>
          </a-flex>
          <a-config-provider>
            <template #renderEmpty>
              <div style="text-align: center">
                <dislike-outlined style="font-size: 20px"/>
                <p>你没有通行密钥，真的太逊了！</p>
              </div>
            </template>
            <a-table bordered :data-source="authenticatorTable" :columns="tableColumns" :pagination="false">
              <template #headerCell="{ column }">
                <template v-if="column.dataIndex === 'sign_count'">
                  <span>已使用次数 </span>
                  <a-tooltip>
                    <template #title>
                      <span>并非所有设备都会递增使用次数，特别是苹果设备。一些现代的 WebAuthn
                        实现，比如苹果的 Passkey 或者 Android 平台凭证，它们的使用次数可能始终是
                        0，因为这些凭证是云同步的，不具备唯一的硬件计数器。</span>
                    </template>
                    <QuestionCircleOutlined style="width: 0.8em; height: 0.8em;" />
                  </a-tooltip>
                </template>
              </template>
              <template #bodyCell="{ column, text, record }">
                <template v-if="column.dataIndex === 'name'">
                  <div class="editable-cell">
                    <div v-if="editableData[record.key]" class="editable-cell-input-wrapper">
                      <a-input v-model:value="editableData[record.key].name" @pressEnter="savePasskey(record.key)"
                               style="width: 7em"/>
                      <check-outlined class="editable-cell-icon-check" @click="savePasskey(record.key)"/>
                    </div>
                    <div v-else class="editable-cell-text-wrapper">
                      {{ text || ' ' }}
                      <edit-outlined class="editable-cell-icon" @click="editPasskey(record.key)"/>
                    </div>
                  </div>
                </template>
                <template v-else-if="column.dataIndex === 'operation'">
<!--                  <a-dropdown>-->
<!--                    <a class="ant-dropdown-link" @click.prevent>-->
<!--                      <EllipsisOutlined/>-->
<!--                    </a>-->
<!--                    <template #overlay>-->
<!--                      <a-menu>-->
<!--                        <a-menu-item key="0">-->
<!--                          <a @click="togglePasskey(record.key)">-->
<!--                            {{ record.disabled ? '启用' : '禁用' }}-->
<!--                          </a>-->
<!--                        </a-menu-item>-->
<!--                        <a-menu-item key="1">-->
<!--                          <a @click="deletePasskey(record.key)">-->
<!--                            删除-->
<!--                          </a>-->
<!--                        </a-menu-item>-->
<!--                      </a-menu>-->
<!--                    </template>-->
<!--                  </a-dropdown>-->
                  <a-popconfirm
                      v-if="authenticatorTable.length"
                      :title="`你确定要删除名称为${record.name}的通行密钥吗？`"
                      @confirm="deletePasskey(record.key)"
                      ok-text="是"
                      cancel-text="否"
                      placement="topRight"
                  >
                    <DeleteOutlined style="color: red" />
                  </a-popconfirm>
                </template>
                <template v-else-if="column.dataIndex === 'disabled'">
                  <a-switch :checked="!record.disabled" checked-children="启用" un-checked-children="禁用"
                            @click="togglePasskey(record.key)"/>
                </template>
              </template>
            </a-table>
          </a-config-provider>
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>
</template>

<script>
import {
  LoadingOutlined, PlusOutlined, DislikeOutlined, EditOutlined, CheckOutlined,
  EllipsisOutlined, QuestionCircleOutlined, DeleteOutlined
} from '@ant-design/icons-vue';
import {mapActions, mapState, mapGetters} from 'vuex';
import axios from 'axios';
import {AVATAR_PROXY} from '@/config/constants';
import apiClient from '@/api';
import {cloneDeep} from 'lodash-es';

export default {
  name: 'My',
  data() {
    return {
      formData: {
        username: '',
        email: ''
      },
      webAuthenticators: [],
      tableColumns: [
        {
          title: '名称',
          dataIndex: 'name',
          key: 'name',
          editable: true
        },
        {
          title: '凭证 ID',
          dataIndex: 'credential_id',
          key: 'credential_id'
        },
        {
          title: '创建时间',
          dataIndex: 'created_at',
          key: 'created_at'
        },
        {
          title: '已使用次数',
          dataIndex: 'sign_count',
          key: 'sign_count'
        },
        {
          title: '状态',
          dataIndex: 'disabled',
          key: 'disabled'
        },
        {
          title: '操作',
          dataIndex: 'operation',
          key: 'operation'
        }
      ],
      editableData: {},
      maxAuthenticators: 0
    };
  },
  components: {
    LoadingOutlined,
    PlusOutlined,
    DislikeOutlined,
    EditOutlined,
    CheckOutlined,
    EllipsisOutlined,
    QuestionCircleOutlined,
    DeleteOutlined
  },
  computed: {
    ...mapState(['isLoading', 'user', 'permissions']),
    ...mapGetters(['hasPermission']),
    userHasAvatar() {
      return this.user.avatar_url !== null;
    },
    authenticatorTable() {
      return this.webAuthenticators.map(authenticator => {
        return {
          key: authenticator.id,
          name: authenticator.name,
          credential_id: authenticator.credential_id,
          created_at: authenticator.created_at,
          sign_count: authenticator.sign_count,
          disabled: authenticator.disabled
        };
      });
    },
    hasMoreAuthenticators() {
      return this.webAuthenticators.length < this.maxAuthenticators;
    },
    authenticatorPercentage() {
      return this.webAuthenticators.length / this.maxAuthenticators * 100;
    }
  },
  methods: {
    ...mapActions(['logout', 'setLoading']),
    async registerWebAuthn() {
      let errorOccurred = false;
      let response;
      let attestationResponse;
      this.setLoading(true)
      try {
        response = await apiClient.get('/webauthn/register/begin');
      } catch (error) {
        console.error('WebAuthn Register Begin error:', error);
        this.setLoading(false)
        this.$message.error('WebAuthn 注册失败');
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
          this.$message.error('WebAuthn 注册失败')
        }
        if (!errorOccurred) {
          try {
            response = await apiClient.post('/webauthn/register/complete', attestationResponse);
          } catch (error) {
            console.error('WebAuthn Register Complete error:', error);
            errorOccurred = true;
          } finally {
            // 在 finally 代码块中弹窗的原因是避免其阻塞 setLoading(false) 的执行
            if (errorOccurred) {
              this.$message.error('WebAuthn 注册失败');
            } else {
              await this.fetchAuthenticators();
              this.$message.success('WebAuthn 注册成功');
            }
            this.setLoading(false)
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
    async confirmNewAvatar(key) {
      try {
        const response = await apiClient.post('/r2/confirm-new-avatar', {
          key: key
        });
        return response.data.success
      } catch (error) {
        return false;
      }
    }
    ,
    async avatarUpload({file, onSuccess, onError}) {
      const maxSize = 5 * 1024 * 1024; // 5MB
      if (file.size >= maxSize) {
        this.$message.error('文件大小不能超过5MB');
        return onError(new Error('文件大小超出限制'));
      }
      this.setLoading(true)
      let uploadResponse, r2PublicUrl, newAvatarUrl;
      try {
        // 1. 获取R2参数
        const fileExt = file.name.split('.').pop();
        const {data} = await apiClient.get(`/r2/upload-avatar?ext=${fileExt}`)
        r2PublicUrl = data.r2_public_url
        newAvatarUrl = data.new_avatar_url

        // 2. 上传文件到R2
        let form = new FormData();
        form.append("r2_params", data.r2_params);
        form.append("file", file);
        uploadResponse = await axios.post(data.r2_proxy, form, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
      } catch (err) {
        this.setLoading(false)
        this.$message.error(err.response.data.msg);
        onError(err);
      }
      if (uploadResponse.status !== 200) {
        this.setLoading(false)
        this.$message.error(`头像上传失败: ${uploadResponse.data.msg}`);
        onError(new Error(`头像上传失败: ${uploadResponse.data.msg}`));
        return;
      }
      this.user.avatar_url = newAvatarUrl
      let confirmCount = 0;
      let confirmSuccess = false;
      do {
        confirmSuccess = await this.confirmNewAvatar(uploadResponse.data.key);
        confirmCount++;
      } while (!confirmSuccess && confirmCount < 3);
      if (confirmSuccess) {
        this.$message.success('头像更新成功');
        onSuccess();
      } else {
        this.$message.error('新头像同步失败，联系管理员处理。');
        onError(new Error('新头像同步失败，联系管理员处理。'));
      }
      this.setLoading(false);
    },
    async fetchAuthenticators() {
      try {
        const response = await apiClient.get('/webauthn/my-authenticators');
        this.webAuthenticators = response.data.authenticators;
        this.maxAuthenticators = response.data.max_authenticators;
      } catch (error) {
        console.error('Fetch authenticators error:', error);
      }
    },
    editPasskey(key) {
      this.editableData[key] = cloneDeep(this.webAuthenticators.find(item => item.id === key));
    },
    async savePasskey(key) {
      const maxNameLength = 30;
      const newData = this.editableData[key];
      if (newData.name.length > maxNameLength) {
        this.$message.error(`名称长度不能超过 ${maxNameLength} 个字符`);
        return;
      }
      this.setLoading(true)
      const index = this.webAuthenticators.findIndex(item => item.id === key);
      const response = await apiClient.put(`/webauthn/operate/${newData.credential_id}`, {
        name: newData.name
      });
      if (response.data.success) {
        if (index > -1) {
          this.webAuthenticators.splice(index, 1, newData);
          delete this.editableData[key];
        }
      } else {
        this.$message.error(response.data.msg);
      }
      this.setLoading(false)
    },
    async deletePasskey(key) {
      this.setLoading(true)
      let deletedAuthenticator = this.webAuthenticators.find(item => item.id === key);
      const response = await apiClient.delete(`/webauthn/operate/${deletedAuthenticator.credential_id}`);
      if (response.data.success) {
        this.webAuthenticators = this.webAuthenticators.filter(item => item.id !== key);
        this.$message.success("通行密钥已删除。受 JavaScript 安全策略限制，你需要自行删除相关设备上本地存储的通行密钥。")
      } else {
        this.$message.error(response.data.msg);
      }
      this.setLoading(false)
    },
    async togglePasskey(key) {
      this.setLoading(true)
      let toggledAuthenticator = this.webAuthenticators.find(item => item.id === key);
      const index = this.webAuthenticators.findIndex(item => item.id === key);
      const response = await apiClient.put(`/webauthn/operate/${toggledAuthenticator.credential_id}`, {
        disabled: !toggledAuthenticator.disabled
      });
      if (response.data.success) {
        toggledAuthenticator.disabled = !toggledAuthenticator.disabled;
        if (index > -1) {
          this.webAuthenticators.splice(index, 1, toggledAuthenticator);
        }
      } else {
        this.$message.error(response.data.msg);
      }
      this.setLoading(false)
    }
  },
  created() {
    this.formData.username = this.user.username;
    this.formData.email = this.user.email;
    this.fetchAuthenticators();
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

.editable-cell {
  position: relative;

  .editable-cell-input-wrapper,
  .editable-cell-text-wrapper {
    padding-right: 24px;
  }

  .editable-cell-text-wrapper {
    padding: 5px 24px 5px 5px;
  }

  .editable-cell-icon,
  .editable-cell-icon-check {
    position: absolute;
    right: 0;
    width: 20px;
    cursor: pointer;
  }

  .editable-cell-icon {
    margin-top: 4px;
    display: none;
  }

  .editable-cell-icon-check {
    margin-top: 10px;
  }

  .editable-cell-icon:hover,
  .editable-cell-icon-check:hover {
    color: #108ee9;
  }

  .editable-add-btn {
    margin-bottom: 8px;
  }
}

.editable-cell:hover .editable-cell-icon {
  display: inline-block;
}
</style>
