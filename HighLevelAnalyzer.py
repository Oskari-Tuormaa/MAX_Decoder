# High Level Analyzer
# For more information and documentation, please go to https://support.saleae.com/extensions/high-level-analyzer-extensions

from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame
from enum import Enum


def is_ascii(b: int) -> bool:
    return b >= 0x30 and b <= 0x39 or b >= 0x41 and b <= 0x46

# High level analyzers must subclass the HighLevelAnalyzer class.
class Hla(HighLevelAnalyzer):
    # An optional list of types this analyzer produces, providing a way to customize the way frames are displayed in Logic 2.
    result_types = {
        'start_frame': {
            'format': '[Start]'
        },
        'end_frame': {
            'format': '[End]'
        },
        'data': {
            'format': '{{data.data}}'
        },
    }

    class State(Enum):
        WAITING = 0
        COLLECTING = 1

    class Message(Enum):
        STX = 0x02
        ETX = 0x03

        # two bytes, a, b
        @staticmethod
        def PAYLOAD(a, b):
            achar = chr(a)
            bchar = chr(b)

            comb = achar + bchar
            val = int(comb, base=16)
            return f"{val:02X}"

    def __init__(self):
        '''
        Initialize HLA.

        Settings can be accessed using the same name used above.
        '''
        self.state = self.State.WAITING
        self.frame_buffer = []

    def parse_frames(self):
        # Add start frame
        print("[ ", end="")
        output_frames = [
            AnalyzerFrame('start_frame', self.frame_buffer[0].start_time, self.frame_buffer[0].end_time, {})
        ]

        pairs = zip(
            self.frame_buffer[1:-1:2],
            self.frame_buffer[2:-1:2],
        )
        for frame1, frame2 in pairs:
            data = self.Message.PAYLOAD(frame1.data['data'][0], frame2.data['data'][0])
            print(f"{data} ", end="")
            output_frames.append(
                AnalyzerFrame('data',
                              frame1.start_time,
                              frame2.end_time,
                              {'data': data})
            )

        # Add end frame
        print("]")
        output_frames.append(
            AnalyzerFrame('end_frame', self.frame_buffer[-1].start_time, self.frame_buffer[-1].end_time, {})
        )

        return output_frames

    def decode(self, frame: AnalyzerFrame):
        '''
        Process a frame from the input analyzer, and optionally return a single `AnalyzerFrame` or a list of `AnalyzerFrame`s.

        The type and data values in `frame` will depend on the input analyzer.
        '''

        b = frame.data['data'][0]

        if self.state == self.State.WAITING:
            if b == self.Message.STX.value:
                self.frame_buffer = [frame]
                self.state = self.State.COLLECTING

        elif self.state == self.State.COLLECTING:
            if b == self.Message.ETX.value:
                self.state = self.State.WAITING
                self.frame_buffer.append(frame)
                if len(self.frame_buffer) % 2 == 0:
                    return self.parse_frames()
            elif is_ascii(b):
                self.frame_buffer.append(frame)
            else:
                self.state = self.State.WAITING


