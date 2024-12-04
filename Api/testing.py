from langchain_community.vectorstores.redis import Redis
from langchain_openai import OpenAIEmbeddings
import os

redis_url =  os.getenv("redis_url")
metadata = [
    {
        "user": "john",
        "age": 18,
        "job": "engineer",
        "credit_score": "high",
    },
    {
        "user": "derrick",
        "age": 45,
        "job": "doctor",
        "credit_score": "low",
    },
    {
        "user": "nancy",
        "age": 94,
        "job": "doctor",
        "credit_score": "high",
    },
    {
        "user": "tyler",
        "age": 100,
        "job": "engineer",
        "credit_score": "high",
    },
    {
        "user": "joe",
        "age": 35,
        "job": "dentist",
        "credit_score": "medium",
    },
]
texts = ["foo", "foo", "foo", "bar", "bar"]

def redis_add_data():
    rds = Redis.from_texts(
        texts,
        OpenAIEmbeddings(),
        metadatas=metadata,
        redis_url=redis_url,
        index_name="users",
    )
    print("Data added to Redis.")
    return "Data added to Redis."

def redis_search(query: str, top_k: int = 3):
    # Reinitialize Redis connection
    embedding = OpenAIEmbeddings()
    rds = Redis(
        redis_url=redis_url,
        index_name="users",
        embedding=embedding
    )
    rds.set_schema({
        'numeric': [{'name': 'age', 'no_index': False, 'sortable': False}],
        'text': [
            {'name': 'user', 'no_index': False, 'no_stem': False, 'sortable': False, 'weight': 1, 'withsuffixtrie': False},
            {'name': 'job', 'no_index': False, 'no_stem': False, 'sortable': False, 'weight': 1, 'withsuffixtrie': False},
            {'name': 'credit_score', 'no_index': False, 'no_stem': False, 'sortable': False, 'weight': 1, 'withsuffixtrie': False},
            {'name': 'content', 'no_index': False, 'no_stem': False, 'sortable': False, 'weight': 1, 'withsuffixtrie': False}
        ],
        'vector': [{'algorithm': 'FLAT', 'datatype': 'FLOAT32', 'dims': 1536, 'distance_metric': 'COSINE', 'name': 'content_vector'}]
    })
    # Perform similarity search
    results = rds.similarity_search(query, k=top_k)
    meta = results[1].metadata
    print("Key of the document in Redis: ", meta.pop("id"))
    print("Metadata of the document: ", meta)
    return meta

def redis_add():
    rds = Redis.from_texts(
        texts,
        OpenAIEmbeddings(),
        metadatas=metadata,
        redis_url=redis_url,
        index_name="users",
        schema={
            # Define how your vectors and metadata will be stored
            'vector_field': {
                'name': 'document_embedding',  # Name of the vector field
                'type': 'VECTOR',
                'dims': 1536,  # Dimension of OpenAI embeddings
                'algorithm': 'HNSW',  # Hierarchical Navigable Small World graph
                'distance_metric': 'COSINE'
            },
            'metadata_fields': [
                {'name': 'source', 'type': 'TAG'},
                {'name': 'chunk', 'type': 'NUMERIC'},
                {'name': 'text', 'type': 'TEXT'}
            ]
        }
    )
    # return metadata
    results = rds.similarity_search("foo", k=3)
    meta = results[1].metadata
    print("Key of the document in Redis: ", meta.pop("id"))
    print("Metadata of the document: ", meta)
    return meta

