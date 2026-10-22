"""하린 얼굴 검사: 첫 학습사진(하린 v1 얼굴 12장)과 얼굴 유사도(코사인)를 잰다.
python tools/facecheck.py 기준이미지들(쉼표구분) 검사이미지...
- 모델: OpenCV YuNet(얼굴 찾기) + SFace(얼굴 특징)  ~/face/yunet.onnx, ~/face/sface.onnx
- 기준: 0.70 이상만 게시용으로 통과. 후보를 여러 장 만들고 가장 높은 것을 쓴다.
"""
import os, sys
import cv2

D = os.path.expanduser("~/face")
det = cv2.FaceDetectorYN.create(f"{D}/yunet.onnx", "", (320, 320), 0.7)
rec = cv2.FaceRecognizerSF.create(f"{D}/sface.onnx", "")
PASS = 0.70


def emb(path):
    img = cv2.imread(path)
    if img is None:
        return None
    h, w = img.shape[:2]
    s = 1280 / max(h, w)
    if s < 1:
        img = cv2.resize(img, (int(w * s), int(h * s)))
    det.setInputSize((img.shape[1], img.shape[0]))
    _, f = det.detect(img)
    if f is None or len(f) == 0:
        return None
    f = max(f, key=lambda x: x[2] * x[3])
    return rec.feature(rec.alignCrop(img, f))


if __name__ == "__main__":
    refs = [e for e in (emb(p) for p in sys.argv[1].split(",")) if e is not None]
    for p in sys.argv[2:]:
        e = emb(p)
        if e is None:
            print(f"{p}\tNOFACE\tFAIL")
            continue
        sc = max(rec.match(r, e, cv2.FaceRecognizerSF_FR_COSINE) for r in refs)
        print(f"{p}\t{sc:.3f}\t{'PASS' if sc >= PASS else 'FAIL'}")
