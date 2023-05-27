from langchain.chat_models import ChatOpenAI
from llama_index import StorageContext, load_index_from_storage, ResponseSynthesizer, ServiceContext, LLMPredictor, \
    GPTTreeIndex, OpenAIEmbedding
from llama_index.embeddings.openai import OpenAIEmbeddingModelType, OpenAIEmbeddingMode
from llama_index.indices.document_summary import GPTDocumentSummaryIndex, DocumentSummaryIndexRetriever
from llama_index.indices.response import ResponseMode
from llama_index.indices.tree import TreeAllLeafRetriever
from llama_index.indices.tree.base import TreeRetrieverMode
from llama_index.optimization import SentenceEmbeddingOptimizer
from llama_index.query_engine import RetrieverQueryEngine


def public_train_documents(documents):
    # return GPTTreeIndex.from_documents(documents=documents)

    llm_predictor_chatgpt = LLMPredictor(llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo"))
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor_chatgpt, chunk_size_limit=1024)
    response_synthesizer = ResponseSynthesizer.from_args(response_mode=ResponseMode.TREE_SUMMARIZE,
                                                         use_async=True,
                                                         service_context=service_context)
    return GPTDocumentSummaryIndex.from_documents(documents=documents,
                                                  service_context=service_context,
                                                  response_synthesizer=response_synthesizer)


def public_query_documents(index_path, query_keywords):
    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir=index_path)
    index = load_index_from_storage(storage_context)

    # Tree index
    # build retriever
    # retriever = index.as_retriever()
    # query_engine = RetrieverQueryEngine.from_args(
    #     streaming=True,
    #     optimizer=SentenceEmbeddingOptimizer(threshold_cutoff=0.7,
    #                                          embed_model=OpenAIEmbedding(model=OpenAIEmbeddingModelType.CURIE,)),
    #     retriever=retriever,
    #     response_mode=ResponseMode.TREE_SUMMARIZE,
    # )

    # Document Summary Index
    # query_engine = index.as_query_engine(response_mode="tree_summarize", use_async=True)
    retriever = DocumentSummaryIndexRetriever(
        index=index,
    )
    llm_predictor_chatgpt = LLMPredictor(llm=ChatOpenAI(streaming=True, temperature=0, model_name="gpt-3.5-turbo"))
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor_chatgpt, chunk_size_limit=1024)
    response_synthesizer = ResponseSynthesizer.from_args(streaming=True,
                                                         # response_mode=ResponseMode.TREE_SUMMARIZE,
                                                         use_async=True,
                                                         # optimizer=SentenceEmbeddingOptimizer(threshold_cutoff=0.7),
                                                         service_context=service_context)
    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer
    )

    return query_engine.query(query_keywords)
