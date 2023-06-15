import datetime

from apscheduler.schedulers.background import BackgroundScheduler
import threading
import time

import config
from common import log

config.load_config()
from common.db.document_record import DocumentRecord
from service.file_training_service import training_service, train_work


def scan_database():
    documents_to_train = DocumentRecord.select().where(DocumentRecord.trained == False, DocumentRecord.deleted == False,
                                                       DocumentRecord.training_status == 2)
    return documents_to_train


def job():
    log.info("Job started")
    # 在此处添加执行任务的逻辑
    documents_to_train = scan_database()
    for document in documents_to_train:
        log.info("start training document:{}".format(document.title))
        document.training_status = 3
        document.updated_time = datetime.datetime.now()
        document.save()
        train_work(document)
        # time.sleep(100)  # 模拟任务耗时
    log.info("Job completed")


def scheduler_job():
    log.info("scheduler_job started")
    data = scan_database()
    if data:
        global job_thread
        if not job_thread.is_alive():
            log.info("job_thread is not alive, start it")
            job_thread = threading.Thread(target=job)
            job_thread.start()
    log.info("scheduler_job completed")


scheduler = BackgroundScheduler()
job_thread = threading.Thread(target=job, daemon=True)
job_thread.start()  # 开始第一次任务
scheduler.add_job(scheduler_job, 'interval', minutes=1)
scheduler.start()

# 防止主线程结束
try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
