
from gearman import GearmanWorker
from DBInterface import DBInterface
from ImageAnalyser import ImageAnalyser, PathLocation
import numpy as np
import json
import cv2

class ImageRecognitionWorker:
    worker = None
    db = None

    def __init__(self):
        self.worker = GearmanWorker(['gearman.emag-bot.com'])
        self.worker.register_task('imgrecon', self.ImageRecognition)

        self.db = DBInterface()

    def Work(self):
        self.worker.work()
    
    def ComputeHistogram(self, url):
        ima = ImageAnalyser()
        ima.LoadImage(url, PathLocation.ONLINE)
        contour = ima.FindContour()
        im_e = ima.ExtractContour(contour)
        #ima.ShowImage(im_e)
        hist = ima.GetHueHistogram(im_e)

        return hist
    
    def ImageRecognition(self, worker, job):
        print("Got job: " + job.data)
        data = json.loads(job.data)
        hist = self.ComputeHistogram(data['url'])

        db_entries = self.db.QueryForLabels(data['labels'])

        accepted_entries = [[], []]
        i = 0
        for row in db_entries:
            #print(row)
            if row[3] is None or row[3] == '':
                continue

            data = json.loads(row[3])
            data = np.array([[d] for d in data], dtype=np.float32)
            res = cv2.compareHist(hist, data, cv2.HISTCMP_CORREL)

            if res >= 0.7:
                if row[4] in accepted_entries[1]:
                    idx = accepted_entries[1].index(row[4])
                    if res > accepted_entries[0][idx]:
                        accepted_entries[0][idx] = res
                else:
                    accepted_entries[0].append(res)
                    accepted_entries[1].append(row[4])
            
        ret = [x for _,x in sorted(zip(accepted_entries[0], accepted_entries[1]), reverse=True)]
        print(ret)
        
        return json.dumps(ret)