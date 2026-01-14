import os, sys
from datetime import datetime
import numpy as np
from gnuradio import gr
import pmt
import reedsolo
from dataclasses import dataclass
import sqlite3 


PROJECT_ROOT = os.getenv('SILVERSAT_ROOT')
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DB_PATH = os.path.join(PROJECT_ROOT, "observations.db")
print(f"[packet_logger] DB PATH: {DB_PATH}")


# this is the generic set of information you would need to construct/deconstruct an IL2P or an AX.25 packet
@dataclass
class Il2pPacket:
    packet_error_type: list
    processing_run_id: int = 0
    header: bytearray = b''
    header_parity: bytearray = b''  # two bytes
    header_corrections: int = 0
    payload: bytearray = b''
    payload_parity: bytearray = b''  # 16 bytes
    payload_corrections: int = 0
    encoded_crc: bytearray = b''  # 4 bytes while encoded
    header_okay: bool = False
    payload_okay: bool = False
    scrambler_okay: bool = False
    crc_success: bool = False  # set true when verified
    payload_byte_count: int = 0  # zero by default
    packet_len: int = 0
    packet_index: int = 0


def list_to_string_str_only(lst, separator=", "):
    if not all(isinstance(item, str) for item in lst):
        raise ValueError("All elements must be strings for this method.")
    return separator.join(lst)


def store_packet(packet): 
    try: 
        conn = sqlite3.connect(DB_PATH) 
        cur = conn.cursor() 
        cur.execute(
            """ INSERT INTO packet (
                length_bytes,
                processing_run_id,
                header_hex,
                header_parity_hex,
                payload_hex,
                payload_parity_hex,
                crc_hex,
                header_ok,
                payload_ok,
                crc_ok,
                scrambler_ok,
                packet_error_type,
                payload_byte_count, 
                packet_index
                ) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) """, 
                (packet.packet_len, packet.processing_run_id, packet.header, packet.header_parity, 
                    packet.payload, packet.payload_parity, 
                    packet.encoded_crc, packet.header_okay, 
                    packet.payload_okay, packet.crc_success, 
                    packet.scrambler_okay, list_to_string_str_only(packet.packet_error_type), 
                    packet.payload_byte_count, packet.packet_index)) 
        conn.commit() 
        conn.close() 
    except Exception as e: 
        print(f"[packet_logger] DB insert error: {e}") 


