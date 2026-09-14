"""Generate icon, cover, and logo images for IFRS 18 Financial Reports Suite using fal.ai."""
import fal_client
import os
import sys
import time

os.environ["FAL_KEY"] = "***REDACTED-FAL-KEY***"

STATIC_DIR = os.path.join(os.path.dirname(__file__), "ai_ifrs18_financial_reports", "static", "description")

# Image generation prompts tailored for IFRS 18 Financial Reports Suite
PROMPTS = {
    "icon.png": (
        "A clean modern app icon for an IFRS 18 financial reports module. "
        "Show a stylized financial document with bar charts and a balance sheet, "
        "deep blue and teal gradient background, white and gold accents, "
        "professional corporate accounting theme, flat design, centered, "
        "no text, 256x256"
    ),
    "cover.png": (
        "A wide professional banner for an IFRS 18 financial reporting software suite. "
        "Show a modern dashboard with financial statements: profit and loss statement, "
        "balance sheet, cash flow statement, with colorful charts and graphs. "
        "Deep navy blue background with teal and gold accents, clean corporate style, "
        "no text, 1280x720 widescreen format"
    ),
    "logo.png": (
        "A professional logo for IFRS 18 Financial Reports Suite. "
        "Show a stylized financial report document with a chart icon, "
        "blue and teal color scheme with gold accents, clean modern design, "
        "centered on white background, no text, square format"
    ),
}

SIZES = {
    "icon.png": "square_hd",
    "cover.png": "landscape_16_9",
    "logo.png": "square",
}


def generate_image(filename, prompt, size):
    print(f"Generating {filename} ({size})...")
    # Use flux/schnell for fast, high-quality generation
    result = fal_client.subscribe(
        "fal-ai/flux/schnell",
        arguments={
            "prompt": prompt,
            "image_size": size,
            "num_inference_steps": 4,
            "num_images": 1,
            "enable_safety_checker": True,
        },
    )
    image_url = result["images"][0]["url"]
    print(f"  Image URL: {image_url}")

    # Download the image
    import urllib.request
    output_path = os.path.join(STATIC_DIR, filename)
    urllib.request.urlretrieve(image_url, output_path)
    file_size = os.path.getsize(output_path)
    print(f"  Saved: {output_path} ({file_size} bytes)")
    return output_path


def main():
    os.makedirs(STATIC_DIR, exist_ok=True)
    for filename, prompt in PROMPTS.items():
        size = SIZES[filename]
        try:
            generate_image(filename, prompt, size)
        except Exception as e:
            print(f"ERROR generating {filename}: {e}", file=sys.stderr)
            # Retry once after a short delay
            print("Retrying in 5 seconds...")
            time.sleep(5)
            generate_image(filename, prompt, size)
    print("\nAll images generated successfully!")


if __name__ == "__main__":
    main()
