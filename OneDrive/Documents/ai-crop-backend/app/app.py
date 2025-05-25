from flask import Flask, render_template, request, jsonify
from keras.models import load_model
from keras.preprocessing import image
import numpy as np
import os
import json

# ✅ Step 1: Create Flask app
app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ✅ Step 2: Build absolute model path and load model
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, 'model', 'crop_disease_model.h5')
model = load_model(model_path)

# ✅ Step 3: Load disease management info
disease_info_path = os.path.join(BASE_DIR, 'disease_info.json')
with open(disease_info_path) as f:
    disease_data = json.load(f)

# ✅ Step 4: Home Route
@app.route('/')
def home():
    return render_template('index.html')

# ✅ Step 5: Predict Route
@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    img = image.load_img(filepath, target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    output = model.predict(img_array)[0]

    if isinstance(output, (np.ndarray, list)) and len(output) > 1:
        class_index = np.argmax(output)
        confidence = float(output[class_index]) * 100
        labels = ["Healthy", "Bacterial Spot", "Late Blight"]  # 🔁 update to match your model
        predicted_label = labels[class_index]
    else:
        prob = float(output)
        confidence = prob * 100
        predicted_label = "Infected" if prob > 0.5 else "Healthy"

    # ✅ Lookup management tip
    label_key = None
    for key in disease_data:
        if disease_data[key]["disease"].lower() == predicted_label.lower():
            label_key = key
            break

    info = disease_data.get(label_key, {"management": "No data available."})
    management_tip = info["management"]

    return jsonify({
        'prediction': predicted_label,
        'confidence': round(confidence, 2),
        'filename': file.filename,
        'management': management_tip
    })

# ✅ Step 6: Launch app
if __name__ == '__main__':
    app.run(debug=True)

