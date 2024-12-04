
from http.client import HTTPException
import random
from fastapi import FastAPI, UploadFile, File
from starlette.responses import RedirectResponse

from OpenAi import generate_tags_ai, generate_tags_with_summary_ai, generate_tags_ai1, smartly_best_search_by_ai
from testing import redis_add_data, redis_search,redis_add
from Models import SaveRequest, SaveTagsRequest, SearchQuery, CourseCollection, Course
from file_handler import process_file, save_task_in_redis_vectors, add, add_to_redis_vector_store, add_redis, \
    search_stored_courses, search_stored_courses_opt, search_stored_courses_ss, create_course_collection
from dotenv import load_dotenv
import redis

app = FastAPI(swagger_ui_parameters={"deepLinking": False})
load_dotenv()
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

@app.post('/upload')
async def upload_file(file):

    if file.filename == '':
        return {"error": "File has no name"}

    try:
        file_content = process_file(file)
        tags = await generate_tags_ai(file_content)

        return {"tags": tags}
    except Exception as e:
        return {"error": str(e)}

@app.post("/generate-payload")
async def generate_payload(text):
    try:
        # Generate a random content ID
        content_id = random.randint(1000, 9999)

        # Construct the response
        response = {
            "text": text,
            "contentId": content_id,
            "contentTitle": "string"
        }
        return response
    except Exception as e:
        raise HTTPException(e)

@app.post('/generate-tags1' , include_in_schema=False)
async def generate_tags1(text):
    try:
        result = await generate_tags_with_summary_ai(text)

        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

@app.post('/generate-tags')
async def generate_tags(text):
    try:
        tags = await generate_tags_ai1(text)

        return {"tags": tags}
    except Exception as e:
        return {"error": str(e)}

@app.post('/save_tags')
async def save_tags(request: SaveTagsRequest):
    try:
        response = save_task_in_redis_vectors(request)
        return response
    except Exception as e:
        return {"error": str(e)}

@app.get('/', include_in_schema=False)
def redirect_to_swagger():
    return RedirectResponse(url="/docs")

@app.post('/add_tags')
async def add_tags(request: SaveTagsRequest):
    try:
        response = await add(request)
        return response
    except Exception as e:
        return {"error": str(e)}

@app.post('/generate-tags_nd_save_in_redis')
async def generate_tags_nd_save_in_redis(request: SaveRequest):
    try:
        tags_summary = await generate_tags_with_summary_ai(request.text)
        tags = tags_summary.get('Tags', [])
        summary = tags_summary.get('Summary', "No summary provided.")
        response = add_redis(request, tags, summary)
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}

@app.post("/search_courses")
async def search_courses(request: SearchQuery):
    try:
        response = await search_stored_courses_ss(request)
        return response
    except Exception as e:
        return {"error": str(e)}

@app.post("/search_courses_opt")
async def search_courses(request: SearchQuery):
    try:
        response = await search_stored_courses(request)
        return response
    except Exception as e:
        return {"error": str(e)}

@app.post("/test-add")
def extract_text():
    try:
        content = redis_add()
        return {"content": content}
    except Exception as e:
        return {"error": str(e)}

@app.post("/test-search")
def extract_text(text: str):
    try:
        content = redis_search(text, top_k=3)
        return {"content": content}
    except Exception as e:
        return {"error": str(e)}

# API endpoint for smart search
@app.post("/smart_search")
async def smart_search(request: SearchQuery):
    try:
        # Assuming search_stored_courses is an async function
        content = await search_stored_courses(request)
        # Run AI-based filtering and ranking
        response = await smartly_best_search_by_ai(content, request.query)
        # Convert the response into a course collection
        final_response = create_course_collection(response)
        # Return the final response
        return {"data": final_response}

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)