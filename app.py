# This is the App of the project

# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "npx",
#     "fastapi",
#     "uvicorn",
#     "requests",
#     "prettier",
#     "openai",
#     "scipy",
#     "pillow",
#     "markdown",
#     "SpeechRecognition", 
#     "pydub",
# ] 
# ///

import base64
import datetime
import re
import sqlite3

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from scipy.spatial.distance import cosine
from PIL import Image
import speech_recognition as sr
from pydub import AudioSegment
import os
# import git
import openai
import markdown
import requests
import json
import subprocess

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=['POST', 'GET'],
    allow_headers=["*"],
)

# AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")

tools = [
    {
        "type" : "function",
        "function" : {
            "name" : "script_runner",
            "description" : "Install the package and run the url with provided arguments.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "script_url" : {
                        "type" : "string",
                        "pattern": r"https?://.*/*.py",
                        "description" : "The url of the script to run."
                    },
                    "arguments" : {
                        "type" : "array",
                        "items" : {
                            "type" : "string"
                        },
                        "description" : "The arguments to pass to the script."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id is 'A1'."
                    }
                },
                "required" : ["script_url", "args", "task_id"]
            }
        },
        "type" : "function",
        "function" : {
            "name" : "format_file",
            "description" : "format the file with prettier@3.4.2.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.md)",
                        "description" : "The path of the file to format."
                    },
                    "prettier_version" : {
                        "type" : "string",
                        "pattern": r"prettier@\d+\.\d+\.\d+",
                        "description" : "The version of prettier to use as example:'prettier@3.4.2'."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id is 'A2'."
                    }
                },
                "required" : ["file_path","prettier_version","task_id"]
            }
        },
        "type" : "function",
        "function" : {
            "name" : "day_counter",
            "description" : "Count the number of wednesdays from the given file destination.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "source_file_path" : {
                        "type" : "string",
                        "pattern": r"/data/(.*\.txt)",
                        "description" : "The path of the file to count the days."
                    },
                    "destination_file_path" : {
                        "type" : "string",
                        "description" : "The path of the file to store the number."
                    },
                    "day_name" : {
                        "type" : "string",
                        "description" : "The name of the day to count."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id is 'A3'."
                    }
                },
                "required" : ["source_file_path","destination_file_path","day_name","task_id"]
            }
        },
        "type" : "function",
        "function" : {
            "name" : "array_sorting",
            "description" : "sorting the list in file with last_name, then first_name and write to destinatin file.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "source_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.json)",
                        "description" : "The path of the file to get the array."
                    },
                    "destination_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.json)",
                        "description" : "The path of the file to store the sorted array."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id is 'A4'."
                    }
                },
                "required" : ["source_file_path","destination_file_path", "task_id"]
            }
        },
        "type" : "function",
        "function" : {
            "name" : "recent_log",
            "description" : "Write the first line of the 10 most recent .log file from the most recent first and write to index file.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "source_file_path" : {
                        "type" : "string",
                        "pattern": r".*/logs",
                        "default": "/data/logs",
                        "description" : "The path to get the log files."
                    },
                    "destination_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.txt)",
                        "default": "/data/logs-recent.txt",
                        "description" : "The path of the file to store the log lines."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id is 'A5'."
                    }
                },
                "required" : ["source_file_path","destination_file_path", "task_id"]
            }
        },
        "type" : "function",
        "function" : {
            "name" : "markdown_mapping",
            "description" : "Find all Markdown (.md) files and for each file, extract the first occurrance of each H1 to create an index file that maps each filename.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "source_file_path" : {
                        "type" : "string",
                        "pattern": r".*/docs",
                        "default": "/data/docs",
                        "description" : "The path of the file to get the markdown files."
                    },
                    "destination_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.json)",
                        "default": "/data/docs/index.json",
                        "description" : "The path of the file to store the mapping indexs."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id is 'A6'."
                    }
                },
                "required" : ["source_file_path","destination_file_path", "task_id"]
            }
        },
        "type" : "function",
        "function" : {
            "name" : "finding_mailadd",
            "description" : "Find email message form a file to extract the senders email address and write the email address to a file.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "source_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.txt)",
                        "default": "/data/email.txt",
                        "description" : "The path of the file to get email message."
                    },
                    "destination_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.txt)",
                        "default": "/data/email-sender.txt",
                        "description" : "The path of the file to store the mail address."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id from set 'A7'."
                    }
                },
                "required" : ["source_file_path","destination_file_path", "task_id"]
            }
        },
        "type" : "function",
        "function" : {
            "name" : "find_cardno",
            "description" : "finding the cardno from a image and storing to a text file.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "source_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.png)",
                        "default": "/data/credit-card.png",
                        "description" : "The path of the file to get the array."
                    },
                    "destination_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.txt)",
                        "default": "/data/credit-card.txt",
                        "description" : "The path of the file to store the sorted array."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id is 'A8'."
                    }
                },
                "required" : ["source_file_path","destination_file_path", "task_id"]
            }
        },
        "type" : "function",
        "function" : {
            "name" : "most_similar_comments",
            "description" : "Finding the most similar pair from a given file path to write it in text file.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "source_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.txt)",
                        "default": "/data/comments.txt",
                        "description" : "The path of the file to get the array."
                    },
                    "destination_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.txt)",
                        "default": "/data/similar-comments.txt",
                        "description" : "The path of the file to store the sorted array."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id is 'A9'."
                    }
                },
                "required" : ["source_file_path","destination_file_path", "task_id"]
            }
        },
        "type" : "function",
        "function" : {
            "name" : "database",
            "description" : "Finding the total sales of all the items in the given ticket type from the SQLite database file path.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "source_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.db)",
                        "default": "/data/ticket-sales.db",
                        "description" : "The path of the file to get the array."
                    },
                    "destination_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.txt)",
                        "default": "/data/ticket-sales.txt",
                        "description" : "The path of the file to store the sorted array."
                    },
                    "ticket_type" : {
                        "type" : "string",
                        "description" : "The type of the ticket."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id is 'A10'."
                    }
                },
                "required" : ["source_file_path","destination_file_path","ticket_type","task_id"]
            }
        },
    
    
        "type" : "function",
        "function" : {
            "name" : "donot_allow",
            "description" : "If the provided data path not contains /data or want to delete any file.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "file_path" : {
                        "type" : "string",
                        "description" : "The path of the file."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id from set 'B12'."
                    }
                },
                "required" : ["file_path", "task_id"]
            }
        },
        "type" : "function",
        "function" : {
            "name" : "download_file",
            "description" : "Download the file from the given url to specifid path.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "url" : {
                        "type" : "string",
                        "pattern": r"https?://.*",
                        "description" : "The url of the file to download."
                    },
                    "destination_file_path" : {
                        "type" : "string",
                        "pattern": r".*/.*",
                        "description" : "The path of the file to store the downloaded file."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id is B3."
                    }
                },
                "required" : ["url","destination_file_path", "task_id"]
            }
        },
        "type" : "function",
        "function" : {
            "name" : "clone_repo",
            "description" : "Clone a git repo form given url to a the given directory and make a commit.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "url" : {
                        "type" : "string",
                        "description" : "The url of the git repo to clone."
                    },
                    "destination_directory" : {
                        "type" : "string",
                        "description" : "The directory to clone the repo."
                    },
                    "commit_message" : {
                        "type" : "string",
                        "description" : "The commit message."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id is B4."
                    }
                },
                "required" : ["url","destination_directory","commit_message", "task_id"]
            }
        },
        "type" : "function",
        "function" : {
            "name" : "run_query",
            "description" : "Run any query from given database file and store it to given destination.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "query" : {
                        "type" : "string",
                        "description" : "The query to run."
                    },
                    "source_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.db)",
                        "description" : "The path of the file to run the query."
                    },
                    "destination_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.txt)",
                        "default": "/data/query-result.txt",
                        "description" : "The path of the file to store the query result."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id is 'B5'."
                    }
                },
                "required" : ["query","source_file_path","destination_file_path","task_id"]
            }
        },
        "type" : "function",
        "function" : {
            "name" : "extract_data",
            "description" : "Extract data from any website or webscraping and store it in a file.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "url" : {
                        "type" : "string",
                        "pattern": r"https?://.*",
                        "description" : "The url of the website to extract data."
                    },
                    "destination_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.txt)",
                        "default": "/data/extracted-data.txt",
                        "description" : "The path of the file to store the extracted data."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id is 'B6'."
                    }
                },
                "required" : ["url","destination_file_path","task_id"]
            }
        },
        "type" : "function",
        "function" : {
            "name" : "compress_image",
            "description" : "Compress or resize any image file.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "source_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.(jpg|jpeg|png|gif|bmp))",
                        "description" : "The path of the file to compress."
                    },
                    "destination_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.png)",
                        "description" : "The path of the file to store the compressed image."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id 'B7'."
                    }
                },
                "required" : ["source_file_path","destination_file_path","task_id"]
            }
        },
        "type" : "function",
        "function" : {
            "name" : "transcribe_audio",
            "description" : "Transcribe audio from an MP3 file.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "source_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.mp3)",
                        "description" : "The path of the file to transcribe."
                    },
                    "destination_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.txt)",
                        "default": "/data/transcription.txt",
                        "description" : "The path of the file to store the transcription."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id is 'B8'."
                    }
                },
                "required" : ["source_file_path","destination_file_path","task_id"]
            }
        },
        "type" : "function",
        "function" : {
            "name" : "markdown_to_html",
            "description" : "Convert a markdown file to HTML.",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "source_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.md)",
                        "description" : "The path of the file to convert."
                    },
                    "destination_file_path" : {
                        "type" : "string",
                        "pattern": r".*/(.*\.html)",
                        "default": "/data/converted.html",
                        "description" : "The path of the file to store the converted HTML."
                    },
                    "task_id" : {
                        "type" : "string",
                        "description" : "The task id is 'B9'."
                    }
                },
                "required" : ["source_file_path","destination_file_path","task_id"]
            }
        }
    }
]

