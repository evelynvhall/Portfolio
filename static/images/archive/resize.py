from PIL import Image

image = Image.open(r"test.jpg")
thumbnail_size = (400, 400)
image.thumbnail(thumbnail_size)
image.save("thumbnail_image.jpg")

