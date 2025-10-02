# app/services/gemini_service.py

import os
import json
import logging
from typing import List, Dict, Any, Optional

# Try different import methods
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
except ImportError:
    try:
        # Alternative import for newer versions
        import vertexai.preview.generative_models as generative_models
        GenerativeModel = generative_models.GenerativeModel
    except ImportError:
        # Fallback: Use google.generativeai instead
        import google.generativeai as genai
        GenerativeModel = None

from flask import current_app

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for interacting with Google Gemini API."""
    
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
    
    def __init__(self):
        """Initialize Gemini service using Vertex AI."""
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel

            project_id = current_app.config.get('GCP_PROJECT_ID')
            location = "us-central1"  # A common, stable region for these models

            if not project_id:
                raise ValueError("GCP_PROJECT_ID is not set in the configuration.")

            # Initialize Vertex AI with your project and location
            vertexai.init(project=project_id, location=location)

            # Use a stable, widely available model on Vertex AI
            # Do NOT include "models/" here when using Vertex AI initialization
            self.model = GenerativeModel("gemini-2.5-pro")

            logger.info(f"Successfully initialized Gemini service via Vertex AI for project '{project_id}'")

        except Exception as e:
            logger.error(f"Error initializing Gemini via Vertex AI: {str(e)}")
            raise
    
    def generate_script(
        self,
        papers: List[Dict[str, Any]],
        technical_level: str = "intermediate",
        target_length: int = 15,
        episode_title: str = None
    ) -> Dict[str, Any]:
        """Generate podcast script from papers."""
        try:
            # Preprocess papers
            processed_papers = self._preprocess_papers(papers)
            
            # Generate episode title
            if not episode_title:
                episode_title = self._generate_episode_title(processed_papers)
            
            # Create prompt
            prompt = self._create_prompt(
                processed_papers,
                technical_level,
                target_length,
                episode_title
            )
            
            # Generate script
            response = self.model.generate_content(prompt)
            script_text = response.text
            
            # Parse and format script
            formatted_script = self._format_script(script_text, episode_title)
            
            return formatted_script
            
        except Exception as e:
            logger.error(f"Error generating script: {str(e)}")
            raise
    
    def _preprocess_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preprocess papers for prompt optimization."""
        processed_papers = []
        
        for i, paper in enumerate(papers):
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
        
        # Identify connections between papers
        if len(processed_papers) > 1:
            processed_papers = self._identify_connections(processed_papers)
        
        return processed_papers
    
    def _format_authors(self, authors: List[str]) -> str:
        """Format author list concisely."""
        if not authors:
            return "Unknown authors"
        
        if len(authors) == 1:
            return authors[0]
        
        if len(authors) == 2:
            return f"{authors[0]} and {authors[1]}"
        
        return f"{authors[0]}, {authors[1]}, et al."
    
    def _truncate_text(self, text: str, max_words: int = 100) -> str:
        """Truncate text to limit token usage."""
        words = text.split()
        if len(words) <= max_words:
            return text
        
        return " ".join(words[:max_words]) + "..."
    
    def _extract_key_points(self, abstract: str) -> List[str]:
        """Extract key points from abstract."""
        # Simplified version - could use NLP for better extraction
        sentences = abstract.split('. ')
        key_points = []
        
        indicators = [
            "we show", "we demonstrate", "we propose", "we present",
            "we find", "we introduce", "results indicate", "we prove"
        ]
        
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in indicators):
                key_points.append(sentence + '.')
        
        if not key_points and len(sentences) > 1:
            key_points = [sentences[0] + '.', sentences[-1] + '.']
        
        return key_points[:3]
    
    def _identify_connections(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify connections between papers."""
        # Simplified version - could use better similarity analysis
        for i, paper in enumerate(papers):
            connections = []
            
            for j, other_paper in enumerate(papers):
                if i == j:
                    continue
                
                # Check shared categories
                shared_categories = set(paper.get("categories", [])) & set(other_paper.get("categories", []))
                
                if shared_categories:
                    connections.append({
                        "paper_id": other_paper["id"],
                        "connection_types": [f"shared categories: {', '.join(shared_categories)}"]
                    })
            
            paper["connections"] = connections
        
        return papers
    
    def _generate_episode_title(self, papers: List[Dict[str, Any]]) -> str:
        """Generate episode title based on papers."""
        # Extract main categories
        all_categories = []
        for paper in papers:
            all_categories.extend(paper.get("categories", []))
        
        if all_categories:
            # Get most common category
            category_counts = {}
            for cat in all_categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            main_category = max(category_counts.items(), key=lambda x: x[1])[0]
            return f"Research Frontiers: {main_category}"
        
        return "Research Paper Discussion"
    
    def _create_prompt(
        self,
        papers: List[Dict[str, Any]],
        technical_level: str,
        target_length: int,
        episode_title: str
    ) -> str:
        """Create prompt for Gemini."""
        prompt = f"""You are a professional podcast script writer. Create a conversational podcast script about scientific research papers.

EPISODE DETAILS:
- Title: {episode_title}
- Technical Level: {technical_level}
- Target Length: {target_length} minutes

HOST PROFILES:
{json.dumps(self.HOST_PROFILES, indent=2)}

PAPERS TO DISCUSS:
{json.dumps(papers, indent=2)}

REQUIREMENTS:
1. Create natural, conversational dialogue between two hosts
2. Match language to the {technical_level} technical level
3. Include questions, insights, and appropriate humor
4. Create smooth transitions between papers
5. Format for audio production

OUTPUT FORMAT:
# {episode_title}

## INTRODUCTION
ALEX: [dialogue]
JORDAN: [dialogue]

## PAPER 1: [Paper Title]
ALEX: [dialogue]
JORDAN: [dialogue]
...

## CONCLUSION
ALEX: [dialogue]
JORDAN: [dialogue]

Generate the script now:"""
        
        return prompt
    
    def _format_script(self, script_text: str, episode_title: str) -> Dict[str, Any]:
        """Parse and format script into structured data."""
        sections = []
        current_section = {"title": "", "segments": []}
        current_speaker = None
        
        lines = script_text.split('\n')
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Check for section headers
            if line.startswith('# '):
                continue
            
            if line.startswith('## '):
                # Save previous section if it has content
                if current_section["title"] and current_section["segments"]:
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    "title": line[3:].strip(),
                    "segments": []
                }
                continue
            
            # Check for speaker lines
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2 and parts[0].isupper():
                    speaker = parts[0].lower()
                    dialogue = parts[1].strip()
                    
                    current_section["segments"].append({
                        "speaker": speaker,
                        "text": dialogue
                    })
        
        # Add last section
        if current_section["title"] and current_section["segments"]:
            sections.append(current_section)
        
        return {
            "title": episode_title,
            "sections": sections
        }
