#!/usr/bin/env python3
"""
Generate MAGNUM Retrofit HTML Report using Jinja2 template.

This script generates an HTML report for LQA Retrofit operations
based on stream results and statistics.
"""

import json
import sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


def calculate_statistics(streams_data):
    """Calculate statistics from streams data."""
    total_streams = len(streams_data)
    enabled_count = sum(1 for s in streams_data.values() if s['enabled'] == 'True')
    success_count = sum(1 for s in streams_data.values() 
                       if s['enabled'] == 'True' and s['result'] == 'Succeeded')
    failed_count = sum(1 for s in streams_data.values() 
                      if s['enabled'] == 'True' and s['result'] == 'Failed')
    skipped_count = sum(1 for s in streams_data.values() 
                       if s['enabled'] == 'True' and s['result'] not in ['Succeeded', 'Failed'])
    
    success_rate = 0
    if enabled_count > 0:
        success_rate = int((success_count * 100) / enabled_count)
    
    return {
        'total_streams': total_streams,
        'enabled_count': enabled_count,
        'success_count': success_count,
        'failed_count': failed_count,
        'skipped_count': skipped_count,
        'success_rate': success_rate
    }


def get_stream_status_class(result, enabled):
    """Get CSS class for stream status."""
    if enabled != 'True':
        return 'disabled'
    elif result == 'Succeeded':
        return 'success'
    elif result == 'Failed':
        return 'failed'
    else:
        return 'skipped'


def get_stream_badge(result, enabled):
    """Get badge text for stream status."""
    if enabled != 'True':
        return {'class': 'badge-disabled', 'text': 'DISABLED'}
    elif result == 'Succeeded':
        return {'class': 'badge-success', 'text': 'SUCCESS'}
    elif result == 'Failed':
        return {'class': 'badge-failed', 'text': 'FAILED'}
    else:
        return {'class': 'badge-skipped', 'text': 'SKIPPED'}


def main():
    """Main function to generate HTML report."""
    if len(sys.argv) < 2:
        print("Usage: generate_retrofit_report.py <config_json>", file=sys.stderr)
        sys.exit(1)
    
    # Load configuration from JSON
    config_path = Path(sys.argv[1])
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Prepare streams data
    streams_data = {}
    for stream_name, stream_info in config['streams'].items():
        streams_data[stream_name] = {
            'name': stream_name,
            'result': stream_info['result'],
            'enabled': stream_info['enabled'],
            'status_class': get_stream_status_class(stream_info['result'], stream_info['enabled']),
            'badge': get_stream_badge(stream_info['result'], stream_info['enabled'])
        }
    
    # Calculate statistics
    stats = calculate_statistics(streams_data)
    
    # Setup Jinja2 environment
    # Template is in the resources directory
    script_dir = Path(__file__).parent
    resources_dir = script_dir / 'resources'
    
    env = Environment(
        loader=FileSystemLoader(str(resources_dir)),
        autoescape=select_autoescape(['html', 'xml'])
    )
    
    # Load template
    template = env.get_template('retrofit_report_template.html')
    
    # Render template
    html_output = template.render(
        retrofit_date=config['retrofit_date'],
        source_branch=config['source_branch'],
        build_number=config['build_number'],
        build_url=config['build_url'],
        dry_run=config['dry_run'],
        stats=stats,
        streams=streams_data
    )
    
    # Write output
    output_path = Path(config['output_file'])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print(f"Report generated successfully: {output_path}")
    return output_path


if __name__ == '__main__':
    main()
