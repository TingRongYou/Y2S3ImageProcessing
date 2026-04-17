from PIL import Image

# 1. Open the original transparent image
img = Image.open("glove.png").convert("RGBA")
alpha = img.split()[-1]

# 2. Ignore ghost pixels
clean_alpha = alpha.point(lambda p: p if p > 50 else 0)
bbox = clean_alpha.getbbox()

if bbox:
    # 3. Crop tightly around the glove
    img_cropped = img.crop(bbox)
    
    # 4. THE BRUTE-FORCE FIX: 
    # Forcefully stretch the image to exactly 256x256. 
    # This ignores aspect ratio and guarantees it fills 100% of the Windows icon box.
    img_stretched = img_cropped.resize((256, 256))
    
    # 5. Save as a multi-size Windows ICO
    img_stretched.save("perfect_icon.ico", format="ICO", sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
    print("Icon aggressively stretched to fill 100% of the space!")
else:
    print("Error: The image appears to be completely empty.")