import base64
import mimetypes
from pathlib import Path
from tkinter import TclError, Tk, filedialog
from langchain.messages import HumanMessage, SystemMessage
from langchain.agents import create_agent
from dotenv import load_dotenv
from prompt import SYSTEM_CHEF_PROMPT, CHEF_PROMPT

from langchain.tools import tool
from tavily import TavilyClient
from typing import Dict, Any
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

load_dotenv()
tavily_client = TavilyClient()

@tool
def recipe_search(query: str) -> Dict[str, Any]:
    """Tool for searching the web for information"""
    logging.info(f"searching for {query}")
    recipe = tavily_client.search(query)
    return recipe
def choose_image_file() -> Path:
    """Open a local file picker when no image path is passed on the command line."""
    root = None
    try:
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        filename = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.webp"),
                ("All files", "*.*"),
            ],
        )
    except TclError:
        filename = input("Image path: ").strip().strip('"').strip("'")
    finally:
        if root is not None:
            root.destroy()

    if not filename:
        raise SystemExit("No image selected.")

    return Path(filename).expanduser()

def image_to_data_url(image_path: Path) -> str:
    image_path = image_path.expanduser().resolve()

    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    mime_type, _ = mimetypes.guess_type(str(image_path))
    if not mime_type or not mime_type.startswith("image/"):
        raise ValueError(f"Not an image file: {image_path}")

    image_b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{image_b64}"

def build_image_message(image_path: Path, prompt) -> HumanMessage:
    return HumanMessage(
        content=[
            {"type": "text", "text": "prompt"},
            {"type": "image_url", "image_url": {"url": image_to_data_url(image_path)}},
        ]
    )

logging.info("creating our agent...")
agent = create_agent(model="gpt-5-nano",
                    tools=[recipe_search],
                    system_prompt=SYSTEM_CHEF_PROMPT)
image_path = choose_image_file()
message = build_image_message(image_path, CHEF_PROMPT)
response = agent.invoke(
    {
        "messages": [message],
    },
 )

ingredients = response["messages"][-1].content
print(ingredients)


# response = agent.invoke(
#     {"messages" : [HumanMessage(content="I want the recipe to use the ingredients " + ingredients + " and make it spicy"),
#                    SystemMessage(content="Please use less than five ingredients")],
#                     },
# )
# print("this is the AI last response")
# print(response["messages"][-1].content)



