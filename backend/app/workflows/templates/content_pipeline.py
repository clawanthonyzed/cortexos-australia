"""Content Pipeline workflow template: brief → research → write → publish."""
from __future__ import annotations

from typing import Any


def get_content_pipeline_template(
    research_agent_id: str | None = None,
    seo_agent_id: str | None = None,
    content_agent_id: str | None = None,
) -> dict[str, Any]:
    """
    Returns a React Flow-compatible graph_json for a content creation pipeline.

    Nodes: topic_research → keyword_research → content_writing
    """
    return {
        "nodes": [
            {"id": "start", "type": "start", "data": {}},
            {
                "id": "topic_research",
                "type": "agent_node",
                "data": {
                    "agent_id": research_agent_id,
                    "agent_type": "research",
                    "task_template": (
                        "Research the topic: {content_topic}. "
                        "Find key angles, statistics, and competitor content. "
                        "Target audience: {target_audience}"
                    ),
                },
            },
            {
                "id": "keyword_research",
                "type": "agent_node",
                "data": {
                    "agent_id": seo_agent_id,
                    "agent_type": "seo",
                    "task_template": (
                        "Find the best keywords for: {content_topic}. "
                        "Research context: {topic_research_output}"
                    ),
                },
            },
            {
                "id": "content_writing",
                "type": "agent_node",
                "data": {
                    "agent_id": content_agent_id,
                    "agent_type": "content",
                    "task_template": (
                        "Write a comprehensive {content_type} about: {content_topic}. "
                        "Research: {topic_research_output}\n"
                        "Target keywords: {keyword_research_output}\n"
                        "Tone: {tone}\n"
                        "Word count: {word_count}"
                    ),
                },
            },
            {"id": "end", "type": "end", "data": {}},
        ],
        "edges": [
            {"id": "e1", "source": "start", "target": "topic_research"},
            {"id": "e2", "source": "topic_research", "target": "keyword_research"},
            {"id": "e3", "source": "keyword_research", "target": "content_writing"},
            {"id": "e4", "source": "content_writing", "target": "end"},
        ],
    }
