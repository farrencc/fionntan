"""
Mock Podcast Generator for Testing

Provides a mock implementation of the podcast generator for testing without
requiring actual API access to Google's Gemini.
"""

import json
import logging
from typing import List, Dict, Any, Optional
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mock_podcast_generator")


class MockPodcastGenerator:
    """Mock implementation of the podcast generator for testing."""
    
    def __init__(self, project_id=None, **kwargs):
        """Initialize the mock generator."""
        logger.info("Initializing mock podcast generator")
        self.project_id = project_id or "mock-project"
    
    def generate_podcast_script(self, papers, config=None):
        """
        Generate a mock podcast script.
        
        Args:
            papers: List of paper dictionaries
            config: Optional configuration
            
        Returns:
            Mock podcast script
        """
        logger.info(f"Generating mock podcast script for {len(papers)} papers")
        
        # Create a mock script
        script = {
            "title": config.episode_title if config else "Mock Podcast Episode",
            "sections": [
                {
                    "title": "INTRODUCTION",
                    "segments": [
                        {
                            "speaker": "alex",
                            "text": "Welcome to our research podcast! Today we'll be discussing some fascinating papers."
                        },
                        {
                            "speaker": "jordan",
                            "text": "That's right, Alex. We've got some interesting research to cover."
                        }
                    ]
                }
            ]
        }
        
        # Add a section for each paper
        for i, paper in enumerate(papers):
            paper_section = {
                "title": f"PAPER {i+1}: {paper.get('title', 'Untitled Paper')}",
                "segments": [
                    {
                        "speaker": "alex" if i % 2 == 0 else "jordan",
                        "text": f"Let's talk about this paper titled '{paper.get('title')}' by {paper.get('authors', ['Unknown'])[0]}."
                    },
                    {
                        "speaker": "jordan" if i % 2 == 0 else "alex",
                        "text": f"This research focuses on {paper.get('abstract', 'unknown topic')[:100]}..."
                    }
                ]
            }
            script["sections"].append(paper_section)
        
        # Add a conclusion
        script["sections"].append({
            "title": "CONCLUSION",
            "segments": [
                {
                    "speaker": "alex",
                    "text": "That wraps up our discussion for today!"
                },
                {
                    "speaker": "jordan",
                    "text": "Thanks for listening, and join us next time for more research insights."
                }
            ]
        })
        
        return script


# Mock config class for testing
class MockPodcastConfig:
    """Mock configuration class."""
    
    def __init__(self, **kwargs):
        """Initialize with provided values."""
        self.episode_title = kwargs.get("episode_title", "Mock Episode")
        self.technical_level = kwargs.get("technical_level", "intermediate")
        self.target_length_minutes = kwargs.get("target_length_minutes", 15)
