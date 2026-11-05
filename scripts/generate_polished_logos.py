#!/usr/bin/env python3
"""
generate_polished_logos.py

Generates and polishes production-ready ResilAI brand assets across:
- 3 Orientations: Horizontal Lockup, Stacked Lockup, Standalone Emblem
- 4 Background Variations: Light Transparent, Dark Transparent, Solid Light (#FFFFFF), Solid Dark (#0B1326)
- Monochrome Variations: White Monochrome, Black/Navy Monochrome
- Formats: High-Resolution PNG (up to 3000px, 300 DPI ready), Scalable SVG (Adaptive & Static), Multi-res ICO
- Deployed to:
  * Navigation bar header (light & dark)
  * Footer (light & dark)
  * Favicons & App Icons (16, 32, 48, 180, 192, 512, ico, svg)
  * Reports & Documentation (PDF reports, docs/assets)
  * GitHub (README.md, .github/assets)
  * Comprehensive brand asset suite in frontend/public/brand/ and docs/assets/brand/
"""

import os
import io
import base64
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

# Source authentic images provided by user
SRC_EMBLEM = "/home/purvansh/.gemini/antigravity/brain/9a380bdd-fb55-4c4d-8604-c7edd7b035f5/.user_uploaded/media_1793860625081_50707ff7.png"
SRC_HORIZ = "/home/purvansh/.gemini/antigravity/brain/9a380bdd-fb55-4c4d-8604-c7edd7b035f5/.user_uploaded/media_1793860718952_3e9c3192.png"
SRC_STACKED = "/home/purvansh/.gemini/antigravity/brain/9a380bdd-fb55-4c4d-8604-c7edd7b035f5/.user_uploaded/media_1793860718970_0dbfee93.png"

# Target directories
ROOT_DIR = "/run/media/purvansh/Software/Projects/AIRS"
PUBLIC_DIR = os.path.join(ROOT_DIR, "frontend", "public")
BRAND_PUBLIC_DIR = os.path.join(PUBLIC_DIR, "brand")
DOCS_BRAND_DIR = os.path.join(ROOT_DIR, "docs", "assets", "brand")
DOCS_ASSETS_DIR = os.path.join(ROOT_DIR, "docs", "assets")
DOCS_IMAGES_DIR = os.path.join(ROOT_DIR, "docs", "images")
GITHUB_ASSETS_DIR = os.path.join(ROOT_DIR, ".github", "assets")

for d in [
    PUBLIC_DIR, BRAND_PUBLIC_DIR, DOCS_BRAND_DIR,
    DOCS_ASSETS_DIR, DOCS_IMAGES_DIR, GITHUB_ASSETS_DIR,
    os.path.join(BRAND_PUBLIC_DIR, "horizontal"),
    os.path.join(BRAND_PUBLIC_DIR, "stacked"),
    os.path.join(BRAND_PUBLIC_DIR, "emblem"),
    os.path.join(BRAND_PUBLIC_DIR, "favicons"),
    os.path.join(DOCS_BRAND_DIR, "horizontal"),
    os.path.join(DOCS_BRAND_DIR, "stacked"),
    os.path.join(DOCS_BRAND_DIR, "emblem"),
    os.path.join(DOCS_BRAND_DIR, "favicons")
]:
    os.makedirs(d, exist_ok=True)

# Brand Color Constants
COLOR_NAVY_LIGHT = np.array([24.0, 41.0, 57.0])     # #182939 ResilAI Deep Corporate Navy
COLOR_GREEN = np.array([110.0, 217.0, 117.0])        # #6ED975 ResilAI Vibrant Emerald Accent
COLOR_WHITE = np.array([255.0, 255.0, 255.0])        # #FFFFFF Pure White
COLOR_BLACK = np.array([15.0, 23.0, 42.0])           # #0F172A Slate 900 for single-color black
BG_DARK = (11, 19, 38, 255)                          # #0B1326 Deep Cyber Navy
BG_LIGHT = (255, 255, 255, 255)                      # #FFFFFF Pure White

def img_to_b64(img, fmt="PNG"):
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/{fmt.lower()};base64,{b64}"

