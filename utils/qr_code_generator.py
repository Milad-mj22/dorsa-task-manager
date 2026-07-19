import qrcode
from PIL import Image

# Data to encode into the QR code
data = "https://dorsa.mykaman.ir/utils/tickets/create/2"

# Create a QR code instance
qr = qrcode.QRCode(
    version=1,  # controls the size of the QR code
    error_correction=qrcode.constants.ERROR_CORRECT_L,  # error correction level
    box_size=10,  # size of each box in the QR code
    border=4,  # thickness of the border
)

# Add the data to the QR code
qr.add_data(data)
qr.make(fit=True)

# Create an image from the QR code with the desired colors
img = qr.make_image(fill='black', back_color='#17203A')

# Convert the image to RGB to manipulate colors
img = img.convert('RGB')

# Get the pixels of the image
pixels = img.load()

# Loop through the image pixels and change black to white
for i in range(img.size[0]):
    for j in range(img.size[1]):
        if pixels[i, j] == (0, 0, 0):  # If the pixel is black
            pixels[i, j] = (250, 250, 250)  # Change it to white

# Save the image to a file
img.save("qrcode_white_on_blue.png")

# Optionally, show the image
img.show()
