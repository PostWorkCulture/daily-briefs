import numpy as np
from PIL import Image
from matplotlib.colors import rgb_to_hsv, hsv_to_rgb

src = Image.open('assets/icons/birthday-balloon-single-master.png')
w, h = src.size
rgba = np.array(src, dtype=np.float32) / 255.0
rgb = rgba[:, :, :3]
alpha = rgba[:, :, 3]

hsv = rgb_to_hsv(rgb)
H = hsv[:, :, 0]
S = hsv[:, :, 1]
V = hsv[:, :, 2]

# Exact balloon mask: balloon body + knot
balloon_mask = np.zeros((h, w), dtype=bool)
for y in range(h):
    for x in range(w):
        if y <= 590:
            balloon_mask[y, x] = True
        elif y <= 632 and (200 <= x <= 268):
            balloon_mask[y, x] = True

balloon_mask = balloon_mask & (alpha > 0.05) & (S > 0.08)
ribbon_base = (~balloon_mask) & (alpha > 0.05) & (S > 0.08)

def make_variant(target_balloon_hue, ribbon_hues, out_name, s_mult=1.0, v_mult=1.0):
    new_H = np.copy(H)
    new_S = np.copy(S)
    new_V = np.copy(V)
    
    # Recolor balloon body
    new_H[balloon_mask] = (target_balloon_hue + (H[balloon_mask] - 0.94)) % 1.0
    new_S[balloon_mask] = np.clip(new_S[balloon_mask] * s_mult, 0.0, 1.0)
    new_V[balloon_mask] = np.clip(new_V[balloon_mask] * v_mult, 0.0, 1.0)
    
    # Ribbon 1 (originally red/pink/magenta: H < 0.04 or H > 0.75)
    m1 = ribbon_base & ((H < 0.04) | (H > 0.75))
    new_H[m1] = (ribbon_hues[0] + (H[m1] - 0.98)) % 1.0
    
    # Ribbon 2 (originally yellow/warm: 0.04 <= H <= 0.30)
    m2 = ribbon_base & (H >= 0.04) & (H <= 0.30)
    new_H[m2] = (ribbon_hues[1] + (H[m2] - 0.12)) % 1.0
    
    # Ribbon 3 (originally blue/cyan: 0.30 < H <= 0.75)
    m3 = ribbon_base & (H > 0.30) & (H <= 0.75)
    new_H[m3] = (ribbon_hues[2] + (H[m3] - 0.58)) % 1.0
    
    new_hsv = np.dstack([new_H, new_S, new_V])
    new_rgb = hsv_to_rgb(new_hsv)
    out_rgba = np.dstack([new_rgb, alpha])
    out_img = Image.fromarray((out_rgba * 255.0).round().astype(np.uint8))
    
    out_img.save(f'assets/icons/{out_name}.png')
    out_img.save(f'assets/icons/{out_name}.webp', 'WEBP', quality=95)
    print(f'Generated {out_name}')

# Girls:
# 1. Hot Pink balloon, ribbons in rose pink, sunny yellow, lavender purple
make_variant(0.93, (0.93, 0.13, 0.77), 'birthday-balloons-girl-1')
# 2. Purple balloon, ribbons in violet, pastel pink, golden yellow
make_variant(0.77, (0.77, 0.93, 0.13), 'birthday-balloons-girl-2', s_mult=1.05)
# 3. Sunny Yellow balloon, ribbons in gold, hot pink, purple
make_variant(0.13, (0.13, 0.93, 0.77), 'birthday-balloons-girl-3', v_mult=1.05)

# Boys:
# 1. Royal Blue balloon, ribbons in royal blue, cyan, emerald green
make_variant(0.60, (0.60, 0.52, 0.36), 'birthday-balloons-boy-1')
# 2. Cyan / Sky Blue balloon, ribbons in deep blue, cyan, bright lime
make_variant(0.52, (0.60, 0.52, 0.38), 'birthday-balloons-boy-2')
# 3. Emerald Green balloon, ribbons in emerald, bright lime, cobalt blue
make_variant(0.35, (0.35, 0.38, 0.60), 'birthday-balloons-boy-3')

# Fallback default (Yellow/Gold with celebratory colors)
make_variant(0.13, (0.93, 0.13, 0.60), 'birthday-balloons')
print('All single balloons generated successfully!')
