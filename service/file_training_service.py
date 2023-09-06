import datetime
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unicodedata import normalize

from flask import jsonify
from llama_index import SimpleDirectoryReader

from common import log
from common.db.document_record import DocumentRecord
from common.log import logger
from common.menu_functions.document_list import DocumentList
from common.menu_functions.public_train_methods import public_train_documents, store_query_engine
from config import project_conf

executor = ThreadPoolExecutor(8)


def upload_file_service(file, user):
    log.info("upload_file_service start{}",file.filename)
    filename = custom_secure_filename(file.filename)
    records = DocumentRecord.select().where(DocumentRecord.title == filename)
    if records.count() > 0:
        return jsonify({'content': '上传失败，同名文件已经存在。'})
    upload_dir = project_conf("upload_pre_training_folder") + Path(filename).stem + "/"  # 上传文件保存的目录

    try:
        new_document = DocumentRecord(
            user_id=user.user_id,
            title=filename,
            path=upload_dir,
            deleted=False,
            read_count=0,
            created_time=datetime.datetime.now(),
            updated_time=datetime.datetime.now(),
            trained=False,
            trained_file_path=upload_dir + 'index_' + Path(filename).stem + ".json",
            type="book",
        )
        new_document.save()
        # 创建根目录（若不存在）
        if not os.path.exists(project_conf("upload_pre_training_folder")):
            os.mkdir(project_conf("upload_pre_training_folder"))
        os.mkdir(upload_dir)
        file.save(os.path.join(upload_dir, filename))
    except Exception as e:
        logger.exception(e)
        return jsonify({'content': 'Error!'}), 400
    #training_service(new_document)
    return jsonify({'content': '文件训练中，请使用"{}"命令查看训练状态。'.format(DocumentList.getCmd())}), 200


def training_service(record: DocumentRecord):
    executor.submit(train_work, record)
    logging.info(record.path + " Training work start:")
    # train_work(record)


def train_work(record):
    log.info("Start training:" + record.title)

    try:
        documents = SimpleDirectoryReader(record.path).load_data()
        start_time = time.time()
        index = public_train_documents(documents)
        record.trained = True
        end_time = time.time()
        logging.info("Total time elapsed: {}".format(end_time - start_time))

        # index = GPTTreeIndex.from_documents(documents)
        # record.trained = True

        # save to disk
        # records[0].trained_data = index.save_to_string()
        path = record.path + 'index_' + Path(record.title).stem + ".json"

        # index.save_to_disk(path)
        index.storage_context.persist(persist_dir=path)

        record.trained_file_path = path
        record.updated_time = datetime.datetime.now()
        record.save()
        logging.info("Training successfully:" + path)

        store_query_engine(index, record.id)
        logging.info("Query engine store successfully:" + path)

    except Exception as e:
        record.trained = False
        logging.error(e)

def custom_secure_filename(filename):
    """
    自定义文件名安全处理函数，保留中文字符
    """
    filename = normalize("NFC", filename)
    filename = re.sub(r"[^\w\u4e00-\u9fa5_.-]", "", filename).strip().lower()
    return filename