# app/api/arxiv.py

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from marshmallow import Schema, fields, validate

from ..services.arxiv_service import ArxivService
from ..api.errors import error_response, ApiException

arxiv_bp = Blueprint('arxiv', __name__)

# Schemas for request validation
class SearchSchema(Schema):
    topics = fields.List(fields.String(), missing=[])
    categories = fields.List(fields.String(), missing=[])
    authors = fields.List(fields.String(), missing=[])
    max_results = fields.Integer(validate=validate.Range(min=1, max=50), missing=10)
    page = fields.Integer(validate=validate.Range(min=1), missing=1)

search_schema = SearchSchema()

@arxiv_bp.route('/search', methods=['GET'])
@jwt_required()
def search_papers():
    """Search ArXiv papers."""
    try:
        # Validate query parameters
        params = search_schema.load(request.args)
        
        # Initialize ArXiv service
        arxiv_service = ArxivService()
        
        # Perform search
        papers, total = arxiv_service.search_papers(
            topics=params['topics'],
            categories=params['categories'],
            authors=params['authors'],
            max_results=params['max_results'],
            page=params['page']
        )
        
        # Calculate pagination
        per_page = params['max_results']
        total_pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'papers': [paper.to_dict() for paper in papers],
            'total': total,
            'page': params['page'],
            'pages': total_pages
        })
    except Exception as e:
        current_app.logger.error(f"ArXiv search error: {str(e)}")
        return error_response(500, "Failed to search papers")

@arxiv_bp.route('/paper/<paper_id>', methods=['GET'])
@jwt_required()
def get_paper(paper_id):
    """Get specific paper by ID."""
    try:
        arxiv_service = ArxivService()
        paper = arxiv_service.get_paper_by_id(paper_id)
        
        if not paper:
            return error_response(404, "Paper not found")
        
        return jsonify(paper.to_dict())
    except Exception as e:
        current_app.logger.error(f"Error retrieving paper {paper_id}: {str(e)}")
        return error_response(500, "Failed to retrieve paper")

@arxiv_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Get available ArXiv categories."""
    categories = {
        'cs.AI': 'Artificial Intelligence',
        'cs.CL': 'Computation and Language',
        'cs.CV': 'Computer Vision and Pattern Recognition',
        'cs.LG': 'Machine Learning',
        'cs.NE': 'Neural and Evolutionary Computing',
        'cs.RO': 'Robotics',
        'math.CO': 'Combinatorics',
        'math.IT': 'Information Theory',
        'math.LO': 'Logic',
        'math.ST': 'Statistics Theory',
        'physics.astro-ph': 'Astrophysics',
        'physics.cond-mat': 'Condensed Matter',
        'physics.gr-qc': 'General Relativity and Quantum Cosmology',
        'physics.hep-ph': 'High Energy Physics - Phenomenology',
        'physics.quant-ph': 'Quantum Physics',
        'q-bio.BM': 'Biomolecules',
        'q-bio.GN': 'Genomics',
        'q-bio.MN': 'Molecular Networks',
        'q-bio.NC': 'Neurons and Cognition',
        'q-bio.PE': 'Populations and Evolution',
        'q-fin.CP': 'Computational Finance',
        'q-fin.EC': 'Economics',
        'q-fin.GN': 'General Finance',
        'q-fin.PM': 'Portfolio Management',
        'q-fin.ST': 'Statistical Finance'
    }
    
    return jsonify({
        'categories': [
            {'id': key, 'name': value} 
            for key, value in categories.items()
        ]
    })