
import cv2
import torch
import numpy as np
from facenet_pytorch import MTCNN


class FaceDetector:
    def __init__(self, **params):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.mtcnn = MTCNN(**params, device=self.device).eval()
        self.frame = None
        self.boxes = None
        self.landmarks = None
    
    def face_detected(func):
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs) if self.boxes is not None else None
        return wrapper

    def detect(self, frame, threshold=0.9, extract=True):
        # detect face box, probability and landmarks
        frame_tensor = torch.as_tensor(frame, device=self.device)
        self.boxes, probs, landmarks = self.mtcnn.detect(frame_tensor, landmarks=True)
        if self.boxes is not None:
            self.frame = frame
            keep = np.where(probs > threshold)
            self.boxes = self.boxes[keep]
            self.landmarks = landmarks[keep]

        if extract:
            return self.extract()
    
    @face_detected
    def draw(self, color=(0, 255, 0), thickness=2, draw_landmarks=False):
        # calculate bb coordinates
        LT = self.boxes[:, :2]
        RB = self.boxes[:, 2:] - LT
        coordinates = np.hstack([LT.astype(int), RB.astype(int)])
        bb_frame = self.frame.copy()
        for coord in coordinates:
            bb_frame = cv2.rectangle(bb_frame, coord, color, thickness)
        # TODO add landmarks
        if draw_landmarks:
            pass
        return bb_frame

    @face_detected
    def extract(self):
        x_ranges = [range(*bounds) for bounds in self.boxes[:, ::2].astype(int)]
        y_ranges = [range(*bounds) for bounds in self.boxes[:, 1::2].astype(int)]
        self.faces = [self.frame[y][:, x] for x, y in zip(x_ranges, y_ranges)]
        return self.faces
