#Fix 1.2 + 1.3 +1.4
#Lightmap Fix for some characters
#Jianxin Shapekey Sum Fix
#Verina Remap, ChangLi Remap
# Author Gustav0

#Modified by Nooble to accomodate versions 2.1 and 2.2

from struct import unpack_from
from argparse import ArgumentParser
from shutil import copy2
import re
from time import time
from zipfile import ZipFile
from pathlib import Path

from json import load
import sys

from dataclasses import dataclass
from typing import Dict, List
import logging
from os import path
from pathlib import Path

@dataclass
class HashMap:
    old_vs_new: Dict[str, Dict[str, str]]
    old_vs_new13: Dict[str, Dict[str, str]]
    old_vs_new14: Dict[str, Dict[str, str]]
    old_vs_new21: Dict[str, Dict[str, str]]
    old_vs_new22: Dict[str, Dict[str, str]]

@dataclass
class RemapData:
    character: str
    indices: List[int] | Dict[int, int]

abs_pth = path.abspath(sys.argv[0])
root_directory = path.dirname(abs_pth)

# Load hash maps from JSON file
# Update load_hash_maps function
def load_hash_maps():
    base_path = root_directory
    json_file = base_path + '/' + "hash_maps.json"
    if not file_exists(json_file):
        raise FileNotFoundError(f"hash_maps.json not found at {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = load(f)
    return HashMap(
        old_vs_new=data["old_vs_new"],
        old_vs_new13=data["old_vs_new13"],
        old_vs_new14=data["old_vs_new14"],
        old_vs_new21=data["old_vs_new21"],
        old_vs_new22=data["old_vs_new22"]
    )

# Helper function to check if a file exists
def file_exists(file_path):
    try:
        with open(file_path, 'r'):
            return True
    except FileNotFoundError:
        return False

# Update the hash_maps initialization
hash_maps = load_hash_maps()

remaps = {
    "83ced9f7": RemapData("Verina", [i for i in range(0, 195)]),
    "fd9483ca": RemapData("ChangLi", [i for i in range(0, 281)]),
    "060f5303": RemapData("Changli_1.4", {
        # Default Changli 1.4 remapping
        135: 137,
        137: 135,
        123: 124,
        124: 125,
        125: 126,
        126: 123,
        # Component remap data for unnamed mod
        "component_remap": {
            "vertex_offset": 16935,
            "indices": {
                64: 65,
                65: 66,
                66: 67,
                67: 64,
                76: 78,
                78: 76
            }
        }
    })
}


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Replace print statements with logger calls
def log_message(log, message, level=logging.INFO):
    log.append(message)
    if level == logging.ERROR:
        logger.error(message)
    elif level == logging.WARNING:
        logger.warning(message)
    else:
        logger.info(message)

# Update create_backup function
def create_backup(file_path, ini_file=False):
    backup_name = ('DISABLED ' if ini_file else '') + file_path[file_path.rfind("\\") + 1:] + '.bak'
    backup_path = file_path[:file_path.rfind("\\")] + "\\" + backup_name
    copy2(file_path, backup_path)
    return backup_path

# Update collect_ini_files function
def collect_ini_files(folder_path: str) -> List[str]:
    log_message([], f"Collecting ini files in folder: {folder_path}, please wait...")
    ini_files = []
    exclude_keywords = {'desktop', 'ntuser', 'disabled_backup', "disabled"}

    try:
        for root, dirs, files in walk_directory(folder_path):
            for file in files:
                if file.endswith('.ini') and not any(keyword in file.lower() for keyword in exclude_keywords):
                    ini_files.append(root + "\\" + file)
    except Exception:
        log_message([], f"Error: Folder {folder_path} does not exist or is not a directory.", level=logging.ERROR)
        return ini_files

    log_message([], f"Found {len(ini_files)} ini files in {folder_path}.")
    return ini_files

# Helper function to walk through directories
def walk_directory(folder_path):
    stack = [folder_path]
    while stack:
        current = stack.pop()
        try:
            entries = list_dir(current)
            dirs = [entry for entry in entries if is_directory(current + "\\" + entry)]
            files = [entry for entry in entries if not is_directory(current + "\\" + entry)]
            yield current, dirs, files
            stack.extend(current + "\\" + d for d in dirs)
        except Exception:
            continue

# Helper function to list directory contents
def list_dir(folder_path):
    try:
        return [entry for entry in __import__('os').listdir(folder_path)]
    except Exception:
        return []

# Helper function to check if a path is a directory
def is_directory(path):
    try:
        return __import__('os').path.isdir(path)
    except Exception:
        return False

# Update extract_texture_from_zip function
def extract_texture_from_zip(textures_folder, texture_name):
    try:
        root_path = __file__[:__file__.rfind("\\")]  # Directory of the script
    except Exception:
        root_path = "."  # Fallback to the current directory
    
    zip_path = root_path + "\\FixTexture.zip"
    
    try:
        with ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extract(texture_name, textures_folder)
            extracted_path = textures_folder + "\\" + texture_name
            return extracted_path
    except FileNotFoundError:
        logger.warning(f"Zip file not found: {zip_path}")
    except KeyError:
        logger.warning(f"Texture {texture_name} not found in the zip file.")
    except Exception as e:
        logger.warning(f"Failed to extract texture {texture_name}: {e}")
    
    return None  # Return None if extraction fails

def apply_lightmap_fix(file_path):
    log = []
    file_modified = False
    match_found = False
    texture_to_extract = None
    try:
        with open(file_path, 'r', encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if line.strip().startswith("[TextureOverride"):
                texture_name = line.strip()[16:-1]
                resource_section = f"[Resource{texture_name}]"

                for j in range(i + 1, min(i + 5, len(lines))):
                    if "435d999a" in lines[j] or "aeb47e33" in lines[j]:
                        match_found = True
                        texture_to_extract = process_resource_section(
                            lines, resource_section, 
                            "Textures/FaceLightMap t=e04dea55.dds"
                        )
                        file_modified = True if texture_to_extract else file_modified
                        break
                    elif "28708ab8" in lines[j]:
                        match_found = True
                        texture_to_extract = process_resource_section(
                            lines, resource_section, 
                            "Textures/FixFaceLightMapSanhua t=0bd3b5ab.dds"
                        )
                        file_modified = True if texture_to_extract else file_modified
                        break

        # Secondary search for filename entries in [ResourceTextureX] sections
        for i, line in enumerate(lines):
            if line.strip().startswith("[Resource") and "Texture" in line:
                if i + 1 < len(lines):
                    current_filename = lines[i + 1].strip()
                    if "filename = Textures/FaceLightMap t=e04dea55.dds" in current_filename:
                        match_found = True
                        texture_to_extract = "FaceLightMap t=e04dea55.dds"
                    elif "filename = Textures/FixFaceLightMapSanhua t=0bd3b5ab.dds" in current_filename:
                        match_found = True
                        texture_to_extract = "FixFaceLightMapSanhua t=0bd3b5ab.dds"

        # Check if Textures folder exists
        textures_folder = Path(file_path).parent / 'Textures'
        if match_found and texture_to_extract:
            if textures_folder.is_dir():
                texture_file = textures_folder / Path(texture_to_extract).name
                if not texture_file.is_file():
                    extracted_path = extract_texture_from_zip(textures_folder, texture_to_extract)
                    if extracted_path:
                        if file_modified:  # Filename was updated during this run
                            log_message(log, f"Extracted texture to complete update: {extracted_path.name}")
                        else:  # Filename was already correct, but texture was missing
                            log_message(log, f"Extracted missing texture: {extracted_path.name}")
                    else:
                        log_message(log, f"Failed to extract texture: {texture_to_extract}", level=logging.WARNING)
                else:
                    log_message(log, f"Texture {texture_file.name} already exists.")
            else:
                log_message(log, f"Skipped texture check: Folder 'Textures' not found.", level=logging.WARNING)

        if file_modified:
            with open(file_path, 'w', encoding="utf-8") as f:
                f.writelines(lines)
            log_message(log, f'Applied lightmap fix to: {Path(file_path).name}')
        elif not match_found:
            log_message(log, f'No matches for lightmap fix in: {Path(file_path).name}', level=logging.WARNING)

    except Exception as e:
        log_message(log, f'Error processing file: {Path(file_path).name}', level=logging.ERROR)
        log_message(log, str(e), level=logging.ERROR)

    return log, file_modified


def process_resource_section(lines, resource_section, target_filename):
    for k, line in enumerate(lines):
        if line.strip() == resource_section:
            if k + 1 < len(lines) and lines[k + 1].strip().startswith("filename ="):
                current_filename = lines[k + 1].strip()
                if current_filename != f"filename = {target_filename}":
                    lines[k + 1] = f"filename = {target_filename}\n"
                    log_message([], f"Updated: {current_filename} -> filename = {target_filename}")
                    return target_filename
                else:
                    log_message([], f"Skipped: {current_filename} (already updated)")
    return None

def ReverseCBHotFix(ini_files):
    log = []
    files_modified = 0
    
    try:
        for file_path in ini_files:
            with open(file_path, 'r', encoding="utf-8") as f:
                lines = f.readlines()
                
            file_modified = False
            for i in range(len(lines)-1):
                if "[TextureOverrideMarkBoneDataCB]" in lines[i]:
                    if "d14bed8b" in lines[i+1]:
                        lines[i+1] = lines[i+1].replace("d14bed8b", "f02baf77")
                        file_modified = True
                        
            if file_modified:
                with open(file_path, 'w', encoding="utf-8") as f:
                    f.writelines(lines)
                log_message(log, f'Applied CB hotfix to: {Path(file_path).name}')
                files_modified += 1
            else:
                log_message(log, f'No CB hotfix needed for: {Path(file_path).name}')
                
    except Exception as e:
        log_message(log, f'Error processing files')
        log_message(log, str(e))
        
    return log, files_modified > 0

def get_root_directory():
    if getattr(sys, 'frozen', False):  # Check if running as a compiled binary
        return Path(sys.executable).parent  # Path to the executable's directory
    else:
        return Path(__file__).parent  # Path to the script's directory

def apply_hash_fix(folder_path=None):
    log = []
    processed_files_count = 0

    # Default to the current working directory if no folder_path is provided
    if folder_path is None:
        folder_path = root_directory

    log_message(log, f"Processing folder: {folder_path}")
    ini_files = collect_ini_files(folder_path)
    
    if not ini_files:
        log_message(log, f"No .ini files found in {folder_path}. Ensure the directory is correct.", level=logging.WARNING)
        return log, processed_files_count, 0
    
    # Apply CB hotfix first
    cb_log, cb_modified = ReverseCBHotFix(ini_files)
    log.extend(cb_log)
    
    # Check ini files for [ResourceMergedSkeleton] for ChangLi 1.4 hashes
    use_default_remap = False
    for ini_file in ini_files:
        try:
            with open(ini_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if '[ResourceMergedSkeleton]' in content and ('060f5303' or 'fd9483ca' in content):
                    use_default_remap = True
                    break
        except Exception as e:
            log_message(log, f"Error reading {ini_file}: {str(e)}")
            continue
    
    for file_path in ini_files:
        try:
            log_message(log, f"Processing INI file: {file_path}")
        
            lightmap_log, lightmap_modified = apply_lightmap_fix(file_path)
            log.extend(lightmap_log)
            
            with open(file_path, 'r', encoding="utf-8") as f:
                s = f.read()
            meshes_folder = Path(file_path).parent / 'Meshes'
            if not meshes_folder.exists():
                log_message(log, f'Meshes folder not found in directory: {meshes_folder.parent}')
                continue

            blend_files = [blend_file for blend_file in meshes_folder.iterdir()
                           if blend_file.is_file() and
                           "blend" in blend_file.name.lower() and ".buf" in blend_file.name.lower() and
                           not blend_file.name.lower().endswith('.bak')]
            
            file_modified = lightmap_modified
            for remap_key, vg_remap in remaps.items():
                if remap_key in s:
                    if not blend_files:
                        log_message(log, f'No blend file found for {vg_remap.character} in folder: {meshes_folder}')
                        continue

                    if remap_key == "fd9483ca":
                        # Apply first remap with fd9483ca
                        log_message(log, f'Found blend files for {vg_remap.character}. Applying first remap...')
                        for blend_file in blend_files:
                            blend_file_path = blend_file
                            try:
                                # Create backup before modifying
                                backup_path = blend_file_path.with_suffix(blend_file_path.suffix + '.bak')
                                copy2(blend_file_path, backup_path)
                                log_message(log, f"Created backup: {backup_path.name}")

                                with open(blend_file_path, "rb") as g:
                                    blend_data = g.read()
                                    remap_data = remap(blend_data, vg_remap.indices, use_default_remap=use_default_remap)
                                with open(blend_file_path, "wb") as g:
                                    g.write(remap_data)
                                    log_message(log, f"File: {blend_file.name} VGs remapped successfully with fd9483ca!")
                                file_modified = True

                                # Apply second remap with 060f5303
                                log_message(log, f'Applying second remap with 060f5303...')
                                with open(blend_file_path, "rb") as g:
                                    blend_data = g.read()
                                    remap_data = remap(blend_data, remaps["060f5303"].indices, use_default_remap=use_default_remap)
                                with open(blend_file_path, "wb") as g:
                                    g.write(remap_data)
                                    log_message(log, f"File: {blend_file.name} VGs remapped successfully with 060f5303!")
                            except Exception as e:
                                log_message(log, f'Error remapping file: {blend_file.name}')
                                log_message(log, str(e))
                                continue
                    else:  
                        log_message(log, f'Found blend files for {vg_remap.character}. Applying remap...')
                        for blend_file in blend_files:
                            blend_file_path = blend_file
                            try:
                                # Create backup before modifying
                                backup_path = blend_file_path.with_suffix(blend_file_path.suffix + '.bak')
                                copy2(blend_file_path, backup_path)
                                log_message(log, f"Created backup: {backup_path.name}")

                                # Check if ChangLi 1.4 remap
                                if use_default_remap == True:
                                    log_message(log, f"Applying Merged Skeleton Remap for ChangLi 1.4")
                                else:
                                    log_message(log, f"Applying Component Remap for {vg_remap.character}")

                                with open(blend_file_path, "rb") as g:
                                    blend_data = g.read()
                                    remap_data = remap(blend_data, vg_remap.indices, use_default_remap=use_default_remap)
                                with open(blend_file_path, "wb") as g:
                                    g.write(remap_data)
                                    log_message(log, f"File: {blend_file.name} VGs remapped successfully!")
                                file_modified = True
                            except Exception as e:
                                log_message(log, f'Error remapping file: {blend_file.name}')
                                log_message(log, str(e))
                                continue

            jianxin_hashes_found = False
            changli_hash_found = False
            for version, hash_map in [("1.2", hash_maps.old_vs_new), 
                                      ("1.3", hash_maps.old_vs_new13), 
                                      ("1.4", hash_maps.old_vs_new14), 
                                      ("2.1", hash_maps.old_vs_new21), 
                                      ("2.2", hash_maps.old_vs_new22)]:
                for character, mappings in hash_map.items():
                    for old, new in mappings.items():
                        # Skip Cantarella hash changes under sections starting with [Resource
                        if character == "Cantarella":
                            lines = s.split('\n')
                            in_resource_section = False
                            for line in lines:
                                if line.strip().startswith("[Resource"):
                                    in_resource_section = True
                                elif line.strip().startswith("[") and not line.strip().startswith("[Resource"):
                                    in_resource_section = False

                                if in_resource_section and re.search(rf'^hash\s*=\s*{re.escape(old.lower())}', line, re.IGNORECASE):
                                    log_message(log, f"Skipped Cantarella hash change ({old} -> {new}) in [Resource] section.", level=logging.WARNING)
                                    break
                            else:
                                # Apply Cantarella hash change if not in a [Resource] section
                                pattern = rf'^hash\s*=\s*{re.escape(old.lower())}'
                                matches = re.findall(pattern, s, re.MULTILINE | re.IGNORECASE)
                                occurrences = len(matches)
                                if occurrences > 0:
                                    s = re.sub(pattern, f'hash = {new.lower()}', s, flags=re.MULTILINE | re.IGNORECASE)
                                    log_message(log, f'[Fix {version}] Found {old} ({occurrences} valid occurrences) ------> Match! to {new} for {character}!')
                                    file_modified = True
                                    version_modified = True
                                continue

                        # Apply hash changes for other characters
                        pattern = rf'^hash\s*=\s*{re.escape(old.lower())}'
                        matches = re.findall(pattern, s, re.MULTILINE | re.IGNORECASE)
                        occurrences = len(matches)
                        if occurrences > 0:
                            s = re.sub(pattern, f'hash = {new.lower()}', s, flags=re.MULTILINE | re.IGNORECASE)
                            log_message(log, f'[Fix {version}] Found {old} ({occurrences} valid occurrences) ------> Match! to {new} for {character}!')
                            file_modified = True
                            version_modified = True
                            if character == "Jianxin" and old in ["affc2fc3", "ead048c8"]:
                                jianxin_hashes_found = True
                            if character == "ChangLi" and (old in ["5f8aac45", "060f5303"] or new in ["d14bed8b", "277e18c9"]):
                                changli_hash_found = True
                        elif re.search(rf'^hash\s*=\s*{re.escape(new.lower())}', s, re.MULTILINE | re.IGNORECASE):
                            new_occurrences = len(re.findall(rf'^hash\s*=\s*{re.escape(new.lower())}', s, re.MULTILINE | re.IGNORECASE))
                            if old == "435d999a" or old == "aeb47e33":
                                log_message(log, f'[Fix {version}] Found {new} ({new_occurrences} valid occurrences) ------> Already remapped for Yinlin, YangYan, Chixia, JianXin and More!')
                            else:
                                log_message(log, f'[Fix {version}] Found {new} ({new_occurrences} valid occurrences) ------> Already remapped for {character}!')
                            if character == "Jianxin" and old in ["affc2fc3", "ead048c8"]:
                                jianxin_hashes_found = True
                            if character == "ChangLi" and (old in ["5f8aac45", "060f5303"] or new in ["d14bed8b", "277e18c9"]):
                                changli_hash_found = True
                        
            # Special handling for Jianxin Shapekey sum, thank you Spectrum :3
            if jianxin_hashes_found:
                lines = s.split('\n')
                shapekey_line_found = False
                for i, line in enumerate(lines):
                    if line.strip().startswith("$\\WWMIv1\\shapekey_checksum"):
                        lines[i] = "$\\WWMIv1\\shapekey_checksum = 1876"
                        log_message(log, f'Updated shapekey_checksum for Jianxin')
                        file_modified = True
                        shapekey_line_found = True
                        break
                if not shapekey_line_found:
                    log_message(log, f'Warning: shapekey_checksum line not found for Jianxin', level=logging.WARNING)
                s = '\n'.join(lines)

            # Special handling for Changli indices
            if changli_hash_found:
                log_message(log, "Starting match fixes for Changli")
                lines = s.split('\n')
                modified_lines = []
                indices_modified = False
                for line in lines:
                    if line.strip().startswith("match_index_count") and "81513" in line:
                        modified_line = line.replace("81513", "82533")
                        log_message(log, f'Changed match_index_count from 81513 to 82533')
                        modified_lines.append(modified_line)
                        indices_modified = True
                    elif line.strip().startswith("match_first_index"):
                        if "152343" in line:
                            modified_line = line.replace("152343", "153363")
                            log_message(log, f'Changed match_first_index from 152343 to 153363')
                            modified_lines.append(modified_line)
                            indices_modified = True
                        elif "198855" in line:
                            modified_line = line.replace("198855", "199875")
                            log_message(log, f'Changed match_first_index from 198855 to 199875')
                            modified_lines.append(modified_line)
                            indices_modified = True
                        elif "283461" in line:
                            modified_line = line.replace("283461", "284481")
                            log_message(log, f'Changed match_first_index from 283461 to 284481')
                            modified_lines.append(modified_line)
                            indices_modified = True
                        elif "285489" in line:
                            modified_line = line.replace("285489", "286509")
                            log_message(log, f'Changed match_first_index from 285489 to 286509')
                            modified_lines.append(modified_line)
                            indices_modified = True
                        else:
                            modified_lines.append(line)
                    else:
                        modified_lines.append(line)
                s = '\n'.join(modified_lines)
                if indices_modified:
                    log_message(log, f'Updated indices for Changli')
                    file_modified = True

            if file_modified:
                backup_ini = create_backup(file_path, ini_file=True)
                log_message(log, f"Backup created: {backup_ini}")
                with open(file_path, 'w', encoding="utf-8") as f:
                    f.write(s)
                log_message(log, f'File: {Path(file_path).name} has been modified!')
                processed_files_count += 1
            else:
                log_message(log, f'File: {Path(file_path).name} had no matches. Skipping')

        except Exception as e:
            log_message(log, f'Error processing file: {Path(file_path).name}', level=logging.ERROR)
            log_message(log, str(e), level=logging.ERROR)
            continue
        log_message(log, "=" * 70)
    
    return log, processed_files_count, len(ini_files)
def remap_verina(folder_path):
    return apply_hash_fix(folder_path)

def remap(blend_data, new_order, stride=8, use_default_remap=False):
    if len(blend_data) % stride != 0:
        raise ValueError("Invalid blend file length")

    remapped_blend = bytearray()

    if isinstance(new_order, dict):
        if use_default_remap:
            # Use default Changli 1.4 remapping
            for i in range(0, len(blend_data), stride):
                blendindices = unpack_from("<BBBB", blend_data, i)
                blendweights = blend_data[i + 4:i + 8]

                outputindices = bytearray()
                for index in blendindices:
                    # Only use the top-level remapping indices
                    remapped_index = new_order.get(index, index) if not isinstance(new_order.get(index), dict) else index
                    outputindices.append(remapped_index)

                remapped_blend += outputindices + blendweights
        else:
            # Use component remap
            comp_remap = new_order["component_remap"]
            offset = comp_remap["vertex_offset"] * stride
            indices_map = comp_remap["indices"]

            # Copy data before component unchanged
            remapped_blend += blend_data[:offset]

            # Remap the component
            for i in range(offset, len(blend_data), stride):
                blendindices = unpack_from("<BBBB", blend_data, i)
                blendweights = blend_data[i + 4:i + 8]

                outputindices = bytearray()
                for index in blendindices:
                    remapped_index = indices_map.get(index, index)
                    outputindices.append(remapped_index)

                remapped_blend += outputindices + blendweights
    else:
        # Handle list-based remapping
        for i in range(0, len(blend_data), stride):
            blendindices = unpack_from("<BBBB", blend_data, i)
            blendweights = blend_data[i + 4:i + 8]

            outputindices = bytearray()
            for index in blendindices:
                remapped_index = new_order[index] if index < len(new_order) else index
                outputindices.append(remapped_index)

            remapped_blend += outputindices + blendweights

    if len(remapped_blend) != len(blend_data):
        raise ValueError("Remapped blend file is invalid")
    
    return remapped_blend



def remap_verina(folder_path):
    return apply_hash_fix(folder_path)

def remap(blend_data, new_order, stride=8, use_default_remap=False):
    if len(blend_data) % stride != 0:
        raise ValueError("Invalid blend file length")

    remapped_blend = bytearray()

    if isinstance(new_order, dict):
        if use_default_remap:
            # Use default Changli 1.4 remapping
            for i in range(0, len(blend_data), stride):
                blendindices = unpack_from("<BBBB", blend_data, i)
                blendweights = blend_data[i + 4:i + 8]

                outputindices = bytearray()
                for index in blendindices:
                    # Only use the top-level remapping indices
                    remapped_index = new_order.get(index, index) if not isinstance(new_order.get(index), dict) else index
                    outputindices.append(remapped_index)

                remapped_blend += outputindices + blendweights
        else:
            # Use component remap
            comp_remap = new_order["component_remap"]
            offset = comp_remap["vertex_offset"] * stride
            indices_map = comp_remap["indices"]

            # Copy data before component unchanged
            remapped_blend += blend_data[:offset]

            # Remap the component
            for i in range(offset, len(blend_data), stride):
                blendindices = unpack_from("<BBBB", blend_data, i)
                blendweights = blend_data[i + 4:i + 8]

                outputindices = bytearray()
                for index in blendindices:
                    remapped_index = indices_map.get(index, index)
                    outputindices.append(remapped_index)

                remapped_blend += outputindices + blendweights
    else:
        # Handle list-based remapping
        for i in range(0, len(blend_data), stride):
            blendindices = unpack_from("<BBBB", blend_data, i)
            blendweights = blend_data[i + 4:i + 8]

            outputindices = bytearray()
            for index in blendindices:
                remapped_index = new_order[index] if index < len(new_order) else index
                outputindices.append(remapped_index)

            remapped_blend += outputindices + blendweights

    if len(remapped_blend) != len(blend_data):
        raise ValueError("Remapped blend file is invalid")
    
    return remapped_blend

def force_remap(folder):
    '''Force remap a character based on the remap options.'''
    log = []
    processed_files_count = 0
    log_message(log, 'Remap options:')
    for i, (k, v) in enumerate(remaps.items()):
        log_message(log, f'{i+1}: {v.character}')

    while True:
        try:
            option = int(input('Select a character to remap: ')) - 1
            if 0 <= option < len(remaps):
                break
            print('Invalid option')
        except ValueError:
            print('Invalid option')

    option_key = list(remaps.keys())[option]
    
    use_default_remap = False
    if remaps[option_key].character == "Changli_1.4":
        log_message(log, "\nSelect remap type for Changli 1.4:")
        log_message(log, "1: Merged")
        log_message(log, "2: Component")
        while True:
            try:
                remap_type = int(input('Select remap type (1 or 2): '))
                if remap_type in [1, 2]:
                    use_default_remap = (remap_type == 1)
                    break
                print('Invalid option')
            except ValueError:
                print('Invalid option')

    files = list(Path(folder).iterdir())
    blend_files = [file for file in files if file.is_file() and file.suffix == '.buf' and 'blend' in file.name.lower()]
    
    if len(blend_files) > 1:
        log_message(log, "Multiple blend.buf files found. Aborting to prevent unsafe modifications.")
        return log, processed_files_count, len(blend_files)
    
    if blend_files:
        bak_files = [file for file in files if file.suffix == '.bak']
        if not bak_files:
            for blend_file in blend_files:
                try:
                    backup_file = blend_file.with_suffix(blend_file.suffix + '.bak')
                    copy2(blend_file, backup_file)
                    log_message(log, f"Backup created: {backup_file}")

                    with open(blend_file, "rb") as g:
                        blend_data = g.read()
                        remap_data = remap(blend_data, remaps[option_key].indices, use_default_remap=use_default_remap)

                    with open(blend_file, "wb") as g:
                        g.write(remap_data)
                    log_message(log, f"File: {blend_file.name} VGs remapped successfully!")
                    processed_files_count += 1

                except Exception as e:
                    log_message(log, f'Error processing file: {blend_file.name}')
                    log_message(log, str(e))
        else:
            log_message(log, f'Found .bak files in {folder}. Skipping remapping for this folder.')
    else:
        log_message(log, f"No blend files found in folder: {folder}")

    return log, processed_files_count, len(blend_files)

# Update the main function to use the current directory and its subdirectories
if __name__ == '__main__':
    try:
        parser = ArgumentParser()
        parser.add_argument('--force_remap', action='store_true', default=False)
        args = parser.parse_args()
        start_time = time()

        if args.force_remap:
            log, processed_files_count, total_files = force_remap(root_directory)
        else:
            log, processed_files_count, total_files = apply_hash_fix(root_directory)
        
        end_time = time()
        elapsed_time = end_time - start_time
        print(f"\nProcessing took {elapsed_time:.2f} seconds")
        print(f"Total files found: {total_files}")
        print(f"Processed {processed_files_count} files")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        input("Press Enter to exit...")  # Pause for unexpected errors
    else:
        input("Press Enter to exit...")
