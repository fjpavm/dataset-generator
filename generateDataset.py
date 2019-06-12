import itertools
from itertools import repeat
import random
import json
import numbers
import datetime

dataFramesPerSecond = 5


def smoothStep(minT, maxT, t):
    x = (t - minT)/(maxT-minT)
    return x*x*(3.0-2.0*x)

def smoothInterpolate(initVal, endVal, initTime, endTime, step):
    valueRange = endVal-initVal
    timeRangeInt = int((endTime-initTime)/step + 0.5)
    return (valueRange*smoothStep(initTime, endTime, t) + initVal for t in ( initTime + (0.5 + r)*step for r in range(0, timeRangeInt, 1)))

def linearInterpolate(initVal, endVal, initTime, endTime, step):
    valueRange = endVal-initVal
    timeRange = (endTime-initTime)
    timeRangeInt = int((endTime-initTime)/step + 0.5)
    return (valueRange*(t - initTime)/timeRange + initVal for t in ( initTime + (0.5 + r)*step for r in range(0, timeRangeInt, 1)))

def stepInterpolate(initVal, endVal, initTime, endTime, step):
    timeRangeInt = int((endTime-initTime)/step + 0.5)
    return ((initVal if t == initTime else endVal) for t in ( initTime + (0.5 + r)*step for r in range(0, timeRangeInt, 1)))
 
interpolateFuncs = [smoothInterpolate, linearInterpolate, stepInterpolate]

def genSingleLine(size, defaultValue, lineDescription):
    singleLine = [defaultValue] * size
    for event in lineDescription:
        interpolate = event['interpolate'] if 'interpolate' in event else False
        st = event['start']
        ed = event['end']
        if not interpolate:
            singleLine[st:ed] = repeat( event['value'], ed-st) 
        else:
            singleLine[st:ed] = random.choice(interpolateFuncs)(event['startValue'], event['endValue'], st, ed, 1)
    return singleLine

def readJsonFromFile(filename):
    with open(filename) as fp:
        situationFileJson = json.load(fp)
    return situationFileJson 

def writeJsonToFile(filename, jsonToWrite, indent = 4):
    with open(filename, 'w') as outfile:
        json.dump(jsonToWrite, outfile, indent = indent)
        outfile.write("\n")

def determineFloatNumber(durationJson):
    if isinstance(durationJson, numbers.Number):
        return durationJson
    return random.uniform(durationJson['min'], durationJson['max'])

def determineRef(refJson, previousEvents, duration):
    if refJson == 'start':
        return 0.0
    if refJson == 'end':
        return duration
    if refJson == 'prev_start':
        return previousEvents[-1]['start']
    if refJson == 'prev_end':
        prevEventInst = previousEvents[-1]
        return prevEventInst['start'] + prevEventInst['duration']
    return nan

def determineEventTiming(startJson, previousEvents, duration):
    if isinstance(startJson, numbers.Number):
        return startJson
    if isinstance(startJson, str):
        return 0.0 if startJson.lower() == 'start' else duration if startJson.lower() == 'end' else nan
    refTiming = 0.0 
    if 'ref' in startJson:
        refTiming = determineRef(startJson['ref'], previousEvents, duration)
    return refTiming + determineFloatNumber(startJson)


def genSituation(inputsJson, situationJson):
    duration = determineFloatNumber(situationJson['duration'])
    numInputs = len(inputsJson)
    durationInFrames = int(dataFramesPerSecond * duration)
    eventInstances = []
    for event in situationJson['events']:
        eventInst = {}
        eventInst['start'] = determineEventTiming(event['start'], eventInstances, duration)
        eventDuration = float('NaN')
        if 'end' in event:
            eventDuration = determineEventTiming(event['end'], eventInstances, duration) - eventInst['start']
        if 'duration' in event:
            eventDuration = determineFloatNumber(event['duration'])
        eventInst['duration'] = min(duration, eventDuration)
        for key,data in event.items():
            if key not in ['start', 'end', 'duration']:
                eventInst[key] = data
        eventInstances.append(eventInst)
    #print(str(eventInstances))
        
    # generate lineDescriptions from eventInstances  
    lineDescriptions = {}
    for input in inputsJson:
        lineDescriptions[input['id']] = []
        for eventInst in eventInstances:
            if eventInst['input_id'] == input['id']:
                if input['type'] == 'real':
                    startDur = eventInst['duration'] *0.1
                    endStart = eventInst['duration'] *0.9
                    midPoint = random.uniform(startDur, endStart)
                    eventFramesStart = {}
                    eventFramesStart['start'] = int(eventInst['start']*dataFramesPerSecond)
                    eventFramesStart['end'] = int((eventInst['start'] + startDur)*dataFramesPerSecond)
                    eventFramesStart['interpolate'] = True
                    eventFramesStart['startValue'] = input['default']
                    eventFramesStart['endValue'] = determineFloatNumber(eventInst['value'])
                    lineDescriptions[input['id']].append(eventFramesStart)
                    eventFramesToMid = {}
                    eventFramesToMid['start'] = int((eventInst['start'] + startDur)*dataFramesPerSecond)
                    eventFramesToMid['end'] = int((eventInst['start'] + midPoint)*dataFramesPerSecond)
                    eventFramesToMid['interpolate'] = True
                    eventFramesToMid['startValue'] = eventFramesStart['endValue']
                    eventFramesToMid['endValue'] = determineFloatNumber(eventInst['value'])
                    lineDescriptions[input['id']].append(eventFramesToMid)
                    eventFramesFromMid = {}
                    eventFramesFromMid['start'] = int((eventInst['start'] + midPoint)*dataFramesPerSecond)
                    eventFramesFromMid['end'] = int((eventInst['start'] + endStart)*dataFramesPerSecond)
                    eventFramesFromMid['interpolate'] = True
                    eventFramesFromMid['startValue'] = eventFramesToMid['endValue']
                    eventFramesFromMid['endValue'] = determineFloatNumber(eventInst['value'])
                    lineDescriptions[input['id']].append(eventFramesFromMid)
                    eventFramesEnd = {}
                    eventFramesEnd['start'] = int((eventInst['start'] + endStart)*dataFramesPerSecond)
                    eventFramesEnd['end'] = int((eventInst['start'] +  eventInst['duration'])*dataFramesPerSecond)
                    eventFramesEnd['interpolate'] = True
                    eventFramesEnd['startValue'] = eventFramesFromMid['endValue']
                    eventFramesEnd['endValue'] = input['default']
                    lineDescriptions[input['id']].append(eventFramesEnd)
                else:
                    eventFrames = {}
                    eventFrames['start'] = int(eventInst['start']*dataFramesPerSecond)
                    eventFrames['end'] = (int(eventInst['start'] + eventInst['duration'])*dataFramesPerSecond)
                    eventFrames['value'] = eventInst['value']
                    lineDescriptions[input['id']].append(eventFrames)     
    
    #print(json.dumps(lineDescriptions, indent=4))                
       
    resultingData = {}
    for input in inputsJson:
        resultingData[input['id']] = genSingleLine(size=durationInFrames, defaultValue=input['default'],lineDescription= lineDescriptions[input['id']])
        #print(str(input['name']) + ':' + str(resultingData[input['id']]))
    #print('numInputs:' + str(numInputs) + ' duration:' + str(duration))
    resultingData['situation_id'] = genSingleLine(size=durationInFrames, defaultValue=situationJson['id'],lineDescription= [])
    
    return resultingData

