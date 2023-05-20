from llama_index import GPTTreeIndex, StorageContext, load_index_from_storage
from llama_index.indices.response import ResponseMode
from llama_index.indices.tree import TreeAllLeafRetriever
from llama_index.optimization import SentenceEmbeddingOptimizer
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.storage.index_store import SimpleIndexStore


def public_train_documents(documents):
    # return GPTTreeIndex.from_documents(documents, build_tree=False)
    return GPTTreeIndex.from_documents(documents)


def public_query_documents(index_path, query_keywords):

    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir=index_path)
    # load index
    index = load_index_from_storage(storage_context)
    retriever = index.as_retriever(retriever_mode='all_leaf')
    query_engine = RetrieverQueryEngine.from_args(
        streaming=True,
        optimizer=SentenceEmbeddingOptimizer(threshold_cutoff=0.7),
        retriever=retriever,
        response_mode=ResponseMode.TREE_SUMMARIZE,
    )
    return query_engine.query(query_keywords)
