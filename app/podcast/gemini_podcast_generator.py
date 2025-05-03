"""
Gemini Podcast Script Generator

This module generates conversational podcast scripts from arXiv papers using
Google's Gemini 1.5 Pro model. It creates engaging two-host dialogues that
discuss research concepts in an accessible and entertaining way.

Features:
- Authenticates with Google Vertex AI to access Gemini 1.5 Pro
- Processes arXiv paper data to optimize for prompt input
- Creates conversational scripts with distinct host personalities
- Identifies connections between papers for cohesive discussion
- Implements retry logic for API failures
- Formats output for audio generation
"""

import os
import time
import json
import logging
import random
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re
from datetime import datetime, timedelta
import base64

# Google libraries for Vertex AI
import google.auth
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Content, Part
from vertexai.generative_models._generative_models import (
    HarmCategory, HarmBlockThreshold
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("gemini_podcast_generator")

# Host personality profiles
HOST_PROFILES = {
    "alex": {
        "name": "Alex",
        "traits": "enthusiastic, curious, fond of analogies, asks probing questions",
        "background": "background in computer science with interests in AI and cognitive science",
        "speech_style": "energetic, uses accessible language to explain complex concepts"
    },
    "jordan": {
        "name": "Jordan",
        "traits": "analytical, thoughtful, good at synthesizing information, occasionally witty",
        "background": "background in physics with broad knowledge across scientific disciplines",
        "speech_style": "measured pace, builds on concepts methodically, occasional dry humor"
    }
}

@dataclass
class PodcastConfig:
    """Configuration for podcast script generation."""
    episode_title: str = "Latest Research Insights"
    intro_length: str = "brief"  # brief, moderate, detailed
    paper_discussion_style: str = "conversational"  # conversational, educational, debate
    technical_level: str = "intermediate"  # beginner, intermediate, advanced
    include_humor: bool = True
    include_analogies: bool = True
    target_length_minutes: int = 15
    conclusion_type: str = "summary"  # summary, questions, future-implications
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for API requests."""
        return {
            "episode_title": self.episode_title,
            "intro_length": self.intro_length,
            "paper_discussion_style": self.paper_discussion_style,
            "technical_level": self.technical_level,
            "include_humor": self.include_humor,
            "include_analogies": self.include_analogies,
            "target_length_minutes": self.target_length_minutes,
            "conclusion_type": self.conclusion_type
        }


class GeminiPodcastGenerator:
    """
    Podcast script generator using Google's Gemini 1.5 Pro model.
    Handles authentication, paper preprocessing, script generation, 
    and error handling.
    """
    
    # Constants for Gemini API
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 2  # Exponential backoff base (seconds)
    MAX_INPUT_TOKENS = 30000  # Approximate max tokens for Gemini 1.5 Pro
    
    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "gemini-1.5-pro",
        service_account_path: Optional[str] = None,
        temperature: float = 0.7
    ):
        """
        Initialize the podcast generator.
        
        Args:
            project_id: Google Cloud project ID
            location: Model location in Google Cloud
            model_name: Gemini model name
            service_account_path: Path to service account JSON file
            temperature: Temperature for text generation (0.0-1.0)
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.service_account_path = service_account_path
        self.temperature = temperature
        self.gemini_model = None
        
        # Initialize model
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Initialize Vertex AI and load the Gemini model."""
        try:
            # Authentication using service account or default credentials
            if self.service_account_path and os.path.exists(self.service_account_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_path,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
            else:
                credentials, _ = google.auth.default()
            
            # Initialize Vertex AI
            vertexai.init(
                project=self.project_id,
                location=self.location,
                credentials=credentials
            )
            
            # Load the model
            self.gemini_model = GenerativeModel(self.model_name)
            logger.info(f"Successfully initialized Gemini model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Gemini model: {e}")
            raise
    
    def _preprocess_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Preprocess paper data to optimize for prompt context.
        
        Args:
            papers: List of paper dictionaries from the arXiv scraper
            
        Returns:
            List of preprocessed paper dictionaries
        """
        processed_papers = []
        
        for i, paper in enumerate(papers):
            # Create a simplified, token-optimized version of each paper
            processed_paper = {
                "id": paper.get("id", f"paper_{i}"),
                "title": paper.get("title", "Untitled Paper"),
                "authors": self._format_authors(paper.get("authors", [])),
                "abstract": self._truncate_text(paper.get("abstract", ""), max_words=150),
                "categories": paper.get("categories", []),
                "published_date": paper.get("published", ""),
                "key_points": self._extract_key_points(paper.get("abstract", ""))
            }
            processed_papers.append(processed_paper)
        
        # Find connections between papers (for a more cohesive script)
        if len(processed_papers) > 1:
            processed_papers = self._identify_connections(processed_papers)
        
        return processed_papers
    
    def _format_authors(self, authors: List[str]) -> str:
        """Format author list to be more concise."""
        if not authors:
            return "Unknown authors"
        
        if len(authors) == 1:
            return authors[0]
        
        if len(authors) == 2:
            return f"{authors[0]} and {authors[1]}"
        
        # For many authors, list first two with et al.
        return f"{authors[0]}, {authors[1]}, et al."
    
    def _truncate_text(self, text: str, max_words: int = 100) -> str:
        """Truncate text to limit token usage."""
        words = text.split()
        if len(words) <= max_words:
            return text
        
        return " ".join(words[:max_words]) + "..."
    
    def _extract_key_points(self, abstract: str) -> List[str]:
        """
        Extract potential key points from the abstract.
        This is a simplified version; in production, consider using
        Gemini itself for this extraction for better results.
        """
        # Simple heuristic: split on sentences and look for key indicators
        sentences = re.split(r'(?<=[.!?])\s+', abstract)
        key_points = []
        
        # Keywords that might indicate important points
        importance_indicators = [
            "we show", "we demonstrate", "we propose", "we present",
            "we find", "we introduce", "results indicate", "we prove",
            "key contribution", "importantly", "significantly"
        ]
        
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in importance_indicators):
                key_points.append(sentence)
        
        # If no key points found with indicators, use first and last sentences
        if not key_points and len(sentences) > 1:
            key_points = [sentences[0], sentences[-1]]
        
        # Limit to 3 key points maximum
        return key_points[:3]
    
    def _identify_connections(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify potential connections between papers for better script flow.
        This uses simple heuristics; for production, consider using Gemini
        for this comparison as well.
        """
        # For each paper, try to find connections to other papers
        for i, paper in enumerate(papers):
            connections = []
            
            # Compare with other papers
            for j, other_paper in enumerate(papers):
                if i == j:
                    continue
                
                # Check for shared categories
                shared_categories = set(paper.get("categories", [])) & set(other_paper.get("categories", []))
                
                # Simple text similarity by checking for common significant words
                paper_words = set(re.findall(r'\b\w{5,}\b', paper.get("abstract", "").lower()))
                other_words = set(re.findall(r'\b\w{5,}\b', other_paper.get("abstract", "").lower()))
                shared_words = paper_words & other_words
                
                # If enough similarity, add a connection
                if shared_categories or len(shared_words) >= 5:
                    connection_type = []
                    if shared_categories:
                        connection_type.append(f"shared categories: {', '.join(shared_categories)}")
                    if shared_words:
                        significant_shared = list(shared_words)[:5]  # Limit to 5 words
                        connection_type.append(f"shared concepts: {', '.join(significant_shared)}")
                    
                    connections.append({
                        "paper_id": other_paper["id"],
                        "connection_types": connection_type
                    })
            
            paper["connections"] = connections
        
        return papers
    
    def _create_prompt(
        self,
        papers: List[Dict[str, Any]],
        config: PodcastConfig
    ) -> str:
        """
        Create a detailed prompt for Gemini to generate the podcast script.
        
        Args:
            papers: List of preprocessed paper dictionaries
            config: Podcast configuration parameters
            
        Returns:
            Formatted prompt string
        """
        # Start with system instructions
        prompt = """You are a professional podcast script writer specializing in creating engaging, conversational scripts about scientific research papers. 
Your task is to write a two-host podcast script discussing recent research papers.

IMPORTANT GUIDELINES:
- Create natural, conversational dialogue between two hosts with distinct personalities
- Make complex research accessible to the specified audience level
- Include questions, insights, and appropriate humor
- Create smooth transitions between different papers
- Format the script properly for audio production
- Maintain scientific accuracy while being entertaining
- Avoid excessive technical jargon unless explained
- Include an introduction, paper discussions, transitions, and conclusion

OUTPUT FORMAT:
Use the following format for the script:
```
# [EPISODE TITLE]

## INTRODUCTION
ALEX: [Alex's dialogue]
JORDAN: [Jordan's dialogue]

## PAPER 1: [Paper Title]
ALEX: [Alex's dialogue]
JORDAN: [Jordan's dialogue]
...

## PAPER 2: [Paper Title]
...

## CONCLUSION
ALEX: [Alex's dialogue]
JORDAN: [Jordan's dialogue]
```
"""

        # Add host profiles
        prompt += "\n## HOST PERSONALITIES\n"
        for host_id, profile in HOST_PROFILES.items():
            prompt += f"### {profile['name'].upper()}\n"
            prompt += f"- Traits: {profile['traits']}\n"
            prompt += f"- Background: {profile['background']}\n"
            prompt += f"- Speech style: {profile['speech_style']}\n\n"
        
        # Add podcast configuration
        prompt += "\n## PODCAST CONFIGURATION\n"
        prompt += f"- Episode title: {config.episode_title}\n"
        prompt += f"- Introduction length: {config.intro_length}\n"
        prompt += f"- Discussion style: {config.paper_discussion_style}\n"
        prompt += f"- Technical level: {config.technical_level}\n"
        prompt += f"- Include humor: {'Yes' if config.include_humor else 'No'}\n"
        prompt += f"- Include analogies: {'Yes' if config.include_analogies else 'No'}\n"
        prompt += f"- Target length: Approximately {config.target_length_minutes} minutes\n"
        prompt += f"- Conclusion type: {config.conclusion_type}\n"
        
        # Add papers to discuss
        prompt += "\n## PAPERS TO DISCUSS\n"
        for i, paper in enumerate(papers):
            prompt += f"\n### PAPER {i+1}: {paper['title']}\n"
            prompt += f"- Authors: {paper['authors']}\n"
            prompt += f"- Published: {paper['published_date']}\n"
            prompt += f"- Categories: {', '.join(paper['categories'])}\n"
            prompt += f"- Abstract: {paper['abstract']}\n"
            
            if paper['key_points']:
                prompt += "- Key points:\n"
                for point in paper['key_points']:
                    prompt += f"  * {point}\n"
            
            # Add connections to other papers if they exist
            if 'connections' in paper and paper['connections']:
                prompt += "- Connections to other papers:\n"
                for connection in paper['connections']:
                    other_paper_idx = next((i for i, p in enumerate(papers) if p['id'] == connection['paper_id']), None)
                    if other_paper_idx is not None:
                        prompt += f"  * Connection to Paper {other_paper_idx+1}: {' and '.join(connection['connection_types'])}\n"
        
        # Add specific instructions for script structure
        prompt += """
## SCRIPT STRUCTURE INSTRUCTIONS
1. Begin with a brief introduction where hosts welcome listeners and preview the papers
2. For each paper discussion:
   - Introduce the paper with its title and authors
   - Explain the key research question or problem
   - Discuss the main findings and their significance
   - Include back-and-forth dialogue with questions and insights
   - Use appropriate analogies to make concepts accessible
3. When transitioning between papers, reference any connections you identified
4. Conclude by summarizing key insights and their broader implications
5. Maintain a balanced speaking role between the two hosts

Now, create an engaging podcast script following these guidelines.
"""
        
        return prompt
    
    def _generate_script(self, prompt: str) -> str:
        """
        Generate the podcast script using Gemini 1.5 Pro with retry logic.
        
        Args:
            prompt: The formatted prompt for the model
            
        Returns:
            Generated podcast script
        """
        retries = 0
        while retries < self.MAX_RETRIES:
            try:
                # Configure safety settings
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
                
                # Create content parts
                content = [Content.from_string(prompt)]
                
                # Generate the script
                response = self.gemini_model.generate_content(
                    content,
                    generation_config={"temperature": self.temperature, "max_output_tokens": 8192},
                    safety_settings=safety_settings
                )
                
                # Extract the script from the response
                script_text = response.text
                
                # Extract the script content between the first and last backtick blocks
                if "```" in script_text:
                    script_parts = script_text.split("```")
                    if len(script_parts) >= 3:
                        # Extract the content between the first and last ``` blocks
                        script_text = script_parts[1]
                        # Remove the first line if it's a language indicator
                        if script_text.strip().split('\n', 1)[0].lower() in ['markdown', 'md']:
                            script_text = script_text.strip().split('\n', 1)[1]
                
                logger.info("Successfully generated podcast script")
                return script_text.strip()
                
            except Exception as e:
                retries += 1
                delay = self.RETRY_DELAY_BASE * (2 ** (retries - 1))  # Exponential backoff
                
                logger.warning(f"Error generating script (attempt {retries}/{self.MAX_RETRIES}): {e}")
                logger.info(f"Retrying in {delay} seconds...")
                
                time.sleep(delay)
        
        # If all retries failed
        raise Exception("Failed to generate podcast script after maximum retries")
    
    def _format_script_for_audio(self, script: str) -> Dict[str, Any]:
        """
        Post-process the script to prepare it for audio generation.
        
        Args:
            script: The raw generated script
            
        Returns:
            Structured script data ready for audio generation
        """
        # Extract script sections
        sections = []
        current_section = {"title": "", "segments": []}
        current_speaker = None
        
        # Process the script line by line
        for line in script.split('\n'):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check for section headers
            if line.startswith('# '):
                # Extract episode title
                episode_title = line[2:].strip()
                continue
                
            if line.startswith('## '):
                # If we already have content in the current section, save it
                if current_section["title"] and current_section["segments"]:
                    sections.append(current_section)
                
                # Start a new section
                current_section = {
                    "title": line[3:].strip(),
                    "segments": []
                }
                current_speaker = None
                continue
            
            # Check for speaker lines
            speaker_match = re.match(r'^([A-Z]+):\s*(.+)$', line)
            if speaker_match:
                speaker = speaker_match.group(1)
                dialogue = speaker_match.group(2)
                
                # Add the dialogue segment
                current_section["segments"].append({
                    "speaker": speaker.lower(),
                    "text": dialogue
                })
                current_speaker = speaker
                continue
            
            # If line is a continuation of the previous speaker's dialogue
            if current_speaker and not line.startswith('#'):
                # Append to the last segment for this speaker
                if current_section["segments"]:
                    current_section["segments"][-1]["text"] += " " + line
        
        # Add the last section if it has content
        if current_section["title"] and current_section["segments"]:
            sections.append(current_section)
        
        # Construct the formatted script
        formatted_script = {
            "title": episode_title if 'episode_title' in locals() else "Research Paper Discussion",
            "sections": sections
        }
        
        return formatted_script
    
    def generate_podcast_script(
        self,
        papers: List[Dict[str, Any]],
        config: Optional[PodcastConfig] = None
    ) -> Dict[str, Any]:
        """
        Generate a podcast script from the provided papers.
        
        Args:
            papers: List of paper dictionaries from the arXiv scraper
            config: Optional podcast configuration parameters
            
        Returns:
            Structured podcast script data
        """
        if not papers:
            raise ValueError("No papers provided for script generation")
        
        # Use default config if none provided
        if not config:
            config = PodcastConfig()
        
        # Limit the number of papers to prevent exceeding token limits
        if len(papers) > 5:
            logger.warning(f"Too many papers provided ({len(papers)}). Limiting to 5 papers.")
            papers = papers[:5]
        
        # Preprocess the papers
        preprocessed_papers = self._preprocess_papers(papers)
        
        # Generate a title based on the papers if not specified
        if config.episode_title == "Latest Research Insights":
            main_categories = self._extract_main_categories(preprocessed_papers)
            config.episode_title = f"Research Frontiers: {', '.join(main_categories)}"
        
        # Create the prompt
        prompt = self._create_prompt(preprocessed_papers, config)
        
        # Generate the script
        raw_script = self._generate_script(prompt)
        
        # Format the script for audio generation
        formatted_script = self._format_script_for_audio(raw_script)
        
        return formatted_script
    
    def _extract_main_categories(self, papers: List[Dict[str, Any]]) -> List[str]:
        """Extract main research categories from papers for title generation."""
        # Collect all categories
        all_categories = []
        for paper in papers:
            all_categories.extend(paper.get("categories", []))
        
        # Count occurrences
        category_counts = {}
        for category in all_categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Get the most common categories (up to 3)
        main_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        main_categories = [category for category, _ in main_categories[:3]]
        
        # Convert category codes to readable names
        category_names = {
            "cs.AI": "Artificial Intelligence",
            "cs.CL": "Computational Linguistics",
            "cs.CV": "Computer Vision",
            "cs.LG": "Machine Learning",
            "cs.NE": "Neural Networks",
            "cs.RO": "Robotics",
            "physics.comp-ph": "Computational Physics",
            "q-bio": "Quantitative Biology",
            "q-fin": "Quantitative Finance",
            "stat.ML": "Statistical Machine Learning"
        }
        
        readable_categories = []
        for category in main_categories:
            if category in category_names:
                readable_categories.append(category_names[category])
            else:
                # Try to make category codes more readable
                parts = category.split('.')
                if len(parts) > 1:
                    readable_categories.append(parts[1])
                else:
                    readable_categories.append(category)
        
        return readable_categories if readable_categories else ["Scientific Research"]


def main():
    """Example usage of the GeminiPodcastGenerator."""
    # Mock paper data for demonstration
    papers = [
        {
            "id": "2305.12140",
            "title": "Attention Temperature Matters in Abstractive Summarization",
            "authors": ["Alex Smith", "Jordan Lee", "Maria Rodriguez"],
            "abstract": "The attention mechanism is central to modern transformer-based language models, but the impact of attention temperature on abstractive summarization remains underexplored. We systematically investigate how varying attention temperature affects summary quality across multiple dimensions. Our findings reveal that higher temperatures significantly improve abstraction and novelty while preserving factual consistency. We demonstrate these effects across three summarization benchmarks and provide an analysis framework for understanding attention temperature's role in controlling the exploration-exploitation trade-off in transformer models.",
            "categories": ["cs.CL", "cs.AI", "cs.LG"],
            "published": "2023-05-20",
            "url": "https://arxiv.org/abs/2305.12140"
        },
        {
            "id": "2305.14314",
            "title": "Efficient Transformers with Dynamic Token Pooling",
            "authors": ["Priya Patel", "Thomas Johnson", "Wei Zhang"],
            "abstract": "Transformer models face efficiency challenges when processing long sequences due to the quadratic attention complexity. We propose Dynamic Token Pooling (DTP), a novel approach that adaptively reduces sequence length during processing. Unlike prior pruning methods, DTP dynamically merges similar tokens based on semantic and structural features, preserving information while reducing computation. Our method achieves 2-3x speedup with minimal accuracy loss across language, vision, and multimodal tasks. We provide theoretical analysis showing how DTP maintains representation capacity while improving efficiency.",
            "categories": ["cs.LG", "cs.AI", "cs.CL"],
            "published": "2023-05-23",
            "url": "https://arxiv.org/abs/2305.14314"
        }
    ]
    
    # Create podcast configuration
    config = PodcastConfig(
        episode_title="Transformer Innovations in NLP",
        technical_level="intermediate",
        target_length_minutes=10
    )
    
    try:
        # In a real scenario, you would use actual credentials
        # This is for demonstration only
        generator = GeminiPodcastGenerator(
            project_id="your-project-id",
            service_account_path="path/to/service-account.json"
        )
        
        # Generate podcast script
        script = generator.generate_podcast_script(papers, config)
        
        # Print formatted script
        print(json.dumps(script, indent=2))
        
    except Exception as e:
        logger.error(f"Error in podcast generation: {e}")


if __name__ == "__main__":
    # This would run the example in a real environment
    # main()
    pass