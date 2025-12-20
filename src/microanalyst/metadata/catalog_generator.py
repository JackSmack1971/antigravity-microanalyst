
import pandas as pd
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import numpy as np

class CatalogGenerator:
    """
    Automatically generates enhanced catalog from actual data files.
    Infers schema, statistics, quality metrics.
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.data_dir = self.project_root / "data_clean"
        self.config_dir = self.project_root / "config"
        
    def generate_full_catalog(self) -> Dict[str, Any]:
        """Generate complete catalog with runtime statistics"""
        
        # Load base catalog
        base_catalog_path = self.config_dir / "data_catalog_enhanced.yml"
        if not base_catalog_path.exists():
            return {"error": "Base catalog not found"}
            
        with open(base_catalog_path, 'r') as f:
            catalog = yaml.safe_load(f)
        
        # Enhance each dataset with runtime data
        for dataset_id, dataset_config in catalog['datasets'].items():
            location = dataset_config['storage']['primary_location']
            file_path = self.project_root / location
            
            if file_path.exists():
                # Fix for empty files or parse errors
                try:
                    df = pd.read_csv(file_path)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    continue
                
                # Update storage metadata
                catalog['datasets'][dataset_id]['storage']['size_bytes'] = file_path.stat().st_size
                catalog['datasets'][dataset_id]['storage']['row_count'] = len(df)
                catalog['datasets'][dataset_id]['storage']['last_modified'] = datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat()
                
                # Infer and validate schema
                inferred_schema = self._infer_schema(df, dataset_config)
                catalog['datasets'][dataset_id]['schema_validation'] = inferred_schema
                
                # Calculate statistics
                stats = self._calculate_statistics(df, dataset_config)
                catalog['datasets'][dataset_id]['runtime_statistics'] = stats
                
                # Check quality metrics
                quality = self._assess_quality(df, dataset_config)
                catalog['datasets'][dataset_id]['quality_metrics']['current_state'] = quality
                
                # Calculate freshness
                freshness = self._calculate_freshness(df, dataset_config)
                catalog['datasets'][dataset_id]['freshness'] = freshness
        
        # Update global metadata
        catalog['catalog_metadata']['generated_at'] = datetime.now().isoformat()
        
        return catalog
    
    def _infer_schema(self, df: pd.DataFrame, config: Dict) -> Dict[str, Any]:
        """Infer actual schema from DataFrame and compare to config"""
        inferred = {
            'fields': [],
            'schema_drift_detected': False,
            'drift_details': []
        }
        
        expected_fields = {f['name']: f for f in config['schema']['fields']}
        
        for col in df.columns:
            field_info = {
                'name': col,
                'actual_type': str(df[col].dtype),
                'null_count': int(df[col].isnull().sum()),
                'unique_count': int(df[col].nunique())
            }
            
            # Compare to expected schema
            if col in expected_fields:
                expected = expected_fields[col]
                
                if not self._types_compatible(str(df[col].dtype), expected['type']):
                    inferred['schema_drift_detected'] = True
                    inferred['drift_details'].append({
                        'field': col,
                        'issue': 'type_mismatch',
                        'expected': expected['type'],
                        'actual': str(df[col].dtype)
                    })
            else:
                inferred['schema_drift_detected'] = True
                inferred['drift_details'].append({
                    'field': col,
                    'issue': 'undocumented_field'
                })
            
            inferred['fields'].append(field_info)
        
        return inferred
    
    def _calculate_statistics(self, df: pd.DataFrame, config: Dict) -> Dict[str, Any]:
        stats = {}
        for field in config['schema']['fields']:
            col_name = field['name']
            if col_name not in df.columns:
                continue
                
            col_stats = {
                'count': int(df[col_name].count()),
                'missing': int(df[col_name].isnull().sum())
            }
            
            dtype = str(df[col_name].dtype)
            if 'float' in dtype or 'int' in dtype:
                 col_stats['mean'] = float(df[col_name].mean()) if not df[col_name].empty else None
            
            stats[col_name] = col_stats
        return stats
    
    def _assess_quality(self, df: pd.DataFrame, config: Dict) -> Dict[str, Any]:
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        completeness = 1 - (null_cells / total_cells) if total_cells > 0 else 0
        
        return {
            'completeness': {'score': float(completeness)},
            'overall_score': float(completeness) # Simplified for MVP
        }
    
    def _calculate_freshness(self, df: pd.DataFrame, config: Dict) -> Dict[str, Any]:
        date_column = next((f['name'] for f in config['schema']['fields'] 
                           if 'datetime' in f['type']), None)
        
        if not date_column or date_column not in df.columns:
            return {'error': 'No date column found'}
        
        try:
            dates = pd.to_datetime(df[date_column])
            latest_date = dates.max()
            now = datetime.now()
            lag_hours = (now - latest_date).total_seconds() / 3600
            
            return {
                'latest_data_timestamp': latest_date.isoformat(),
                'current_lag_hours': float(lag_hours),
                'freshness_status': 'fresh' if lag_hours < 24 else 'stale'
            }
        except:
            return {'error': 'Date parsing failed'}
    
    def _types_compatible(self, actual: str, expected: str) -> bool:
        # Simplified compatibility check
        if 'float' in actual and 'float' in expected: return True
        if 'int' in actual and 'float' in expected: return True # Upcast ok
        if 'object' in actual and 'string' in expected: return True
        return False
    
    def save_catalog(self, catalog: Dict[str, Any], format: str = 'json'):
        output_path = self.config_dir / f"catalog_enhanced.{format}"
        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(catalog, f, indent=2, default=str)
        return output_path
