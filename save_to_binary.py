import struct

def encode_moves_bitpacked(moves: str) -> bytes:
    """
    Encode a string of moves into bit-packed bytes.
    Mapping:
        S -> 00
        R -> 01
        L -> 10
        End of Segment -> 11
    """
    mapping = {'S': 0b00, 'R': 0b01, 'L': 0b10}
    bits = 0
    bit_len = 0

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

def decode_moves_bitpacked(packed: bytes) -> str:
    bits = int.from_bytes(packed, "big")
    bit_len = len(packed) * 8
    moves = []
    for i in range(bit_len // 2):
        val = (bits >> ((bit_len - (i + 1) * 2))) & 0b11
        if val == 0b11:  # end-of-segment
            break
        elif val == 0b00:
            moves.append('S')
        elif val == 0b01:
            moves.append('R')
        elif val == 0b10:
            moves.append('L')
    return ''.join(moves)


def replay_to_binary_struct(data: dict, output_path: str):
    """
    Converts a loaded snake replay dictionary into a compact binary format.

    Expected structure:
    {
      "version": "4.0",
      "result": {"score": 2, "reason": 2},
      "metadata": {
        "map": {"width": 10, "height": 10},
        "initial": {"snake": [40, 41, 42]}, 
        "seed": 12345
      },
      "segments": [
        "SSSSS",
        "LLR",
        "RSS"
      ]
    }

    Binary Format Layout:
    -------------------------------------------------------------
    | Header: "SNAK"                                      -> 4 bytes
    | Result:
        - score (H)                                       -> 2 bytes
        - reason code (B)                                 -> 1 bytes
    | Map width (B), height (B)                           -> 2 bytes
    | Map seed (I)                                        -> 4 bytes
    | Initial snake length (B) + positions (H * n)        -> variable (n=3 => 7 bytes)
    | Segment count (H)                                   -> 2 bytes
        For each segment:
            - packed move bytes                           -> 4 moves per byte
    -------------------------------------------------------------
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

    # Segments
    binary_data.extend(struct.pack("H", len(segments)))
    for seg in segments:
        packed_moves = encode_moves_bitpacked(seg)
        binary_data.extend(packed_moves)

    # Write to file
    with open(output_path, "wb") as f:
        f.write(binary_data)

    print(f"✅ Replay written to {output_path} ({len(binary_data)} bytes)")

def binary_to_replay_struct(input_path: str) -> dict:
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
    seed, = struct.unpack_from("I", data, offset)
    offset += 4

    # Segments
    seg_count, = struct.unpack_from("H", data, offset)
    offset += 2
    segments = []
    for _ in range(seg_count):
        packed_moves = data[offset:]
        moves = decode_moves_bitpacked(packed_moves)
        offset += len(moves) // 4 + (len(moves) % 4 > 0)    # implementation of ceil
        segments.append(moves)

    return {
        "version": "4.0",
        "metadata": {
            "map": {"width": width, "height": height},
            "initial": {"snake": snake},
            "seed": seed,
        },
        "result": {"score": score, "reason": reason},
        "segments": segments
    }

# Example usage:
if __name__ == "__main__":
    import json

    # Load externally (for example purposes)
    with open("new_replay.json", "r") as f:
        replay_data = json.load(f)

    replay_to_binary_struct(replay_data, "new_replay.bin")

    decoded = binary_to_replay_struct("new_replay.bin")
    print(json.dumps(decoded, indent=2))
