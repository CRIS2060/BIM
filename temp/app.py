from flask import Flask, request, render_template
import os
import re
from collections import defaultdict

app = Flask(__name__)

# Paths for datasets and images
dataset_path = '/Users/shirishkarmacharya/Desktop/temp/dataset'
image_folder_path = 'static/dog_pics'

# Preprocessing function to clean and tokenize text
def preprocess(text):
    return re.findall(r'\b\w+\b', text.lower())

# Load documents and associated images
def load_documents(dataset_path, image_folder_path):
    docs = {}
    for filename in os.listdir(dataset_path):
        if filename.endswith('.txt'):
            breed_name = filename.replace('.txt','')
            with open(os.path.join(dataset_path, filename), 'r') as file:
                docs[filename] = {
                    'text': preprocess(file.read()),
                    'photo_url': os.path.join(image_folder_path, f"{breed_name}.jpg")  # Link to photo

                }
    return docs

# Compute term frequencies and document frequencies
def compute_statistics(docs):
    doc_count = len(docs)
    term_doc_freq = defaultdict(int)
    term_freq = defaultdict(lambda: defaultdict(int))

    for doc_id, words in docs.items():
        word_set = set(words['text'])
        for word in words['text']:
            term_freq[doc_id][word] += 1
        for word in word_set:
            term_doc_freq[word] += 1

    return term_freq, term_doc_freq, doc_count

# Compute relevance probabilities using BIM
def compute_relevance_prob(query, term_freq, term_doc_freq, doc_count):
    scores = {}
    for doc_id in term_freq:
        score = 1.0
        for term in query:
            tf = term_freq[doc_id].get(term, 0)
            df = term_doc_freq.get(term, 0)
            p_term_given_relevant = (tf + 1) / (sum(term_freq[doc_id].values()) + len(term_doc_freq))
            p_term_given_not_relevant = (df + 1) / (doc_count - df + len(term_doc_freq))
            score *= (p_term_given_relevant / p_term_given_not_relevant)
        scores[doc_id] = score
    return scores

# Main function to retrieve documents based on query
# Main function to retrieve documents based on query
def retrieve_documents(dataset_path, image_folder_path, query):
    docs = load_documents(dataset_path, image_folder_path)
    term_freq, term_doc_freq, doc_count = compute_statistics(docs)

    query_terms = preprocess(query)
    scores = compute_relevance_prob(query_terms, term_freq, term_doc_freq, doc_count)
    ranked_docs = sorted(scores.items(), key=lambda item: item[1], reverse=True)

    # Prepare results including title (filename), photo URL, and score
    results = []
    for doc_id, score in ranked_docs[:10]:  # Show top 10 results
        results.append({
            'title': doc_id.replace('.txt', ''),
            'photo_url': docs[doc_id]['photo_url'],
            'score': score,
            'document_text': open(os.path.join(dataset_path, doc_id)).read()  # Load document text
        })

    # Only keep top 3 ranked documents
    top_results = []
    for result in results[:3]:
        top_results.append(result)

    return top_results

# Flask route to render search form
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/breed/<breed>')
def breed_info(breed):
    # Load the corresponding breed file
    filename = f"{breed}.txt"
    file_path = os.path.join(dataset_path, filename)
    
    # Read the contents of the file
    with open(file_path, 'r') as file:
        content = file.read()

    return render_template('breed_info.html', breed=breed, content=content)

# Flask route to handle search and display results
@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    results = retrieve_documents(dataset_path, image_folder_path, query)
    return render_template('results.html', results=results)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
