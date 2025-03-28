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
    EMAIL_CODE_EXPIRATION = os.environ.get('EMAIL_CODE_EXPIRATION', 600)  # 邮件验证代码过期时间, 默认为 10 分钟
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)  # 设置访问 token 有效期为 15 分钟
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # 设置刷新 token 有效期为 30 天
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cloudflare R2 配置
    R2_ENDPOINT = os.environ.get('R2_ENDPOINT')
    R2_ACCESS_KEY = os.environ.get('R2_ACCESS_KEY')
    R2_SECRET_KEY = os.environ.get('R2_SECRET_KEY')
    R2_BUCKET_NAME = os.environ.get('R2_BUCKET_NAME')
    R2_PARAM_EXPIRATION = 300  # R2 参数有效期(秒)
    R2_PUBLIC_URL = f'https://r2.dowdah.com'
    R2_PROXY = 'https://r2-proxy.dowdah.com' # 接受用户请求的 Cloudflare Worker 代理

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
