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
    
    # Count streams with actual changes that succeeded
    success_count = sum(1 for s in streams_data.values() 
                       if s['enabled'] == 'True' 
                       and s['result'] == 'Succeeded'
                       and s.get('hasChanges', 'true').lower() != 'false')
    
    failed_count = sum(1 for s in streams_data.values() 
                      if s['enabled'] == 'True' and s['result'] == 'Failed')
    
    # Count streams with no changes (hasChanges is 'false' or empty)
    no_changes_count = sum(1 for s in streams_data.values() 
                          if s['enabled'] == 'True' 
                          and (s.get('hasChanges', '').lower() == 'false' or s.get('hasChanges', '') == ''))
    
    # Streams processed = enabled streams that had changes
    processed_count = enabled_count - no_changes_count
    
    success_rate = 0
    if processed_count > 0:
        success_rate = int((success_count * 100) / processed_count)
    elif enabled_count > 0 and no_changes_count == enabled_count:
        # All enabled streams had no changes - show 100%
        success_rate = 100
    
    return {
        'total_streams': total_streams,
        'enabled_count': enabled_count,
        'success_count': success_count,
        'failed_count': failed_count,
        'no_changes_count': no_changes_count,
        'processed_count': processed_count,
        'success_rate': success_rate
    }


def get_stream_status_class(result, enabled, has_changes):
    """Get CSS class for stream status."""
    if enabled != 'True':
        return 'disabled'
    # Check if there were no changes (has_changes is 'false' string or empty)
    elif has_changes.lower() == 'false' or has_changes == '':
        return 'skipped'
    elif result == 'Succeeded':
        return 'success'
    elif result == 'Failed':
        return 'failed'
    else:
        return 'skipped'


def get_stream_badge(result, enabled, has_changes):
    """Get badge text for stream status."""
    if enabled != 'True':
        return {'class': 'badge-disabled', 'text': 'DISABLED'}
    # Check if there were no changes (has_changes is 'false' string or empty)
    elif has_changes.lower() == 'false' or has_changes == '':
        return {'class': 'badge-skipped', 'text': 'NO CHANGES'}
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
        has_changes = stream_info.get('hasChanges', 'unknown')
        streams_data[stream_name] = {
            'name': stream_name,
            'result': stream_info['result'],
            'enabled': stream_info['enabled'],
            'hasChanges': has_changes,
            'status_class': get_stream_status_class(stream_info['result'], stream_info['enabled'], has_changes),
            'badge': get_stream_badge(stream_info['result'], stream_info['enabled'], has_changes)
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
