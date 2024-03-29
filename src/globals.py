import os
import sys

import supervisely as sly
from supervisely.app.v1.app_service import AppService

app_root_directory = os.path.dirname(os.getcwd())
sys.path.append(app_root_directory)
sys.path.append(os.path.join(app_root_directory, "src"))
print(f"App root directory: {app_root_directory}")
sly.logger.info(f'PYTHONPATH={os.environ.get("PYTHONPATH", "")}')

# order matters
# from dotenv import load_dotenv
# load_dotenv(os.path.join(app_root_directory, "unpack-key-value-tags", "secret_debug.env"))
# load_dotenv(os.path.join(app_root_directory, "unpack-key-value-tags", "debug.env"))

my_app = AppService()
api = sly.Api.from_env()

TASK_ID = int(os.environ["TASK_ID"])
TEAM_ID = int(os.environ["context.teamId"])
WORKSPACE_ID = int(os.environ["context.workspaceId"])
PROJECT_ID = int(os.environ["modal.state.slyProjectId"])

SELECTED_TAGS = [i.strip() for i in os.environ["modal.state.tags"][1:-1].replace('"',"").replace("'", "").split(',')]
if not SELECTED_TAGS:
    message = "Please select at least 1 tag"
    sly.logger.error(msg=message)
    raise Exception(message)

KEEP_TAGS = os.environ["modal.state.keepTags"]
INPUT_PROJECT_NAME = str(os.environ["modal.state.inputProjectName"])

unpacked_tags_names = []
