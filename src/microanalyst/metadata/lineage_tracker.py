from typing import Dict, List, Any
from datetime import datetime
import json
from pathlib import Path

class LineageTracker:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.lineage_file = self.project_root / "logs" / "data_lineage.json"
        self.lineage_store = {}
        self._load_lineage()
    
    def record_transformation(
        self,
        dataset_id: str,
        source_datasets: List[str],
        transformation_module: str,
        transformation_function: str,
        metadata: Dict[str, Any] = None
    ):
        event = {
            'timestamp': datetime.now().isoformat(),
            'dataset_id': dataset_id,
            'sources': source_datasets,
            'transformation': {
                'module': transformation_module,
                'function': transformation_function
            },
            'metadata': metadata or {}
        }
        
        if dataset_id not in self.lineage_store:
            self.lineage_store[dataset_id] = []
        
        self.lineage_store[dataset_id].append(event)
        self._save_lineage()
        
    def get_upstream_lineage(self, dataset_id: str) -> Dict:
        return self.lineage_store.get(dataset_id, [])

    def _load_lineage(self):
        if self.lineage_file.exists():
            try:
                with open(self.lineage_file, 'r') as f:
                    self.lineage_store = json.load(f)
            except:
                self.lineage_store = {}
                
    def _save_lineage(self):
        self.lineage_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.lineage_file, 'w') as f:
            json.dump(self.lineage_store, f, indent=2)
