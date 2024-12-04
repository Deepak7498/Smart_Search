from pydantic import BaseModel, Field


class SaveTagsRequest(BaseModel):
    tags: list[str]
    contentId: str
    contentTitle: str


class SaveRequest(BaseModel):
    text: str
    contentId: int
    contentTitle: str

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5

class Course:
    def __init__(self, content, tags, summary, content_title, score):
        self.content = content
        self.tags = tags
        self.summary = summary
        self.content_title = content_title
        self.score = score

class CourseCollection:
    def __init__(self, courses=None):
        self.courses = courses if courses is not None else []

    def add_course(self, course):
        self.courses.append(course)

    def get_courses(self):
        return self.courses
