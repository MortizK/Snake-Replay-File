import struct

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
        
        mapping = {'S': 0b00, 'R': 0b01, 'L': 0b10}
        bits = 0
        bit_len = 0

        # Start with all bits from lastbyte until the 11 EOS
        mask = 0b11
        for i in range(3):
            if lastbyte & mask == mask:
                bits = lastbyte >> 2 * i
                bit_len = 8 - 2 * i
                break
            mask = mask << 2

        for move in moves:
            bits = (bits << 2) | mapping[move]
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

        # Initial snake (no direction)
        snake = meta["initial"]["snake"]
        binary_data.extend(struct.pack("B", len(snake)))
        for pos in snake:
            binary_data.extend(struct.pack("H", pos))

        # Seed (4 bytes)
        seed = meta["seed"]
        binary_data.extend(struct.pack("I", seed))

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
        header = data[offset:offset + 4]
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

        # Snake
        snake_len, = struct.unpack_from("B", data, offset)
        offset += 1
        snake = [struct.unpack_from("H", data, offset + i*2)[0] for i in range(snake_len)]
        offset += snake_len * 2

        # Seed
        seed = struct.unpack_from("I", data, offset)
        offset += 4

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

    def updateResult(filepath: str) -> bytes:
        return

    def addSegment(filepath: str, moves: str) -> bytes:
        return

if __name__ == "__main__":
    import json
    handler = ReplayHandler()
    
    # Load externally (for example purposes)
    with open("new_replay.json", "r") as f:
        replay_data = json.load(f)

    handler.encode_to_binary(replay_data, "new_replay.bin")

    decoded = handler.decode_to_dict("new_replay.bin")
    print(json.dumps(decoded, indent=2))