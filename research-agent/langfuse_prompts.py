"""Load all system prompts from Langfuse Prompt Management.

Every agent prompt is stored in Langfuse with label "production".
This module provides a single function to fetch and compile them.

Prompt names in Langfuse:
  - supervisor-prompt  (template var: {{max_revisions}})
  - planner-prompt     (no template vars)
  - researcher-prompt  (no template vars)
  - critic-prompt      (template var: {{current_date}})
"""

import logging

from langfuse import Langfuse

logger = logging.getLogger("langfuse_prompts")

_langfuse = Langfuse()


def get_system_prompt(name: str, **variables: str) -> str:
    """Fetch a prompt from Langfuse and compile with template variables.

    Args:
        name: Prompt name in Langfuse (e.g. "supervisor-prompt").
        **variables: Template variables to substitute (e.g. max_revisions="2").

    Returns:
        Compiled prompt string.
    """
    prompt = _langfuse.get_prompt(name, label="production")
    compiled = prompt.compile(**variables)
    logger.info("Loaded prompt '%s' from Langfuse (version %s)", name, prompt.version)
    return compiled
