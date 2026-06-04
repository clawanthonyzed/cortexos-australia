"""Workflow templates."""
from app.workflows.templates.product_launch import get_product_launch_template
from app.workflows.templates.content_pipeline import get_content_pipeline_template

__all__ = ["get_product_launch_template", "get_content_pipeline_template"]
