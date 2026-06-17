import os
import math
from PIL import Image, ImageDraw, ImageFilter

os.makedirs('assets/sleep', exist_ok=True)

def draw_z(d, x, y, size, color):
    d.line([(x, y), (x+size, y)], fill=color, width=3)
    d.line([(x+size, y), (x, y+size)], fill=color, width=3)
    d.line([(x, y+size), (x+size, y+size)], fill=color, width=3)

def draw_sleeping_beautiful_ghost(frame_index):
    size = 160
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    
    breath = math.sin(frame_index * math.pi / 1.5) * 4
    bob = 8 - breath
    
    # 1. Base Silhouette
    base_mask = Image.new('L', (size, size), 0)
    d_mask = ImageDraw.Draw(base_mask)
    
    skirt_poly = [
        (40, 70+bob),
        (24, 104+bob),
        (12-breath*2, 136+bob),  # left tip
        (48, 114+bob),           # inner left
        (80, 144+bob),           # center tip
        (112, 114+bob),          # inner right
        (148+breath*2, 136+bob), # right tip
        (136, 104+bob),
        (120, 70+bob)
    ]
    d_mask.ellipse([(40, 30+bob), (120, 110+bob)], fill=255)
    d_mask.polygon(skirt_poly, fill=255)
    
    base_color = Image.new('RGBA', (size, size), (245, 248, 255, 255))
    
    # 2. Add Shading
    shading_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d_shade = ImageDraw.Draw(shading_layer)
    d_shade.ellipse([(70, 50+bob), (150, 130+bob)], fill=(160, 175, 195, 180))
    d_shade.ellipse([(90, 70+bob), (140, 120+bob)], fill=(130, 145, 170, 120))
    d_shade.line([(48, 114+bob), (64, 70+bob)], fill=(140, 155, 175, 200), width=16)
    d_shade.line([(112, 114+bob), (96, 70+bob)], fill=(140, 155, 175, 200), width=16)
    d_shade.polygon([(12-breath*2, 136+bob), (48, 114+bob), (80, 144+bob), 
                     (112, 114+bob), (148+breath*2, 136+bob), (136, 160+bob), 
                     (24, 160+bob)], fill=(140, 155, 175, 220))
    
    shading_layer = shading_layer.filter(ImageFilter.GaussianBlur(12))
    base_color.alpha_composite(shading_layer)
    
    # 3. Add Highlights
    highlight_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d_high = ImageDraw.Draw(highlight_layer)
    d_high.ellipse([(45, 35+bob), (70, 60+bob)], fill=(255, 255, 255, 255))
    d_high.ellipse([(55, 45+bob), (85, 75+bob)], fill=(255, 255, 255, 150))
    d_high.line([(40, 70+bob), (12-breath*2, 136+bob)], fill=(255, 255, 255, 220), width=10) 
    d_high.line([(80, 80+bob), (80, 144+bob)], fill=(255, 255, 255, 220), width=10)
    d_high.line([(120, 70+bob), (148+breath*2, 136+bob)], fill=(255, 255, 255, 220), width=10)
    
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
    
    # 5. Eyes (Closed, sleeping curves)
    eye_lx, eye_rx = 56, 92
    eye_y = 66+bob
    eye_w = 16
    
    # Thicker curves for sleepy eyes
    d.arc([(eye_lx, eye_y), (eye_lx+eye_w, eye_y+8)], 0, 180, fill=(10, 40, 60, 255), width=4)
    d.arc([(eye_rx, eye_y), (eye_rx+eye_w, eye_y+8)], 0, 180, fill=(10, 40, 60, 255), width=4)
    
    # Blush
    blush_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d_blush = ImageDraw.Draw(blush_layer)
    d_blush.ellipse([(42, 74+bob), (58, 86+bob)], fill=(255, 100, 150, 220))
    d_blush.ellipse([(102, 74+bob), (118, 86+bob)], fill=(255, 100, 150, 220))
    blush_layer = blush_layer.filter(ImageFilter.GaussianBlur(3))
    final_img.alpha_composite(blush_layer)
    
    # Mouth (Small closed curve)
    d.arc([(74, 82+bob), (86, 90+bob)], 0, 180, fill=(130, 20, 20, 255), width=3)
    
    # Zzz particles floating up
    z_y = 40 - frame_index * 12
    if frame_index == 0:
        draw_z(d, 110, z_y + 20, 10, (100, 150, 200, 200))
    elif frame_index == 1:
        draw_z(d, 110, z_y + 20, 10, (100, 150, 200, 150))
        draw_z(d, 124, z_y, 14, (100, 150, 200, 180))
    else:
        draw_z(d, 124, z_y + 10, 14, (100, 150, 200, 120))
        draw_z(d, 136, z_y - 10, 18, (100, 150, 200, 150))

    return final_img

for i in range(3):
    img = draw_sleeping_beautiful_ghost(i)
    img.save(f'assets/sleep/{i+1}.png')