
"""
    config.py
    - settings for the flask application object
"""

class BaseConfig(object):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql://admin:password@uts-studio-quantum.cgxjp9m1gyhm.ap-southeast-2.rds.amazonaws.com:3306/quantum'
    SQLALCHEMY_TRACK_MODIFICATIONS = False