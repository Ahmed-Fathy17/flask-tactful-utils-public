from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))



from flask_tactful import TactfulFlask
import sys

config = dict(
    SQLALCHEMY_DATABASE_URI="postgresql://slickuser:slickpass@localhost/auth",
    JWT_HEADER_NAME='X-API-KEY',
    JWT_DECODE_ALGORITHMS = ["HS256","RS256"],
    LOG_LEVEL='DEBUG',
    REDIS_BUS_URL='redis://localhost:6379/11',
    REDIS_CONSUMER_GROUP="users",
    REDIS_CONSUMER_NAME="users-1",
    BUGSNAG_KEY=os.getenv("BUGSNAG_KEY")

)

application = TactfulFlask(__name__)
application.configure(config, api_title="Tactful AI Flask Utils Test API", api_name='flask', api_version="v1")
APP_HOME = "/flask_tactful"
sys.path.insert(0, APP_HOME)
