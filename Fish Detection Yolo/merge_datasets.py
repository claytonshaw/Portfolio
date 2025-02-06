#!/usr/bin/env python3
import os
import yaml
import shutil
import glob

def update_yaml(current_yaml_path, new_yaml_path, output_yaml_path):
    """
    Loads the current and new YAML files, compares their "names" lists,
    and updates the current YAML's names with any new labels.
    Also updates the number of classes ("nc") and the train/val paths.
    Returns a mapping for the new dataset label indices.
    """
    with open(current_yaml_path, 'r') as f:
        current_data = yaml.safe_load(f)
    with open(new_yaml_path, 'r') as f:
        new_data = yaml.safe_load(f)

    current_names = current_data.get('names', [])
    new_names = new_data.get('names', [])

    # Build a mapping from new dataset label indices to merged dataset label indices.
    mapping = {}  # mapping[new_dataset_index] = merged_index
    for i, new_label in enumerate(new_names):
        if new_label in current_names:
            mapping[i] = current_names.index(new_label)
        else:
            new_index = len(current_names)
            current_names.append(new_label)
            mapping[i] = new_index

    current_data['names'] = current_names
    current_data['nc'] = len(current_names)

    # Update train/val keys to match the merged dataset structure.
    # We want the merged YAML to point to "train/images" and "valid/images".
    if 'train' in current_data:
        current_data['train'] = os.path.join('train', 'images')
    if 'val' in current_data:
        current_data['val'] = os.path.join('valid', 'images')

    with open(output_yaml_path, 'w') as f:
        yaml.dump(current_data, f)

    return mapping

def update_new_labels(new_labels_dir, mapping, output_labels_dir):
    """
    Processes each label file in the new dataset (train or valid):
      - Reads the file (YOLO format: label_id followed by bounding box coordinates).
      - Replaces the original label id with the new merged id using the provided mapping.
      - Writes the updated file to the output labels directory.
    """
    os.makedirs(output_labels_dir, exist_ok=True)
    for label_file in glob.glob(os.path.join(new_labels_dir, '*.txt')):
        with open(label_file, 'r') as f:
            lines = f.readlines()

        updated_lines = []
        for line in lines:
            if line.strip() == "":
                continue
            parts = line.strip().split()
            old_label_id = int(parts[0])
            new_label_id = mapping.get(old_label_id, old_label_id)
            parts[0] = str(new_label_id)
            updated_lines.append(" ".join(parts))

        base_name = os.path.basename(label_file)
        output_file = os.path.join(output_labels_dir, base_name)
        with open(output_file, 'w') as f:
            f.write("\n".join(updated_lines))

def copy_dataset_files(source_dir, output_dir, file_extension=None):
    """
    Copies files from the source directory to the output directory.
    If file_extension is specified, only files with that extension are copied.
    """
    os.makedirs(output_dir, exist_ok=True)
    for file in os.listdir(source_dir):
        if file_extension and not file.endswith(file_extension):
            continue
        src = os.path.join(source_dir, file)
        dst = os.path.join(output_dir, file)
        shutil.copy(src, dst)

def merge_datasets(config):
    # Derive dataset paths from the root folders.
    current_root = config['current_root']
    new_root = config['new_root']
    output_dir = config['output_dir']

    # Assume each dataset uses the following structure:
    #   <root>/data.yaml
    #   <root>/train/images, <root>/train/labels
    #   <root>/valid/images, <root>/valid/labels

    current_yaml = os.path.join(current_root, "data.yaml")
    new_yaml = os.path.join(new_root, "data.yaml")

    current_train_images = os.path.join(current_root, "train", "images")
    current_train_labels = os.path.join(current_root, "train", "labels")
    new_train_images = os.path.join(new_root, "train", "images")
    new_train_labels = os.path.join(new_root, "train", "labels")

    current_valid_images = os.path.join(current_root, "valid", "images")
    current_valid_labels = os.path.join(current_root, "valid", "labels")
    new_valid_images = os.path.join(new_root, "valid", "images")
    new_valid_labels = os.path.join(new_root, "valid", "labels")

    # Define output directories for the merged dataset in the desired format:
    # merged_dataset/train/images, merged_dataset/train/labels, etc.
    output_train_images_dir = os.path.join(output_dir, "train", "images")
    output_train_labels_dir = os.path.join(output_dir, "train", "labels")
    output_valid_images_dir = os.path.join(output_dir, "valid", "images")
    output_valid_labels_dir = os.path.join(output_dir, "valid", "labels")

    os.makedirs(output_train_images_dir, exist_ok=True)
    os.makedirs(output_train_labels_dir, exist_ok=True)
    os.makedirs(output_valid_images_dir, exist_ok=True)
    os.makedirs(output_valid_labels_dir, exist_ok=True)

    # Update the YAML file and get the mapping for new dataset labels.
    output_yaml_path = os.path.join(output_dir, "data.yaml")
    mapping = update_yaml(current_yaml, new_yaml, output_yaml_path)
    print("New dataset label mapping:", mapping)

    # Process training set: update new dataset labels and copy images and labels.
    update_new_labels(new_train_labels, mapping, output_train_labels_dir)
    copy_dataset_files(current_train_labels, output_train_labels_dir, file_extension='.txt')
    copy_dataset_files(current_train_images, output_train_images_dir)
    copy_dataset_files(new_train_images, output_train_images_dir)

    # Process validation set: update new dataset labels and copy images and labels.
    update_new_labels(new_valid_labels, mapping, output_valid_labels_dir)
    copy_dataset_files(current_valid_labels, output_valid_labels_dir, file_extension='.txt')
    copy_dataset_files(current_valid_images, output_valid_images_dir)
    copy_dataset_files(new_valid_images, output_valid_images_dir)

    print("Datasets merged successfully.")
    print("Updated YAML file written to:", output_yaml_path)

if __name__ == '__main__':
    # Prompt the user for the three root paths.
    current_root = input("Enter the current dataset root directory (e.g., aquarium_pretrain): ").strip()
    new_root = input("Enter the new dataset root directory (e.g., fish-dataset): ").strip()
    output_dir = input("Enter the output directory for the merged dataset: ").strip()

    config = {
        'current_root': current_root,
        'new_root': new_root,
        'output_dir': output_dir
    }

    merge_datasets(config)
