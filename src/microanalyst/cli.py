import click
import json
import pandas as pd
from datetime import datetime, timedelta
from src.microanalyst.reports.generator import ReportGenerator
from src.microanalyst.validation.suite import DataValidator
from pathlib import Path

# Fix for path if running from root
import sys
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

@click.group()
def cli():
    """BTC Microanalyst CLI for agent automation"""
    pass

@cli.command()
@click.option('--output', type=click.Choice(['json', 'csv']), default='json')
@click.option('--days', type=int, default=30)
def get_price(output, days):
    """Fetch normalized BTC price data"""
    # Direct file read for CLI speed vs API call
    file_path = Path("data_clean/btc_price_normalized.csv")
    if not file_path.exists():
        click.echo("Error: Price data not found", err=True)
        return

    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    
    start_date = datetime.now() - timedelta(days=days)
    df = df[df['date'] >= start_date]

    if output == 'json':
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        click.echo(df.to_json(orient='records', indent=2))
    elif output == 'csv':
        click.echo(df.to_csv(index=False))

@cli.command()
@click.option('--report-type', type=click.Choice(['daily']), default='daily')
@click.option('--format', type=click.Choice(['markdown', 'json']), default='markdown')
def generate_report(report_type, format):
    """Generate analysis report"""
    reporter = ReportGenerator()
    
    result = {}
    if report_type == 'daily':
        result = reporter.generate_daily_market_summary()
        
    if "error" in result:
        click.echo(f"Error generating report: {result['error']}", err=True)
        return

    if format == 'markdown':
        report = reporter.generate_markdown_report(result)
        click.echo(report)
    else:
        click.echo(json.dumps(result, indent=2))

@cli.command()
def validate_data():
    """Run data quality checks"""
    validator = DataValidator()
    
    file_path = Path("data_clean/btc_price_normalized.csv")
    if not file_path.exists():
        click.echo("Error: Data file not found for validation", err=True)
        return

    df = pd.read_csv(file_path)
    results = validator.run_suite(df, "btc_price")
    
    for r in results:
        status = "✓" if r.passed else "✗"
        click.echo(f"{status} [{r.severity.value.upper()}] {r.check_name}: {r.message}")
        if not r.passed and r.remediation:
             click.echo(f"  -> Remediation: {r.remediation}")

if __name__ == "__main__":
    cli()
