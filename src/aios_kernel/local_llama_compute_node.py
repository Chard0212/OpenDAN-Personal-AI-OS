
import logging
import requests
from typing import Optional
from pydantic import BaseModel

from .compute_task import ComputeTask, ComputeTaskState, ComputeTaskType
from .queue_compute_node import Queue_ComputeNode

logger = logging.getLogger(__name__)

"""
This is a custom implementation, it should be redesigned.
"""

class LocalLlama_ComputeNode(Queue_ComputeNode):
    async def execute_task(self, task: ComputeTask) -> {
        "content": str,
        "message": str,
        "state": ComputeTaskState,
        "error": {
            "code": int,
            "message": str,
        }
    }:
        class GenerateResponse(BaseModel):
            error: Optional[int]
            msg: Optional[str]
            results: Optional[str]

        try:    
            body = {
                "prompts": task.params["prompts"]
            }
            
            response = requests.post("http://aigc:7880/generate", data = body, verify=False)
            response.close()

            logger.info(f"LocalLlama_ComputeNode task responsed, request: {body}, status-code: {response.status_code}, headers: {response.headers}, content: {response.content}")

            if response.status_code != 200:
                return {
                    "state": ComputeTaskState.ERROR,
                    "error": {
                        "code": response.status_code,
                        "message": "http request failed: " + response.status_code
                    }
                }
            else:
                resp = GenerateResponse.parse_raw(response.content.decode("utf-8"))
                if resp.error:
                    return {
                        "state": ComputeTaskState.ERROR,
                        "error": {
                            "code": resp.error,
                            "message": "local llama failed:" + resp.msg
                        }
                    }
                else:
                    return {
                        "content": str(resp.results),
                        "message": {}
                    }
        except Exception as err:
            import traceback
            logger.error(f"{traceback.format_exc()}, error: {err}")
            
            return {
                "state": ComputeTaskState.ERROR,
                "error": {
                    "code": -1,
                    "message": "unknown exception: " + str(err)
                }
            }

    def display(self) -> str:
        return f"LocalLlama_ComputeNode: {self.node_id}"

    def get_capacity(self):
        pass

    def is_support(self, task: ComputeTask) -> bool:
        return task.task_type == ComputeTaskType.LLM_COMPLETION and (not task.params["model_name"] or task.params["model_name"] == "llama")

    def is_local(self) -> bool:
        return True
