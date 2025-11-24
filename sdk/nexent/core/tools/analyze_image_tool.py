import json
import logging
from io import BytesIO

from jinja2 import Template, StrictUndefined
from pydantic import Field
from smolagents.tools import Tool

from ..models.openai_vlm import OpenAIVLModel
from ..utils.observer import MessageObserver, ProcessType
from ..utils.prompt_template_utils import get_prompt_template
from ..utils.tools_common_message import ToolCategory, ToolSign
from ... import MinIOStorageClient
from ...multi_modal.load_save_object import LoadSaveObjectManager

logger = logging.getLogger("analyze_image_tool")


class AnalyzeImageTool(Tool):
    """Tool for understanding and analyzing image"""

    name = "analyze_image"
    description = (
        "This tool uses a visual language model to understand images based on your query and then returns a description of the image."
        "It's used to understand and analyze images stored in S3 buckets, via HTTP and HTTPS."
        "Use this tool when you want to retrieve information contained in an image and provide the image's URL and your query."
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
    ):
        super().__init__()
        self.observer = observer
        self.vlm_model = vlm_model
        self.storage_client = storage_client
        # Create LoadSaveObjectManager with the storage client
        self.mm = LoadSaveObjectManager(storage_client=self.storage_client)

        # Dynamically apply the load_object decorator to forward method
        self.forward = self.mm.load_object(input_names=["image_url"])(self._forward_impl)

        self.running_prompt_zh = "正在分析图片..."
        self.running_prompt_en = "Analyzing image..."

    def _forward_impl(self, image_url: bytes, query: str) -> str:
        """
        Analyze images of S3 URL, HTTP URL, or HTTPS URL and return the identified text.
        
        Note: This method is wrapped by load_object decorator which downloads
        the image from S3 URL, HTTP URL, or HTTPS URL and passes bytes to this method.

        Args:
            image_url: Image bytes (converted from S3 URL, HTTP URL, or HTTPS URL by decorator).

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
            card_content = [{"icon": "image", "text": "Analyzing image..."}]
            self.observer.add_message("", ProcessType.CARD, json.dumps(card_content, ensure_ascii=False))

        # Load prompts from yaml file
        prompts = get_prompt_template(template_type='analyze_image', language=self.observer.lang)

        try:

            response = self.vlm_model.analyze_image(
                image_input=image_stream,
                system_prompt=Template(prompts['system_prompt'], undefined=StrictUndefined).render({'query': query}))
        except Exception as e:
            raise Exception(f"Error understanding image: {str(e)}")
        text = response.content
        # Record the detailed content of this search
        # todo 返回的结构体是什么？
        search_results_data = {'text': text}
        return json.dumps(search_results_data, ensure_ascii=False)
