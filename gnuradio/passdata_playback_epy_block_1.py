import numpy as np
from gnuradio import gr
import pmt

class blk(gr.basic_block):
    """
    Bit-domain frame framer for:
      [SYNC (32 bits: 0x33 0x55 0x33 0x55)]
      [LEN (1 byte)]
      [EXTRA + PAYLOAD (LEN bytes, starting at EXTRA)]

    Input:
      - Live bitstream (1 bit per item, uint8 0/1) with 'sync' tags from
        Correlate Access Code - Tag.

    Output:
      - PDUs (u8vector) containing [EXTRA, PAYLOAD ...] only.
      - No meaningful stream output (out_sig = []).
    """

    def __init__(self, sync_tag="sync", code_len_bits=32):
        gr.basic_block.__init__(
            self,
            name="bit_frame_framer",
            in_sig=[np.uint8],
            out_sig=[],
        )

        self.sync_tag = pmt.intern(sync_tag)
        self.code_len_bits = int(code_len_bits)

        # Rolling bit buffer and its starting absolute bit index
        self.bit_buffer = []            # list of 0/1
        self.buffer_start_abs = 0       # absolute offset of bit_buffer[0]
        self.pending_sync_offsets = []  # absolute bit offsets of sync END bits

        # PDU output
        self.message_port_register_out(pmt.intern("pdus"))

        self.initialized = False

    def _try_extract_frames(self):
        """
        Try to extract as many complete frames as possible from bit_buffer
        based on pending sync offsets.
        """
        new_pending = []

        for sync_end_abs in self.pending_sync_offsets:
            # Correlator tag is assumed on LAST bit of sync.
            # First bit of LEN is at sync_end_abs + 1.
            len_start_abs = sync_end_abs # + 1  # <-- if tag is already after sync, drop '+ 1'

            len_start_rel = len_start_abs - self.buffer_start_abs
            if len_start_rel < 0:
                # This sync refers to bits we've already dropped
                continue

            # Need 8 bits for LEN
            if len_start_rel + 8 > len(self.bit_buffer):
                new_pending.append(sync_end_abs)
                continue

            # Read LEN (1 byte, MSB-first)
            length_bits = self.bit_buffer[len_start_rel:len_start_rel+8]
            length_byte = 0
            for b in length_bits:
                length_byte = (length_byte << 1) | int(b)

            if length_byte <= 0:
                # Invalid length; drop this sync
                continue

            # EXTRA+PAYLOAD is LEN bytes = LEN * 8 bits
            frame_bits_needed = length_byte * 8
            data_start_rel = len_start_rel + 8      # first bit of EXTRA
            data_end_rel = data_start_rel + frame_bits_needed

            if data_end_rel > len(self.bit_buffer):
                # Not enough bits yet for full frame
                new_pending.append(sync_end_abs)
                continue

            # We have a full frame [EXTRA+PAYLOAD]
            frame_bits = self.bit_buffer[data_start_rel:data_end_rel]

            # Pack bits into bytes (MSB-first)
            bytes_out = []
            for i in range(0, len(frame_bits), 8):
                byte_bits = frame_bits[i:i+8]
                val = 0
                for b in byte_bits:
                    val = (val << 1) | int(b)
                bytes_out.append(val)

            # Prepend LENGTH byte so PDU = [LEN, EXTRA, PAYLOAD...]
            bytes_out = [length_byte] + bytes_out

            # Emit PDU: [EXTRA, PAYLOAD...]
            vec = np.array(bytes_out, dtype=np.uint8)
            meta = pmt.make_dict()
            payload = pmt.init_u8vector(len(vec), vec.tolist())
            pdu = pmt.cons(meta, payload)
            self.message_port_pub(pmt.intern("pdus"), pdu)

            # Optionally, drop bits up to end of this frame to bound buffer size
            # and avoid re-processing the same region.
            drop_abs_until = self.buffer_start_abs + data_end_rel
            drop_count = drop_abs_until - self.buffer_start_abs
            if drop_count > 0:
                self.bit_buffer = self.bit_buffer[drop_count:]
                self.buffer_start_abs = drop_abs_until

        self.pending_sync_offsets = new_pending

        # Additional trimming if no pending syncs (keep a small tail)
        if not self.pending_sync_offsets and len(self.bit_buffer) > 8 * 1024:
            # Keep last 1 KB of bits
            keep = 8 * 1024
            drop_count = len(self.bit_buffer) - keep
            self.bit_buffer = self.bit_buffer[drop_count:]
            self.buffer_start_abs += drop_count

    def general_work(self, input_items, output_items):
        inp = input_items[0]

        nread = self.nitems_read(0)
        n_in = len(inp)
        if n_in == 0:
            return 0

        # Initialize buffer_start_abs on first call
        if not self.initialized:
            self.buffer_start_abs = nread
            self.initialized = True

        # Append bits to buffer
        self.bit_buffer.extend(int(b) & 1 for b in inp)

        # Collect sync tags in this window
        tags = self.get_tags_in_window(0, 0, n_in)
        for t in tags:
            if t.key == self.sync_tag:
                # Tag is on LAST bit of sync
                sync_end_abs = t.offset
                self.pending_sync_offsets.append(sync_end_abs)

        # Try to extract frames
        self._try_extract_frames()

        # We have no stream outputs; just consume input
        self.consume_each(n_in)
        return 0

