import cv2
import numpy as np
import os
import glob

# Define the minimum number of matches needed for ORB feature matching
min_matches = 20  # You can easily adjust this value here
special_factor = 20  # Factor for the special image recognition

# Function to clear all .png files in the photos and parser folders
def clear_photos_and_parser_folders(photo_folder, parser_folder):
    for folder in [photo_folder, parser_folder]:
        files = glob.glob(os.path.join(folder, '*.png'))
        for f in files:
            os.remove(f)

# Define the path to the templates, photos, and parser folders
template_folder = 'templates'
photo_folder = 'photos'
parser_folder = 'parser'

# Clear all PNG files from the photos and parser folders before processing
if not os.path.exists(photo_folder):
    os.makedirs(photo_folder)

if not os.path.exists(parser_folder):
    os.makedirs(parser_folder)

# Clear the `photos` and `parser` folders
clear_photos_and_parser_folders(photo_folder, parser_folder)

# Load the chessboard image
image_path = 'template.png'  # Path to your main chessboard image
image = cv2.imread(image_path)

# Ensure the image is loaded
if image is None:
    raise ValueError(f"Could not load the chessboard image at {image_path}")

# Load the pawn templates from the templates folder
black_pawn_dark = cv2.imread(os.path.join(template_folder, 'black-pawn-dark-square.png'), 0)  # Load grayscale
black_pawn_light = cv2.imread(os.path.join(template_folder, 'black-pawn-light-square.png'), 0)
white_pawn_dark = cv2.imread(os.path.join(template_folder, 'white-pawn-dark-square.png'), 0)
white_pawn_light = cv2.imread(os.path.join(template_folder, 'white-pawn-light-square.png'), 0)

# Check if the templates are loaded properly
if black_pawn_dark is None or black_pawn_light is None or white_pawn_dark is None or white_pawn_light is None:
    raise ValueError("Could not load one or more pawn templates.")

# Function to use ORB feature matching to detect pawns
def orb_feature_match(square, template, min_matches=min_matches):
    # Initialize ORB detector
    orb = cv2.ORB_create()

    # Find keypoints and descriptors in both template and target (square)
    kp1, des1 = orb.detectAndCompute(template, None)
    kp2, des2 = orb.detectAndCompute(square, None)

    if des1 is None or des2 is None:
        return False

    # Use brute force matcher with Hamming distance
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    # Match descriptors between template and square
    matches = bf.match(des1, des2)

    # Sort matches by distance (best matches first)
    matches = sorted(matches, key=lambda x: x.distance)

    # Return True if we have enough good matches
    return len(matches) > min_matches

# Function to use ORB for special image recognition (with the factor applied)
def special_orb_match(image, template, factor):
    return orb_feature_match(image, template, min_matches=factor)

# Get the dimensions of the chessboard image
height, width, _ = image.shape

# Define the size of each square (assuming 8x8 board)
square_height = height // 8
square_width = width // 8

# Standard and reversed chess notation for rows and columns
standard_columns = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
standard_rows = ['1', '2', '3', '4', '5', '6', '7', '8']
reversed_columns = ['h', 'g', 'f', 'e', 'd', 'c', 'b', 'a']
reversed_rows = ['8', '7', '6', '5', '4', '3', '2', '1']

# Prepare an 8x8 board for FEN notation (initially empty)
board_fen = [['' for _ in range(8)] for _ in range(8)]

# Extract the top-left 1/3.6 by 1/3.6 of the a1 square and save it as black-or-white.png
a1_x_start = 0 * square_width
a1_y_start = 7 * square_height  # Reverse for 'a1' (bottom-left)
a1_square = image[a1_y_start:a1_y_start + square_height, a1_x_start:a1_x_start + square_width]

