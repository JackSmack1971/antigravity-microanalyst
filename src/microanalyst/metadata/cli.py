import click
import json
import sys
from pathlib import Path
from src.microanalyst.metadata.catalog_generator import CatalogGenerator
from src.microanalyst.metadata.semantic_search import SemanticCatalogSearch
from src.microanalyst.metadata.lineage_tracker import LineageTracker

# Path hack for imports
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

@click.group()
def metadata_cli():
    """Data catalog management CLI"""
    pass

@metadata_cli.command()
def generate_catalog():
    """Generate enhanced catalog from data files"""
    generator = CatalogGenerator()
    catalog = generator.generate_full_catalog()
    path = generator.save_catalog(catalog)
    click.echo(f"✓ Catalog generated: {path}")

@metadata_cli.command()
@click.argument('query')
def search(query):
    """Search catalog with natural language"""
    searcher = SemanticCatalogSearch()
    results = searcher.search(query)
    
    for r in results:
        click.echo(f"\n{r['display_name']} (relevance: {r['relevance_score']:.2f})")
        click.echo(f"  {r['description']}")
        click.echo(f"  API: {r['api_endpoint']}")

@metadata_cli.command()
@click.argument('dataset_id')
def describe(dataset_id):
    """Show detailed dataset metadata"""
    generator = CatalogGenerator()
    catalog = generator.generate_full_catalog()
    
    if dataset_id not in catalog['datasets']:
        click.echo(f"Dataset '{dataset_id}' not found", err=True)
        return
    
    dataset = catalog['datasets'][dataset_id]
    
    click.echo(f"\n=== {dataset['display_name']} ===")
    click.echo(f"Description: {dataset['description']}")
    click.echo(f"Rows: {dataset['storage'].get('row_count', 'N/A')}")
    click.echo(f"Freshness: {dataset.get('freshness', {}).get('freshness_status', 'N/A')}")
    # Fix for missing quality when new
    quality_score = dataset['quality_metrics'].get('current_state', {}).get('overall_score', 0.0)
    click.echo(f"Quality Score: {quality_score:.2f}")
    
    click.echo("\nFields:")
    for field in dataset['schema']['fields']:
        click.echo(f"  - {field['name']} ({field['type']}): {field.get('description', '')}")

@metadata_cli.command()
@click.argument('dataset_id')
def lineage(dataset_id):
    """Show data lineage"""
    tracker = LineageTracker()
    lineage = tracker.get_upstream_lineage(dataset_id)
    
    click.echo(json.dumps(lineage, indent=2))

if __name__ == "__main__":
    metadata_cli()
