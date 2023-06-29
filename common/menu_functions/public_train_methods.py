import logging
import time

from langchain import OpenAI
from langchain.chat_models import ChatOpenAI
from llama_index import StorageContext, load_index_from_storage, ResponseSynthesizer, ServiceContext, LLMPredictor, \
    set_global_service_context
from llama_index.indices.document_summary import GPTDocumentSummaryIndex, DocumentSummaryIndexRetriever, \
    DocumentSummaryIndexEmbeddingRetriever
from llama_index.indices.response import ResponseMode
from llama_index.query_engine import RetrieverQueryEngine

from app import query_engine_dict, query_engine_dict_size
from common.const import MODEL_GPT_35_TURBO, MODEL_TEXT_BABBAGE_001
from common.expire_time import ExpireTime

current_learning_model = MODEL_TEXT_BABBAGE_001
current_querying_model = MODEL_GPT_35_TURBO


# index_llm_predictor = LLMPredictor(llm=OpenAI(
#     streaming=True,
#     # use_async=True,
#     temperature=0,
#     model_name=current_learning_model,
#     # callbacks=[StreamingStdOutCallbackHandler()]
# ))
# index_service_context = ServiceContext.from_defaults(
#     llm_predictor=index_llm_predictor,
#     # chunk_size_limit=2048
# )
# index_response_synthesizer = ResponseSynthesizer.from_args(
#     streaming=True,
#     # use_async=True,
#     service_context=index_service_context
# )


# query_llm_predictor = LLMPredictor(llm=ChatOpenAI(
#     streaming=True,
#     # use_async=True,
#     temperature=0,
#     model_name=current_querying_model,
#     # max_tokens=100,
#     # callbacks=[StreamingStdOutCallbackHandler()]
# ))
# query_service_context = ServiceContext.from_defaults(
#     llm_predictor=query_llm_predictor,
#     # chunk_size_limit=2048
# )
# query_response_synthesizer_chatgpt = ResponseSynthesizer.from_args(
#     streaming=True,
#     # use_async=True,
#     service_context=query_service_context
# )


def public_train_documents(documents):
    index_llm_predictor = LLMPredictor(llm=OpenAI(
        # streaming=True,
        # use_async=True,
        temperature=0,
        model_name=current_learning_model,
        # callbacks=[StreamingStdOutCallbackHandler()]
    ))
    index_service_context = ServiceContext.from_defaults(
        llm_predictor=index_llm_predictor,
        chunk_size_limit=2048
    )
    index_response_synthesizer = ResponseSynthesizer.from_args(
        # streaming=True,
        # use_async=True,
        service_context=index_service_context
    )
    # return GPTVectorStoreIndex.from_documents(documents)
    return GPTDocumentSummaryIndex.from_documents(
        documents=documents,
        service_context=index_service_context,
        response_synthesizer=index_response_synthesizer
    )


def store_query_engine(index, index_order):
    query_llm_predictor = LLMPredictor(llm=ChatOpenAI(
        streaming=True,
        # use_async=True,
        temperature=0,
        model_name=current_querying_model,
        # max_tokens=100,
        # callbacks=[StreamingStdOutCallbackHandler()]
    ))
    query_service_context = ServiceContext.from_defaults(
        llm_predictor=query_llm_predictor,
        chunk_size_limit=2048
    )
    query_response_synthesizer = ResponseSynthesizer.from_args(
        streaming=True,
        # use_async=True,
        service_context=query_service_context
    )
    query_retriever = DocumentSummaryIndexEmbeddingRetriever(
        index=index,
        service_context=query_service_context
    )
    query_engine = RetrieverQueryEngine.from_args(
        streaming=True,
        # use_async=True,
        # optimizer=SentenceEmbeddingOptimizer(threshold_cutoff=0.7),
        top_k=1,
        retriever=query_retriever,
        service_context=query_service_context,
        response_synthesizer=query_response_synthesizer
    )
    # set_global_service_context(query_service_context)

    # store query engine
    query_engine['expire_time'] = ExpireTime()
    # pop the index expired or least recently used
    if len(query_engine_dict) >= query_engine_dict_size:
        # pop the item expired or closest to the expired time
        is_popped = False
        for key in query_engine_dict.keys():
            if query_engine_dict[key]['expire_time'].is_expired():
                query_engine_dict.pop(key)
                is_popped = True
                break
        if not is_popped:
            query_engine_dict.pop(min(query_engine_dict, key=lambda k: query_engine_dict[k]['last_access_time']))

    query_engine_dict[index_order] = query_engine


def public_load_index(index_path):
    # rebuild storage context
    index_llm_predictor = LLMPredictor(llm=OpenAI(
        # streaming=True,
        # use_async=True,
        temperature=0,
        model_name=current_learning_model,
        # callbacks=[StreamingStdOutCallbackHandler()]
    ))
    index_service_context = ServiceContext.from_defaults(
        llm_predictor=index_llm_predictor,
        chunk_size_limit=2048
    )
    index_response_synthesizer = ResponseSynthesizer.from_args(
        # streaming=True,
        # use_async=True,
        service_context=index_service_context
    )
    storage_context = StorageContext.from_defaults(persist_dir=index_path)
    return load_index_from_storage(
        storage_context=storage_context,
        index_type=GPTDocumentSummaryIndex,
        service_context=index_service_context,
        response_synthesizer=index_response_synthesizer
    )


def public_query_documents(index_path, query_keywords, index_order):

    # # vector store index
    # query_engine = index.as_query_engine(
    #     streaming=True,
    #     similarity_top_k=1
    # )

    # # Document Summary Index
    # query_llm_predictor = LLMPredictor(llm=ChatOpenAI(
    #     streaming=True,
    #     # use_async=True,
    #     temperature=0,
    #     model_name=current_querying_model,
    #     # max_tokens=100,
    #     # callbacks=[StreamingStdOutCallbackHandler()]
    # ))
    # query_service_context = ServiceContext.from_defaults(
    #     llm_predictor=query_llm_predictor,
    #     # chunk_size_limit=2048
    # )
    # query_response_synthesizer = ResponseSynthesizer.from_args(
    #     streaming=True,
    #     # use_async=True,
    #     service_context=query_service_context
    # )
    # index = public_load_index(index_path)
    # # query_retriever = DocumentSummaryIndexRetriever(
    # #     index=index,
    # #     service_context=query_service_context
    # # )
    # query_retriever = DocumentSummaryIndexEmbeddingRetriever(
    #     index=index,
    #     service_context=query_service_context
    # )
    # query_engine = RetrieverQueryEngine.from_args(
    #     streaming=True,
    #     # use_async=True,
    #     # optimizer=SentenceEmbeddingOptimizer(threshold_cutoff=0.7),
    #     top_k=1,
    #     retriever=query_retriever,
    #     service_context=query_service_context,
    #     response_synthesizer=query_response_synthesizer
    # )

    logging.info("Query engine list before query: " + str(query_engine_dict))
    if query_engine_dict.get(index_order) is None:
        index = public_load_index(index_path)
        store_query_engine(index, index_order)
    else:
        query_engine_dict[index_order]['last_access_time'] = time.time()
    query_engine = query_engine_dict[index_order]
    return query_engine.query(query_keywords)