# Extract the top-left 1/3.6 by 1/3.6 part of the a1 square
top_left_a1 = a1_square[0:int(square_height // 3.6), 0:int(square_width // 3.6)]

# Save the top-left portion of a1 as 'black-or-white.png'
cv2.imwrite(os.path.join(photo_folder, 'black-or-white.png'), top_left_a1)

# Load the saved 'black-or-white.png' image for matching
black_or_white_img = cv2.imread(os.path.join(photo_folder, 'black-or-white.png'), cv2.IMREAD_GRAYSCALE)

# Function to check for pawn using ORB matching on template
def detect_pawn(square, pawn_template):
    return orb_feature_match(square, pawn_template)

# Determine the prefix based on ORB matching with special factor
def determine_prefix(image, white_template, black_template):
    if special_orb_match(image, black_template, special_factor):
        return "black_"
    elif special_orb_match(image, white_template, special_factor):
        return "white_"
    else:
        return "whoareyou_"

# Load black and white templates for determining active color
black_template = cv2.imread(os.path.join(template_folder, 'black.png'), cv2.IMREAD_GRAYSCALE)
white_template = cv2.imread(os.path.join(template_folder, 'white.png'), cv2.IMREAD_GRAYSCALE)

# Determine the prefix (and therefore active color) for the game
prefix = determine_prefix(black_or_white_img, white_template, black_template)

# Loop through each square, extract it, and detect pawns using ORB
for row in range(8):
    for col in range(8):
        # Coordinates of the current square
        x_start = col * square_width
        y_start = (7 - row) * square_height  # Reverse order for rows (a1 is bottom left)
        x_end = x_start + square_width
        y_end = y_start + square_height
        
        # Extract the square from the chessboard image
        square = image[y_start:y_end, x_start:x_end]

        # Get the notation for the current square
        notation = standard_columns[col] + standard_rows[row]

        # Save the raw image in the 'parser' folder with the appropriate prefix and notation
        raw_image_filename = f'{parser_folder}/{prefix}{notation}.png'
        cv2.imwrite(raw_image_filename, square)

        # Perform ORB-based template matching for all pawn types
        piece = ''
        if detect_pawn(square, black_pawn_dark):
            piece = 'black_pawn_dark'
        elif detect_pawn(square, black_pawn_light):
            piece = 'black_pawn_light'
        elif detect_pawn(square, white_pawn_dark):
            piece = 'white_pawn_dark'
        elif detect_pawn(square, white_pawn_light):
            piece = 'white_pawn_light'

        # Only save files in the 'photos' folder if a pawn is detected
        if piece:
            # Determine chess notation and FEN character for pawns
            if piece.startswith('black'):
                board_fen[7-row][col] = 'p'  # Black pawn (lowercase 'p')
            elif piece.startswith('white'):
                board_fen[7-row][col] = 'P'  # White pawn (uppercase 'P')

            # Create the filename for the current square based on chess notation
            square_filename = f'{photo_folder}/{notation}_{piece}.png'

            # Save the square as an image file (in the same color depth as the input)
            cv2.imwrite(square_filename, square)

            # Optional: print confirmation
            print(f"Saved: {square_filename}")

# Convert the FEN board representation to a proper FEN string
fen_rows = []
for row in board_fen:
    fen_row = ''
    empty_count = 0
    for cell in row:
        if cell == '':
            empty_count += 1
        else:
            if empty_count > 0:
                fen_row += str(empty_count)
                empty_count = 0
            fen_row += cell
    if empty_count > 0:
        fen_row += str(empty_count)
    fen_rows.append(fen_row)

# Join the FEN rows to create the final FEN string
fen_string = '/'.join(fen_rows)

# Determine active color based on prefix
active_color = 'w' if prefix == 'white_' else 'b'

# Add the rest of the FEN components: active color, castling rights, en passant target, halfmove clock, fullmove number
castling_rights = 'KQkq'  # Assuming both sides have castling rights
en_passant = '-'  # No en passant target square
halfmove_clock = '0'  # Halfmove clock is reset to 0
fullmove_number = '1'  # Assuming it's the first move of the game

final_fen = f"{fen_string} {active_color} {castling_rights} {en_passant} {halfmove_clock} {fullmove_number}"
print(f"\nFEN Notation: {final_fen}")