def build_adaptive_svg(img_light, img_dark, width, height):
    b64_light = img_to_b64(img_light)
    b64_dark = img_to_b64(img_dark)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <defs>
    <style>
      .theme-light {{ display: block; }}
      .theme-dark {{ display: none; }}
      @media (prefers-color-scheme: dark) {{
        .theme-light {{ display: none; }}
        .theme-dark {{ display: block; }}
      }}
    </style>
  </defs>
  <image href="{b64_light}" class="theme-light" width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet" />
  <image href="{b64_dark}" class="theme-dark" width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet" />
</svg>"""

def build_static_svg(img, width, height):
    b64 = img_to_b64(img)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%">
  <image href="{b64}" width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet" />
</svg>"""

def process_orientation(src_path, prefix, scale=6, pad=12):
    print(f"Processing orientation: {prefix} (scale={scale}x)...")
    img = Image.open(src_path).convert("RGBA")
    bbox = img.getbbox()
    crop_box = (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(img.width, bbox[2] + pad),
        min(img.height, bbox[3] + pad)
    )
    cropped = img.crop(crop_box)

    # High-quality Lanczos upscale
    up = cropped.resize((cropped.width * scale, cropped.height * scale), Image.Resampling.LANCZOS)
    arr = np.array(up).astype(float)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]

    # Separation of Green vs Navy channels
    is_green = (rgb[:, :, 1] > rgb[:, :, 0] + 15) & (rgb[:, :, 1] > rgb[:, :, 2] + 10) & (alpha > 30)
    is_dark = (alpha > 30) & (~is_green)

    mask_green = gaussian_filter(is_green.astype(float), sigma=1.2)
    mask_dark = gaussian_filter(is_dark.astype(float), sigma=1.2)
    alpha_norm = gaussian_filter(alpha / 255.0, sigma=0.6)

    # 1. LIGHT TRANSPARENT (Navy #182939 + Emerald #6ED975 on transparent)
    out_light = np.zeros_like(arr)
    for c in range(3):
        out_light[:, :, c] = mask_dark * COLOR_NAVY_LIGHT[c] + mask_green * COLOR_GREEN[c]
    out_light[:, :, 3] = np.clip((mask_dark + mask_green) * alpha_norm, 0, 1) * 255
    im_light_trans = Image.fromarray(out_light.astype(np.uint8))

    # 2. DARK TRANSPARENT (White #FFFFFF + Emerald #6ED975 on transparent)
    out_dark = np.zeros_like(arr)
    for c in range(3):
        out_dark[:, :, c] = mask_dark * COLOR_WHITE[c] + mask_green * COLOR_GREEN[c]
    out_dark[:, :, 3] = np.clip((mask_dark + mask_green) * alpha_norm, 0, 1) * 255
    im_dark_trans = Image.fromarray(out_dark.astype(np.uint8))

    # 3. SOLID LIGHT (#FFFFFF background)
    im_light_solid = Image.new("RGBA", im_light_trans.size, BG_LIGHT)
    im_light_solid.alpha_composite(im_light_trans)
    im_light_solid = im_light_solid.convert("RGB")

    # 4. SOLID DARK (#0B1326 background)
    im_dark_solid = Image.new("RGBA", im_dark_trans.size, BG_DARK)
    im_dark_solid.alpha_composite(im_dark_trans)
    im_dark_solid = im_dark_solid.convert("RGB")

    # 5. WHITE MONOCHROME
    out_white_mono = np.zeros_like(arr)
    for c in range(3):
        out_white_mono[:, :, c] = (mask_dark + mask_green) * COLOR_WHITE[c]
    out_white_mono[:, :, 3] = np.clip((mask_dark + mask_green) * alpha_norm, 0, 1) * 255
    im_white_mono = Image.fromarray(out_white_mono.astype(np.uint8))

    # 6. BLACK MONOCHROME
    out_black_mono = np.zeros_like(arr)
    for c in range(3):
        out_black_mono[:, :, c] = (mask_dark + mask_green) * COLOR_BLACK[c]
    out_black_mono[:, :, 3] = np.clip((mask_dark + mask_green) * alpha_norm, 0, 1) * 255
    im_black_mono = Image.fromarray(out_black_mono.astype(np.uint8))

    w, h = im_light_trans.size
    svg_adaptive = build_adaptive_svg(im_light_trans, im_dark_trans, w, h)
    svg_light = build_static_svg(im_light_trans, w, h)
    svg_dark = build_static_svg(im_dark_trans, w, h)

    results = {
        "light_trans": im_light_trans,
        "dark_trans": im_dark_trans,
        "light_solid": im_light_solid,
        "dark_solid": im_dark_solid,
        "white_mono": im_white_mono,
        "black_mono": im_black_mono,
        "svg_adaptive": svg_adaptive,
        "svg_light": svg_light,
        "svg_dark": svg_dark,
        "size": (w, h)
    }
    print(f"  -> Generated {prefix} at {w}x{h}")
    return results

