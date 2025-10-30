import struct

from SnakeReplay import SnakeReplay

DIRECTION_MAP = {"w":0, "d":1, "s":2, "a":3}
REVERSE_DIR = {v:k for k,v in DIRECTION_MAP.items()}

class SnakeBinaryReplay:
    HEADER_MAGIC = b"SNAK"
    VERSION = 1

    @staticmethod
    def encode_moves(moves):
        bits = 0
        bitcount = 0
        buf = bytearray()
        for move in moves:
            bits = (bits << 2) | DIRECTION_MAP[move]
            bitcount += 2
            if bitcount >= 8:
                buf.append(bits >> (bitcount - 8))
                bitcount -= 8
                bits &= (1 << bitcount) - 1
        if bitcount > 0:
            buf.append(bits << (8 - bitcount))
        return bytes(buf)

    @staticmethod
    def decode_moves(data, count):
        moves = []
        bitstring = int.from_bytes(data, "big")
        total_bits = len(data) * 8
        for i in range(count):
            shift = total_bits - (i + 1) * 2
            val = (bitstring >> shift) & 0b11
            moves.append(REVERSE_DIR[val])
        return moves

    def save(self, path, replay_json):
        meta = replay_json["metadata"]
        init = meta["initial"]
        width = meta["map"]["width"]
        height = meta["map"]["height"]
        snake = init["snake"]
        direction = DIRECTION_MAP[init["direction"]]
        segments = replay_json["segments"]

        with open(path, "wb") as f:
            f.write(self.HEADER_MAGIC)
            f.write(struct.pack("BHHB", self.VERSION, width, height, len(snake)))
            for x,y in snake:
                f.write(struct.pack("BB", x, y))
            f.write(struct.pack("B", direction))
            f.write(struct.pack("H", len(segments)))

            for seg in segments:
                apple_x, apple_y = seg["apple"]
                moves = seg["moves"]
                packed_moves = self.encode_moves(moves)
                f.write(struct.pack("BBH", apple_x, apple_y, len(moves)))
                f.write(packed_moves)
                f.write(struct.pack("H", seg["length"]))

    def load(self, path):
        with open(path, "rb") as f:
            data = f.read()
        offset = 0
        assert data[offset:offset+4] == self.HEADER_MAGIC
        offset += 4

        version, width, height, snake_len = struct.unpack_from("BHHB", data, offset)
        offset += struct.calcsize("BHHB")
        snake = [tuple(data[offset+i*2:offset+i*2+2]) for i in range(snake_len)]
        offset += snake_len * 2

        direction = REVERSE_DIR[data[offset]]
        offset += 1

        segment_count, = struct.unpack_from("H", data, offset)
        offset += 2

        segments = []
        for _ in range(segment_count):
            apple_x, apple_y, move_len = struct.unpack_from("BBH", data, offset)
            offset += 4
            move_bytes_len = (move_len * 2 + 7) // 8
            move_bytes = data[offset:offset+move_bytes_len]
            offset += move_bytes_len
            moves = self.decode_moves(move_bytes, move_len)
            length, = struct.unpack_from("H", data, offset)
            offset += 2
            segments.append({"apple": [apple_x, apple_y], "moves": moves, "length": length})

        return {
            "version": version,
            "metadata": {"map": {"width": width, "height": height},
                         "initial": {"snake": snake, "direction": direction}},
            "segments": segments
        }
    
    def writeToJson(self, path_json, path_bin):
        replay_data = self.load(path_bin)
        with open(path_json, "w", encoding="utf-8") as f:
            import json
            json.dump(replay_data, f, indent=2)
