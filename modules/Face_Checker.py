import dlib
import numpy as np
import cv2
import os
import pandas as pd


def process(image):
    # Initialize dlib components
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("data/data_dlib/shape_predictor_68_face_landmarks.dat")
    face_reco_model = dlib.face_recognition_model_v1("data/data_dlib/dlib_face_recognition_resnet_model_v1.dat")

    # If input is a file path, read the image
    if isinstance(image, str):
        if not os.path.exists(image):
            raise FileNotFoundError(f"Image file not found: {image}")
        img = cv2.imread(image)
    else:
        img = image.copy()

    # Load known faces from features.csv
    face_features_known_list = []
    face_name_known_list = []

    if os.path.exists("data/features_all.csv"):
        csv_rd = pd.read_csv("data/features_all.csv", header=None)
        for i in range(csv_rd.shape[0]):
            features_someone_arr = []
            face_name_known_list.append(csv_rd.iloc[i][0])
            for j in range(1, 129):
                if csv_rd.iloc[i][j] == '':
                    features_someone_arr.append('0')
                else:
                    features_someone_arr.append(csv_rd.iloc[i][j])
            face_features_known_list.append(features_someone_arr)
    else:
        raise FileNotFoundError("'features_all.csv' not found! Please create it first.")

    # Detect faces in the image
    faces = detector(img, 0)  # [Up-Scaling factor (0 means no Up-Scaling).]
    recognized_names = []

    if len(faces) == 0:
        return ["No faces detected"]

    for face in faces:
        # Get face landmarks
        shape = predictor(img, face)

        # Compute face descriptor
        face_descriptor = face_reco_model.compute_face_descriptor(img, shape)

        # Compare with known faces
        min_distance = float('inf')
        recognized_name = "unknown"

        #Main Comparison and logic part
        for i, known_feature in enumerate(face_features_known_list):
            if str(known_feature[0]) != '0.0':
                # Convert features to numpy arrays
                current_feature = np.array(face_descriptor)
                known_feature_np = np.array(known_feature, dtype=float)

                # Calculate Euclidean distance
                distance = np.sqrt(np.sum(np.square(current_feature - known_feature_np)))

                if distance < min_distance:
                    min_distance = distance
                    if distance < 0.3:  # Threshold for recognition
                        recognized_name = face_name_known_list[i]

        recognized_names.append(recognized_name)

    return recognized_names
