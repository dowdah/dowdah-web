from sqlalchemy.exc import IntegrityError
from faker import Faker
from . import db, s3
from .models import User, Role
from alive_progress import alive_bar
import os


def users(count=10):
    print("Making users...")
    fake = Faker()
    i = 0
    with alive_bar(count) as bar:
        while i < count:
            u = User(email=fake.email(),
                     username=fake.name(),
                     password='666666',
                     created_at=fake.date_time_this_year(),
                     comments='由 fake.py 生成的随机数据'
                     )
            db.session.add(u)
            try:
                db.session.commit()
                i += 1
            except IntegrityError:
                db.session.rollback()
            bar()


def main(count=10, db_exists=False):
    if db_exists:
        users_with_avatar = User.query.filter(User.avatar_filename.isnot(None)).all()
        avatar_count = len(users_with_avatar)
        i = 0
        with alive_bar(avatar_count) as bar:
            while i < avatar_count:
                user_with_avatar = users_with_avatar[i]
                s3.delete_object(Bucket=os.environ.get('R2_BUCKET_NAME'),
                                 Key=f"{user_with_avatar.r2_uuid}/{user_with_avatar.avatar_filename}")
                i += 1
                bar()
        print("Deleted all avatars.")
    print("Dropping all tables...")
    db.session.rollback()
    db.drop_all()
    print("Creating all tables...")
    db.session.expunge_all()  # 移除 session 缓存的对象
    db.session.commit()  # 确保事务结束
    db.session.close()  # 关闭 session 以清理状态
    db.create_all()
    Role.insert_roles()
    admin = Role.query.filter_by(name='Administrator').first()
    user = Role.query.filter_by(name='User').first()
    u_1 = User(email='x@dowdah.com', username='Dowdah', password='666666', role=admin)
    db.session.add(u_1)
    u_2 = User(email='strangecarhead@foxmail.com', username='Dowdah1', password='666666', role=user)
    db.session.add(u_2)
    u_3 = User(email='1534887783@qq.com', username='Joecos', password='666666', role=user)
    db.session.add(u_3)
    db.session.commit()
    users(count=count)
    print("Done.")
