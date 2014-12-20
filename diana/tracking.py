from . import packet as p

class Tracker:
    def __init__(self):
        self.objects = {}

    def update_object(self, record):
        try:
            oid = record['object']
        except KeyError:
            return
        else:
            self.objects.setdefault(oid, {}).update(record)

    def remove_object(self, oid):
        try:
            del self.objects[oid]
        except KeyError:
            pass

    def rx(self, packet):
        if isinstance(packet, p.ObjectUpdatePacket):
            for record in packet.records:
                self.update_object(record)
        elif isinstance(packet, p.DestroyObjectPacket):
            self.remove_object(packet.object)

