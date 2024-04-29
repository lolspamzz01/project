from flask import Flask , render_template

from flask import request, redirect,Response , url_for, jsonify

from flask import Flask , render_template

from flask import request, redirect,Response , url_for
import pickle
import numpy as np
from flask_sqlalchemy import SQLAlchemy
import tensorflow as tf
import os
from tensorflow.keras.models import load_model
from PIL import Image

#import cv2
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']= "sqlite:///db.sqlite3"

app.config['UPLOAD_FOLDER_SHOULDER'] = './static/imagedata/shoulder'
alzmodel=load_model('models/shoulder.h5')
alzmodel.summary()
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()
with app.app_context():
    db.create_all()

ALLOWED_EXTENSIONS = {'webp', 'png', 'jpg', 'jpeg', 'gif', 'svg'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class Shoulder(db.Model):
    __tablename__= 'shoulder'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True,nullable = False)
    image = db.Column(db.String)
    target = db.Column(db.String)

with app.app_context():
    db.create_all()


@app.route("/", methods = ["GET","POST"])
def shoulder():
    if request.method =="GET":
        return render_template("index.html")
    if request.method =="POST":
        data = db.session.query(Shoulder).all()
        a = str(data[-1].id)
        a = int(a)+1
        print(request.files)
        file = request.files['photo']
        person_name =  request.form['name']
        print(person_name)
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = file.filename
            ext = filename.split(".")[-1]
            file.save(os.path.join(app.config['UPLOAD_FOLDER_SHOULDER'], str(a)+"."+ext))
            
            image_path = os.path.join(app.config['UPLOAD_FOLDER_SHOULDER'], str(a)+"."+ext)
            image = Image.open(image_path)

            # Preprocess the image
            img = image.resize((224, 224))
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = tf.expand_dims(img_array, 0)

            # Make predictions
            predictions = alzmodel.predict(img_array)
            class_labels = ['Abnormal','Normal']
            score = tf.nn.softmax(predictions[0])
            print(score)
            print(predictions)
            accuracy = round(max(predictions[0])*100,2)
            print(accuracy)
            max_index = np.array(predictions).argmax()
            target = class_labels[max_index]
            data = Shoulder(image = str(a)+"."+ext, target = target)
            db.session.add(data)
            db.session.commit()
            text = """<h2 class="result-s">Abnormality</h2> <h2 class="result-f">Normal</h2>"""
            if target == 'Normal':
                text = '<h2 class="result-s">'+ person_name+", your Shoulders are Normal.Thank you for using our website" + '</h2>'
            else:
                text = '<h2 class="result-f">'+ person_name+", your Shoulders are Abnormal. Please consult a doctor. Thank you for using our website." + '</h2>'
            print(text)
            return render_template("result.html", accuracy = accuracy,text = text)



if __name__ == "__main__":
  app.run(host = '0.0.0.0',debug = True,port = 8080) 