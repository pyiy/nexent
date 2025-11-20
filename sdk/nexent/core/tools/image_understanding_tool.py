import json
import logging
from io import BytesIO

from jinja2 import Template
from pydantic import Field
from smolagents.tools import Tool

from ..models.openai_vlm import OpenAIVLModel
from ..utils.observer import MessageObserver, ProcessType
from ..utils.tools_common_message import ToolCategory, ToolSign
from ... import MinIOStorageClient
from ...multi_modal.load_save_object import LoadSaveObjectManager

logger = logging.getLogger("image_understanding_tool")


class ImageUnderstandingTool(Tool):
    """Tool for extracting text from images stored in S3-compatible storage."""

    name = "image_understanding"
    description = (
        "Understand an image stored in S3-compatible storage or HTTP and return the text content inside the image. "
        "Provide the object location via an s3:// URL or http:// URL or https:// URL."
    )
    inputs = {
        "image_url": {
            "type": "string",
            "description": "URL of the image to analyze (e.g., 's3://bucket/path/to/image.png',"
                           "'http://image.png', 'https://image.png')."
        },
        "query": {
            "type": "string",
            "description": "The user query to perform."
        }
    }
    output_type = "string"
    # todo
    category = ToolCategory.FILE.value
    tool_sign = ToolSign.FILE_OPERATION.value

    def __init__(
            self,
            observer: MessageObserver = Field(description="Message observer", default=None, exclude=True),
            vlm_model: OpenAIVLModel = Field(description="The VLM model to use", default=None, exclude=True),
            storage_client: MinIOStorageClient = Field(description="Storage client to use", default=None, exclude=True),
            # todo 这么写对不对
            system_prompt_template: Template = Field(description="System prompt template to use", default=None, exclude=True),
    ):
        super().__init__()
        self.observer = observer
        self.vlm_model = vlm_model
        # Use provided storage_client or create a default one
        # if storage_client is None:
        #     storage_client = create_storage_client_from_config()
        self.storage_client = storage_client
        self.system_prompt_template = system_prompt_template


        # Create LoadSaveObjectManager with the storage client
        self.mm = LoadSaveObjectManager(storage_client=self.storage_client)

        # Dynamically apply the load_object decorator to forward method
        self.forward = self.mm.load_object(input_names=["image_url"])(self._forward_impl)

        self.running_prompt_zh = "正在分析图片文字..."
        self.running_prompt_en = "Analyzing image text..."

    def _forward_impl(self, image_url: bytes, query: str) -> str:
        """
        Analyze the image specified by the S3 URL and return recognized text.
        
        Note: This method is wrapped by load_object decorator which downloads
        the image from S3 URL and passes bytes to this method.

        Args:
            image_url: Image bytes (converted from S3 URL by decorator).

        Returns:
            JSON string containing the recognized text.

        Raises:
            Exception: If the image cannot be downloaded or analyzed.
        """
        # Note: image_url is now bytes after decorator processing
        image_stream = BytesIO(image_url)

        # Send tool run message
        if self.observer:
            running_prompt = self.running_prompt_zh if self.observer.lang == "zh" else self.running_prompt_en
            self.observer.add_message("", ProcessType.TOOL, running_prompt)
            card_content = [{"icon": "image", "text": "Processing image..."}]
            self.observer.add_message("", ProcessType.CARD, json.dumps(card_content, ensure_ascii=False))

        # # Load messages based on language
        # messages = get_file_processing_messages_template(language)

        try:
            text = self.vlm_model.analyze_image(
                image_input=image_stream,
                system_prompt=self.system_prompt_template.render({'query': query})).content
            return text
            # return messages["IMAGE_CONTENT_SUCCESS"].format(filename=filename, content=text)
        except Exception as e:
            raise e

