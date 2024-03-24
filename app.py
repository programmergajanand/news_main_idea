from flask import Flask, render_template, request, send_file
from PIL import Image, ImageEnhance, ImageFilter
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
EDITED_FOLDER = 'edited'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['EDITED_FOLDER'] = EDITED_FOLDER

def apply_filters(image_path, contrast=1.0, blur=0, brightness=1.0, rotation=0, vintage=0, grayscale=False):
    image = Image.open(image_path)
    
    # Apply rotation
    rotated_image = image.rotate(rotation, expand=True)
    
    # Apply contrast
    enhancer = ImageEnhance.Contrast(rotated_image)
    contrasted_image = enhancer.enhance(contrast)
    
    # Apply blur
    blurred_image = contrasted_image.filter(ImageFilter.GaussianBlur(blur))
    
    # Apply brightness
    enhancer = ImageEnhance.Brightness(blurred_image)
    brightness_image = enhancer.enhance(brightness)
    
    # Apply vintage (sepia) effect
    if vintage > 0:
        vintage_filter = Image.new('RGB', brightness_image.size, (vintage, 100, 50))
        vintage_image = Image.blend(brightness_image, vintage_filter, vintage / 100)
    else:
        vintage_image = brightness_image
    
    # Apply grayscale
    if grayscale:
        grayscale_image = vintage_image.convert('L')
    else:
        grayscale_image = vintage_image
    
    return grayscale_image

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_image():
    if request.method == 'POST':
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
                image.save(image_path)

                # Apply filters
                processed_image = apply_filters(image_path)

                # Save edited image
                edited_image_path = os.path.join(app.config['EDITED_FOLDER'], 'edited_' + image.filename)
                processed_image.save(edited_image_path)

    return '', 204

@app.route('/download')
def download_image():
    filename = 'edited_image.png'  # You need to specify the correct filename here
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
