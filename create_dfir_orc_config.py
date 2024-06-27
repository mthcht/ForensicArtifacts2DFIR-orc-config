import os
import yaml
import argparse
import requests
import zipfile
import io
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

GITHUB_REPO_URL = "https://github.com/ForensicArtifacts/artifacts/archive/refs/heads/main.zip"
DEFAULT_INPUT_DIR = "ForensicArtifacts_to_convert"
DEFAULT_OUTPUT_DIR = "DFIR-ORC-Config"

def download_and_extract_artifacts(url, extract_to):
    logging.info(f"Downloading artifacts from {url}...")
    response = requests.get(url)
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(extract_to)
        logging.info(f"Artifacts downloaded and extracted to {extract_to}")
    else:
        logging.error(f"Failed to download artifacts: {response.status_code}")

def prettify_xml(element):
    """Return a pretty-printed XML string for the Element."""
    rough_string = tostring(element, 'utf-8')
    reparsed = parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")

def replace_windows_vars(path):
    windows_env_vars = {
        '%%environ_allusersappdata%%': 'ProgramData',
        '%%environ_allusersprofile%%': 'ProgramData',
        '%%environ_programdata%%': 'ProgramData',
        '%%environ_programfiles%%': 'Program Files',
        '%%environ_programfilesx86%%': 'Program Files (x86)',
        '%%environ_systemdrive%%': '',
        '%%environ_systemroot%%': 'Windows',
        '%%environ_windir%%': 'Windows',
        '%%users.appdata%%': 'Users\\*\\AppData\\Roaming',
        '%%users.localappdata%%': 'Users\\*\\AppData\\Local',
        '%%users.temp%%': 'Users\\*\\AppData\\Local\\Temp',
        '%%users.userprofile%%': 'Users\\*',
        '%%users.sid%%': '*'
    }
    for var, replacement in windows_env_vars.items():
        path = path.replace(var, replacement)
    return path.lstrip('\\')

def convert_yaml_to_orc(yaml_file_path, output_dir):
    try:
        with open(yaml_file_path, 'r') as yaml_file:
            yaml_content = yaml.safe_load_all(yaml_file)
            for doc in yaml_content:
                if not doc or 'sources' not in doc:
                    logging.warning(f"No valid sources in {yaml_file_path}")
                    continue

                if 'supported_os' not in doc or 'Windows' not in doc['supported_os']:
                    logging.info(f"Skipping non-Windows artifact in {yaml_file_path} - supported os {doc['supported_os']}")
                    continue

                valid_sources = [source for source in doc['sources'] if source['type'] in ['FILE', 'REGISTRY_KEY', 'REGISTRY_VALUE']]
                if not valid_sources:
                    logging.warning(f"No valid sources in {yaml_file_path}")
                    continue

                root = Element('getthis', reportall="")
                SubElement(root, 'output', compression="fast")

                is_file_source = any(source['type'] == 'FILE' for source in valid_sources)
                if is_file_source:
                    SubElement(root, 'location').text = "%SystemDrive%\\"

                def add_sample(doc_name, paths, output_element):
                    for path in paths:
                        sample = SubElement(output_element, 'sample', name=doc_name)
                        SubElement(sample, 'ntfs_find', path_match=path)

                for source in valid_sources:
                    source_type = source['type']
                    attributes = source.get('attributes', {})

                    if source_type == 'REGISTRY_VALUE':
                        for pair in attributes.get('key_value_pairs', []):
                            sample = SubElement(root, 'sample', name=doc['name'])
                            SubElement(sample, 'reg_find', hive=pair['key'].split('\\')[0], key='\\'.join(pair['key'].split('\\')[1:]), value=pair['value'])

                    elif source_type == 'REGISTRY_KEY':
                        for key in attributes.get('keys', []):
                            sample = SubElement(root, 'sample', name=doc['name'])
                            SubElement(sample, 'reg_list', hive=key.split('\\')[0], key='\\'.join(key.split('\\')[1:]))

                    elif source_type == 'FILE':
                        for path in attributes.get('paths', []):
                            windows_paths = [replace_windows_vars(path.replace('C:\\', '').replace('/', '\\'))]
                            add_sample(doc['name'], windows_paths, root)
                    else:
                        logging.warning(f"Unknown source type {source_type} in {yaml_file_path}")

                xml_str = prettify_xml(root)
                xml_filename = f"{doc['name']}.xml"
                xml_file_path = os.path.join(output_dir, xml_filename)
                with open(xml_file_path, 'w') as xml_file:
                    xml_file.write(xml_str)
                logging.info(f"Converted {yaml_file_path} to {xml_file_path}")

    except Exception as e:
        logging.error(f"Failed to convert {yaml_file_path}: {e}")

def process_directory(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.yml') or file.endswith('.yaml'):
                yaml_file_path = os.path.join(root, file)
                convert_yaml_to_orc(yaml_file_path, output_dir)

def main():
    parser = argparse.ArgumentParser(description="Convert YAML files to DFIR ORC XML format.")
    parser.add_argument('input_dir', nargs='?', default=DEFAULT_INPUT_DIR, help="The input directory containing YAML files (can contain subdirectories).")
    parser.add_argument('output_dir', nargs='?', default=DEFAULT_OUTPUT_DIR, help="The output directory for the converted XML files.")
    parser.add_argument('--auto', action='store_true', help="Automatically download and extract artifacts.")

    args = parser.parse_args()

    if args.auto:
        if not os.path.exists(DEFAULT_INPUT_DIR):
            os.makedirs(DEFAULT_INPUT_DIR)
        download_and_extract_artifacts(GITHUB_REPO_URL, DEFAULT_INPUT_DIR)

    process_directory(args.input_dir, args.output_dir)

if __name__ == "__main__":
    main()
