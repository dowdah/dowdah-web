import datetime
import uuid

from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.mysql import BLOB
from flask_jwt_extended import create_access_token, create_refresh_token
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer


from . import db, s3


OUTPUT_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer, default=0)
    users = db.relationship('User', backref='role', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return '<Role %r>' % self.name

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        if self.permissions & Permission.ADMIN == Permission.ADMIN:
            return True
        else:
            return self.permissions & perm == perm

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'default': self.default,
            'permissions': self.permissions
        }

    @staticmethod
    def insert_roles():
        roles = {
            'User': [
                Permission.LOGIN,
                Permission.SELF_CHANGE_PASSWORD,
                Permission.SELF_CHANGE_EMAIL
            ],
            'Administrator': [
                Permission.ADMIN
            ]
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()


class Permission:
    LOGIN = 1  # 登录权限
    SELF_CHANGE_PASSWORD = 2  # 自己修改密码
    SELF_CHANGE_EMAIL = 4  # 自己修改邮箱
    VIEW_USER_INFO = 8  # 查看用户信息
    MODIFY_USER_INFO = 16  # 修改用户信息
    DEL_USER = 32  # 删除用户
    MANAGE_PERMISSIONS = 64  # 调整角色权限
    BACKUP_DATA = 128  # 备份数据
    RESTORE_DATA = 256  # 恢复数据
    ADD_USER = 512  # 添加用户
    ADMIN = 1024  # 最高权限

    @staticmethod
    def to_json():
        d = dict()
        for k, v in Permission.__dict__.items():
            if not k.startswith('__') and not callable(v) and isinstance(v, int):
                d[k] = v
        return d


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    alternative_id = db.Column(db.String(32), unique=True, index=True)  # 用户的替代ID，用于生成token，初始化时自动生成
    r2_uuid = db.Column(db.String(32), unique=True, index=True)  # 用户的R2 UUID，初始化时自动生成
    avatar_filename = db.Column(db.String(32), nullable=True, default=None)  # 用户头像文件名
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)  # 用户名
    email = db.Column(db.String(64), unique=True, index=True, nullable=False)  # 邮箱，用于二步验证
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)  # 创建时间
    last_seen = db.Column(db.DateTime, default=datetime.datetime.now)  # 最后一次出现时间
    password_hash = db.Column(db.String(128))  # 密码哈希值
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))  # 用户的身份
    comments = db.Column(db.Text, nullable=True, default='')  # 备注(管理员添加)
    webauthn_credentials = db.relationship('WebAuthnCredential', backref='user', lazy=True)

    def __repr__(self):
        return '<User %s>' % self.username

    def ping(self):
        self.last_seen = datetime.datetime.now()
        db.session.add(self)
        db.session.commit()

    @property
    def formatted_created_at(self):
        return self.created_at.strftime(OUTPUT_TIME_FORMAT)

    @property
    def formatted_last_seen(self):
        return self.last_seen.strftime(OUTPUT_TIME_FORMAT)

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    @property
    def avatar_url(self):
        if self.avatar_filename:
            return (f"{current_app.config['R2_PUBLIC_URL']}/"
                    f"{self.r2_uuid}/{self.avatar_filename}")
        else:
            return None

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def generate_access_token(self, expires_in=None):
        if expires_in is None:
            expires_in = current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        return create_access_token(identity=self.alternative_id, expires_delta=expires_in)

    def generate_refresh_token(self, expires_in=None):
        if expires_in is None:
            expires_in = current_app.config['JWT_REFRESH_TOKEN_EXPIRES']
        return create_refresh_token(identity=self.alternative_id, expires_delta=expires_in)

    @staticmethod
    def generate_alternative_id():
        alternative_id = uuid.uuid4().hex
        while User.query.filter_by(alternative_id=alternative_id).first() is not None:
            alternative_id = uuid.uuid4().hex
        return alternative_id

    def generate_presigned_post(self, file_path, mime_type, expires_in=None, min_size=None, max_size=None):
        """
        Generate a presigned POST URL to securely upload files directly to S3.
        Currently, this method is not supported by Cloudflare R2.

        :param file_path: Path of the file (excluding R2_UUID).
        :param mime_type: MIME type of the file to upload.
        :param expires_in: Expiration time for presigned URL in seconds (default from config).
        :param min_size: Minimum file size allowed (in bytes), if specified.
        :param max_size: Maximum file size allowed (in bytes), if specified.
        :return: A dictionary containing URL and fields for POST.
        """
        if expires_in is None:
            expires_in = current_app.config['R2_PRESIGNED_URL_EXPIRES']

        conditions = [
            {"bucket": current_app.config['R2_BUCKET_NAME']},
            ["starts-with", "$key", f"{self.r2_uuid}/{file_path}"],
            {"Content-Type": mime_type}
        ]

        if min_size is not None or max_size is not None:
            size_condition = ["content-length-range"]
            if min_size is not None:
                size_condition.append(min_size)
            else:
                size_condition.append(0)  # No minimum size restriction
            if max_size is not None:
                size_condition.append(max_size)
            conditions.append(size_condition)

        fields = {
            "Content-Type": mime_type,
        }

        response = s3.generate_presigned_post(
            Bucket=current_app.config['R2_BUCKET_NAME'],
            Key=f"{self.r2_uuid}/{file_path}",
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=expires_in
        )

        return response

    def r3_delete_file(self, file_path):
        """
        Delete a file from R3 storage.

        :param file_path: Path of the file (excluding R2_UUID).
        :return: A dictionary containing the response from S3.
        """
        return s3.delete_object(Bucket=current_app.config['R2_BUCKET_NAME'], Key=f"{self.r2_uuid}/{file_path}")

    def to_json(self, include_sensitive=False, include_related=True):
        user_json = {
            'username': self.username,
            'created_at': self.formatted_created_at,
            'last_seen': self.formatted_last_seen,
            'id': self.id,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'role': self.role.to_json()
        }
        if include_related:
            related_json = {}
            user_json.update(related_json)
        if include_sensitive:
            sensitive_json = {
                'comments': self.comments,
            }
            user_json.update(sensitive_json)
        return user_json


class WebAuthnCredential(db.Model):
    __tablename__ = 'webauthn_credentials'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    credential_id = db.Column(db.String(255), unique=True, nullable=False)  # in Base64url format
    public_key = db.Column(BLOB, nullable=False)
    sign_count = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    disabled = db.Column(db.Boolean, default=False)

    @property
    def formatted_created_at(self):
        return self.created_at.strftime(OUTPUT_TIME_FORMAT)

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'credential_id': self.credential_id,
            'sign_count': self.sign_count,
            'disabled': self.disabled,
            'created_at': self.formatted_created_at
        }
