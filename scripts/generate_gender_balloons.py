import colorsys
import os
from PIL import Image

def recolor_balloons(src_path, out_name, red_target_hue, yellow_target_hue, blue_target_hue,
                     sat_mult=(1.0, 1.0, 1.0), val_mult=(1.0, 1.0, 1.0)):
    im = Image.open(src_path).convert('RGBA')
    pixels = list(im.getdata())
    new_pixels = []
    
    # Original baseline hues:
    # Red: ~0.0 (360 deg)
    # Yellow: ~0.13 (47 deg)
    # Blue: ~0.60 (216 deg)
    red_shift = (red_target_hue - 0.0) % 1.0
    yellow_shift = (yellow_target_hue - 0.13) % 1.0
    blue_shift = (blue_target_hue - 0.60) % 1.0
    
    for r, g, b, a in pixels:
        if a < 5:
            new_pixels.append((r, g, b, a))
            continue
        
        rn, gn, bn = r / 255.0, g / 255.0, b / 255.0
        h, s, v = colorsys.rgb_to_hsv(rn, gn, bn)
        
        if s > 0.12:
            if h < 0.08 or h > 0.92:
                # Left balloon & ribbons (originally Red)
                h = (h + red_shift) % 1.0
                s = min(1.0, max(0.0, s * sat_mult[0]))
                v = min(1.0, max(0.0, v * val_mult[0]))
            elif 0.08 <= h < 0.24:
                # Center balloon & ribbons (originally Yellow)
                h = (h + yellow_shift) % 1.0
                s = min(1.0, max(0.0, s * sat_mult[1]))
                v = min(1.0, max(0.0, v * val_mult[1]))
            elif 0.45 <= h < 0.75:
                # Right balloon & ribbons (originally Blue)
                h = (h + blue_shift) % 1.0
                s = min(1.0, max(0.0, s * sat_mult[2]))
                v = min(1.0, max(0.0, v * val_mult[2]))
                
        nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
        new_pixels.append((int(round(nr * 255)), int(round(ng * 255)), int(round(nb * 255)), a))
        
    out_im = Image.new('RGBA', im.size)
    out_im.putdata(new_pixels)
    
    png_path = f"assets/icons/{out_name}.png"
    webp_path = f"assets/icons/{out_name}.webp"
    out_im.save(png_path)
    out_im.save(webp_path, 'WEBP', quality=95)
    print(f"Generated {png_path} and {webp_path}")

src = 'assets/icons/birthday-balloons.png'

# Girls: Girly pink, yellow, purple combinations
# Target hues:
# Pink: ~330 deg (0.92) / ~340 deg (0.94)
# Yellow: ~46 deg (0.13) / ~40 deg (0.11)
# Purple: ~275 deg (0.76) / ~285 deg (0.79) / ~265 deg (0.74)

# Girl 1: Pink (left), Yellow (center), Purple (right)
recolor_balloons(src, 'birthday-balloons-girl-1',
                 red_target_hue=0.92, yellow_target_hue=0.13, blue_target_hue=0.77,
                 sat_mult=(1.05, 1.0, 1.1))

# Girl 2: Purple (left), Rose Pink (center), Bright Yellow (right)
recolor_balloons(src, 'birthday-balloons-girl-2',
                 red_target_hue=0.76, yellow_target_hue=0.93, blue_target_hue=0.13,
                 sat_mult=(1.1, 1.05, 1.0))

# Girl 3: Sunny Yellow (left), Magenta Pink (center), Violet (right)
recolor_balloons(src, 'birthday-balloons-girl-3',
                 red_target_hue=0.13, yellow_target_hue=0.91, blue_target_hue=0.79,
                 sat_mult=(1.0, 1.1, 1.1))

# Boys: Boy colours (blues, cyans, greens)
# Target hues:
# Royal Blue: ~216 deg (0.60) / ~225 deg (0.62)
# Cyan / Sky: ~188 deg (0.52) / ~195 deg (0.54)
# Emerald / Mint / Lime Green: ~135 deg (0.37) / ~145 deg (0.40) / ~105 deg (0.29)

# Boy 1: Royal Blue (left), Cyan (center), Emerald Green (right)
recolor_balloons(src, 'birthday-balloons-boy-1',
                 red_target_hue=0.60, yellow_target_hue=0.52, blue_target_hue=0.37,
                 sat_mult=(1.05, 1.1, 1.05))

# Boy 2: Vibrant Green (left), Deep Azure (center), Cyan Sky (right)
recolor_balloons(src, 'birthday-balloons-boy-2',
                 red_target_hue=0.36, yellow_target_hue=0.60, blue_target_hue=0.52,
                 sat_mult=(1.05, 1.05, 1.1))

# Boy 3: Teal / Cyan (left), Bright Green (center), Cobalt Blue (right)
recolor_balloons(src, 'birthday-balloons-boy-3',
                 red_target_hue=0.50, yellow_target_hue=0.37, blue_target_hue=0.62,
                 sat_mult=(1.1, 1.05, 1.05))

print("All gendered balloon variations created successfully!")
