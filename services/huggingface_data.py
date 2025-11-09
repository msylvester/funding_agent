"""
Service for fetching and processing Hugging Face model data
"""

import os
import requests
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class HuggingFaceDataService:
    """Service for managing Hugging Face model data"""

    def __init__(self, hf_token: str = None):
        self.hf_api_base = "https://huggingface.co/api"
        self.hf_token = hf_token or os.getenv('HF_TOKEN')

        # Set up headers with authentication if token is available
        self.headers = {}
        if self.hf_token:
            self.headers['Authorization'] = f'Bearer {self.hf_token}'
            logger.info("Hugging Face token configured - using authenticated requests")
        else:
            logger.info("No Hugging Face token found - using unauthenticated requests")

    def get_trending_models(self, limit: int = 20, filter_param: str = None) -> List[Dict[str, Any]]:
        """
        Fetch trending models from Hugging Face

        Args:
            limit: Maximum number of models to return
            filter_param: Filter by task type (e.g., 'text-generation', 'image-classification')

        Returns:
            List of model data
        """
        try:
            # Hugging Face API endpoint for models
            url = f"{self.hf_api_base}/models"

            params = {
                "sort": "trending",
                "direction": -1,
                "limit": limit
            }

            if filter_param:
                params["filter"] = filter_param

            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            models = []

            for model in data:
                model_data = {
                    "full_name": model.get("id", model.get("modelId", "Unknown")),
                    "name": model.get("id", model.get("modelId", "Unknown")).split("/")[-1] if "/" in model.get("id", "") else model.get("id", "Unknown"),
                    "author": model.get("author", "Unknown"),
                    "downloads": model.get("downloads", 0),
                    "likes": model.get("likes", 0),
                    "url": f"https://huggingface.co/{model.get('id', model.get('modelId', ''))}",
                    "tags": model.get("tags", []),
                    "pipeline_tag": model.get("pipeline_tag", None),
                    "created_at": model.get("createdAt", None),
                    "last_modified": model.get("lastModified", None),
                    "private": model.get("private", False),
                    "gated": model.get("gated", False)
                }
                models.append(model_data)

            logger.info(f"Retrieved {len(models)} trending models from Hugging Face")
            return models

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching trending models: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []

    def get_model_details(self, model_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model

        Args:
            model_id: Model ID (e.g., "username/model-name")

        Returns:
            Model details
        """
        try:
            url = f"{self.hf_api_base}/models/{model_id}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            model = response.json()

            details = {
                "full_name": model.get("id", model.get("modelId", "Unknown")),
                "name": model.get("id", "Unknown").split("/")[-1] if "/" in model.get("id", "") else model.get("id", "Unknown"),
                "author": model.get("author", "Unknown"),
                "downloads": model.get("downloads", 0),
                "likes": model.get("likes", 0),
                "url": f"https://huggingface.co/{model.get('id', '')}",
                "tags": model.get("tags", []),
                "pipeline_tag": model.get("pipeline_tag", None),
                "created_at": model.get("createdAt", None),
                "last_modified": model.get("lastModified", None),
                "private": model.get("private", False),
                "gated": model.get("gated", False),
                "library_name": model.get("library_name", None),
                "datasets": model.get("datasets", []),
                "siblings": model.get("siblings", [])
            }

            logger.info(f"Retrieved details for model {model_id}")
            return details

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching model details for {model_id}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error getting model details: {e}")
            return {}

    def search_models(self, query: str, limit: int = 30, filter_param: str = None) -> List[Dict[str, Any]]:
        """
        Search models by query

        Args:
            query: Search query
            limit: Maximum number of results
            filter_param: Filter by task type

        Returns:
            List of matching models
        """
        try:
            url = f"{self.hf_api_base}/models"

            params = {
                "search": query,
                "sort": "downloads",
                "direction": -1,
                "limit": limit
            }

            if filter_param:
                params["filter"] = filter_param

            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            models = []

            for model in data:
                model_data = {
                    "full_name": model.get("id", model.get("modelId", "Unknown")),
                    "name": model.get("id", "Unknown").split("/")[-1] if "/" in model.get("id", "") else model.get("id", "Unknown"),
                    "author": model.get("author", "Unknown"),
                    "downloads": model.get("downloads", 0),
                    "likes": model.get("likes", 0),
                    "url": f"https://huggingface.co/{model.get('id', '')}",
                    "tags": model.get("tags", []),
                    "pipeline_tag": model.get("pipeline_tag", None),
                    "created_at": model.get("createdAt", None),
                    "last_modified": model.get("lastModified", None)
                }
                models.append(model_data)

            logger.info(f"Found {len(models)} models for query: {query}")
            return models

        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching models: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching models: {e}")
            return []


if __name__ == "__main__":
    # Test the service
    import logging
    logging.basicConfig(level=logging.INFO)

    service = HuggingFaceDataService()
    print("Fetching trending models...")
    models = service.get_trending_models(limit=10)

    print(f"\nFound {len(models)} trending models:")
    for i, model in enumerate(models, 1):
        print(f"{i}. {model['full_name']}")
        print(f"   Downloads: {model['downloads']:,}, Likes: {model['likes']:,}")
        print(f"   Type: {model['pipeline_tag'] or 'N/A'}")
        print(f"   URL: {model['url']}\n")
