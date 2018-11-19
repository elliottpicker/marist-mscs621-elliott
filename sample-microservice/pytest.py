from __future__ import print_function
import json
from os.path import join, dirname
from watson_developer_cloud import TextToSpeechV1

service = TextToSpeechV1(iam_apikey='PyalNFzdVXqBtZhmuWKGc24FWDKy40s2ML2ViCcJD6MU')



response = service.synthesize(
    'Hello world!', accept='audio/wav',
    voice="en-US_AllisonVoice").get_result()


print(response)

for key, value in response:
    print (key)