class il2p_decoder(gr.basic_block):

    # IL2P CRC decode table
    decode_table = [
        0x0,0x0,0x0,0x3,0x0,0x5,0xe,0x7,
        0x0,0x9,0xe,0xb,0xe,0xd,0xe,0xe,
        0x0,0x3,0x3,0x3,0x4,0xd,0x6,0x3,
        0x8,0xd,0xa,0x3,0xd,0xd,0xe,0xd,
        0x0,0x5,0x2,0xb,0x5,0x5,0x6,0x5,
        0x8,0xb,0xb,0xb,0xc,0x5,0xe,0xb,
        0x8,0x1,0x6,0x3,0x6,0x5,0x6,0x6,
        0x8,0x8,0x8,0xb,0x8,0xd,0x6,0xf,
        0x0,0x9,0x2,0x7,0x4,0x7,0x7,0x7,
        0x9,0x9,0xa,0x9,0xc,0x9,0xe,0x7,
        0x4,0x1,0xa,0x3,0x4,0x4,0x4,0x7,
        0xa,0x9,0xa,0xa,0x4,0xd,0xa,0xf,
        0x2,0x1,0x2,0x2,0xc,0x5,0x2,0x7,
        0xc,0x9,0x2,0xb,0xc,0xc,0xc,0xf,
        0x1,0x1,0x2,0x1,0x4,0x1,0x6,0xf,
        0x8,0x1,0xa,0xf,0xc,0xf,0xf,0xf
    ]

    def __init__(self, lfsr_seed=0x1F0, output_dir="", processing_run_id=0, store_packets=0):
        """
        lfsr_seed:   9-bit seed for self-synchronizing descrambler
        output_dir:  directory where payload file will be written
        processing_run_id: unique identifier for this processing run
        store_packets: 1 = store packets to the database, 0 = do not store
        """
        
        flowgraph_dir = os.path.join(PROJECT_ROOT, "gnuradio")
        output_dir = os.path.join(PROJECT_ROOT, "received_packets")

        # DB_PATH = os.path.join(PROJECT_ROOT, "observations.db")

        gr.basic_block.__init__(
            self,
            name="il2p_rs_and_descramble_crc",
            in_sig=[],
            out_sig=[]
        )

        # Scrambler state
        self.lfsr_seed = lfsr_seed & 0x1FF

        # RS codecs
        self.rs_header = reedsolo.RSCodec(2)
        self.rs_payload = reedsolo.RSCodec(16)

        # AX.25 header (fixed)
        self.ax25_header = bytes([
            0xAE,0xA0,0x64,0xB0,0x8E,0xAE,0x00,0xAE,
            0xA0,0x64,0xB0,0x8E,0xAE,0x01,0x03,0xF0
        ])

        # Output file setup
        self.output_dir = output_dir
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except Exception as e:
            print(f"[IL2P] Warning: could not create output_dir '{self.output_dir}': {e}")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_path = os.path.join(self.output_dir, f"il2p_payloads_{ts}.bin")
        try:
            # Unbuffered append-binary; one file per run
            self.outfile = open(self.output_path, "ab", buffering=0)
            print(f"[IL2P] Writing raw payloads to: {self.output_path}")
        except Exception as e:
            self.outfile = None
            print(f"[IL2P] ERROR: could not open output file '{self.output_path}': {e}")
            
        try:
            conn = sqlite3.connect(DB_PATH) 
            cur = conn.cursor()
            cur.execute(
            "UPDATE processing_run SET output_file = ? WHERE id = ?", (self.output_path, processing_run_id)) 
            conn.commit()
            conn.close()
        except Exception as e: 
            print(f"[packet_logger] DB update error on output file: {e}") 

        # Message ports
        self.message_port_register_in(pmt.intern("pdus"))
        self.set_msg_handler(pmt.intern("pdus"), self.handle_pdu)
        self.message_port_register_out(pmt.intern("out"))
        
        # variables
        self.processing_run_id = processing_run_id  # the unique id of this processing run
        self.packet_index = 0  # a incrementing counter for this processing run
        self.store_packets = store_packets  # 1 = store packets to the database
        

    # ------------------------------------------------------------
    # Self-synchronizing descrambler
    # ------------------------------------------------------------
    def _descramble_bits(self, scrambled_bytes):
        state = self.lfsr_seed
        out_bytes = bytearray(len(scrambled_bytes))

        for b in range(len(scrambled_bytes)):
            out_byte = 0
            for i in range(8):
                mask = 0x80 >> i
                in_bit = 1 if (scrambled_bytes[b] & mask) else 0

                out_bit = (in_bit ^ (state & 1)) & 1
                state = (state >> 1)
                state ^= (in_bit << 8)
                state ^= (in_bit << 3)
                state &= 0x1FF

                if out_bit:
                    out_byte |= mask

            out_bytes[b] = out_byte

        return bytes(out_bytes)


    # ------------------------------------------------------------
    # Scrambler state validator
    # ------------------------------------------------------------
    def _validate_scrambler(self, scrambled, descrambled):
        """
        Re-scramble descrambled bytes and compare to original scrambled bytes.
        Returns True if all bytes match.
        """
        state = self.lfsr_seed
        for b in range(len(descrambled)):
            out_byte = 0
            for i in range(8):
                mask = 0x80 >> i
                plain_bit = 1 if (descrambled[b] & mask) else 0

                # Transmit scrambler
                # scr_bit = plain_bit XOR (state & 1)
                scr_bit = plain_bit ^ (state & 1)

                # Feedback uses the SCRAMBLED bit (self-synchronizing scrambler)
                state = (state >> 1)
                state ^= (scr_bit << 8)
                state ^= (scr_bit << 3)
                state &= 0x1FF

                if scr_bit:
                    out_byte |= mask

            if out_byte != scrambled[b]:
                print(f"[IL2P] SCR mismatch at byte {b}: exp={scrambled[b]:02X}, got={out_byte:02X}")
                return False

        return True


    # ------------------------------------------------------------
    # Decode 10-bit payload length from header
    # ------------------------------------------------------------
    def _decode_len_from_header(self, header_plain):
        val = 0
        for i in range(2, 12):
            bit = (header_plain[i] >> 7) & 1
            val = (val << 1) | bit
        return val


    # ------------------------------------------------------------
    # CRC-16/X.25 (AX.25 FCS)
    # ------------------------------------------------------------
    def _crc16_x25(self, data):
        crc = 0xFFFF
        for b in data:
            crc ^= b
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0x8408
                else:
                    crc >>= 1
        return crc ^ 0xFFFF


    # ------------------------------------------------------------
    # Main PDU handler
    # ------------------------------------------------------------
    def handle_pdu(self, msg): 
        vec = pmt.cdr(msg)
        data = bytes(pmt.u8vector_elements(vec))
        total_len = len(data)
        il2p_pack = Il2pPacket(packet_error_type=[])
        il2p_pack.processing_run_id = self.processing_run_id

        # Minimum frame length guard (LEN + EXTRA + FRAMING + HEADER + HEADER_PARITY + PAYLOAD_PARITY + CRC)
        if total_len < 40:
            print("[IL2P] DROP: too short")
            il2p_pack.packet_error_type.append("[IL2P] DROP: too short")
            return

        LEN = data[0]
        
        print(f"[IL2P] handle_pdu() total_len={total_len}, LEN={LEN}")

        # LEN consistency guard
        if LEN + 1 != total_len:
            print("[IL2P} DROP: LEN mismatch")
            il2p_pack.packet_error_type.append("[IL2P} DROP: LEN mismatch")
            return
            
        il2p_pack.packet_len = LEN

        # IL2P field sizes
        EXTRA = 1
        FRAMING = 3
        HEADER = 13
        HEADER_PARITY = 2
        PAYLOAD_PARITY = 16
        CRC_SIZE = 4

        idx = 1

        # EXTRA + FRAMING (not used further here)
        idx += EXTRA
        idx += FRAMING

        # Header + parity
        header_scrambled = data[idx:idx+HEADER]
        idx += HEADER

        header_parity = data[idx:idx+HEADER_PARITY]
        il2p_pack.header_parity = header_parity
        idx += HEADER_PARITY

        # RS decode header
        try:
            dec = self.rs_header.decode(header_scrambled + header_parity)
            header_corr = dec[0] if isinstance(dec, tuple) else dec
            il2p_pack.header_corrections = header_corr
        except Exception:
            il2p_pack.packet_error_type.append("[IL2P] BAD HEADER")
            return

        # Descramble header
        header_plain = self._descramble_bits(header_corr)
        il2p_pack.header = header_plain

        # Scrambler alignment check on header
        scr_ok = self._validate_scrambler(header_corr, header_plain)
        if not scr_ok:
            print("[IL2P] scrambler mismatch")
            il2p_pack.packet_error_type.append("[IL2P] scrambler mismatch")
            return

        # Decode payload length (minus one) from header
        decoded_len = self._decode_len_from_header(header_plain)

        # Your implementation: payload_size = decoded_len (subtract EXTRA)
        payload_size = decoded_len
        il2p_pack.payload_byte_count = payload_size

        # Guard against impossible payload sizes
        if payload_size <= 0:
            print("[IL2P] DROP: payload_size <= 0")
            il2p_pack.packet_error_type.append("[IL2P] DROP: payload_size <= 0")
            return
        if idx + payload_size + PAYLOAD_PARITY + CRC_SIZE > total_len:
            print("[IL2P] DROP: insufficient bytes for payload+parity+crc")
            il2p_pack.packet_error_type.append("[IL2P] DROP: insufficient bytes for payload+parity+crc")
            return

        # Slice payload, parity, CRC
        payload_scrambled = data[idx:idx+payload_size]
        idx += payload_size

        payload_parity = data[idx:idx+PAYLOAD_PARITY]
        idx += PAYLOAD_PARITY
        il2p_pack.payload_parity = payload_parity

        crc_ham = data[idx:idx+CRC_SIZE]
        il2p_pack.encoded_crc = crc_ham

        # RS decode payload
        try:
            dec = self.rs_payload.decode(payload_scrambled + payload_parity)
            payload_corr = dec[0] if isinstance(dec, tuple) else dec
            il2p_pack.payload_corrections = payload_corr
        except Exception:
            return

        # Descramble payload
        payload_plain = self._descramble_bits(payload_corr)
        il2p_pack.payload = payload_plain

        # Decode IL2P CRC nibbles
        n3 = self.decode_table[crc_ham[0] & 0x7F]
        n2 = self.decode_table[crc_ham[1] & 0x7F]
        n1 = self.decode_table[crc_ham[2] & 0x7F]
        n0 = self.decode_table[crc_ham[3] & 0x7F]

        received_fcs = ((n3 & 0xF) << 12) | ((n2 & 0xF) << 8) | ((n1 & 0xF) << 4) | (n0 & 0xF)

        # Build AX.25 frame and compute FCS
        ax25_frame = self.ax25_header + payload_plain
        computed_fcs = self._crc16_x25(ax25_frame)
        crc_ok = (computed_fcs == received_fcs)
        print(f"CRC check: {crc_ok}, payload_len={len(payload_plain)}")
        if crc_ok:
            il2p_pack.crc_success = True
        
        il2p_pack.packet_index = self.packet_index
        self.packet_index += 1
        
        # this provides the option to not store the packets to the database
        if self.store_packets:
            store_packet(il2p_pack)

        # -----------------------------
        # Write raw payload bytes (no delimiters)
        # -----------------------------
        if self.outfile is not None and crc_ok:
            try:
                self.outfile.write(payload_plain)
            except Exception as e:
                print(f"[IL2P] ERROR writing payload to file '{self.output_path}': {e}")

        # -----------------------------
        # Build metadata for downstream
        # -----------------------------
        md = pmt.make_dict()
        md = pmt.dict_add(md, pmt.intern("SCRAMBLER_OK"), pmt.from_bool(scr_ok))
        md = pmt.dict_add(md, pmt.intern("CRC16_OK"), pmt.from_bool(crc_ok))
        md = pmt.dict_add(md, pmt.intern("CRC16_COMPUTED"), pmt.from_long(computed_fcs))
        md = pmt.dict_add(md, pmt.intern("CRC16_RECEIVED"), pmt.from_long(received_fcs))
        md = pmt.dict_add(md, pmt.intern("PAYLOAD"),
                          pmt.init_u8vector(len(payload_plain), list(payload_plain)))

        out_pdu = pmt.cons(md, pmt.init_u8vector(len(data), list(data)))
        self.message_port_pub(pmt.intern("out"), out_pdu)


    def __del__(self):
        # Best-effort close of the output file
        try:
            if hasattr(self, "outfile") and self.outfile is not None:
                self.outfile.close()
        except Exception:
            pass

