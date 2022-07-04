import unittest
import sqlalchemy

from app import app
from app.app_creator import db

class DBTestCase(unittest.TestCase):
    
    def setUp(self):
        with app.app_context():
            url = 'postgresql://slickuser:slickpass@localhost/slickdb.test'
            app.config['SQLALCHEMY_DATABASE_URI'] = url
            app.config['TESTING'] = True
            app.config['SQLALCHEMY_ECHO'] = False
            app.config['CSRF_ENABLED'] = False
            app.config['WTF_CSRF_ENABLED'] = False
            self.engine = sqlalchemy.create_engine(url)
            # self.connection = self.engine.connect()
            
            db.create_all()
            
            # enable billing for usage test cases to work
            self.client = app.test_client()
            #app.config['SQLALCHEMY_ECHO'] = True # uncomment to see SQL generated

    def tearDown(self):
        with app.app_context():
            db.session.close()
            db.session.remove()
            db.drop_all()
