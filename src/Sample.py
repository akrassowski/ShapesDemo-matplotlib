class SampleInfo:
    def __init__(self, loaned_info):
        self.source_guid = loaned_info.source_guid # read-only, not passed into matplotlib
        self.reception_sequence_number = loaned_info.reception_sequence_number
        self.valid = loaned_info.valid

    def __repr__(self):
        return f'{{source_guid: {self.source_guid} reception_seq#: {self.reception_sequence_number} valid: {self.valid}}} '


class SampleData:
    def __init__(self, loaned_data):
        self.x = loaned_data['x']
        self.y = loaned_data['y']
        self.color = loaned_data['color']
        self.shapesize = loaned_data['shapesize']
        self.fillKind = None # = loaned_data.get('fillKind'))
        self.angle = None #loaned_data.get('angle')

    def __repr__(self):
        return f'{{xy: {self.x},{self.y} color: {self.color} size: {self.shapesize} fill: {self.fillKind} angle: {self.angle}}} '

class Sample:
    def __init__(self, loaned):
        self.info = SampleInfo(loaned.info)
        self.data = SampleData(loaned.data)

    def __repr__(self):
        return f'{{data: {self.data} info: {self.info}}} '


