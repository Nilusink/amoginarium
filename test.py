from PIL import Image

img = Image.open("assets/images/potions/Green Potions.png")

cropped = img.crop((0, 0, 16, 16))
cropped.save("assets/images/potions/empty.png")
