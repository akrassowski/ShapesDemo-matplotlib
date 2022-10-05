

import json

def check_shapes(shape):    
    n = shape[0].upper()
    if 'C' == n: print("circle")
    elif 'S' == n: print("square")
    elif 'T' == n: print("Triangle")

with open('pub_s_t.cfg', 'r') as cfg_file:
    cfg = json.load(cfg_file)
    for act in cfg.keys():
        action = act[0:3].upper()
        if "PUB" == action: 
            print('pub')
            for shape in cfg[act].keys():
                check_shapes(shape)
                color, size, fill, angle = "BLUE", 30, None, 0
                for attr in cfg[act][shape].keys():
                    attru = attr.upper()
                    value = cfg[act][shape][attr]
                    if type(value) is str: 
                        value = value.upper()
                    if attru == "COLOR": 
                        color = value
                    elif attru == "SIZE":
                        size = value
                    elif attru == "ANGLE":
                        angle = value
                    elif attru == "FILL":
                        fill = value
                print(color, size, fill, angle)
                  

        if "SUB" == action: 
            print('sub')
            check_shapes(cfg[act])

    
