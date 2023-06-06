from langchain import OpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chat_models import ChatOpenAI
from llama_index import StorageContext, load_index_from_storage, ResponseSynthesizer, ServiceContext, LLMPredictor
from llama_index.indices.document_summary import GPTDocumentSummaryIndex, DocumentSummaryIndexRetriever
from llama_index.indices.response import ResponseMode
from llama_index.query_engine import RetrieverQueryEngine

from common.const import MODEL_GPT_35_TURBO, MODEL_TEXT_BABBAGE, MODEL_TEXT_BABBAGE_001


def public_train_documents(documents):
    # return GPTVectorStoreIndex.from_documents(documents)

    # llm_predictor_chatgpt = LLMPredictor(llm=OpenAI(
    #     streaming=True,
    #     # use_async=True,
    #     temperature=0,
    #     model_name=MODEL_TEXT_BABBAGE_001
    # ))
    llm_predictor_chatgpt = LLMPredictor(llm=ChatOpenAI(
        streaming=True,
        # use_async=True,
        temperature=0,
        model_name=MODEL_GPT_35_TURBO,
        # callbacks=[StreamingStdOutCallbackHandler()]
    ))
    service_context = ServiceContext.from_defaults(
        llm_predictor=llm_predictor_chatgpt,
        chunk_size_limit=2048
    )
    response_synthesizer = ResponseSynthesizer.from_args(
        response_mode=ResponseMode.TREE_SUMMARIZE,
        # use_async=True,
        service_context=service_context
    )
    return GPTDocumentSummaryIndex.from_documents(
        documents=documents,
        service_context=service_context,
        response_synthesizer=response_synthesizer
    )


def public_query_documents(index_path, query_keywords):

    # # vector store index
    # query_engine = index.as_query_engine(
    #     streaming=True,
    #     similarity_top_k=1
    # )

    # Document Summary Index
    llm_predictor_babbage = LLMPredictor(llm=OpenAI(
        streaming=True,
        # use_async=True,
        temperature=0,
        model_name=MODEL_TEXT_BABBAGE_001
    ))
    llm_predictor_chatgpt = LLMPredictor(llm=ChatOpenAI(
        streaming=True,
        # use_async=True,
        temperature=0,
        model_name=MODEL_GPT_35_TURBO,
        callbacks=[StreamingStdOutCallbackHandler()]
    ))
    service_context_babbage = ServiceContext.from_defaults(
        llm_predictor=llm_predictor_babbage,
        # chunk_size_limit=1024
    )
    service_context_chatgpt = ServiceContext.from_defaults(
        llm_predictor=llm_predictor_chatgpt,
        # chunk_size_limit=1024
    )
    response_synthesizer_babbage = ResponseSynthesizer.from_args(
        streaming=True,
        # use_async=True,
        service_context=service_context_babbage
    )
    response_synthesizer_chatgpt = ResponseSynthesizer.from_args(
        streaming=True,
        # use_async=True,
        service_context=service_context_chatgpt
    )
    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir=index_path)
    index = load_index_from_storage(
        storage_context=storage_context,
        index_type=GPTDocumentSummaryIndex,
        service_context=service_context_babbage,
        response_synthesizer=response_synthesizer_babbage
    )
    retriever = DocumentSummaryIndexRetriever(
        index=index,
        service_context=service_context_chatgpt
    )
    query_engine = RetrieverQueryEngine.from_args(
        streaming=True,
        # use_async=True,
        # optimizer=SentenceEmbeddingOptimizer(threshold_cutoff=0.7),
        retriever=retriever,
        service_context=service_context_chatgpt,
        response_synthesizer=response_synthesizer_chatgpt
    )

    return query_engine.query(query_keywords)
