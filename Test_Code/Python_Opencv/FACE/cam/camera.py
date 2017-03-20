#coding=utf-8
import sys
import cv2
import cv2.cv as cv
import time

#start = time.clock()
#img = cv2.imread("./fa01.jpg")

camera = cv2.VideoCapture(0)
camera.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH,640)
camera.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT,480)
cascade_fs='/usr/local/share/OpenCV/haarcascades/haarcascade_profileface.xml'
cascade_fn ='/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt.xml'
cascade = cv2.CascadeClassifier(cascade_fn)
cascade_s = cv2.CascadeClassifier(cascade_fs)


def detect(img, cascade):
    rects = cascade.detectMultiScale(img, scaleFactor=1.3,
            minNeighbors=5, minSize=(30, 30), flags = cv.CV_HAAR_SCALE_IMAGE)
    if len(rects) == 0:
        return []
    rects[:, 2:] += rects[:, :2]
    # print rects
    return rects


def draw_rects(img, rects, color):
    for x1, y1, x2, y2 in rects:
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)


def main():
    while True:
        start = time.clock()
        success, img = camera.read()
        # cv2.imshow("camera", img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        rects = detect(gray, cascade)
        rects_s = detect(gray, cascade_s)
        vis = img.copy()
        draw_rects(vis, rects, (0, 255, 0))
        draw_rects(vis, rects_s, (255, 0, 0))
        end = time.clock()
        print "runtime: %f s" % (end - start)
        cv2.imshow("face", vis)
        key = cv2.waitKey(2)
        c = chr(key & 255)
        if c in ['q', 'Q', chr(27)]:
            break
    print('exit')
    cv2.destroyWindow("camera")
    cv2.destroyWindow("face")
    camera.release()


if __name__ == '__main__':
    main()