def save_variant_pack(pack, category_name):
    # Save into brand/category_name
    for base_dir in [BRAND_PUBLIC_DIR, DOCS_BRAND_DIR]:
        target_dir = os.path.join(base_dir, category_name)
        pack["light_trans"].save(os.path.join(target_dir, f"resilai_{category_name}_light_trans.png"), "PNG")
        pack["dark_trans"].save(os.path.join(target_dir, f"resilai_{category_name}_dark_trans.png"), "PNG")
        pack["light_solid"].save(os.path.join(target_dir, f"resilai_{category_name}_light_solid.png"), "PNG")
        pack["dark_solid"].save(os.path.join(target_dir, f"resilai_{category_name}_dark_solid.png"), "PNG")
        pack["white_mono"].save(os.path.join(target_dir, f"resilai_{category_name}_white_mono.png"), "PNG")
        pack["black_mono"].save(os.path.join(target_dir, f"resilai_{category_name}_black_mono.png"), "PNG")

        with open(os.path.join(target_dir, f"resilai_{category_name}_adaptive.svg"), "w") as f:
            f.write(pack["svg_adaptive"])
        with open(os.path.join(target_dir, f"resilai_{category_name}_light.svg"), "w") as f:
            f.write(pack["svg_light"])
        with open(os.path.join(target_dir, f"resilai_{category_name}_dark.svg"), "w") as f:
            f.write(pack["svg_dark"])

# Execute processing
horiz_pack = process_orientation(SRC_HORIZ, "horizontal", scale=6, pad=10) # ~3000x1000
stacked_pack = process_orientation(SRC_STACKED, "stacked", scale=5, pad=12) # ~1600x2300
emblem_pack = process_orientation(SRC_EMBLEM, "emblem", scale=8, pad=12)    # ~1600x2100

print("Saving organized brand packages...")
save_variant_pack(horiz_pack, "horizontal")
save_variant_pack(stacked_pack, "stacked")
save_variant_pack(emblem_pack, "emblem")

# ==========================================================
# FAVICONS & APP ICONS GENERATION (Using Emblem)
# ==========================================================
print("Generating Favicon and App Icon Suite...")
emblem_dark = emblem_pack["dark_trans"]
emblem_light = emblem_pack["light_trans"]

# Make square canvas for icons with subtle padding
def make_square_icon(img, size, bg_color=None):
    w, h = img.size
    side = max(w, h)
    pad_ratio = 1.15
    canvas_side = int(side * pad_ratio)
    
    if bg_color:
        canvas = Image.new("RGBA", (canvas_side, canvas_side), bg_color)
    else:
        canvas = Image.new("RGBA", (canvas_side, canvas_side), (0, 0, 0, 0))
    
    offset_x = (canvas_side - w) // 2
    offset_y = (canvas_side - h) // 2
    canvas.alpha_composite(img, (offset_x, offset_y))
    return canvas.resize((size, size), Image.Resampling.LANCZOS)

icon_sizes = [16, 32, 48, 64, 128, 180, 192, 512]
icons_dark = {s: make_square_icon(emblem_dark, s) for s in icon_sizes}
icons_light = {s: make_square_icon(emblem_light, s) for s in icon_sizes}

