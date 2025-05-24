# app/api/arxiv.py

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from marshmallow import Schema, fields, validate, ValidationError

from ..services.arxiv_service import ArxivService
from ..api.errors import error_response

arxiv_bp = Blueprint('arxiv', __name__)

class SearchSchema(Schema):
    topics = fields.List(fields.String(), load_default=[])
    categories = fields.List(fields.String(), load_default=[])
    authors = fields.List(fields.String(), load_default=[])
    max_results = fields.Integer(validate=validate.Range(min=1, max=50), load_default=10)
    page = fields.Integer(validate=validate.Range(min=1), load_default=1)
    # Renamed field to match what ArxivService expects, will use data_key for query param
    sort_by_preference = fields.String(
        validate=validate.OneOf(['relevance', 'lastUpdatedDate', 'submittedDate']),
        load_default='relevance',
        data_key='sort_by_preference' # Explicitly state data_key for clarity, though it's default
    )

search_schema = SearchSchema()

@arxiv_bp.route('/search', methods=['GET'])
@jwt_required()
def search_papers():
    """Search ArXiv papers."""
    try:
        # Manually parse MultiDict into a dict suitable for Marshmallow,
        # ensuring list fields get lists and single fields get single values.
        parsed_args = {}
        for key in request.args:
            if key in ['topics', 'categories', 'authors']: # Fields expected as lists
                parsed_args[key] = request.args.getlist(key)
            else: # Scalar fields
                parsed_args[key] = request.args.get(key)
        
        # Validate query parameters using the manually parsed dictionary
        params = search_schema.load(parsed_args)
        
        arxiv_service = ArxivService()
        
        papers_list, total_results = arxiv_service.search_papers(
            topics=params.get('topics'), # .get() is fine, schema provides defaults
            categories=params.get('categories'),
            authors=params.get('authors'),
            max_results=params.get('max_results'),
            page=params.get('page'),
            sort_by_preference=params.get('sort_by_preference')
        )
        
        per_page = params.get('max_results')
        total_pages = (total_results + per_page - 1) // per_page if total_results > 0 and per_page > 0 else 0
        
        return jsonify({
            'papers': papers_list,
            'total': total_results,
            'page': params.get('page'),
            'pages': total_pages
        })
    except ValidationError as err: 
        current_app.logger.error(f"ArXiv search schema validation error: {err.messages}")
        return error_response(400, err.messages)
    except Exception as e:
        current_app.logger.error(f"ArXiv search error: {str(e)}", exc_info=True)
        return error_response(500, "Failed to search papers")

@arxiv_bp.route('/paper/<path:paper_id>', methods=['GET'])
@jwt_required()
def get_paper(paper_id):
    """Get specific paper by ID."""
    try:
        arxiv_service = ArxivService()
        paper = arxiv_service.get_paper_by_id(paper_id)
        
        if not paper:
            return error_response(404, "Paper not found")
        
        return jsonify(paper)
    except Exception as e:
        current_app.logger.error(f"Error retrieving paper {paper_id}: {str(e)}", exc_info=True)
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