

def IDGenerator(startId, step = 1):
    currentId = [startId]
    tidTable = {}

    def createId(tid = None):

        if tid in tidTable:
            resultId = tidTable[tid]
        else:
            resultId = currentId[0]
            currentId[0] += step

            if tid:
                tidTable[tid] = resultId

        return resultId

    return createId
