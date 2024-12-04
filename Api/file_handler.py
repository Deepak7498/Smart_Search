import json
import os

import numpy as np
import chardet
import mimetypes
import redis
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores.redis import Redis

from Models import CourseCollection, Course

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
VECTOR_DIM = os.getenv("VECTOR_DIM")
INDEX_NAME = os.getenv("INDEX_NAME")
redis_url =  os.getenv("redis_url")


def process_file(file):
    try:
        mime_type, _ = mimetypes.guess_type(file.filename)
        if not mime_type:
            raise ValueError("Unable to determine file type.")

        raw_data = file.read()

        if mime_type.startswith("text"):
            detected = chardet.detect(raw_data)
            encoding = detected.get("encoding", "utf-8")

            # Decode the text content
            content = raw_data.decode(encoding)
            if not content.strip():
                raise ValueError("File is empty.")
            return content

        elif mime_type == "application/json":
            # Decode JSON file content
            import json
            try:
                content = raw_data.decode("utf-8")
                json_data = json.loads(content)
                return json.dumps(json_data, indent=2)
            except Exception as e:
                raise ValueError(f"Invalid JSON file: {e}")

        elif mime_type.startswith("application"):
            return f"File is a binary type: {mime_type}"

        else:
            raise ValueError(f"Unsupported file type: {mime_type}")

    except Exception as e:
        raise ValueError(f"Error reading file: {e}")

def process_video_file(file):
    try:
        raise ValueError("File is empty.")

    except Exception as e:
        raise ValueError(f"Error reading file: {e}")

def create_course_collection(json_data):
    if not isinstance(json_data, dict) or 'matches' not in json_data:
        return {"Error": "Invalid or missing data in response"}

    course_collection = CourseCollection()

    # Efficiently add courses to the collection
    for item in json_data.get('matches', []):
        course = Course(
            content=item.get('content', ''),
            tags=item.get('tags', []),
            summary=item.get('summary', ''),
            content_title=item.get('contentTitle', ''),
            score=item.get('score', 0.0)
        )
        course_collection.add_course(course)

    return course_collection

def save_tags_in_redis(request):
    try:
        content_data = {
            "contentId": request.contentId,
            "contentTitle": request.contentTitle,
            "tags": request.tags
        }
        redis_key = f"content:{request.contentId}"
        redis_client.set(redis_key, json.dumps(content_data))
        return {"message": "Tags saved successfully.", "redis_key": redis_key}
    except Exception as e:
        raise ValueError(f"Error saving tags in Redis: {e}")


def save_task_in_redis_vectors(request):
    try:
        create_vector_index(INDEX_NAME, int(VECTOR_DIM))
        vector = np.random.rand(int(VECTOR_DIM))
        redis_key = save_vector(INDEX_NAME, vector, request.contentId, request.contentTitle, request.tags)
        return {"message": "Vector and metadata saved successfully under key.", "redis_key": redis_key}
    except Exception as e:
        raise ValueError(f"Error saving task in Redis: {e}")


def save_vector(index_name: str, vector: np.ndarray, contentId: int, contentTitle: str, tags: list[str]):
    try:
        redis_key = f"{index_name}:{contentId}"

        # Convert vector to bytes (float32 array)
        vector_bytes = vector.astype(np.float32).tobytes()

        # Save data to Redis as a hash
        redis_client.hset(
            redis_key,
            mapping={
                "contentId": contentId,
                "contentTitle": contentTitle,
                "tags": json.dumps(tags),
                "vector": vector_bytes
            }
        )
        return redis_key
    except Exception as e:
        return ValueError (f"Error saving vector: {e}")


def create_vector_index(index_name: str, vector_dim: int):
    """
    Create a vector index in Redis for storing vector data.
    """
    try:

        existing_indices = redis_client.execute_command("FT._LIST")
        if index_name in existing_indices:
            print(f"Index '{index_name}' already exists. Skipping creation.")
            return

        redis_client.execute_command(
            "FT.CREATE",
            index_name,
            "ON", "HASH",
            "PREFIX", "1", f"{index_name}:",
            "SCHEMA",
            "contentId", "NUMERIC",  # Metadata: content ID
            "contentTitle", "TEXT",  # Metadata: content title
            "tags", "TEXT",          # Metadata: tags
            "vector", "VECTOR", "FLAT",  # Vector field
            "6",                      # Vector index parameters
            "TYPE", "FLOAT32",
            "DIM", vector_dim,
            "DISTANCE_METRIC", "COSINE"
        )
        print(f"Vector index '{index_name}' created successfully.")
    except Exception as e:
        print(f"Error creating index: {e}")