# Save into public/ and public/brand/favicons/
for base_dir in [BRAND_PUBLIC_DIR, DOCS_BRAND_DIR]:
    f_dir = os.path.join(base_dir, "favicons")
    for s in icon_sizes:
        icons_dark[s].save(os.path.join(f_dir, f"favicon-{s}.png"), "PNG")
        icons_light[s].save(os.path.join(f_dir, f"favicon-light-{s}.png"), "PNG")
    
    # Apple Touch Icon
    icons_dark[180].save(os.path.join(f_dir, "apple-touch-icon.png"), "PNG")
    icons_light[180].save(os.path.join(f_dir, "apple-touch-icon-light.png"), "PNG")

    # Multi-res ICO
    icons_dark[16].save(
        os.path.join(f_dir, "favicon.ico"),
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
        append_images=[icons_dark[32], icons_dark[48]]
    )

# Save root public/ favicons
print("Deploying root public/ favicons...")
icons_dark[512].save(os.path.join(PUBLIC_DIR, "favicon.png"), "PNG")
icons_dark[512].save(os.path.join(PUBLIC_DIR, "favicon-512.png"), "PNG")
icons_dark[192].save(os.path.join(PUBLIC_DIR, "favicon-192.png"), "PNG")
icons_dark[48].save(os.path.join(PUBLIC_DIR, "favicon-48.png"), "PNG")
icons_dark[32].save(os.path.join(PUBLIC_DIR, "favicon-32.png"), "PNG")
icons_dark[16].save(os.path.join(PUBLIC_DIR, "favicon-16.png"), "PNG")

icons_dark[512].save(os.path.join(PUBLIC_DIR, "favicon-dark.png"), "PNG")
icons_light[512].save(os.path.join(PUBLIC_DIR, "favicon-light.png"), "PNG")
icons_dark[180].save(os.path.join(PUBLIC_DIR, "apple-touch-icon.png"), "PNG")

# Multi-res ICO in root public/
icons_dark[16].save(
    os.path.join(PUBLIC_DIR, "favicon.ico"),
    format="ICO",
    sizes=[(16, 16), (32, 32), (48, 48)],
    append_images=[icons_dark[32], icons_dark[48]]
)

# Adaptive Favicon SVG
favicon_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <style>
      .theme-light {{ display: block; }}
      .theme-dark {{ display: none; }}
      @media (prefers-color-scheme: dark) {{
        .theme-light {{ display: none; }}
        .theme-dark {{ display: block; }}
      }}
    </style>
  </defs>
  <image href="{img_to_b64(icons_light[512])}" class="theme-light" width="512" height="512" />
  <image href="{img_to_b64(icons_dark[512])}" class="theme-dark" width="512" height="512" />
