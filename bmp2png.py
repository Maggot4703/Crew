import os
from PIL import Image

def convert_bmp_to_png(input_folder, output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Walk through the input folder and its subfolders
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith('.bmp'):
                # Construct the full file path
                input_path = os.path.join(root, file)
                # Construct the output file path
                relative_path = os.path.relpath(root, input_folder)
                output_subfolder = os.path.join(output_folder, relative_path)
                if not os.path.exists(output_subfolder):
                    os.makedirs(output_subfolder)
                output_path = os.path.join(output_subfolder, file.replace('.bmp', '.png'))

                # Open the BMP file and convert to PNG
                with Image.open(input_path) as img:
                    img.save(output_path, 'PNG')
                print(f'Converted {input_path} to {output_path}')

def convert_bmp_to_png_in_multiple_folders(folder_list, output_folder):
    for folder in folder_list:
        convert_bmp_to_png(folder, output_folder)

# Example usage
folders_to_convert = ['folder1', 'folder2', 'folder3']
output_folder = 'converted_images'
convert_bmp_to_png_in_multiple_folders(folders_to_convert, output_folder)
