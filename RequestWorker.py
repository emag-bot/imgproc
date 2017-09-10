
from gearman import GearmanWorker
from ImageAnalyser import ImageAnalyser, PathLocation
import json
import time

class RequestWorker:
    worker = None

    def __init__(self):
        self.worker = GearmanWorker(['gearman.emag-bot.com'])
        self.worker.register_task('getrawdata', self.GetRawData)

    def Work(self):
        self.worker.work()
    
    def GetRawData(self, worker, job):
        print("Got job: " + job.data)

        ima = ImageAnalyser()

        ima.LoadImage(job.data, PathLocation.ONLINE)
        contour = ima.FindContour()
        im_e = ima.ExtractContour(contour)
        #ima.ShowImage(im_e, "mask")

        hist = ima.GetHueHistogram(im_e)

        return json.dumps(hist.flatten().tolist())