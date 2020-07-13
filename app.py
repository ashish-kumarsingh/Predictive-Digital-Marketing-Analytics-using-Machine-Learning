from flask import Flask, render_template, request
from sklearn.externals import joblib
import pandas as pd
import numpy as np
from flask_mail import Mail,Message
from google.oauth2 import service_account #For GCP Account connection
from google.cloud import pubsub_v1 # For PubSub Client
from google.cloud import bigquery # For BigQuery Client
from google.cloud import storage # For Cloud Storage Client
import json # For Message syntax

app = Flask(__name__)

app.config['DEBUG']= True
app.config['TESTING']= False
app.config['MAIL_SERVER']= 'smtp.gmail.com'
app.config['MAIL_PORT']= 465
app.config['MAIL_USE_TLS']= False
app.config['MAIL_USE_SSL']= True
# app.config['MAIL_DEBUG']= True
app.config['MAIL_USERNAME']= 'subway2offers@gmail.com'
app.config['MAIL_PASSWORD']= 'Subway123'
app.config['MAIL_DEFAULT_SENDER']= 'subway2offers@gmail.com'
app.config['MAIL_MAX_EMAILS']=None
# app.config['MAIL_SUPPRESS_SEND']
app.config['MAIL_ASCII_ATTACHMENT']= False

mail= Mail(app)

mul_reg = open("classifier_subway.pkl", "rb")
ml_model = joblib.load(mul_reg)


@app.route("/")
def home():
    return render_template('home.html')



@app.route("/predict", methods=['GET', 'POST'])
def predict():
    print("I was here 1")
    if request.method == 'POST':
        print(request.form.get('age'))
        try:
            age = float(request.form['age'])
            income = float(request.form['income'])
            Gender = float(request.form['Gender'])
            MaritalStatus = float(request.form['MaritalStatus'])
            HaveKids = float(request.form['HaveKids'])
            isVeg = float(request.form['isVeg'])
            IsStudent = float(request.form['IsStudent'])
            email= request.form['email']
            offer_received = 0
            pred_args = [age, income, Gender,MaritalStatus,HaveKids,isVeg,IsStudent]
            pred_args_arr = np.array(pred_args)
            pred_args_arr = pred_args_arr.reshape(1, -1)
            # mul_reg = open("multiple_regression_model.pkl", "rb")
            # ml_model = joblib.load(mul_reg)
            model_prediction = ml_model.predict(pred_args_arr)
            model_prediction = round(float(model_prediction), 2)

            cred = service_account.Credentials.from_service_account_file(
                'subway_cred.json')

            # Setting up the Configuration Variables:
            project_id = "subwayoffers"
            bucket_name = "bucket_subway"
            topic_name = "subwaytopic"
            subscription_name = "subwayoffers"
            dataset_name = "data"
            table_name = "Profile"

            publisher = pubsub_v1.PublisherClient(credentials=cred)

            client = pubsub_v1.PublisherClient(credentials=cred)
            topic_path = publisher.topic_path(project_id, topic_name)
            print(topic_path)

            subscriber = pubsub_v1.SubscriberClient(credentials=cred)
            topic_path = subscriber.topic_path(project_id, topic_name)
            subscription_path = subscriber.subscription_path(project_id, subscription_name)





            model_prediction_dict='dict'

            if isVeg==0:
                model_prediction_dict = "Free Subway Chicken Sandwich"
            elif HaveKids==1:
                model_prediction_dict = "40% on Happy Meal"

            else:
                model_prediction_dict = "30 % of on any Subway Sandwich"



            if model_prediction==1 :
                offer_received='1'
                model_prediction = 0
                msg = Message(subject="Subway offers",
                          sender=app.config.get("MAIL_USERNAME"),
                          recipients=[email],  # replace with your email for testing
                          body="Thank you for taking this survey. Your offer is "+str(model_prediction_dict))
                print(str(model_prediction))
                mail.send(msg)


            else:
                msg = Message(subject="Subway offers",
                          sender=app.config.get("MAIL_USERNAME"),
                          recipients=[email],  # replace with your email for testing
                          body="Thank you for taking this survey. You have earned a cookie")
                mail.send(msg)
                #print(str(model_prediction))


                model_prediction=0

            data_row = {"age": age, "income": income, "Gender": Gender, "MaritalStatus": MaritalStatus,
                    "HaveKids": HaveKids, "isVeg": isVeg, "IsStudent": IsStudent, "offer_received": offer_received,
                    "offer_completed": model_prediction, "email": email}


            # print(data_row)
            message_data = json.dumps(data_row)
            message_data = message_data.encode('utf-8')

            print(message_data)
            # Publishing a message on the PubSub Topic Created:
            response = publisher.publish(topic_path, message_data, origin='python-sample')
            print(response)


        except ValueError:
            return "Please check if the values are entered correctly"
    return render_template('predict.html', prediction = model_prediction)


if __name__ == "__main__":
    app.run(debug=True)