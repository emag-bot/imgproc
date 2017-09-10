
from ImageRecognitionWorker import ImageRecognitionWorker
from DBInterface import DBInterface

def main():
    worker = ImageRecognitionWorker()
    worker.Work()
    #db = DBInterface()
    #db.QueryForLabels(["watch","watch accessory","watch strap"])

if __name__ == "__main__":
    main()