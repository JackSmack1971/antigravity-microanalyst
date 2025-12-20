from typing import List, Dict, Any
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class SemanticCatalogSearch:
    def __init__(self, catalog_path: Path = None):
        self.project_root = Path(__file__).parent.parent.parent.parent
        if catalog_path is None:
            catalog_path = self.project_root / "config" / "catalog_enhanced.json"
        
        if not catalog_path.exists():
            # Fallback to generating it on fly or error
            # For robustness, we assume it exists or use empty
            self.catalog = {"datasets": {}}
        else:
            with open(catalog_path, 'r') as f:
                self.catalog = json.load(f)
        
        self.search_index = self._build_search_index()
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        
        if self.search_index:
            self.document_vectors = self.vectorizer.fit_transform(
                [doc['searchable_text'] for doc in self.search_index]
            )
        else:
            self.document_vectors = None

    def _build_search_index(self) -> List[Dict[str, Any]]:
        index = []
        if 'datasets' not in self.catalog: return []
        
        for dataset_id, dataset in self.catalog['datasets'].items():
            fields = " ".join([f['name'] + " " + f.get('description', '') 
                             for f in dataset.get('schema', {}).get('fields', [])])
                             
            searchable_text = " ".join([
                dataset.get('display_name', ''),
                dataset.get('description', ''),
                dataset.get('category', ''),
                fields,
                " ".join(dataset.get('usage_metadata', {}).get('primary_use_cases', []))
            ])
            
            index.append({
                'dataset_id': dataset_id,
                'dataset': dataset,
                'searchable_text': searchable_text
            })
        return index

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.search_index or self.document_vectors is None:
            return []
            
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.document_vectors)[0]
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:
                result = {
                    'dataset_id': self.search_index[idx]['dataset_id'],
                    'display_name': self.search_index[idx]['dataset']['display_name'],
                    'description': self.search_index[idx]['dataset']['description'],
                    'relevance_score': float(similarities[idx]),
                    'api_endpoint': f"/data/{self.search_index[idx]['dataset_id']}" # Approx mapping
                }
                results.append(result)
        return results