@app.get("/")
async def root():
    return {"message": "Hello World from Project"}

@app.get("/read")
async def read(path: str):
    if not path.startswith("/data"):
        raise HTTPException(status_code = 403, detail = "File Access Denied!!")
    if not os.path.exists(path):
        raise HTTPException(status_code = 404, detail = "File Not Found!!")
    try:
        with open(path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

@app.post("/run")
async def task(task: str = Query(None)):
    if not task:
        raise HTTPException(status_code=400, detail="Bad Request:Task is empty")
    task_code = get_task_code(task)
    print(task_code)
    if task_code == 'Error fetching the result. ErrorCode: 500':
        raise HTTPException(status_code=500, detail=task_code)
    if task_code['task_id'] == 'A1':
        msg = A1_script_runner(task_code)
    elif task_code['task_id'] == 'A2':
        msg = A2_format_file(task_code)
    elif task_code['task_id'] == 'A3':
        msg = A3_day_counter(task_code)
    elif task_code['task_id'] == 'A4':
        msg = A4_array_sorting(task_code)
    elif task_code['task_id'] == 'A5':
        msg = A5_recent_log(task_code)
    elif task_code['task_id'] == 'A6':
        msg = A6_markdown_mapping(task_code)
    elif task_code['task_id'] == 'A7':
        msg = A7_finding_mailadd(task_code)
    elif task_code['task_id'] == 'A8':
        msg = A8_find_cardno(task_code)
    elif task_code['task_id'] == 'A9':
        msg = A9_most_similar_comments(task_code)
    elif task_code['task_id'] == 'A10':
        msg = A10_database(task_code)

    elif task_code['task_id'] == 'B12':
        msg = B12_donot_allow(task_code)
    elif task_code['task_id'] == 'B3':
        msg = B3_download_file(task_code)
    # elif task_code['task_id'] == 'B4':
    #     msg = B4_clone_repo(task_code)
    elif task_code['task_id'] == 'B5':
        msg = B5_run_query(task_code)
    elif task_code['task_id'] == 'B6':
        msg = B6_extract_data(task_code)
    elif task_code['task_id'] == 'B7':
        msg = B7_compress_image(task_code)
    elif task_code['task_id'] == 'B8':
        msg = B8_transcribe_audio(task_code)
    elif task_code['task_id'] == 'B9':
        msg = B9_markdown_to_html(task_code)
    return msg

def get_task_code(task: str)-> dict:
    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('AIPROXY_TOKEN')}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": """
        You are a Task execution agent. I am providing a set of options as A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, B12, B3, B4, B5, B6, B7, B8, B9 for you to choose the tool to run the task.
        A1 : If the task contains running a script with uv, you can use script_runner tool.
        A2 : If the task contains formating any file with given directry with prettier, you can use format_file tool.
        A3 : If the task contains counting the number of weekday, you can use day_counter tool.
        A4 : If the task contains sorting of array by last_name, then first_name, you can use array_sorting tool.
        A5 : If the task contains writing the first line of the 10 most recent .log file from the most recent first, you can use recent_log tool.
        A6 : If the task contains finding all Markdown (.md) files and for each file, extract the first occurrance of each H1 to create an index file that maps each filename, you can use markdown_mapping tool.
        A7 : If the task contains finding email message form a file path to extract the senders email address and write the email address to a file, you can use finding_mailadd tool.
        A8 : If the task contains finding credit card no from a image and storing to a text file, you can use find_cardno tool.
        A9 : If the task contains finding the most similar pair of comments from given file path and write them to a text file, you can use most_similar_comments tool.
        A10 : If the task contains the SQLite database file path to find the total sales of all the items in the given ticket type, write the number in a text file, you can use database tool.
        
        B12 : If the provided want to delete any file, you can use donot_allow tool.
        B3 : If the task download the file from the given url to specifid path, you can use download_file tool.
        B5 : If the task is to run any query from given database file, you can use run_query tool.
        B6 : If the task is to extract data from any website or webscraping and store it in a file, you can use extract_data tool.
        B7 : If the task is to compress or resize any image file, you can use compress_image tool.
        B8 : If the task is to transcribe audio from an MP3 file, you can use transcribe_audio tool.
        B9 : If the task is to convert a markdown file to HTML, you can use markdown_to_html tool.
        Make sure to provide task_id from the set A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, B12, B3, B4, B5, B6, B7, B8, B9 in the task_id argument.
                """
            },
            {
                "role": "user",
                "content": task
            }
        ],
        "tools" : tools,
        "tool_choice" : "auto"
    }

    response = requests.post(url=url, headers=headers, json=data)
    # return response.json()
    if response.status_code == 200:
        result = response.json()["choices"][0]["message"]["tool_calls"][0]["function"]
        print(result)
        res = json.loads(result["arguments"])
        return res
    else:
        return 'Error fetching the result. ErrorCode: {}'.format(response.status_code)
    
def A1_script_runner(task_code):
    script_url = task_code['script_url']
    email = task_code['args'][0]
    
    # Run the script with the email argument
    command = ["uv", "run", script_url, email]
    try:
        subprocess.run(command, check=True)
        print("Script executed successfully.")
        return {"message": "Script executed successfully."}
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        return {"message": "Task execution failed."}
    
def A2_format_file(task_code):
    file_path = task_code['file_path']
    prettier_version = task_code['prettier_version']
    if not prettier_version.startswith("prettier@") or prettier_version == "prettier":
        prettier_version = "prettier@3.4.2"
    command = ["npx", prettier_version, "--write", file_path]
    try:
        subprocess.run(command, check=True)
        print("Prettier executed successfully.")
        return {"message": "Prettier executed successfully."}
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        return {"message": "Task execution failed."}

def A3_day_counter(task_code):
    source_file_path = task_code['source_file_path']
    destination_file_path = task_code['destination_file_path']
    if not os.path.exists(destination_file_path):
        destination_file_path = os.path.join(os.path.dirname("/data"), "dates-wednesdays.txt")
    day = weekday_map[task_code['day_name']]

    weekday_map = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6
    }

    date_formats = [
        "%Y/%m/%d %H:%M:%S",  # e.g., 2008/04/22 06:26:02
        "%Y-%m-%d",           # e.g., 2006-07-21
        "%b %d, %Y",          # e.g., Sep 11, 2006
        "%d-%b-%Y",           # e.g., 28-Nov-2021
    ]

    day_count = 0

    with open(source_file_path, "r") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue  # Skip empty lines

            parsed_date = None
            # Try each date format until one succeeds.
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(line, fmt)
                    break  # Exit loop if parsing is successful.
                except ValueError:
                    continue

            if parsed_date is None:
                # Optionally log the unparsable line.
                print(f"Warning: Could not parse date: {line}")
                continue

            # datetime.weekday() returns Monday=0, Tuesday=1, Wednesday=2, etc.
            if parsed_date.weekday() == day:
                day_count += 1

    # Write just the count to the output file.
    with open(destination_file_path, "w") as file:
        file.write(str(day_count))

    return {"wednesday_count": day_count}

def A4_array_sorting(task_code):
    source_file_path = task_code['source_file_path']
    destination_file_path = task_code['destination_file_path']
    if not os.path.exists(destination_file_path):
        destination_file_path = os.path.join(os.path.dirname("/data"), "contacts-sorted.json")
    if not os.path.exists(source_file_path):
        raise HTTPException(status_code=500, detail="Source file not found.")
     # Load the contacts from the JSON file
    with open(source_file_path, 'r') as file:
        try:
            contacts = json.load(file)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON file.")

    # Sort the contacts by last_name and then by first_name
    sorted_contacts = sorted(contacts, key=lambda x: (x['last_name'], x['first_name']))

    # Write the sorted contacts to the new JSON file
    with open(destination_file_path, 'w') as file:
        json.dump(sorted_contacts, file, indent=4)

    return {"message": "File sorted successfully."}

def A5_recent_log(task_code):
    source_file_path = task_code['source_file_path']
    destination_file_path = task_code['destination_file_path']
    if not os.path.exists(destination_file_path):
        destination_file_path = os.path.join(os.path.dirname("/data"), "recent-logs.txt")
    if not os.path.exists(source_file_path):
        raise HTTPException(status_code=500, detail="Source file not found.")
    # Get list of .log files sorted by modification time (most recent first)
    log_files = sorted(source_file_path.glob('*.log'), key=os.path.getmtime, reverse=True)[:10]

    # Read first line of each file and write to the output file
    with destination_file_path.open('w') as f_out:
        for log_file in log_files:
            with log_file.open('r') as f_in:
                first_line = f_in.readline().strip()
                f_out.write(f"{first_line}\n")

    return {"message": "Recent logs written successfully."}

def A6_markdown_mapping(task_code):
    source_file_path = task_code['source_file_path']
    destination_file_path = task_code['destination_file_path']
    if not os.path.exists(destination_file_path):
        destination_file_path = os.path.join(os.path.dirname("/data/docs"), "index.json")
    if not os.path.exists(source_file_path):
        raise HTTPException(status_code=500, detail="Source file not found.")
    # Get list of .md files
    docs_dir = source_file_path
    output_file = destination_file_path
    index_data = {}

    # Walk through all files in the docs directory
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                # print(file)
                file_path = os.path.join(root, file)
                # Read the file and find the first occurrence of an H1
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('# '):
                            # Extract the title text after '# '
                            title = line[2:].strip()
                            # Get the relative path without the prefix
                            relative_path = os.path.relpath(file_path, docs_dir).replace('\\', '/')
                            index_data[relative_path] = title
                            break  # Stop after the first H1
    # Write the index data to index.json
    # print(index_data)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=4)
    return {"message": "Markdown files mapped successfully."}

def A7_finding_mailadd(task_code):
    source_file_path = task_code['source_file_path']
    destination_file_path = task_code['destination_file_path']
    if not os.path.exists(destination_file_path):
        destination_file_path = os.path.join(os.path.dirname("/data"), "email-sender.txt")
    if not os.path.exists(source_file_path):
        raise HTTPException(status_code=500, detail="Source file not found.")
    input_file = source_file_path
    output_file = destination_file_path

    with open(input_file, "r", encoding="utf-8") as f:
        email_content = f.read()

    token = os.environ.get("AIPROXY_TOKEN")

    if not token:
        return {"error": "AIPROXY_TOKEN environment variable not set."}

    openai.api_key = token
    openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"

    # 4. Build a prompt instructing GPT-4o-Mini to extract only the sender’s email
    #    We'll ask for a JSON response to parse it safely.
    prompt = (
        "You are a helpful assistant. I have an email message:\n\n"
        f"{email_content}\n\n"
        "Please extract only the sender’s email address from this email. "
        "Return your answer in a JSON object with a single key 'sender_email'. For example:\n"
        "{\n  \"sender_email\": \"example@domain.com\"\n}\n\n"
        "Return only the JSON object."
    )

    try:
        # 5. Make the GPT-4o-Mini chat request
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant to find the email address."},
                {"role": "user", "content": prompt},
            ]
        )

        # 6. Parse the raw response
        raw_message = response["choices"][0]["message"]["content"].strip()
        # Remove potential code fences
        raw_message = re.sub(r"^```json\s*", "", raw_message)
        raw_message = re.sub(r"\s*```$", "", raw_message)

        if not raw_message:
            return {"error": "LLM returned empty response."}

        # Attempt to parse JSON
        try:
            data = json.loads(raw_message)
        except json.JSONDecodeError:
            return {
                "error": "LLM response was not valid JSON.",
                "raw_response": raw_message
            }

        sender_email = data.get("sender_email", "").strip()
        if not sender_email:
            return {
                "error": "No 'sender_email' found in LLM response.",
                "raw_response": raw_message
            }

        # 7. Write the sender’s email to /data/email-sender.txt
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(sender_email + "\n")

        return {
            "status": "success",
            "sender_email": sender_email,
            "written_file": output_file
        }

    except Exception as e:
        return {"error": str(e)}

def png_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        base64_string = base64.b64encode(image_file.read()).decode('utf-8')
    return base64_string

def A8_find_cardno(task_code):
    source_file_path = task_code['source_file_path']
    destination_file_path = task_code['destination_file_path']
    if not os.path.exists(destination_file_path):
        destination_file_path = os.path.join(os.path.dirname("/data"), "cardno.txt")
    if not os.path.exists(source_file_path):
        raise HTTPException(status_code=500, detail="Source file not found.")
    # Construct the request body for the AIProxy call
    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "There is 8 or more digit number is there in this image, with space after every 4 digit, only extract the those digit number without spaces and return just the number without any other characters"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{png_to_base64(source_file_path)}"
                        }
                    }
                ]
            }
        ]
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('AIPROXY_TOKEN')}"
    }
    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

    # Make the request to the AIProxy service
    response = requests.post(url=url, headers=headers, data=json.dumps(body))
    # response.raise_for_status()

    # Extract the credit card number from the response
    result = response.json()
    # print(result); return None
    card_number = result['choices'][0]['message']['content'].replace(" ", "")

    # Write the extracted card number to the output file
    with open(destination_file_path, 'w') as file:
        file.write(card_number)

    return {"message": "Card number extracted successfully."}

def get_embedding(text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('AIPROXY_TOKEN')}"
    }
    data = {
        "model": "text-embedding-3-small",
        "input": [text]
    }
    url = "http://aiproxy.sanand.workers.dev/openai/v1/embeddings"
    response = requests.post(url=url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]

def A9_most_similar_comments(task_code):
    source_file_path = task_code['source_file_path']
    destination_file_path = task_code['destination_file_path']
    if not os.path.exists(destination_file_path):
        destination_file_path = os.path.join(os.path.dirname("/data"), "similar-comments.txt")
    if not os.path.exists(source_file_path):
        raise HTTPException(status_code=500, detail="Source file not found.")
    # Construct the request body for the AIProxy call
     # Read comments
    with open(source_file_path, 'r') as f:
        comments = [line.strip() for line in f.readlines()]

    # Get embeddings for all comments
    embeddings = [get_embedding(comment) for comment in comments]

    # Find the most similar pair
    min_distance = float('inf')
    most_similar = (None, None)

    for i in range(len(comments)):
        for j in range(i + 1, len(comments)):
            distance = cosine(embeddings[i], embeddings[j])
            if distance < min_distance:
                min_distance = distance
                most_similar = (comments[i], comments[j])

    # Write the most similar pair to file
    with open(source_file_path, 'w') as f:
        f.write(most_similar[0] + '\n')
        f.write(most_similar[1] + '\n')

    return {"message": "Most similar comments found successfully."}

def A10_database(task_code):
    source_file_path = task_code['source_file_path']
    destination_file_path = task_code['destination_file_path']
    ticket_type = task_code['ticket_type']
    if not os.path.exists(destination_file_path):
        destination_file_path = os.path.join(os.path.dirname("/data"), "total-sales.txt")
    if not os.path.exists(source_file_path):
        raise HTTPException(status_code=500, detail="Source file not found.")
    # Connect to the SQLite database
    conn = sqlite3.connect(source_file_path)
    c = conn.cursor()

    # Query the total sales for the given ticket type
    c.execute("SELECT SUM(price) FROM sales WHERE ticket_type = ?", (ticket_type,))
    total_sales = c.fetchone()[0]

    # Write the total sales to the output file
    with open(destination_file_path, 'w') as f:
        f.write(str(total_sales))

    return {"message": "Total sales calculated successfully."}



def B12_donot_allow(task_code):
    file_path = task_code['file_path']
    if not file_path.startswith("/data"):
        raise HTTPException(status_code = 403, detail = "File Access Denied!!")
    else:
        raise HTTPException(status_code = 403, detail = "You can not delete any thing.")

def B3_download_file(task_code):
    url = task_code['url']
    destination_file_path = task_code['destination_file_path']
    if not destination_file_path.startswith("/data"):
        raise HTTPException(status_code = 403, detail = "File Access Denied!!")
    if not os.path.exists(destination_file_path):
        os.makedirs(os.path.dirname('/data'), "downloaded_file.txt") 
    try:
        r = requests.get(url)
        with open(destination_file_path, 'wb') as f:
            f.write(r.content)
        return {"message": "File downloaded successfully."}
    except Exception as e:
        return {"message": f"An error occurred: {e}"}

# def B4_clone_repo(task_code):
    # url = task_code['url']
    # destination_directory = task_code['destination_directory']
    # commit_message = task_code['commit_message']
    # if not destination_directory.startswith("/data"):
    #     raise HTTPException(status_code = 403, detail = "File Access Denied!!")
    # if not os.path.exists(destination_directory):
    #     destination_directory = os.makedirs(os.path.dirname('/data'), "cloned_repo") 

    # # Clone the repository
    # repo_url = url
    # local_path = destination_directory
    # repo = git.Repo.clone_from(repo_url, local_path)
    # print(f"Repository cloned to {local_path}")

    # # Make a change (for example, create a new file)
    # new_file_path = os.path.join(local_path, "new_file.txt")
    # with open(new_file_path, "w") as f:
    #     f.write("This is a new file")

    # # Add all changes to staging
    # repo.git.add(A=True)

    # # Commit the changes
    # commit_message = "Add new file"
    # repo.index.commit(commit_message)
    # print(f"Changes committed with message: {commit_message}")

    # # Push changes to the remote repository
    # origin = repo.remote(name='origin')
    # origin.push()
    # print("Changes pushed to remote repository")

    # return {"message": "Repository cloned and changes committed successfully."}
    
def B5_run_query(task_code):
    query = task_code['query']
    source_file_path = task_code['source_file_path']
    destination_file_path = task_code['destination_file_path']
    if not os.path.exists(destination_file_path):
        destination_file_path = os.path.join(os.path.dirname("/data"), "query-result.txt")
    if not os.path.exists(source_file_path):
        raise HTTPException(status_code=500, detail="Source file not found.")
    # Connect to the SQLite database
    conn = sqlite3.connect(source_file_path) 
    c = conn.cursor()

    # Run the query
    c.execute(query)
    result = c.fetchall()

    # Write the result to the output file
    with open(destination_file_path, 'w') as f:
        for row in result:
            f.write(str(row) + '\n')

    return {"message": "Query executed successfully."}

def B6_extract_data(task_code):
    url = task_code['url']
    destination_file_path = task_code['destination_file_path']
    if not destination_file_path.startswith("/data"):
        raise HTTPException(status_code = 403, detail = "File Access Denied!!")
    if not os.path.exists(destination_file_path):
        os.makedirs(os.path.dirname('/data'), "extracted_data.txt") 
    try:
        response = requests.get(url).text
        with open(destination_file_path, 'w') as f:
            f.write(response.text)
        return {"message": "Data extracted successfully."}
    except Exception as e:
        return {"message": f"An error occurred: {e}"}

def B7_compress_image(task_code):
    source_file_path = task_code['source_file_path']
    destination_file_path = task_code['destination_file_path']
    if not source_file_path.startswith("/data"):
        raise HTTPException(status_code = 403, detail = "File Access Denied!!")
    if not os.path.exists(destination_file_path):
        destination_file_path = os.path.join(os.path.dirname("/data"), "compressed_image.jpg")
    if not os.path.exists(source_file_path):
        raise HTTPException(status_code=500, detail="Source file not found.")
    # Load the image
    image = Image.open(source_file_path)

    # Compress the image
    image.save(destination_file_path, quality=50)

    return {"message": "Image compressed successfully."}

def B8_transcribe_audio(task_code):
    source_file_path = task_code['source_file_path']
    destination_file_path = task_code['destination_file_path']
    if not source_file_path.startswith("/data"):
        raise HTTPException(status_code = 403, detail = "File Access Denied!!")
    if not os.path.exists(destination_file_path):
        destination_file_path = os.path.join(os.path.dirname("/data"), "transcription.txt")
    if not os.path.exists(source_file_path):
        raise HTTPException(status_code=500, detail="Source file not found.")
    # Convert mp3 to wav
    audio = AudioSegment.from_file(source_file_path)
    wav_path = "temp.wav"
    audio.export(wav_path, format="wav")

    # Initialize recognizer
    recognizer = sr.Recognizer()

    # Transcribe audio file
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            print("Transcription: " + text)
        except sr.UnknownValueError:
            print("Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Speech Recognition service; {0}".format(e))

    # Write the transcription to the output file
    with open(destination_file_path, 'w') as file:
        file.write(text)

    # Remove temporary wav file
    os.remove(wav_path)

    return {"message": "Audio transcribed successfully."}

def B9_markdown_to_html(task_code):
    source_file_path = task_code['source_file_path']
    destination_file_path = task_code['destination_file_path']
    if not source_file_path.startswith("/data"):
        raise HTTPException(status_code = 403, detail = "File Access Denied!!")
    if not os.path.exists(destination_file_path):
        destination_file_path = os.path.join(os.path.dirname("/data"), "converted.html")
    if not os.path.exists(source_file_path):
        raise HTTPException(status_code=500, detail="Source file not found.")
    # Convert the markdown file to HTML
    with open(source_file_path, 'r') as file:
        html = markdown.markdown(file.read())
    with open(destination_file_path, 'w') as file:
        file.write(html)

    return {"message": "Markdown file converted to HTML successfully."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run (app, host="0.0.0.0", port=8000)