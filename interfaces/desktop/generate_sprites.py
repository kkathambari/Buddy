import os
import math
from PIL import Image, ImageDraw, ImageFilter

os.makedirs('assets/idle', exist_ok=True)
os.makedirs('assets/walk', exist_ok=True)

def draw_beautiful_ghost(frame_index, state):
    size = 160
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    
    bob = math.sin(frame_index * math.pi / 1.5) * 4
    sway = math.sin(frame_index * math.pi) * 4 if state == 'walk' else 0
    
    # 1. Base Silhouette for masking
    base_mask = Image.new('L', (size, size), 0)
    d_mask = ImageDraw.Draw(base_mask)
    
    skirt_poly = [
        (40, 70+bob),
        (28+sway, 100+bob),
        (16+sway*2, 130+bob),    # left tip
        (48+sway, 110+bob),      # inner left
        (80+sway*1.5, 140+bob),  # center tip
        (112+sway, 110+bob),     # inner right
        (144+sway*2, 130+bob),   # right tip
        (132+sway, 100+bob),
        (120, 70+bob)
    ]
    d_mask.ellipse([(40, 30+bob), (120, 110+bob)], fill=255)
    d_mask.polygon(skirt_poly, fill=255)
    
    base_color = Image.new('RGBA', (size, size), (245, 248, 255, 255))
    
    # 2. Add Shading (Airbrush / Blur effect)
    shading_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d_shade = ImageDraw.Draw(shading_layer)
    
    # Sphere volume shadow (bottom right)
    d_shade.ellipse([(70, 50+bob), (150, 130+bob)], fill=(160, 175, 195, 180))
    d_shade.ellipse([(90, 70+bob), (140, 120+bob)], fill=(130, 145, 170, 120))
    
    # Skirt drape creases (shadows extending up from inner folds)
    d_shade.line([(48+sway, 110+bob), (64, 70+bob)], fill=(140, 155, 175, 200), width=16)
    d_shade.line([(112+sway, 110+bob), (96, 70+bob)], fill=(140, 155, 175, 200), width=16)
    
    # Bottom shading along the wavy edge
    d_shade.polygon([(16+sway*2, 130+bob), (48+sway, 110+bob), (80+sway*1.5, 140+bob), 
                     (112+sway, 110+bob), (144+sway*2, 130+bob), (132+sway, 160+bob), 
                     (28+sway, 160+bob)], fill=(140, 155, 175, 220))
    
    shading_layer = shading_layer.filter(ImageFilter.GaussianBlur(12))
    base_color.alpha_composite(shading_layer)
    
    # 3. Add Highlights
    highlight_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d_high = ImageDraw.Draw(highlight_layer)
    
    # Specular head highlight
    d_high.ellipse([(45, 35+bob), (70, 60+bob)], fill=(255, 255, 255, 255))
    d_high.ellipse([(55, 45+bob), (85, 75+bob)], fill=(255, 255, 255, 150))
    
    # Raised drape ridges highlights
    d_high.line([(40, 70+bob), (16+sway*2, 130+bob)], fill=(255, 255, 255, 220), width=10) 
    d_high.line([(80, 80+bob), (80+sway*1.5, 140+bob)], fill=(255, 255, 255, 220), width=10)
    d_high.line([(120, 70+bob), (144+sway*2, 130+bob)], fill=(255, 255, 255, 220), width=10)
    
    highlight_layer = highlight_layer.filter(ImageFilter.GaussianBlur(6))
    base_color.alpha_composite(highlight_layer)
    
    # 4. Apply Mask
    img.paste(base_color, (0, 0), mask=base_mask)
    
    # Outer stroke mask
    final_img = Image.new('RGBA', (size, size), (0,0,0,0))
    stroke_layer = Image.new('RGBA', (size, size), (0,0,0,0))
    d_stroke = ImageDraw.Draw(stroke_layer)
    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (1,1), (-1,1), (1,-1), (0,2)]:
        d_stroke.ellipse([(40+dx, 30+bob+dy), (120+dx, 110+bob+dy)], fill=(120, 130, 150, 180))
        d_stroke.polygon([(x+dx, y+dy) for x, y in skirt_poly], fill=(120, 130, 150, 180))
        
    final_img.alpha_composite(stroke_layer)
    final_img.alpha_composite(img)
    
    d = ImageDraw.Draw(final_img)
    
    # 5. Eyes (Gradient effect)
    eye_lx, eye_rx = 56, 88
    eye_y = 56+bob
    eye_w, eye_h = 16, 24
    
    for i in range(6):
        shade = int(60 + i*25)
        shrink = i * 1.2
        d.ellipse([(eye_lx+shrink, eye_y+shrink), (eye_lx+eye_w-shrink, eye_y+eye_h)], fill=(10, 40, shade, 255))
        d.ellipse([(eye_rx+shrink, eye_y+shrink), (eye_rx+eye_w-shrink, eye_y+eye_h)], fill=(10, 40, shade, 255))
    
    # Eye highlights
    d.ellipse([(eye_lx+3, eye_y+3), (eye_lx+9, eye_y+11)], fill=(255, 255, 255, 255))
    d.ellipse([(eye_rx+3, eye_y+3), (eye_rx+9, eye_y+11)], fill=(255, 255, 255, 255))
    d.ellipse([(eye_lx+10, eye_y+15), (eye_lx+13, eye_y+19)], fill=(255, 255, 255, 255))
    d.ellipse([(eye_rx+10, eye_y+15), (eye_rx+13, eye_y+19)], fill=(255, 255, 255, 255))
    
    # Cute eyebrows
    d.arc([(58, 48+bob), (66, 54+bob)], 180, 360, fill=(100, 110, 130, 255), width=2)
    d.arc([(90, 48+bob), (98, 54+bob)], 180, 360, fill=(100, 110, 130, 255), width=2)
    
    # Blush
    blush_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d_blush = ImageDraw.Draw(blush_layer)
    d_blush.ellipse([(42, 70+bob), (58, 82+bob)], fill=(255, 100, 150, 220))
    d_blush.ellipse([(102, 70+bob), (118, 82+bob)], fill=(255, 100, 150, 220))
    blush_layer = blush_layer.filter(ImageFilter.GaussianBlur(3))
    final_img.alpha_composite(blush_layer)
    
    # Mouth (Deep red with pink tongue)
    d.chord([(68, 72+bob), (92, 92+bob)], 0, 180, fill=(130, 20, 20, 255))
    d.chord([(72, 82+bob), (88, 92+bob)], 0, 180, fill=(240, 100, 100, 255))
    
    return final_img

for i in range(3):
    img = draw_beautiful_ghost(i, 'idle')
    img.save(f'assets/idle/{i+1}.png')
    
for i in range(3):
    img = draw_beautiful_ghost(i, 'walk')
    img.save(f'assets/walk/{i+1}.png')