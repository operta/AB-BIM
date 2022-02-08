class Round:
    def __init__(self, start_meter, end_meter, cross_section_type):
        self.start_meter = start_meter
        self.end_meter = end_meter
        self.cross_section_type = cross_section_type
        self.material = []

    def __str__(self):
        return f'Round(start_meter: {self.start_meter}, end_meter: {self.end_meter}, cross_section_type: {self.cross_section_type}'
