import os
import dlib
import csv
import numpy as np
import logging
import cv2


def extract_and_save_features(
        input_faces_dir="./saved_images",
        output_csv_path="./data/features_all.csv",
        shape_predictor_path='./data/data_dlib/shape_predictor_68_face_landmarks.dat',
        face_recognition_model_path="./data/data_dlib/dlib_face_recognition_resnet_model_v1.dat",
        logging_level=logging.INFO):
    try:

        # Configure logging
        logging.basicConfig(level=logging_level)

        # Initialize dlib tools
        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor(shape_predictor_path)
        face_reco_model = dlib.face_recognition_model_v1(face_recognition_model_path)

        def return_128d_features(path_img):
            """Return 128D features for single image"""
            img_rd = cv2.imread(path_img)
            faces = detector(img_rd, 1)

            logging.info("%-40s %-20s", " Image with faces detected:", path_img)

            if len(faces) != 0:
                shape = predictor(img_rd, faces[0])
                face_descriptor = face_reco_model.compute_face_descriptor(img_rd, shape)
            else:
                face_descriptor = 0
                logging.warning("no face")
            return face_descriptor

        def return_features_mean_personX(path_face_personX, person_name):
            """Return the mean value of 128D face descriptor for person X"""
            features_list_personX = []
            photos_list = os.listdir(path_face_personX)

            if photos_list:
                for i in range(len(photos_list)):
                    logging.info("%-40s %-20s", " / Reading image:", path_face_personX + "/" + photos_list[i])
                    features_128d = return_128d_features(path_face_personX + "/" + photos_list[i])
                    if features_128d == 0:
                        i += 1
                    else:
                        features_list_personX.append(features_128d)
            else:
                logging.warning(" Warning: No images in%s/", path_face_personX)

            if features_list_personX:
                features_mean_personX = np.array(features_list_personX, dtype=object).mean(axis=0)
            else:
                features_mean_personX = np.zeros(128, dtype=object, order='C')
            return features_mean_personX

        # Main processing
        person_list = os.listdir(input_faces_dir)
        person_list.sort()

        with open(output_csv_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for person in person_list:
                person_path = os.path.join(input_faces_dir, person)
                if os.path.isdir(person_path):  # Only process directories
                    logging.info("Processing folder: %s", person)
                    features_mean_personX = return_features_mean_personX(person_path, person)

                    # Insert the person's name (folder name) as the first element
                    features_mean_personX = np.insert(features_mean_personX, 0, person, axis=0)
                    writer.writerow(features_mean_personX)
                    logging.info('\n')

            logging.info(f"Save all the features of faces registered into: {output_csv_path}")

        return True

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return False

