import datetime
import asyncio
import logging
import os

from flask import jsonify
from llama_index import SimpleDirectoryReader, GPTSimpleVectorIndex

from common.db.document_record import DocumentRecord
from model.menuFunctions.document_list import DocumentList

from config import project_conf
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(2)


def upload_file_service(file):
    filename = file.filename.replace(" ", "")
    records = DocumentRecord.select().where(DocumentRecord.title == filename)
    if records.count() > 0:
        return jsonify({'result': '上传失败，同名文件已经存在。'})
    upload_dir = project_conf("upload_pre_training_folder") + Path(filename).stem + "/"  # 上传文件保存的目录

    # 创建根目录（若不存在）

    if not os.path.exists(project_conf("upload_pre_training_folder")):
        os.mkdir(project_conf("upload_pre_training_folder"))
    os.mkdir(upload_dir)
    file.save(os.path.join(upload_dir, filename))
    try:
        new_document = DocumentRecord(
            user_id=1,
            title=filename,
            path=upload_dir,
            deleted=False,
            read_count=0,
            created_time=datetime.datetime.now(),
            updated_time=datetime.datetime.now(),
            trained=False
        )
        new_document.save()
    except Exception as e:
        logging.ERROR(e)
        return jsonify({'result': 'Error!'})

    training_service(new_document)
    return jsonify({'result': '文件训练成功，请使用"{}"命令查看训练状态。'.format(DocumentList.getCmd())})


def training_service(record: DocumentRecord):
    logging.info("Start training:" + record.title)
    documents = SimpleDirectoryReader(record.path).load_data()
    index = GPTSimpleVectorIndex.from_documents(documents)
    # save to disk
    # records[0].trained_data = index.save_to_string()
    path = record.path + 'index_' + Path(record.title).stem + ".json"
    index.save_to_disk(path)
    record.trained = True
    record.trained_file_path = path
    record.updated_time = datetime.datetime.now()
    record.save()
    logging.info("Training successfully:" + path)
