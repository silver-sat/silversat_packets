import numpy as np
from gnuradio import gr
import pmt

class blk(gr.basic_block):
    def __init__(self, sync_tag="sync", window=64):
        gr.basic_block.__init__(
            self,
            name="bit_tag_window_debug",
            in_sig=[np.uint8],
            out_sig=[np.uint8],
        )
        self.sync_tag = pmt.intern(sync_tag)
        self.window = int(window)

    def general_work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]

        nread = self.nitems_read(0)
        n = min(len(inp), len(out))
        if n == 0:
            return 0

        out[:n] = inp[:n]

        tags = self.get_tags_in_window(0, 0, n)
        for t in tags:
            if t.key == self.sync_tag:
                tag_abs = t.offset
                start_abs = tag_abs - self.window
                end_abs = tag_abs + self.window

                # Clamp window to what's actually in this buffer
                start_rel = max(start_abs - nread, 0)
                end_rel = min(end_abs - nread, n)

                bits = inp[start_rel:end_rel].tolist()

                print("\n=== sync tag at abs {} ===".format(tag_abs))
                print("window abs [{}, {}):".format(start_abs, end_abs))
                print("bits ({}): {}".format(len(bits), "".join(str(int(b)) for b in bits)))

        self.consume_each(n)
        return n