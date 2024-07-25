import os
import pandas as pd
import numpy as np
import tensorflow as tf

class LieDetectorModel:
    def __init__(self, data_directory, answers_directory):
        self.data_directory = data_directory
        self.answers_directory = answers_directory
    
    def extract_timestamp(self, filename):
        parts = filename.split("_")
        timestamp = parts[1] + "_" + parts[2]
        return timestamp.split(".")[0]  
    
    def load_data(self):
        data_files = os.listdir(self.data_directory)
        answer_files = os.listdir(self.answers_directory)

        data_list = []
        labels = []

        for data_file in data_files:
            timestamp = self.extract_timestamp(data_file)
            answer_file = next((af for af in answer_files if timestamp in af), None)
            if not answer_file:
                continue

            data_path = os.path.join(self.data_directory, data_file)
            data_df = pd.read_csv(data_path)

            answer_path = os.path.join(self.answers_directory, answer_file)
            answer_df = pd.read_csv(answer_path, header=None, names=["Question", "Answer", "Truth"])

            truth_value = answer_df["Truth"].map({"Truth": 1, "Lie": 0}).values[0]

            data_list.append(data_df)
            labels.append(truth_value)

        return data_list, labels
    
    def preprocess_data(self, data, labels):
        new_data = []
        new_labels = []

        for i in range(len(labels)):
            if isinstance(labels[i], (bool, int, np.int64)):
                new_data.append(data[i])
                new_labels.append(labels[i])

        X = np.array([data_df.to_numpy() for data_df in new_data])
        y = np.array(new_labels)
        return X, y 
    
    def build_model(self, shape):
        model = tf.keras.Sequential(
            [
                tf.keras.layers.Flatten(input_shape=shape), 
                tf.keras.layers.Dense(128, activation="relu"),
                tf.keras.layers.Dense(64, activation="relu"),
                tf.keras.layers.Dense(1, activation="sigmoid"),
            ]
        )
        model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
        return model
    
    def train_model(self, X_train, y_train, X_test, y_test, epochs=10, batch_size=32):
        self.model = self.build_model(X_train.shape[1:])
        self.model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(X_test, y_test))
    
    def evaluate_model(self, X_test, y_test):
        loss, accuracy = self.model.evaluate(X_test, y_test)
        print(f"Test Accuracy: {accuracy}")
    
    def save_model(self, path):
        self.model.save(path)
    
    def load_model(self, path):
        self.model = tf.keras.models.load_model(path)
    
    def predict(self, X):
        X = np.expand_dims(X, axis=0) 
        print(X.shape[0], X.shape[1])
        return self.model.predict(X)
    