import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF

def create_test_files():
    """
    Create test files for document upload testing.
    """
    print("Creating test files...")
    
    # Create test_files directory if it doesn't exist
    test_files_dir = Path(__file__).parent / "test_files"
    test_files_dir.mkdir(exist_ok=True)
    
    # Create test PDF
    create_test_pdf(test_files_dir / "test.pdf")
    
    # Create test Markdown
    create_test_markdown(test_files_dir / "test.md")
    
    # Create test image
    create_test_image(test_files_dir / "test.jpg")
    
    print("Test files created successfully!")

def create_test_pdf(filepath):
    """
    Create a test PDF file with multiple pages and embedded images.
    """
    print(f"Creating test PDF at {filepath}...")
    
    # Create a new PDF document
    doc = fitz.open()
    
    # Add a few pages with text and images
    for i in range(3):
        page = doc.new_page()
        
        # Add text to the page
        text = f"This is page {i+1} of the test PDF document.\n\n"
        text += "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        text += "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
        text += "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
        text += "nisi ut aliquip ex ea commodo consequat.\n\n"
        text += f"Page {i+1} contains test content for document processing."
        
        # Insert text
        page.insert_text((50, 50), text, fontsize=11)
        
        # Create a simple image and embed it
        img_path = create_temp_image(f"Image {i+1}")
        img_rect = fitz.Rect(50, 200, 250, 350)
        page.insert_image(img_rect, filename=img_path)
        
        # Clean up the temporary image
        os.remove(img_path)
    
    # Save the PDF
    doc.save(filepath)
    doc.close()

def create_test_markdown(filepath):
    """
    Create a test Markdown file.
    """
    print(f"Creating test Markdown at {filepath}...")
    
    content = """# Test Markdown Document

This is a test markdown document for testing document processing.

## Section 1

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

## Section 2

* Item 1
* Item 2
* Item 3

## Section 3

This is a code block:

```python
def hello_world():
    print("Hello, world!")
```

## Conclusion

This document is used for testing the document processing functionality.
"""
    
    with open(filepath, 'w') as f:
        f.write(content)

def create_test_image(filepath):
    """
    Create a test image with text for OCR testing.
    """
    print(f"Creating test image at {filepath}...")
    
    # Create a new image with white background
    width, height = 800, 600
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a font that's likely to be available
    try:
        font = ImageFont.truetype("Arial", 24)
    except IOError:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Add text to the image
    text = "This is a test image for OCR processing."
    draw.text((50, 50), text, fill='black', font=font)
    
    text = "It contains text that should be extractable."
    draw.text((50, 100), text, fill='black', font=font)
    
    text = "Instant-RAG Document Processing Test"
    draw.text((50, 200), text, fill='black', font=font)
    
    # Save the image
    image.save(filepath)

def create_temp_image(text):
    """
    Create a temporary image with the given text.
    
    Args:
        text: Text to display in the image
        
    Returns:
        Path to the temporary image
    """
    # Create a new image with white background
    width, height = 200, 150
    image = Image.new('RGB', (width, height), color='lightblue')
    draw = ImageDraw.Draw(image)
    
    # Try to use a font that's likely to be available
    try:
        font = ImageFont.truetype("Arial", 16)
    except IOError:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Add text to the image
    draw.text((20, 20), text, fill='black', font=font)
    draw.text((20, 50), "Test Image", fill='black', font=font)
    
    # Save the image to a temporary file
    temp_path = "temp_image.png"
    image.save(temp_path)
    
    return temp_path

if __name__ == "__main__":
    create_test_files()
