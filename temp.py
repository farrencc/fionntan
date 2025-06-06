from app import create_app
from app.services.arxiv_service import ArxivService #

app = create_app('development') # Or your appropriate config

with app.app_context():
    service = ArxivService()
    paper_id_to_test = '2308.02657' # Example paper ID from your guide
    # You can also try another valid ArXiv ID like 'cs.AI/0001001'
    # or a more recent one like '2401.00001' (if it exists)

    print(f"Attempting to fetch paper: {paper_id_to_test}")
    paper = service.get_paper_by_id(paper_id_to_test)

    if paper:
        print(f"Paper found: {paper.get('title', 'N/A')[:50]}...")
        print(f"ID: {paper.get('id')}")
        print(f"Authors: {paper.get('authors')}")
    else:
        print(f"X Paper with ID '{paper_id_to_test}' failed to fetch or was not found.")