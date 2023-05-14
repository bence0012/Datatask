import json
import cv2
import os
import numpy as np

def get_first_key_str(s):
  for key in s:
    return key

def build_output_element(label):
  shape=label['shape']
  element={'track_id':str(label['Trackid']),
                 'category':label['category'],
                 'attributes':[],
                 'coordinates':[{'x':list_to_str_list(shape['x'])},
                                {'y':list_to_str_list(shape['y'])}]}
  for attribute in label['attributes']:
    element['attributes'].append({attribute:label['attributes'][attribute][0].split(",")})
  return element

def list_to_str_list(x):
  return list(map(str,x))

def create_output(data, dictionary):
  error=""
  output={'frames': []}
  for element in data:
    frame={'frame_id':str(element['FrameNumber']),'box':[], '2dcuboid':[]}

    for label in element['FrameObjectLabels']:
      newinstance=build_output_element(label)
      ltype=label['shape']['type']
      frame[ltype.lower()].append(newinstance)
      error+=check_mandatory_values(label,dictionary)
    
    output['frames'].append(frame)
  if error!="":
    with open("error.txt","w") as outfile:
      outfile.write(error)
    raise Exception("Error, check error.txt")
  return output

def check_mandatory_values(label,mandatories):
  error_msg=""
  if label['category'] in mandatories:
      for attrib in mandatories[label['category']]:
        try:
          if label['attributes'][attrib][0] not in mandatories[label['category']][attrib]['Values']:
            error_msg+="Bad value in mandatory attribute: \nHas: "+ str(label['attributes'][attrib])+ "\nNeeds: "+ str(mandatories[label['category']][attrib]['Values'])+ "\n"
        except:
          error_msg+='Doesnt have the mandatory attribute: \nHas: ' + str(label['attributes']) +"\nNeeds: "+ attrib+"\n"
  return error_msg

def save_to_json(output, name):
  jsonobj=json.dumps(output,indent=2)
  with open(name,"w") as outfile:
    outfile.write(jsonobj)

def find_mandatories(schema):
  dictionary={}
  for element in schema:
    try:
        name=element['Category']
        dictionary[name]={}
        for attribs in element['Attributes']:
          key=get_first_key_str(attribs)
          if attribs[key]['Mandatory']=='Yes':
            dictionary[name][key]=attribs[key]
    except:
      dictionary.pop(name)
  return dictionary

def main():
    for j in range(0,2):
      f=open('result_{}.json'.format(j+1))
      data=json.load(f)
      data=data['Sequence'][0]['ObjectLabels']
      f=open('schema.json')
      schema=json.load(f)
      schema=schema['LabelConfig']['Anno Elements']

      dictionary=find_mandatories(schema)
        
      output=create_output(data,dictionary)
      save_to_json(output,'output{}.json'.format(j+1))

      images={}
      for filename in os.listdir('images'):
        images[filename.removesuffix('.jpg')]=cv2.imread('images/'+filename)
      
      for element in data:
        currimg=images[element['TimeStamp']]
        for obj in element['FrameObjectLabels']:
          x=obj['shape']['x']
          y=obj['shape']['y']
          vals=[]
          for i in range(0,len(x)):
            vals.append([x[i],y[i]])
          vals=np.array(vals,np.int32)
          cv2.polylines(currimg,[vals],True,(0,0,255),3)
        cv2.imwrite(element['TimeStamp']+'new.jpg',currimg)
      


if __name__ == "__main__":
    main()