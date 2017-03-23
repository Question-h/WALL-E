import cv2
import numpy as np
import time


cv = cv2.cv

start = time.clock()
img = cv2.imread("./test.jpg")

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
color = (255, 0, 0)  # red
classfier = cv2.CascadeClassifier("/usr/share/opencv/haarcascades/haarcascade_frontalface_alt.xml")
print(classfier)
# size of img
size = img.shape[:2]
print(size)
image = np.zeros(size, dtype=np.float16)
image = cv2.cvtColor(img, cv2.cv.CV_BGR2GRAY)
cv2.imwrite('./face2.jpg', image)
cv2.equalizeHist(image, image)
cv2.imwrite('./face3.jpg', image)

divisor = 8
h, w = size
minSize = (w / divisor, h / divisor)

# haarCascade = cv.Load('/usr/share/opencv/haarcascades/haarcascade_frontalface_alt.xml')
# faceRects = cv.HaarDetectObjects(image,haarCascade,cv.CreateMemStorage(),1.2, 2,cv.CV_HAAR_DO_CANNY_PRUNING,(50, 50))
# cascade = cv2.cv.cvLoadHaarClassifierCascade('haarcascade_frontalface_alt.xml',cv2.cv.cvSize(1,1))
# faceRects = classfier.detectMultiScale(image, 1.2, 2, cv2.CASCADE_SCALE_IMAGE,minSize)
# if len(faceRects) >0:
    # print("faceRects")
# print(faceRects)

# gray = cv2.equalizeHist(gray)
# cv2.imwrite('./face4.jpg',gray)
facerects = classfier.detectMultiScale(gray, scaleFactor=1.3,
                                            minNeighbors=5, minSize=(30, 30), flags = cv.CV_HAAR_SCALE_IMAGE)
print(facerects)
if len(facerects) > 0:
    for facerect in facerects:
        x, y, w, h = facerect
        cv2.rectangle(img, (x, y), (x + w, y + h), color)
        cv2.circle(img, (x + w / 2, y + h / 2), 2, color, 2, 8, 0)
cv2.imwrite('./ok.jpg', img)
end = time.clock()

print "runtime: %f s" % (end - start)


if __name__ == '__main__':
    main()

