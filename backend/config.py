import os
from datetime import timedelta


class Config:
    SECRET_KEY = JWT_SECRET_KEY = os.environ.get('SECRET_KEY') or 'LutalliLovesGalgame'
    SITE_NAME = os.environ.get('SITE_NAME')
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_ACCOUNT = os.environ.get('MAIL_ACCOUNT')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  # 注意 MAIL_PASSWORD 为 flask_mail 的配置项
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    if SITE_NAME and MAIL_SERVER and MAIL_PORT and MAIL_ACCOUNT and MAIL_PASSWORD and SQLALCHEMY_DATABASE_URI:
        MAIL_PORT = int(MAIL_PORT)
        MAIL_USERNAME = MAIL_ACCOUNT  # 注意 MAIL_USERNAME 为 flask_mail 的配置项
    else:
        raise SystemExit('Please set the environment variables: SITE_NAME, MAIL_SERVER, MAIL_PORT, MAIL_ACCOUNT, '
                         'MAIL_PASSWORD, DATABASE_URL.')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() in \
        ['True', 'on', '1']
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() in \
        ['True', 'on', '1']
    MAIL_ADMIN = os.environ.get('MAIL_ADMIN', 'dowdah@qq.com')
    MAIL_SUBJECT_PREFIX = '[DOWDAH]'
    MAX_WEB_AUTHN_CREDENTIALS_PER_USER = 5  # 每个用户最多拥有的 WebAuthn 凭证数量
    API_TOKEN_EXPIRATION = os.environ.get('TOKEN_EXPIRATION', 3600)  # API token 过期时间, 默认为 1 小时
    EMAIL_TOKEN_EXPIRATION = os.environ.get('EMAIL_TOKEN_EXPIRATION', 3600)  # 邮件 token 过期时间, 默认为 1 小时
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)  # 设置访问 token 有效期为 15 分钟
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # 设置刷新 token 有效期为 30 天
    CELERY_BROKER_URL = 'redis://redis:6379/0'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cloudflare R2 配置
    R2_ENDPOINT = os.environ.get('R2_ENDPOINT')
    R2_ACCESS_KEY = os.environ.get('R2_ACCESS_KEY')
    R2_SECRET_KEY = os.environ.get('R2_SECRET_KEY')
    R2_BUCKET_NAME = os.environ.get('R2_BUCKET_NAME')
    R2_PRESIGNED_URL_EXPIRES = 300  # Presigned URL 有效期为 5 分钟
    R2_PUBLIC_URL = f'https://r2.dowdah.com'

    # 鉴于 Cloudflare R2 不能使用 Presigned Post，这里使用
    # Worker 来代理 Presigned Put，以控制文件大小
    AVATAR_PROXY = 'https://avatar-proxy.dowdah.com'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SENDER = f"{Config.SITE_NAME.lower()}-push-service-dev<{Config.MAIL_ACCOUNT}>"
    USE_SSL = False
    DOMAIN = 'localhost'


class TestingConfig(Config):
    TESTING = True
    MAIL_SENDER = f"{Config.SITE_NAME.lower()}-push-service-test<{Config.MAIL_ACCOUNT}>"
    USE_SSL = False
    DOMAIN = 'localhost'


class ProductionConfig(Config):
    MAIL_SENDER = f"{Config.SITE_NAME.lower()}-push-service<{Config.MAIL_ACCOUNT}>"
    USE_SSL = True
    DOMAIN = 'www.dowdah.com'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
