import os
import math
from PIL import Image, ImageDraw, ImageFilter

os.makedirs('assets/fall', exist_ok=True)

def draw_falling_beautiful_ghost(frame_index):
    size = 160
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    
    # Fast fluttering bob for falling
    flutter = math.sin(frame_index * math.pi) * 4
    bob = -frame_index * 2 # Slight upward movement while falling
    
    # Parachute effect to make it "soft fluffy fall"
    spread = 18 
    lift = 25
    
    # 1. Base Silhouette for masking
    base_mask = Image.new('L', (size, size), 0)
    d_mask = ImageDraw.Draw(base_mask)
    
    skirt_poly = [
        (40, 70+bob),
        (28-spread, 100-lift+bob+flutter),
        (16-spread, 130-lift+bob+flutter*2),    # left tip
        (48, 110-lift//2+bob),                  # inner left
        (80, 140-lift+bob+flutter*1.5),         # center tip
        (112, 110-lift//2+bob),                 # inner right
        (144+spread, 130-lift+bob+flutter*2),   # right tip
        (132+spread, 100-lift+bob+flutter),
        (120, 70+bob)
    ]
    d_mask.ellipse([(40, 30+bob), (120, 110+bob)], fill=255)
    d_mask.polygon(skirt_poly, fill=255)
    
    base_color = Image.new('RGBA', (size, size), (245, 248, 255, 255))
    
    # 2. Add Shading (Airbrush / Blur effect)
    shading_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d_shade = ImageDraw.Draw(shading_layer)
    
    # Sphere volume shadow
    d_shade.ellipse([(70, 50+bob), (150, 130+bob)], fill=(160, 175, 195, 180))
    d_shade.ellipse([(90, 70+bob), (140, 120+bob)], fill=(130, 145, 170, 120))
    
    # Skirt drape creases
    d_shade.line([(48, 110-lift//2+bob), (64, 70+bob)], fill=(140, 155, 175, 200), width=16)
    d_shade.line([(112, 110-lift//2+bob), (96, 70+bob)], fill=(140, 155, 175, 200), width=16)
    
    # Bottom shading along the wavy edge
    d_shade.polygon([(16-spread, 130-lift+bob+flutter*2), (48, 110-lift//2+bob), (80, 140-lift+bob+flutter*1.5), 
                     (112, 110-lift//2+bob), (144+spread, 130-lift+bob+flutter*2), (132+spread, 160-lift+bob), 
                     (28-spread, 160-lift+bob)], fill=(140, 155, 175, 220))
    
    shading_layer = shading_layer.filter(ImageFilter.GaussianBlur(12))
    base_color.alpha_composite(shading_layer)
    
    # 3. Add Highlights
    highlight_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d_high = ImageDraw.Draw(highlight_layer)
    
    # Specular head highlight
    d_high.ellipse([(45, 35+bob), (70, 60+bob)], fill=(255, 255, 255, 255))
    d_high.ellipse([(55, 45+bob), (85, 75+bob)], fill=(255, 255, 255, 150))
    
    # Raised drape ridges highlights
    d_high.line([(40, 70+bob), (16-spread, 130-lift+bob+flutter*2)], fill=(255, 255, 255, 220), width=10) 
    d_high.line([(80, 80+bob), (80, 140-lift+bob+flutter*1.5)], fill=(255, 255, 255, 220), width=10)
    d_high.line([(120, 70+bob), (144+spread, 130-lift+bob+flutter*2)], fill=(255, 255, 255, 220), width=10)
    
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
    
    # 5. Eyes (Scared, wide)
    eye_lx, eye_rx = 56, 88
    eye_y = 52+bob
    eye_w, eye_h = 16, 26
    
    for i in range(6):
        shade = int(60 + i*25)
        shrink = i * 1.2
        d.ellipse([(eye_lx+shrink, eye_y+shrink), (eye_lx+eye_w-shrink, eye_y+eye_h)], fill=(10, 40, shade, 255))
        d.ellipse([(eye_rx+shrink, eye_y+shrink), (eye_rx+eye_w-shrink, eye_y+eye_h)], fill=(10, 40, shade, 255))
    
    # Eye highlights looking up slightly (scared)
    d.ellipse([(eye_lx+3, eye_y+3), (eye_lx+9, eye_y+11)], fill=(255, 255, 255, 255))
    d.ellipse([(eye_rx+3, eye_y+3), (eye_rx+9, eye_y+11)], fill=(255, 255, 255, 255))
    d.ellipse([(eye_lx+10, eye_y+15), (eye_lx+13, eye_y+19)], fill=(255, 255, 255, 255))
    d.ellipse([(eye_rx+10, eye_y+15), (eye_rx+13, eye_y+19)], fill=(255, 255, 255, 255))
    
    # Scared eyebrows (tilted upwards)
    d.line([(54, 46+bob), (68, 42+bob)], fill=(100, 110, 130, 255), width=2)
    d.line([(92, 42+bob), (106, 46+bob)], fill=(100, 110, 130, 255), width=2)
    
    # Blush
    blush_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d_blush = ImageDraw.Draw(blush_layer)
    d_blush.ellipse([(42, 70+bob), (58, 82+bob)], fill=(255, 100, 150, 220))
    d_blush.ellipse([(102, 70+bob), (118, 82+bob)], fill=(255, 100, 150, 220))
    blush_layer = blush_layer.filter(ImageFilter.GaussianBlur(3))
    final_img.alpha_composite(blush_layer)
    
    # Scared mouth (O shape)
    d.ellipse([(74, 76+bob), (86, 92+bob)], fill=(130, 20, 20, 255))
    
    # Action lines (streaks moving UP as ghost falls DOWN)
    streak_y = frame_index * -15
    d.line([(30, 60+streak_y), (30, 90+streak_y)], fill=(170, 180, 195, 150), width=3)
    d.line([(130, 80+streak_y), (130, 120+streak_y)], fill=(170, 180, 195, 150), width=3)
    d.line([(140, 40+streak_y), (140, 60+streak_y)], fill=(170, 180, 195, 150), width=3)

    return final_img

for i in range(3):
    img = draw_falling_beautiful_ghost(i)
    img.save(f'assets/fall/{i+1}.png')