</svg>"""

with open(os.path.join(PUBLIC_DIR, "favicon.svg"), "w") as f:
    f.write(favicon_svg)
with open(os.path.join(PUBLIC_DIR, "Favicon Light.svg"), "w") as f:
    f.write(build_static_svg(icons_light[512], 512, 512))
with open(os.path.join(PUBLIC_DIR, "Favicon Dark.svg"), "w") as f:
    f.write(build_static_svg(icons_dark[512], 512, 512))
with open(os.path.join(PUBLIC_DIR, "Android App Icon - Light.svg"), "w") as f:
    f.write(build_static_svg(icons_light[512], 512, 512))
with open(os.path.join(PUBLIC_DIR, "Android App Icon - Dark.svg"), "w") as f:
    f.write(build_static_svg(icons_dark[512], 512, 512))

# ==========================================================
# ROOT & RUNTIME ASSETS DISTRIBUTION
# ==========================================================
print("Deploying root Header, Footer, and Navigation Assets...")

# Header Assets
horiz_pack["dark_trans"].save(os.path.join(PUBLIC_DIR, "logo_header_dark.png"), "PNG")
horiz_pack["light_trans"].save(os.path.join(PUBLIC_DIR, "logo_header_light.png"), "PNG")
horiz_pack["light_solid"].save(os.path.join(PUBLIC_DIR, "logo_header_light_solid.png"), "PNG")

with open(os.path.join(PUBLIC_DIR, "logo_header.svg"), "w") as f:
    f.write(horiz_pack["svg_adaptive"])
with open(os.path.join(PUBLIC_DIR, "logo_header_dark.svg"), "w") as f:
    f.write(horiz_pack["svg_dark"])
with open(os.path.join(PUBLIC_DIR, "logo_header_light.svg"), "w") as f:
    f.write(horiz_pack["svg_light"])

# Footer Assets
horiz_pack["dark_trans"].save(os.path.join(PUBLIC_DIR, "logo_footer_dark.png"), "PNG")
horiz_pack["light_trans"].save(os.path.join(PUBLIC_DIR, "logo_footer_light.png"), "PNG")

with open(os.path.join(PUBLIC_DIR, "logo_footer_and_github.svg"), "w") as f:
    f.write(horiz_pack["svg_adaptive"])
with open(os.path.join(PUBLIC_DIR, "logo_footer_and github.svg"), "w") as f:
    f.write(horiz_pack["svg_adaptive"])

# resilai_logo.svg (canonical stacked/emblem SVG replacement)
with open(os.path.join(PUBLIC_DIR, "resilai_logo.svg"), "w") as f:
    f.write(stacked_pack["svg_adaptive"])

# Generic logo_dark.png / logo_light.png
horiz_pack["dark_trans"].save(os.path.join(PUBLIC_DIR, "logo_dark.png"), "PNG")
horiz_pack["light_trans"].save(os.path.join(PUBLIC_DIR, "logo_light.png"), "PNG")

# Docs Assets Distribution
print("Deploying Docs & Report Assets...")
horiz_pack["dark_trans"].save(os.path.join(DOCS_ASSETS_DIR, "logo_header_dark.png"), "PNG")
horiz_pack["light_trans"].save(os.path.join(DOCS_ASSETS_DIR, "logo_header_light.png"), "PNG")
horiz_pack["dark_trans"].save(os.path.join(DOCS_ASSETS_DIR, "airs-logo-dark.png"), "PNG")
horiz_pack["light_trans"].save(os.path.join(DOCS_ASSETS_DIR, "airs-logo-light.png"), "PNG")
emblem_pack["dark_solid"].save(os.path.join(DOCS_IMAGES_DIR, "logo.jpg"), "JPEG")

with open(os.path.join(DOCS_ASSETS_DIR, "logo_header.svg"), "w") as f:
    f.write(horiz_pack["svg_adaptive"])
with open(os.path.join(DOCS_ASSETS_DIR, "logo_footer_and github.svg"), "w") as f:
    f.write(horiz_pack["svg_adaptive"])
with open(os.path.join(DOCS_ASSETS_DIR, "resilai_logo.svg"), "w") as f:
    f.write(stacked_pack["svg_adaptive"])
with open(os.path.join(DOCS_ASSETS_DIR, "Favicon Dark.svg"), "w") as f:
    f.write(build_static_svg(icons_dark[512], 512, 512))
with open(os.path.join(DOCS_ASSETS_DIR, "Favicon Light.svg"), "w") as f:
    f.write(build_static_svg(icons_light[512], 512, 512))

# GitHub Assets Distribution
print("Deploying GitHub Assets...")
horiz_pack["dark_trans"].save(os.path.join(GITHUB_ASSETS_DIR, "logo_header_dark.png"), "PNG")
horiz_pack["light_trans"].save(os.path.join(GITHUB_ASSETS_DIR, "logo_header_light.png"), "PNG")
horiz_pack["dark_trans"].save(os.path.join(GITHUB_ASSETS_DIR, "logo_dark.png"), "PNG")
horiz_pack["light_trans"].save(os.path.join(GITHUB_ASSETS_DIR, "logo_light.png"), "PNG")
emblem_pack["dark_solid"].save(os.path.join(GITHUB_ASSETS_DIR, "avatar_dark.png"), "PNG")
emblem_pack["light_solid"].save(os.path.join(GITHUB_ASSETS_DIR, "avatar_light.png"), "PNG")

with open(os.path.join(GITHUB_ASSETS_DIR, "logo.svg"), "w") as f:
    f.write(horiz_pack["svg_adaptive"])
with open(os.path.join(GITHUB_ASSETS_DIR, "logo_header.svg"), "w") as f:
    f.write(horiz_pack["svg_adaptive"])
with open(os.path.join(GITHUB_ASSETS_DIR, "logo_footer_and_github.svg"), "w") as f:
    f.write(horiz_pack["svg_adaptive"])

print("All brand assets generated, polished, and deployed successfully!")
