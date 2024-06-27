# ForensicArtifacts to DFIR-orc-config
## DFIR ORC Artifact Converter
The script `create_dfir_orc_config.py` converts artifact definitions from YAML format to DFIR ORC XML format. The script is specifically designed to process artifact definitions from the [ForensicArtifacts](https://github.com/ForensicArtifacts/artifacts) repository, focusing only on Windows artifacts.

DFIR-ORC is a forensic artifact collecter for Windows system: https://github.com/DFIR-ORC/dfir-orc

### Requierement
Required Python libraries: requests, pyyaml


### Automatic Download and Conversion
To automatically download the artifact definitions and convert them to DFIR ORC XML format:
```python
python3 artefacttoorc.py --auto
```
The converted files will be saved in the DFIR-ORC-Config directory.

To convert artifact definitions from a specified input directory to a specified output directory:
```python
python3 artefacttoorc.py path/to/input_dir path/to/output_dir
```

- path/to/input_dir: The input directory containing YAML files (can contain subdirectories). Defaults to ForensicArtifacts_to_convert.
- path/to/output_dir: The output directory for the converted XML files. Defaults to DFIR-ORC-Config.
- `--auto`: Automatically download and extract artifacts from the ForensicArtifacts repository.

