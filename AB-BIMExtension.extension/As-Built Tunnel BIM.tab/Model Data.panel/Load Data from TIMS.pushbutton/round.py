class Round:
    def __init__(self, id, start_meter, end_meter, cross_section_type, comment, start_datetime, end_datetime, duration):
        self.id = id
        self.start_meter = start_meter
        self.end_meter = end_meter
        self.cross_section_type = cross_section_type
        self.comment = comment
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.duration = duration
        self.material = []

    def __str__(self):
        return f'Round(start_meter: {self.start_meter}, end_meter: {self.end_meter}, cross_section_type: {self.cross_section_type}, comment: {self.comment}'
