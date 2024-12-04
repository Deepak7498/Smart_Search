import openai
import os
import json
import re

from pyexpat.errors import messages

openai.api_key = os.getenv("OPENAI_API_KEY")

async def generate_tags_ai1(content):
    #prompt = f"Analyze the following content and provide a list of 10 related tags:\n\n{content}"
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for generating content tags."},
            {"role": "user", "content": f"As an LMS provider, we aim to implement a smart search feature for our courses. Please analyze the following course description and generate a list of highly up to 10 relevant tags. The tags should be directly related to the course content, indicating what the course is about, what can be learned from it, and whether it is technical or non-technical. Additionally, include the level of the course (beginner, intermediate, or advanced). Provide the tags as a plain, comma-separated list.\n{content}"}
        ]
    )

    try:
        tags = response.choices[0].message.content.strip().split(', ')
    except Exception:
        tags = response.choices[0].message.content.strip().split('\n')
    print(tags)
    return tags


async def generate_tags_ai(content):
    #prompt = f"Analyze the following content and provide a list of 10 related tags:\n\n{content}"
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for generating content tags."},
            {"role": "user", "content": f"Analyze the following course description to generate a concise summary (minimum word count of 30) and a list of up to 10 highly relevant tags. Ensure the tags reflect the core topics, skills taught, and level of the course (beginner, intermediate, or advanced). Indicate whether the content is technical or non-technical. If the provided description lacks sufficient detail to create a proper summary and tags, include a polite message requesting more information. Present the tags as a plain, comma-separated list.{content}"}
            # {"role": "user", "content": f"As an LMS provider, we aim to implement a smart search feature for our courses. Please analyze the following course description and generate a list of highly up to 10 relevant tags. The tags should be directly related to the course content, indicating what the course is about, what can be learned from it, and whether it is technical or non-technical. Additionally, include the level of the course (beginner, intermediate, or advanced). Provide the tags as a plain, comma-separated list.\n{content}"}
        ]
    )

    try:
        tags = response.choices[0].message.content.strip().split(', ')
    except Exception:
        tags = response.choices[0].message.content.strip().split('\n')
    return tags

async def generate_tags_with_summary_ai(content):
    try:
        # Call the OpenAI API with the provided content
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for generating content tags."},
                {
                    "role": "user",
                    "content": (
                        f"Analyze the following course description to generate a concise summary (minimum word count of 30) "
                        f"and a list of up to 10 highly relevant tags. Ensure the tags reflect the core topics, skills taught, "
                        f"and level of the course (beginner, intermediate, or advanced). Indicate whether the content is technical "
                        f"or non-technical. If the provided description lacks sufficient detail to create a proper summary and tags, "
                        f"include a polite message requesting more information. Present the output as a JSON object with the fields "
                        f"'summary' (string) and 'tags' (array).\n\n{content}"
                    )
                }
            ]
        )

        # Extract and parse the API response
        response_content = response.choices[0].message.content.strip()
        # Assuming the response is JSON-like, convert it to a Python dictionary
        if response_content.startswith("```json"):
            response_content = response_content[7:-3].strip()
            response_data = json.loads(response_content)  # Use `json.loads` if it's a proper JSON string
            summary = response_data.get('summary', "No summary provided.")
            tags = response_data.get('tags', [])
            return {"Summary": summary, "Tags": tags}
        else:
            response_data = str(response_content)
            msg_cleaned = response_data.split('```json')[1].split('```')[0].strip()
            match = re.search(r'"summary":\s*"(.*?)"', msg_cleaned, re.DOTALL)
            summary = match.group(1) if match else "Summary not found."
            return {"Error": summary}


    except Exception as e:
        return {"Summary": "Error occurred in processing.", "Tags": []}


