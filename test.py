import argparse
import struct
import sys
from threading import Thread

import pvporcupine
from pvrecorder import PvRecorder

class PorcupineDemo(Thread):
    def __init__(self, access_key, device_index, sensitivity):
        super(PorcupineDemo, self).__init__()

        self._device_index = device_index
        self._keywords = ["Hey-Howey"]
        self._porcupine = pvporcupine.create(access_key=access_key, keywords=self._keywords, sensitivities=[sensitivity] * 1)

    def run(self):
        recorder = None

        try:
            recorder = PvRecorder(device_index=self._device_index, frame_length=self._porcupine.frame_length)
            recorder.start()

            print('[Listening ...]')

            while True:
                pcm = recorder.read()
                keyword_index = self._porcupine.process(pcm)
                if keyword_index >= 0:
                    print("detected '%s'" % self._keywords[keyword_index])
                    # self._set_color(COLORS_RGB[KEYWORDS_COLOR[self._keywords[keyword_index]]])
        except KeyboardInterrupt:
            sys.stdout.write('\b' * 2)
            print('Stopping ...')
        finally:
            if recorder is not None:
                recorder.delete()

            self._porcupine.delete()

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--audio_device_index', help='Index of input audio device.', type=int, default=-1)

    args = parser.parse_args()

    o = PorcupineDemo(access_key="hW2ayLGCpyhg+w/tHHFFcpr0Df+zGciHcgdSSO9TcYDzpuimmsh8fg==",
                      device_index=args.audio_device_index,
                      sensitivity=0.6)
    o.run()


if __name__ == '__main__':
    main()
