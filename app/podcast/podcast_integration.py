"""
Podcast Integration Module

Integrates the arXiv scraper with the Gemini podcast generator to create
full podcast scripts based on user research preferences. Acts as the primary
interface for the application.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

# Import the arXiv scraper module and Gemini podcast generator
from arxiv_scraper import ArXivScraper, UserPreferences
from gemini_podcast_generator import GeminiPodcastGenerator, PodcastConfig
from config import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("podcast_integration")


class PodcastIntegrationError(Exception):
    """Custom exception for podcast integration errors."""
    pass


class PodcastCreator:
    """
    Integrates arXiv paper scraping with Gemini podcast script generation.
    Provides methods to generate podcast scripts based on user preferences.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the podcast creator.
        
        Args:
            config_path: Optional path to a configuration file
        """
        self.config_manager = ConfigManager(config_path)
        self.gemini_config = self.config_manager.get_gemini_config()
        
        # Initialize Gemini podcast generator
        self.podcast_generator = GeminiPodcastGenerator(
            project_id=self.gemini_config.project_id,
            location=self.gemini_config.location,
            model_name=self.gemini_config.model_name,
            service_account_path=self.gemini_config.service_account_path,
            temperature=self.gemini_config.temperature
        )
        
        logger.info("Podcast creator initialized successfully")
    
    def generate_from_user_preferences(
        self,
        user_preferences: Dict[str, Any],
        podcast_title: Optional[str] = None,
        technical_level: str = "intermediate",
        target_length: int = 15
    ) -> Dict[str, Any]:
        """
        Generate a podcast script based on user research preferences.
        
        Args:
            user_preferences: User research preferences dictionary
            podcast_title: Optional custom title for the podcast
            technical_level: Technical level of the podcast (beginner, intermediate, advanced)
            target_length: Target length of the podcast in minutes
            
        Returns:
            Dictionary containing the podcast script
        """
        try:
            # Convert user preferences to ArXiv UserPreferences object
            arxiv_prefs = UserPreferences(
                topics=user_preferences.get("topics", []),
                categories=user_preferences.get("categories", []),
                authors=user_preferences.get("authors", []),
                max_results=user_preferences.get("max_results", 50),
                days_back=user_preferences.get("days_back", 30),
                sort_by=user_preferences.get("sort_by", "relevance")
            )
            
            # Limit the number of papers for podcast generation
            max_papers = 5
            if arxiv_prefs.max_results > max_papers:
                logger.info(f"Limiting max_results from {arxiv_prefs.max_results} to {max_papers} for podcast generation")
                arxiv_prefs.max_results = max_papers
            
            # Create arXiv scraper
            scraper = ArXivScraper(arxiv_prefs)
            
            # Fetch papers based on preferences
            papers = scraper.search_papers()
            
            if not papers:
                logger.warning("No papers found matching the given preferences")
                return {
                    "success": False,
                    "error": "No papers found matching the given preferences",
                    "script": None
                }
            
            # Create podcast configuration
            podcast_config = PodcastConfig(
                episode_title=podcast_title or f"Research Frontiers: {', '.join(arxiv_prefs.topics[:3])}",
                technical_level=technical_level,
                target_length_minutes=target_length
            )
            
            # Generate podcast script
            script = self.podcast_generator.generate_podcast_script(papers, podcast_config)
            
            # Add metadata to the response
            response = {
                "success": True,
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "paper_count": len(papers),
                    "topics": arxiv_prefs.topics,
                    "categories": arxiv_prefs.categories,
                    "paper_ids": [paper.get("id") for paper in papers]
                },
                "script": script
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating podcast: {e}")
            raise PodcastIntegrationError(f"Failed to generate podcast: {e}")
    
    def generate_from_paper_ids(
        self,
        paper_ids: List[str],
        podcast_title: Optional[str] = None,
        technical_level: str = "intermediate",
        target_length: int = 15
    ) -> Dict[str, Any]:
        """
        Generate a podcast script based on specific arXiv paper IDs.
        
        Args:
            paper_ids: List of arXiv paper IDs
            podcast_title: Optional custom title for the podcast
            technical_level: Technical level of the podcast
            target_length: Target length of the podcast in minutes
            
        Returns:
            Dictionary containing the podcast script
        """
        try:
            if not paper_ids:
                raise ValueError("No paper IDs provided")
            
            # Limit the number of papers
            if len(paper_ids) > 5:
                logger.info(f"Limiting number of papers from {len(paper_ids)} to 5")
                paper_ids = paper_ids[:5]
            
            # Create a minimal preferences object for each paper ID
            papers = []
            for paper_id in paper_ids:
                # Create an arXiv scraper with minimal preferences
                prefs = UserPreferences(
                    topics=[""],  # Empty topic to avoid filtering
                    max_results=1
                )
                scraper = ArXivScraper(prefs)
                
                # Build a query specific to this paper ID
                query = f"id:{paper_id}"
                search = scraper._build_search_query()
                
                # Override the search query with the paper ID specific query
                search = query
                
                # Use the search method but with our custom query
                paper_results = scraper.search_papers()
                
                if paper_results:
                    papers.extend(paper_results)
            
            if not papers:
                return {
                    "success": False,
                    "error": "Could not retrieve the specified papers",
                    "script": None
                }
            
            # Create podcast configuration
            podcast_config = PodcastConfig(
                episode_title=podcast_title or "Research Paper Discussion",
                technical_level=technical_level,
                target_length_minutes=target_length
            )
            
            # Generate podcast script
            script = self.podcast_generator.generate_podcast_script(papers, podcast_config)
            
            # Add metadata to the response
            response = {
                "success": True,
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "paper_count": len(papers),
                    "paper_ids": [paper.get("id") for paper in papers]
                },
                "script": script
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating podcast from paper IDs: {e}")
            raise PodcastIntegrationError(f"Failed to generate podcast from paper IDs: {e}")
    
    def save_script(self, script: Dict[str, Any], output_path: str) -> str:
        """
        Save the generated script to a file.
        
        Args:
            script: Script dictionary from generator
            output_path: Path to save the script
            
        Returns:
            Absolute path to the saved file
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Write script to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(script, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved script to {output_path}")
            return os.path.abspath(output_path)
            
        except Exception as e:
            logger.error(f"Error saving script to {output_path}: {e}")
            raise PodcastIntegrationError(f"Failed to save script: {e}")
    
    def generate_text_script(self, script_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable text script from the script data.
        
        Args:
            script_data: Script dictionary from generator
            
        Returns:
            Formatted text script
        """
        if not script_data or "script" not in script_data:
            raise ValueError("Invalid script data provided")
        
        script = script_data["script"]
        text_script = []
        
        # Add title
        text_script.append(f"# {script['title']}")
        text_script.append("")
        
        # Add metadata if available
        if "metadata" in script_data:
            text_script.append("## Metadata")
            text_script.append(f"Generated: {script_data['metadata'].get('generated_at', 'Unknown')}")
            text_script.append(f"Papers: {script_data['metadata'].get('paper_count', 0)}")
            text_script.append("")
        
        # Add sections
        for section in script.get("sections", []):
            text_script.append(f"## {section['title']}")
            text_script.append("")
            
            for segment in section.get("segments", []):
                speaker = segment["speaker"].upper()
                text = segment["text"]
                text_script.append(f"{speaker}: {text}")
                text_script.append("")
        
        return "\n".join(text_script)


def main():
    """Example usage of the PodcastCreator."""
    # Example user preferences
    user_preferences = {
        "topics": ["transformer models", "attention mechanisms"],
        "categories": ["cs.CL", "cs.AI"],
        "authors": ["Yoshua Bengio", "Geoffrey Hinton"],
        "max_results": 3,
        "days_back": 90,
        "sort_by": "relevance"
    }
    
    try:
        # Initialize podcast creator
        # In a real environment, you would use actual credentials
        creator = PodcastCreator()
        
        # Generate podcast script
        result = creator.generate_from_user_preferences(
            user_preferences,
            podcast_title="Recent Advances in Transformer Models",
            technical_level="intermediate",
            target_length=10
        )
        
        if result["success"]:
            # Save script to file
            creator.save_script(result, "podcast_script.json")
            
            # Generate text script
            text_script = creator.generate_text_script(result)
            print(text_script)
        else:
            print(f"Error: {result.get('error')}")
        
    except Exception as e:
        logger.error(f"Error in podcast creation: {e}")


if __name__ == "__main__":
    # This would run the example in a real environment
    # main()
    pass