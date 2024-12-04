# from flask import Flask, request, jsonify, send_from_directory
# from flask_swagger_ui import get_swaggerui_blueprint
# from file_handler import process_file
# import openai
# from flask_cors import CORS
# import os
# from dotenv import load_dotenv
#
# load_dotenv()
# openai.api_key = os.getenv("OPENAI_API_KEY")
#
# app = FastAPI(swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"})
# CORS(app)
# upload_folder = r"D:\videos"
# os.makedirs(upload_folder, exist_ok=True)
# app.config["UPLOAD_FOLDER"] = upload_folder
#
# SWAGGER_URL = "/swagger"
# API_URL = "http://127.0.0.1:5000/swagger.json"
#
# swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL)
# app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
#
# @app.route('/')
# def home():
#     return """
#     <h1>Welcome to the File Tagging API</h1>
#     <p>Visit <a href='/swagger'>Swagger UI</a> to explore the API documentation.</p>
#     """
#
# @app.route('/swagger.json')
# def swagger_json():
#     return send_from_directory('.', 'swagger.json')
#
#
# if __name__ == "__main__":
#     app.run(debug=True, use_reloader=False)