async def add(request):
    content_data = {
        "contentId": request.contentId,
        "tags": request.tags
    }
    vector_store = Redis(
        redis_url=redis_url,
        index_name=f"smart_search",
        embedding=OpenAIEmbeddings()

    )

    document = [
        Document(
            page_content=request.contentTitle,
            metadata=content_data
        )
    ]
    try:
        document_ids = await vector_store.aadd_documents(documents=document)
        return document_ids
    except (Exception,) as ex:
        return ex

def add_redis(request, tags, summary):
    from redis.commands.search.field import VectorField, TagField

    metadata = {
        "content": request.contentId,
        "tags": tags,
        "contentTitle": request.contentTitle,
        "summary": summary
    }

    vector_store = Redis(
        redis_url=redis_url,
        index_name=f"smart_search",
        embedding=OpenAIEmbeddings()
    )

    document = [
        Document(
            page_content=request.contentTitle,
            metadata=metadata,
        )
    ]
    try:
        document_ids = vector_store.add_documents(document)
        return document_ids
    except (Exception,) as ex:
        return ValueError (f"Error saving vector: {ex}")

async def add_to_redis_vector_store(request, tags):
    """
    Add a document to the Redis vector store with optimized metadata and schema definition.
    """
    from redis.commands.search.field import TextField, NumericField, TagField, VectorField

    # Corrected schema with field names specified
    index_schema = {
        "title": TextField(name="title"),           # Title field for full-text search
        "contentId": NumericField(name="contentId"), # Numeric field for content ID
        "tags": TagField(name="tags"),              # Tag field for categories/tags
        "vector": VectorField(name="vector",         # Vector field for similarity search
                              algorithm="FLAT",      # Storage algorithm
                              attributes={
                                  "TYPE": "FLOAT32",
                                  "DIM": 1536,       # Match the embedding model output dimension
                                  "DISTANCE_METRIC": "COSINE"
                              })
    }

    # Define metadata for the document
    metadata = {
        "contentId": request.contentId,
        "tags": ",".join(tags),  # Store tags as a comma-separated string for TAG indexing
    }

    # Initialize Redis vector store
    vector_store = Redis(
        redis_url=redis_url,
        index_name="smart_search",
        embedding=OpenAIEmbeddings(),
        index_schema=index_schema,  # Pass schema as a dictionary
    )

    # Prepare the document
    document = [
        Document(
            page_content=request.contentTitle,
            metadata=metadata
        )
    ]

    try:
        # Add the document to the vector store
        document_ids = await vector_store.aadd_documents(documents=document)
        return {"status": "success", "document_ids": document_ids}
    except Exception as ex:
        raise ValueError(f"Error adding document to Redis: {ex}")




async def search_stored_courses_ss(query):
    vector_store = Redis(
        redis_url=redis_url,
        index_name="smart_search",
        embedding=OpenAIEmbeddings(),

    )

    try:
        results = await vector_store.asimilarity_search_with_relevance_scores(
            query.query,
            k=query.top_k
        )

        response = [
            {"contentId": result.metadata["id"], "score": score}
            for result, score in results
        ]
        return {"matches": response}
    except Exception as e:
        raise ValueError(f"Error searching for courses: {e}")

async def search_stored_courses2(query):
    """
    Perform similarity search to retrieve matching content IDs and fetch full metadata for each ID.
    """
    vector_store = Redis(
        redis_url=redis_url,
        index_name="smart_search",
        embedding=OpenAIEmbeddings(),
    )

    try:
        # Perform similarity search
        results = await vector_store.asimilarity_search_with_relevance_scores(
            query.query,
            k=query.top_k
        )

        # Initialize Redis client for fetching full metadata
        redis_client = vector_store.client  # Reuse the existing Redis client

        # Fetch data for each result
        response = []
        for result, score in results:
            # Extract the document ID (ensure compatibility with your metadata key structure)
            doc_id = result.metadata.get("id")
            if doc_id:
                # Fetch full data from Redis using the document ID
                key = doc_id
                data = redis_client.hgetall(key)

                # Decode byte strings into proper strings
                parsed_data = {
                    k.decode("utf-8"): v.decode("utf-8") if isinstance(v, bytes) else v
                    for k, v in data.items()
                }

                # Add score and parsed data to the response
                parsed_data["score"] = score
                response.append(parsed_data)

        return {"matches": response}

    except Exception as e:
        raise ValueError(f"Error searching for courses: {e}")

