class Round:
    def __init__(self, id, start_meter, end_meter, cross_section_type, comment):
        self.id = id
        self.start_meter = start_meter
        self.end_meter = end_meter
        self.cross_section_type = cross_section_type
        self.comment = comment
        self.material = []

    def __str__(self):
        return f'Round(start_meter: {self.start_meter}, end_meter: {self.end_meter}, cross_section_type: {self.cross_section_type}, comment: {self.comment}'
