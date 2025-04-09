import os
from PIL import Image
import io
from werkzeug.datastructures import FileStorage


def file_storage_to_bytes(file_storage: FileStorage) -> bytes:
    # Reset the file pointer to beginning in case it was read before
    file_storage.seek(0)

    # Read the file data into bytes
    file_bytes = file_storage.read()

    # Reset the file pointer again for good practice
    file_storage.seek(0)

    return file_bytes


def save_image(name, image_blob):
    try:
        # Convert file storage to bytes if needed
        if hasattr(image_blob, 'read'):  # If it's a FileStorage object
            image_blob = image_blob.read()

        # Create directories if they don't exist
        base_dir = "saved_images"
        save_dir = os.path.join(base_dir, name)
        os.makedirs(save_dir, exist_ok=True)

        # Find the next available number for the image
        existing_files = [f for f in os.listdir(save_dir)
                          if f.startswith(f"{name}_") and f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        # Extract numbers from existing files
        existing_numbers = []
        for f in existing_files:
            try:
                num = int(f.split('_')[1].split('.')[0])
                existing_numbers.append(num)
            except (IndexError, ValueError):
                continue

        # Determine next available number
        image_number = max(existing_numbers) + 1 if existing_numbers else 1

        # Create filename with padded zeros (optional)
        file_path = os.path.join(save_dir, f"{name}_{image_number:04d}.jpg")

        # Open and process image
        image = Image.open(io.BytesIO(image_blob))

        # Convert RGBA to RGB if needed
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        # Save image
        image.save(file_path, 'JPEG', quality=95)
        return True

    except Exception as e:
        print(f"Error saving image: {str(e)}")
        return False
