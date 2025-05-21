from pymongo import MongoClient
import wikipediaapi

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['wikipedia_clickstream']
collection = db['clickstream_data']

# Set up Wikipedia API
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='YourAppName (yourname@example.com) - Python Wikipedia API client'
)

# Function to get the top child based on clicks
def get_top_child(node, visited, n_branches=3):
    visited.add(node)
    max_clicks = -1
    top_child = None
    count = 0

    results = list(collection.find({"prev": node}).sort("n", -1).limit(n_branches))
    print(f"Found {len(results)} results for node {node}")

    for result in results:
        child = result.get("cur")
        if child in visited:
            continue
        visited.add(child)
        count += 1
        if count >= n_branches:
            break
        clicks = result.get("n", 0)
        if clicks > max_clicks:
            max_clicks = clicks
            top_child = child

    return top_child

# Recursive hierarchy traversal function
def traverse_hierarchy_recursive(start_node, depth):
    visited = set()
    path = []

    def traverse(node, curr_depth):
        if curr_depth >= depth:
            return
        top_child = get_top_child(node, visited)
        if top_child:
            path.append((node, curr_depth, top_child))
            traverse(top_child, curr_depth + 1)

    traverse(start_node, 0)
    print(f"Traversal completed for {start_node} with path length {len(path)}")
    return path

# Format categories to select top 5
def format_categories(categories):
    filtered_categories = [cat.title.replace("Category:", "") for cat in categories.values() if not cat.title.startswith("Category:Articles with")]
    top_5_categories = filtered_categories[:5]  # Limit to 5 categories
    return ", ".join(top_5_categories).strip()

# Format summary to limit length
def format_summary(summary, max_length=500):
    summary = summary.replace('\n', ' ')
    if len(summary) > max_length:
        summary = summary[:max_length] + '...'
    return summary

# Function to print the traversal sequence
def print_traversal_sequence(sequence):
    result = []
    for parent, depth, page in sequence:
        try:
            page_py = wiki_wiki.page(page)
            summary = format_summary(page_py.summary)
            categories = format_categories(page_py.categories)
            result.append(f"{page} -> Page - Summary: {summary} Categories: {categories}")
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            continue

    return result

# Main process without Excel saving
keywords = [doc['cur'] for doc in collection.find().limit(100000)]

# Process each keyword
for i, keyword in enumerate(keywords, 1):
    print(f"Processing keyword {i}/{len(keywords)}: {keyword}")
    path = traverse_hierarchy_recursive(keyword, 5)
    sequence = [(parent, depth, child) for parent, depth, child in path]
    output = print_traversal_sequence(sequence)

    # Extract the top 5 recommendations and their categories
    recoms = [item.split(' -> ')[0] for item in output[:5]]
    categories = output[0].split('Categories: ')[1] if output else ''

    # Print the results for each keyword
    print(f"Keyword: {keyword}")
    print(f"Top 5 recommendations: {recoms}")
    print(f"Categories: {categories}")
    print()
