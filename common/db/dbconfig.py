from playhouse.pool import PooledMySQLDatabase

from common import const
from config import config

host = config.get(const.MYSQL).get('host')
userName = config.get(const.MYSQL).get('userName')
password = config.get(const.MYSQL).get('password')
dbName = config.get(const.MYSQL).get('db')

db = PooledMySQLDatabase(
    dbName,
    max_connections=20,  # 连接池允许的最大连接数量
    stale_timeout=10,  # 一个连接未使用多长时间后被视为“过时”并丢弃
    host=host,
    port=3306,
    user=userName,
    password=password,
    charset='utf8mb4'
)


