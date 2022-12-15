import argparse
import os
import math
import numpy as np
from utils import *
from scipy import fftpack
from PIL import Image
from huffman import HuffmanTree


def quantize(block, component):
    q = load_quantization_table(component)
    return (block / q).round().astype(np.int32)


# def block_to_zigzag(block):
#     return np.array([block[point] for point in zigzag_points(*block.shape)])


def block_to_zigzag(block):
    flatten_arr = block.flatten()
    result = np.zeros(64, np.int16)
    zz = [0,   1,  8, 16,  9,  2,  3, 10,
          17, 24, 32, 25, 18, 11,  4,  5,
          12, 19, 26, 33, 40, 48, 41, 34,
          27, 20, 13,  6,  7, 14, 21, 28,
          35, 42, 49, 56, 57, 50, 43, 36,
          29, 22, 15, 23, 30, 37, 44, 51,
          58, 59, 52, 45, 38, 31, 39, 46,
          53, 60, 61, 54, 47, 55, 62, 63]
    for index, item in enumerate(flatten_arr):
        result[index] = flatten_arr[zz[index]]
    
    return result


def dct_2d(image):
    return fftpack.dct(fftpack.dct(image.T, norm='ortho').T, norm='ortho')


def run_length_encode(arr):
    # Xác định nơi trình tự kết thúc sớm
    last_nonzero = -1
    for i, elem in enumerate(arr):
        if elem != 0:
            last_nonzero = i

    # Mỗi symbol là một (RUNLENGTH, SIZE) tuple
    symbols = []

    # values là các biểu diễn binary của các phần tử sử dụng các bit SIZE
    values = []

    run_length = 0

    for i, elem in enumerate(arr):
        if i > last_nonzero:
            symbols.append((0, 0))
            values.append(int_to_binstr(0))
            break
        elif elem == 0 and run_length < 15:
            run_length += 1
        else:
            size = bits_required(elem)
            symbols.append((run_length, size))
            values.append(int_to_binstr(elem))
            run_length = 0
    return symbols, values


def write_to_file(filepath, dc, ac, blocks_count, tables):
    try:
        f = open(filepath, 'w')
    except FileNotFoundError as e:
        raise FileNotFoundError(
                "No such directory: {}".format(
                    os.path.dirname(filepath))) from e

    for table_name in ['dc_y', 'ac_y', 'dc_c', 'ac_c']:

        # 16 bits cho 'table_size'
        f.write(uint_to_binstr(len(tables[table_name]), 16))

        for key, value in tables[table_name].items():
            if table_name in {'dc_y', 'dc_c'}:
                # 4 bits cho the 'category'
                # 4 bits cho 'code_length'
                # 'code_length' bits cho 'huffman_code'
                f.write(uint_to_binstr(key, 4))
                f.write(uint_to_binstr(len(value), 4))
                f.write(value)
            else:
                # 4 bits cho 'run_length'
                # 4 bits cho 'size'
                # 8 bits cho 'code_length'
                # 'code_length' bits cho 'huffman_code'
                f.write(uint_to_binstr(key[0], 4))
                f.write(uint_to_binstr(key[1], 4))
                f.write(uint_to_binstr(len(value), 8))
                f.write(value)

    # 32 bits cho 'blocks_count'
    f.write(uint_to_binstr(blocks_count, 32))

    for b in range(blocks_count):
        for c in range(3):
            category = bits_required(dc[b, c])
            symbols, values = run_length_encode(ac[b, :, c])

            dc_table = tables['dc_y'] if c == 0 else tables['dc_c']
            ac_table = tables['ac_y'] if c == 0 else tables['ac_c']

            f.write(dc_table[category])
            f.write(int_to_binstr(dc[b, c]))

            for i in range(len(symbols)):
                f.write(ac_table[tuple(symbols[i])])
                f.write(values[i])
    f.close()


def main(input):
    input_file = input
    output_file = 't.txt'

    image = Image.open(input_file)
    ycbcr = image.convert('YCbCr')

    npmat = np.array(ycbcr, dtype=np.uint8)
    if len(npmat.shape) != 3:
        return 0
    rows, cols = npmat.shape[0], npmat.shape[1], 
    
    # Kích thước mỗi block: 8x8
    if rows % 8 == cols % 8 == 0:
        blocks_count = rows // 8 * cols // 8
    else:
        return 2

    # DC là phần tử đầu tiên của block, Ac là các phần tử còn lại
    dc = np.empty((blocks_count, 3), dtype=np.int32)
    ac = np.empty((blocks_count, 63, 3), dtype=np.int32)

    for i in range(0, rows, 8):
        for j in range(0, cols, 8):
            try:
                block_index += 1
            except NameError:
                block_index = 0

            for k in range(3):
                # [0, 255] --> [-128, 127]
                block = npmat[i:i+8, j:j+8, k] - 128

                # Áp dụng DCT2D vào mỗi block
                dct_matrix = dct_2d(block)

                # Áp dụng Quantization vào mỗi block 
                quant_matrix = quantize(dct_matrix,
                                        'lum' if k == 0 else 'chrom')
                # Chuyển block 8 x 8 thành array zigzag 1 x 64
                zz = block_to_zigzag(quant_matrix)
                
                dc[block_index, k] = zz[0]
                ac[block_index, :, k] = zz[1:]
   
    # Áp dụng Huffman Tre với input là array các bít cần được lấy từ dc[:, 0] (Luminance) -> Y
    H_DC_Y = HuffmanTree(np.vectorize(bits_required)(dc[:, 0]))

    # Áp dụng Huffman Tre với input là array các bít cần được lấy từ dc[:, 1:] (Chrominance) -> Cb, Cr
    H_DC_C = HuffmanTree(np.vectorize(bits_required)(dc[:, 1:].flat))
   
    H_AC_Y = HuffmanTree(
            flatten(run_length_encode(ac[i, :, 0])[0]
                    for i in range(blocks_count)))
    H_AC_C = HuffmanTree(
            flatten(run_length_encode(ac[i, :, j])[0]
                    for i in range(blocks_count) for j in [1, 2]))

    # dc_y: eg: {5: '0000', 6: '0001', 8: '001', 7: '010', 9: '011', 10: '1'}
    # dc_c: eg: 
    #           {5: '0000', 6: '0001', 8: '001', 7: '010', 9: '011', 10: '1'}
    #           {5: '0000', 6: '0001', 8: '001', 7: '010', 9: '011', 10: '1'}
    # ac_y: eg: {(0, 1): '00', (1, 2): '01000', (2, 1): '01001', (0, 7): '01010'}
    # ac_c: eg: 
    #       {(0, 1): '00', (1, 2): '01000', (2, 1): '01001', (0, 7): '01010'}
    #       {(0, 1): '00', (1, 2): '01000', (2, 1): '01001', (0, 7): '01010'}

    tables = {'dc_y': H_DC_Y.value_to_bitstring_table(),
              'ac_y': H_AC_Y.value_to_bitstring_table(),
              'dc_c': H_DC_C.value_to_bitstring_table(),
              'ac_c': H_AC_C.value_to_bitstring_table()}
   
    write_to_file(output_file, dc, ac, blocks_count, tables)
    return 1

if __name__ == "__main__":
    main()
