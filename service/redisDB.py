from redis import Redis

from config import project_conf


def get_connection(db: int = 0):
    r = Redis(host=project_conf("redis_host"), port=project_conf("redis_port"), db=db)
    if project_conf("redis_password"):
        r.auth(project_conf("redis_password"))
    return r
