#!/usr/bin/env python3
"""
Check all localization keys in handlers against ru.yml
"""
import re
import yaml
from pathlib import Path

def get_all_keys_from_yaml(yaml_file):
    """Get all keys from YAML file."""
    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    def flatten_keys(d, prefix=''):
        """Recursively flatten nested dict keys."""
        keys = []
        for k, v in d.items():
            new_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                keys.extend(flatten_keys(v, new_key))
            else:
                keys.append(new_key)
        return keys
    
    return set(flatten_keys(data))

def get_all_used_keys(handlers_dir):
    """Get all localization keys used in handlers."""
    used_keys = set()
    pattern = r'MessageLoader\.get_message\(["\']([^"\']+)["\']'
    pattern2 = r'localization\.get_text\(["\']([^"\']+)["\']'
    
    for py_file in Path(handlers_dir).rglob('*.py'):
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
            matches = re.findall(pattern, content)
            matches2 = re.findall(pattern2, content)
            used_keys.update(matches)
            used_keys.update(matches2)
    
    return used_keys

if __name__ == '__main__':
    yaml_file = 'locales/ru.yml'
    handlers_dir = 'src/handlers'
    
    print("🔍 Checking localization keys...")
    
    available_keys = get_all_keys_from_yaml(yaml_file)
    used_keys = get_all_used_keys(handlers_dir)
    
    missing_keys = used_keys - available_keys
    
    if missing_keys:
        print(f"\n❌ Missing {len(missing_keys)} keys in {yaml_file}:")
        for key in sorted(missing_keys):
            print(f"  - {key}")
    else:
        print(f"\n✅ All {len(used_keys)} used keys are present in {yaml_file}")
    
    # Show unused keys (optional)
    unused_keys = available_keys - used_keys
    if unused_keys:
        print(f"\nℹ️  {len(unused_keys)} unused keys (can be cleaned up):")
        for key in sorted(list(unused_keys)[:10]):  # Show first 10
            print(f"  - {key}")
        if len(unused_keys) > 10:
            print(f"  ... and {len(unused_keys) - 10} more")
