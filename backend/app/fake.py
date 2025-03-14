from sqlalchemy.exc import IntegrityError
from faker import Faker
from . import db
from .models import User, Role
from alive_progress import alive_bar


def users(count=20):
    print("Making users...")
    fake = Faker()
    i = 0
    with alive_bar(count) as bar:
        while i < count:
            u = User(email=fake.email(),
                     username=fake.name(),
                     password='666666',
                     email_verified=True,
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


def main(count=20):
    db.drop_all()
    db.create_all()
    Role.insert_roles()
    admin = Role.query.filter_by(name='Administrator').first()
    user = Role.query.filter_by(name='User').first()
    u_1 = User(email='x@dowdah.com', username='Dowdah', password='666666', email_verified=True, role=admin)
    db.session.add(u_1)
    u_2 = User(email='strangecarhead@foxmail.com', username='Dowdah2', password='666666', email_verified=True,
               role=user)
    db.session.add(u_2)
    u_unconfirmed_1 = User(email='dowdah@qq.com', username='Dowdah3', password='666666', email_verified=False,
                           role=user)
    db.session.add(u_unconfirmed_1)
    u_unconfirmed_2 = User(email='1534887783@qq.com', username='Joecos', password='666666', email_verified=False,
                            role=user)
    db.session.add(u_unconfirmed_2)
    db.session.commit()
    users(count=count)
    print("Done.")