async def search_stored_courses(query):
    """
    Perform similarity search to retrieve matching content IDs and fetch full metadata for each ID.
    """
    vector_store = Redis(
        redis_url=redis_url,
        index_name="smart_search",
        embedding=OpenAIEmbeddings(),
    )

    try:
        # Perform similarity search
        results = await vector_store.asimilarity_search_with_relevance_scores(
            query.query,
            k=query.top_k#,
            #score_threshold = 0.9
        )

        # Initialize Redis client for fetching full metadata
        redis_client = vector_store.client  # Reuse the existing Redis client

        # Fetch data for each result
        response = []
        for result, score in results:
            # Extract the document ID (ensure compatibility with your metadata key structure)
            doc_id = result.metadata.get("id")
            if doc_id:
                # Fetch full data from Redis using the document ID
                # key = f"doc:smart_search:{doc_id}"
                data = redis_client.hgetall(doc_id)
                # Decode byte strings into proper strings
                parsed_data = {}
                for k, v in data.items():
                    try:
                        key = k.decode("utf-8") if isinstance(k, bytes) else k
                        value = v.decode("utf-8") if isinstance(v, bytes) else v
                        parsed_data[key] = value
                    except UnicodeDecodeError:
                        pass
                        # Log or handle the decoding error if needed
                        # print(f"Skipping item due to decoding error: {k} -> {v}")

                # Add score and parsed data to the response
                parsed_data["score"] = score
                response.append(parsed_data)

        return {"matches": response}

    except Exception as e:
        raise ValueError(f"Error searching for courses: {e}")

async def search_stored_courses_opt(query):
    """
    Perform similarity search to retrieve matching content IDs and fetch full metadata for each ID.
    """
    vector_store = Redis(
        redis_url=redis_url,
        index_name="smart_search",
        embedding=OpenAIEmbeddings(),
    )

    try:
        # Perform similarity search
        results = await vector_store.asimilarity_search_with_relevance_scores(
            query.query,
            k=query.top_k
        )

        # Initialize Redis client for fetching full metadata
        redis_client = vector_store.client  # Reuse the existing Redis client

        # Optimize data fetching by batching results
        doc_ids = [result.metadata.get("id") for result, _ in results if result.metadata.get("id")]

        if doc_ids:
            # Batch fetching the documents
            data_batch = redis_client.hmget(*doc_ids)  # Adjust depending on Redis client capabilities
            data_dict = {doc_id: data for doc_id, data in zip(doc_ids, data_batch)}

        response = []
        for result, score in results:
            doc_id = result.metadata.get("id")
            if doc_id:
                # Use cached data from batch fetch
                data = data_dict.get(doc_id, {})

                # Decode byte strings into proper strings
                parsed_data = {}
                for k, v in data.items():
                    try:
                        key = k.decode("utf-8") if isinstance(k, bytes) else k
                        value = v.decode("utf-8") if isinstance(v, bytes) else v
                        parsed_data[key] = value
                    except UnicodeDecodeError:
                        # Log or handle the decoding error if needed
                        print(f"Skipping item due to decoding error: {k} -> {v}")

                # Add score and parsed data to the response
                parsed_data["score"] = score
                response.append(parsed_data)

        return {"matches": response}

    except Exception as e:
        raise ValueError(f"Error searching for courses: {e}")


async def search_stored_courses3(query):
    """
    Perform a similarity search and return matching metadata with scores in a single operation.
    """
    vector_store = Redis(
        redis_url=redis_url,
        index_name="smart_search",
        embedding=OpenAIEmbeddings()
    )

    try:
        # Perform similarity search
        results = await vector_store.asimilarity_search_with_relevance_scores(
            query.query,
            k=query.top_k
        )

        # Combine metadata and scores into a single response
        response = [
            {
                "contentId": result.page_content,
                "contentTitle": result.metadata.get("contentTitle"),
                "tags": result.metadata.get("tags"),
                "score": score,
            }
            for result, score in results
        ]

        return {"matches": response}

    except Exception as e:
        raise ValueError(f"Error during search: {e}")