async def smartly_best_search_by_ai(content, query):
    try:
        content = str(content)

        # Efficiently call the OpenAI API
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert AI in content categorization and ranking. "
                        "Your task is to filter and rank programming-related courses based on the user's query. "
                        "Prioritize courses that are closely related to the user's query, focusing on programming languages, frameworks, or technologies. "
                        "If the user specifies that they are looking for 'technical' courses, filter for courses that focus on programming languages, frameworks, tools, and technologies. "
                        "If they specify 'non-technical' courses, filter for courses that focus on soft skills, industry knowledge, or general concepts. "
                        "Make sure to include exact or partial matches to the query in the 'content_title', 'tags', and 'summary'. You should return the courses that most closely match the query based on the provided keywords. "
                        "You must only include courses that are classified as 'Beginner' or 'Intermediate' level. "
                        "Rank the courses based on how closely they match the user's query. "
                        "Start with a score of 1.0 for the course with the best match (highest relevance), with descending scores based on relevance to the query. "
                        "Return the results in JSON format, including all properties of each course. If no courses match, return an empty array. "
                        "Ensure that the comparison between the query and course titles or descriptions allows for partial matches, so that courses like 'Introduction to APIs' can be correctly identified."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"I have a collection of courses, and I need to filter and rank those that are related to '{query}' and match the following criteria: "
                        f"1. Filter by courses that closely match the query, including exact or partial matches in 'content_title', 'tags', or 'summary'. "
                        f"2. If I specify 'technical' or 'non-technical', filter courses accordingly (technical courses focus on programming languages, frameworks, or development tools). "
                        f"3. Only include courses that are 'Beginner' or 'Intermediate' level. "
                        f"4. Rank the courses starting from 1.0 for the best match based on relevance to the query. "
                        f"5. Please provide the filtered and ranked results in JSON format only, under 'matches' with the following structure: "
                        f"6. including all properties of each course. with no extra explanations.\n\n{content}"
                        f"7. If no courses match, return an empty JSON array."
                    )
                }
            ]
            # messages= [
            #     {
            #         "role": "system",
            #         "content": (
            #             "You are an expert AI in content categorization and ranking. "
            #             "Your task is to filter and rank programming-related courses based on the user's query. "
            #             "You should prioritize courses that are most closely related to programming languages, frameworks, or technologies. "
            #             "If the user specifies that they are looking for 'technical' courses, filter for courses that focus on programming languages, frameworks, tools, and technologies. "
            #             "If they specify 'non-technical' courses, filter for courses that focus on soft skills, concepts, or general industry knowledge. "
            #             "The courses should only include those categorized as 'Beginner' or 'Intermediate'. "
            #             "Rank the courses based on how closely they match the user's query. "
            #             "The scores should start at 1.0 for the course with the closest match, with descending scores for less relevant matches. "
            #             "Return the filtered and ranked courses in descending order with updated scores in JSON format. "
            #             "If no courses match the query, return an empty JSON array, and provide no other explanations."
            #         )
            #     },
            #     {
            #         "role": "user",
            #         "content": (
            #             f"I have a collection of courses, and I need to filter those that are {query} Related Courses. "
            #             f"Please return the filtered courses ranked based on the relevance to programming languages, frameworks, or technologies. "
            #             f"If I specify technical or non-technical courses, please filter accordingly. "
            #             f"Assign each course a relevance score, starting from 1.0 (best match), and descending sequentially based on the contentTitle's match to the search query. "
            #             f"Only include courses classified as Beginner or Intermediate. "
            #             f"Return the results in JSON format collection under matches like related query, including all course properties, with no extra explanations.\n\n{content}"
            #         )
            #     }
            # ]
            # messages=[
            #     {
            #         "role": "system",
            #         "content": (
            #             "You are an expert AI in content categorization and ranking. "
            #             "Your task is to filter and rank programming-related courses based on their level "
            #             "(Beginner to Intermediate) and relevance to the topic. Prioritize technical courses "
            #             "that focus on programming languages, frameworks, or technologies. Assign scores starting "
            #             "from 1.0 (best match) and descending sequentially based on relevance. Only include courses "
            #             "that are classified as Beginner or Intermediate level. Return the filtered and ranked courses "
            #             "in descending order with updated scores."
            #         )
            #     },
            #     {
            #         "role": "user",
            #         "content": f"I have a collection of courses, and I need to filter those that are {query} Related Courses. The filtered courses should be ranked based on relevance to programming languages, frameworks, or technologies. Each course should be assigned a score starting from 1.0 and descending sequentially. Please provide the filtered and ranked results in JSON format only, including all course properties, with no additional explanations.\n\n{content}"
            #     }
            # ]
        )

        # Safely parse the response, handling any potential errors in the response format
        response_data = response.choices[0].message.content.strip()
        print(response_data)
        if response_data.startswith("```json"):
            clean_string = response_data.replace("```json\n", "").replace("\n```", "")
            json_data = json.loads(clean_string)
            print(json_data)
            return json_data
        else:
            raise ValueError("Unexpected response format from OpenAI API.")

    except openai.OpenAIError as e:
        return {"Error": f"OpenAI API error: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"Error": f"JSON decoding error: {str(e)}"}
    except Exception as e:
        return {"Error": f"Error occurred: {str(e)}"}