from app import create_app
from app.services.arxiv_service import ArxivService

# User preferences to test with
test_preferences = {
    "topics": ["language model", "reinforcement learning"],
    "categories": ["cs.AI"],
    "authors": [],
    "max_results": 3
}

# --- Script Starts ---
app = create_app('development')

with app.app_context():
    service = ArxivService()

    # Manually call the internal query builder to see what will be sent to ArXiv
    built_query = service._build_search_query(
        topics=test_preferences["topics"],
        categories=test_preferences["categories"],
        authors=test_preferences["authors"]
    )
    print("="*50)
    print(f"Constructed ArXiv Query: {built_query}")
    print("="*50)

    # Now, perform the actual search
    try:
        papers, total = service.search_papers(**test_preferences)

        if papers:
            print(f"\nSuccessfully found {len(papers)} papers (Total matches: {total}):")
            for i, paper in enumerate(papers):
                print(f"  {i+1}. {paper['title']}")
        else:
            print("\nNo papers found for the given preferences.")

    except Exception as e:
        print(f"\nAn error occurred during the search: {e}")