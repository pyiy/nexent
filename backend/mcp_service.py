import logging

from tool_collection.mcp.blur_image_tool import local_blur_image
from tool_collection.mcp.get_image_by_s3_url_tool import local_get_image_by_s3_url_tool
from utils.logging_utils import configure_logging
from fastmcp import FastMCP
from tool_collection.mcp.local_mcp_service import local_mcp_service

"""
hierarchical proxy architecture:
- local service layer: stable local mount service
- remote proxy layer: dynamic managed remote mcp service proxy
"""

configure_logging(logging.INFO)
logger = logging.getLogger("mcp_service")

# initialize main mcp service
nexent_mcp = FastMCP(name="nexent_mcp")

# mount local service (stable, not affected by remote proxy)
nexent_mcp.mount(local_mcp_service.name, local_mcp_service)
nexent_mcp.mount(local_blur_image.name, local_blur_image)
nexent_mcp.mount(local_get_image_by_s3_url_tool.name, local_get_image_by_s3_url_tool)

if __name__ == "__main__":
    nexent_mcp.run(transport="sse", host="0.0.0.0", port=5011)