def determineIntNumber(numberJson):
    if isinstance(numberJson, numbers.Number):
        return numberJson
    return random.randint(numberJson['min'], numberJson['max'])

def genSituationSequence(situationsJson, aversiveID, numAversive, aversiveSeparation, length):
    nonAversiveIDs = [sitJson['id'] for sitJson in situationsJson if sitJson['id'] != aversiveID] 
    numAversive = determineIntNumber(numAversive)
    genAversive = 0
    resultSeq = [random.choice(nonAversiveIDs) for x in range(length)]
    while genAversive != numAversive:
        numAversive = determineIntNumber(numAversive)
        genAversive = 0
        currentAversive = determineIntNumber(aversiveSeparation)
        resultSeq = [random.choice(nonAversiveIDs) for x in range(length)]
        while currentAversive < length:
            resultSeq[currentAversive] = aversiveID
            currentAversive += determineIntNumber(aversiveSeparation)
            genAversive += 1
    return resultSeq    

def genAndExportSituationSequence(filename, situationFileJson):
    aversiveID=0
    numAversive=28
    aversiveSeparation={'min' : 4, 'max' : 50}
    length=553
    situationSequence = genSituationSequence(situationFileJson['situations'], aversiveID=aversiveID, numAversive=numAversive, aversiveSeparation=aversiveSeparation, length=length)
    situationSequenceJson = {'situations' : situationFileJson['situations']}
    situationSequenceGenParamJson = {'aversiveID' : aversiveID, 'numAversive' : numAversive, 'aversiveSeperation' : aversiveSeparation, 'length' : length}
    situationSequenceJson['genParams'] = situationSequenceGenParamJson
    situationSequenceJson['sequence'] = situationSequence
    situationSequenceJson['genDateTime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    writeJsonToFile(filename, situationSequenceJson)
        
def appendSituationInstance(situationInstanceSequence, newSituationInstance):
    for inputID in situationInstanceSequence:
        situationInstanceSequence[inputID].extend(newSituationInstance[inputID])
        
def genSituationSequenceInstance(situationSequence, situationFileJson):
    inputsJson = situationFileJson['inputs']
    resultSequenceInstance = genSituation(inputsJson, {'duration':0.0, 'events':[], 'id':-1})
    #print(json.dumps(resultSequenceInstance, indent=4))
    for situationID in situationSequence:
        situationJson = situationFileJson['situations'][situationID]
        situationInstance = genSituation(inputsJson, situationJson)
        appendSituationInstance(resultSequenceInstance, situationInstance)
    return resultSequenceInstance

def genAndExportSituationSequenceInstance(outputFilename, situationFileJson, situationSequenceJson):
    situationSequenceInstanceJson = {'situationFileJson' : situationFileJson, 'situationSequenceJson':situationSequenceJson}
    situationSequenceInstanceJson['sequenceInstance'] = genSituationSequenceInstance(situationSequenceJson['sequence'], situationFileJson)
    situationSequenceInstanceJson['genDateTime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    writeJsonToFile(outputFilename, situationSequenceInstanceJson)
    
if __name__ == '__main__':
    situationFileJson = readJsonFromFile("situations.json")
    situationSequenceJson = readJsonFromFile('situationSequence.json')
    
    for i in range(10):
        genAndExportSituationSequenceInstance('sitSeq_'+str(i)+'.json', situationFileJson, situationSequenceJson)


    