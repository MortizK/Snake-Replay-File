import struct
import os

class ReplayHandler:
    """
    Handles the encoding and decoding of snake game replay files.

    Example Input Data Structure:
    {
      "version": "5.0",
      "result": {"score": 2, "reason": 2},
      "metadata": {
        "map": {"width": 10, "height": 10},
        "seed": 12345,
        "initial": {"snake": [40, 41, 42]}
      },
      "segments": [
          "SSSSS", 
          "LLR", 
          "RSS"
      ]
    }
    
    The Binary Replay File Format:
    -------------------------------------------------------------
    | Header: "SNAK"                                      -> 4 bytes
    | Result:
        - score (H)                                       -> 2 bytes
        - reason code (B)                                 -> 1 bytes
    | Metadata:
        - Map width (B), height (B)                       -> 2 bytes
        - Map seed (I)                                    -> 4 bytes
        - Initial snake length (B) + positions (H * n)    -> variable (n=3 => 7 bytes)
    | For each segment:
        - packed move bytes                               -> 2 bits * moves + 2 bits
    """

    HEADER_SIZE_WITHOUT_INITIAL_SNAKE = 13
    MAPPING = {'S': 0b00, 'R': 0b01, 'L': 0b10}
    
    def encode_moves_bitpacked(self, moves: str, lastbyte: bytes) -> bytes:
        """
        The last byte may have unused bits.
        These will be filled an returned with the bits from these moves.

        Encodes a string of moves ('S', 'R', 'L') into a bit-packed byte array.
        Each move is represented by 2 bits:
            00 -> 'S'
            01 -> 'R'
            10 -> 'L'
            11 -> End of Segment
        """
        
        bits = 0
        bit_len = 0

        # Start with all bits from lastbyte until the 11 EOS
        mask = 0b11
        for i in range(4):
            if lastbyte & mask == mask:
                bits = lastbyte >> 2 * i
                bit_len = 8 - 2 * i
                break
            mask = mask << 2

        for move in moves:
            bits = (bits << 2) | self.MAPPING[move]
            bit_len += 2

        # Add 11 (end of segment marker)
        bits = (bits << 2) | 0b11
        bit_len += 2

        # Pad to full byte boundary
        pad = (8 - (bit_len % 8)) % 8
        bits <<= pad
        bit_len += pad

        # Convert to bytes
        return bits.to_bytes(bit_len // 8, "big")

    def encode_to_binary(self, data: dict, output_path: str) -> bytes:
        """
        Encodes the given replay data dictionary into a binary format.
        """
        meta = data["metadata"]
        segments = data["segments"]
        result = data["result"]

        # Start binary buffer
        binary_data = bytearray()
        binary_data.extend(b"SNAK")

        # Result
        binary_data.extend(struct.pack("H", result["score"]))
        binary_data.extend(struct.pack("B", result["reason"]))

        # Map info
        width = meta["map"]["width"]
        height = meta["map"]["height"]
        binary_data.extend(struct.pack("BB", width, height))

        # Seed (4 bytes)
        seed = meta["seed"]
        binary_data.extend(struct.pack("I", seed))

        # Initial snake (no direction)
        snake = meta["initial"]["snake"]
        binary_data.extend(struct.pack("B", len(snake)))
        for pos in snake:
            binary_data.extend(struct.pack("H", pos))

        last_seg_byte = 0b0
        binary_data.extend(struct.pack("B", last_seg_byte))
        for seg in segments:
            packed_moves = self.encode_moves_bitpacked(seg, last_seg_byte)
            last_seg_byte = packed_moves[-1]
            binary_data.pop()                   # Remove last Byte
            binary_data.extend(packed_moves)    # Last Byte is within this packed_moves

        # Write to file
        with open(output_path, "wb") as f:
            f.write(binary_data)

        print(f"✅ Replay written to {output_path} ({len(binary_data)} bytes)")

    def decode_to_dict(self, input_path: str) -> dict:
        with open(input_path, "rb") as f:
            data = f.read()

        offset = 0
        header = data[:offset + 4]
        offset += 4
        if header != b"SNAK":
            raise ValueError("Invalid file format")
        
        # Result
        score, = struct.unpack_from("H", data, offset)
        offset += 2
        reason, = struct.unpack_from("B", data, offset)
        offset += 1

        # Map
        width, height = struct.unpack_from("BB", data, offset)
        offset += 2

        # Seed
        seed, = struct.unpack_from("I", data, offset)
        offset += 4

        # Snake
        snake_len, = struct.unpack_from("B", data, offset)
        offset += 1
        snake = [struct.unpack_from("H", data, offset + i*2)[0] for i in range(snake_len)]
        offset += snake_len * 2

        # Segments
        lenData = len(data)
        segments = []
        moves = []
        while offset < lenData:
            byte, = struct.unpack_from("B", data, offset)
            offset += 1
            for i in range(4):
                val = (byte >> 8 - (i + 1) * 2) & 0b11
                if val == 0b11:  # end-of-segment
                    segments.append(''.join(moves))
                    moves = []
                elif val == 0b00:
                    moves.append('S')
                elif val == 0b01:
                    moves.append('R')
                elif val == 0b10:
                    moves.append('L')

        return {
        "version": "5.0",
        "result": {"score": score, "reason": reason},
        "metadata": {
            "map": {"width": width, "height": height},
            "seed": seed,
            "initial": {"snake": snake}
        },
        "segments": segments
    }

    def updateResult(self, filepath: str, score: int, reason: int = 1) -> bytes:
        with open(filepath, "r+b") as f:
            # Score at byte offset 4
            f.seek(4)  # "SNAK" is 4 bytes
            f.write(struct.pack("H", score))  # New Score

            # Reason at byte offset 6
            f.seek(6)  # "SNAK" + score is 6 bytes
            f.write(struct.pack("B", reason))     # New Reason

    def findStartOfSegments(self, filepath: str) -> int:
        '''
        Returns the size in bytes of the entire Header with the initial snake
        '''
        with open(filepath, "rb") as f:
            f.seek(self.HEADER_SIZE_WITHOUT_INITIAL_SNAKE)
            snake_len_data = f.read(1)
            snake_len, = struct.unpack("B", snake_len_data)

            offset = self.HEADER_SIZE_WITHOUT_INITIAL_SNAKE + snake_len * 2 + 1
            return offset

    def addSegments(self, filepath: str, segments: list[str]) -> bytes:
        with open(filepath, "r+b") as f:
            # Read last byte
            f.seek(-1, 2)
            lastbyte_data = f.read(1)
            lastbyte, = struct.unpack("B", lastbyte_data)

            # go back and truncate last byte
            f.seek(-1, 2)
            f.truncate()

            # encode and write new data
            binary_data = bytearray()
            binary_data.extend(struct.pack("B", lastbyte))
            for moves in segments:
                packed_moves = self.encode_moves_bitpacked(moves, lastbyte)
                lastbyte = packed_moves[-1]
                binary_data.pop()                   # Remove last Byte
                binary_data.extend(packed_moves)    # Last Byte is within this packed_moves
            f.write(binary_data)

if __name__ == "__main__":
    import json
    handler = ReplayHandler()
    path = "replay.bin"

    # read json input
    # with open(path + ".json", "r") as f:
    #     input_data = json.load(f)

    # handler.encode_to_binary(input_data, path)

    # handler.addSegments(path, ["L", "RR", "SLS"])
    # handler.updateResult(path, 42, 2)
    handler.findStartOfSegments(path)
    
    # Load externally (for example purposes)
    # path = input("Enter replay file (.bin): ").strip()

    decoded = handler.decode_to_dict(path)

    # Write Binary to json
    with open(path + ".json", "w") as f:
        json.dump(decoded, f, indent=2)

    print("\nReplay saved to " + path + ".json ✅")