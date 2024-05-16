# Copyright (c) 2024 Allen Cruiz. All rights reserved.
# GitHub: https://github.com/AlienWolfX
# Facebook: https://www.facebook.com/cruizallen

import os
import sys
from dotenv import load_dotenv
import utils
import cv2 
from roboflow import Roboflow
import chess
from stockfish import Stockfish
import chess.svg
from cairosvg import svg2png
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

class App:
    def __init__(self):
        self.root = None
        self.image_label = None
        self.fen_text = None
        
PROJECT_ROOT = os.path.abspath(os.path.join(
                  os.path.dirname(__file__), 
                  os.pardir)
)
sys.path.append(PROJECT_ROOT)

load_dotenv()

ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
STOCKFISH_PATH = os.getenv("STOCKFISH_PATH")

label_id_to_class={
    8:'K',
    12:'R',
    11:'Q',
    7:'B',
    10:'P',
    9:'N',
    1:'b',
    3:'n',
    5:'q',
    4:'p',
    2:'k',
    6:'r'
}

stockfish=Stockfish(STOCKFISH_PATH)

def predict(path):
    
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    project = rf.workspace().project("chessv1-5ew7x") # Added by Allen
    # project = rf.workspace().project("chessv1-ghvlw")
    model = project.version(1).model # 3
    predictions=model.predict(path, confidence=70, overlap=60).json()
    predictions=predictions['predictions']
    model.predict(path, confidence=50, overlap=50).save("prediction.jpg")
    return predictions

def assign(predictions,squares):

    dict_={}
    for prediction in predictions:
        x , y ,_,_, piece = prediction['x'] , prediction['y'] , prediction['width'] , prediction['height'] , int(prediction['class'])
        for i,square in enumerate(squares.items()):
            tl , _ , _ ,br =square[1]
            min_x=tl[0]
            min_y=tl[1]
            max_x=br[0]
            max_y=br[1]
            if min_x<=x and max_x>=x and min_y<=y and max_y>=y:
                dict_[i+1]=label_id_to_class[piece]
                continue
    sorted_dict = dict(sorted(dict_.items()))
    return sorted_dict
            
def dict_to_fen(dictionary_of_pieces , white_moves):

    fen=''
    c=0
    for i in range(1,65):
        if i in dictionary_of_pieces.keys():
            if c>0:
                fen+=str(c)
            fen+=dictionary_of_pieces[i]
            c=0
        else:
            c=c+1
        if i%8==0:
            if c>0:
                fen+=str(c)
            c=0
            fen+=('/')
    fen=fen[:-1]
    if white_moves==True:
        fen_link=fen+"%20w"
        fen+=' w - - 0 1'
    else:
        fen_link=fen+r"%20b"
        fen+=' b - - 0 1'
    link='https://lichess.org/analysis/standard/'+fen_link
    return fen, link

def position_to_png(fen):

    board=chess.Board(fen=fen)
    boardsvg = chess.svg.board(board=board)
    outputfile = open('digital_board.svg', "w")
    outputfile.write(boardsvg)
    outputfile.close()
    svg2png(url='digital_board.svg' , write_to="output.png")

'''
Tkinter GUI Functions
'''

def show_about():
    """Displays the about window."""
    
    about_window = tk.Toplevel(root)
    about_window.title("About")
    about_window.geometry("300x100")
    
    info_label = tk.Label(about_window, text="RookEye.ph Beta", font=("Arial", 16))
    info_label.pack(pady=10)

    link_label = tk.Label(about_window, text="Made with ❤️ by Allen Cruiz", font=("Arial", 12))
    link_label.pack(pady=10)
    
def clear_image():
    """Clears the image and FEN text."""
    
    global image_label
    
    if image_label is not None:
        image_label.destroy()
        image_label = None
    
    if fen_text is not None: 
        fen_text.delete('1.0', tk.END)
        
def select_file():
    """Opens a file dialog to select an image."""
    
    global root
    file_path = filedialog.askopenfilename()
    if not file_path:
        print("No file selected.")
        return

    loading_label = tk.Label(root, text="Loading...", pady=20)
    loading_label.pack()

    root.after(100, process_file, file_path, loading_label)

def process_image(file_path):
    """Processes the image and returns the necessary data."""
    
    image = cv2.imread(file_path)
    squares, rectified_chessboard, corners = utils.square_detection(image, False)
    path = utils.save_to_path('image', 'rectified_chessboard', rectified_chessboard)
    predictions = predict(path)
    dict_ = assign(predictions, squares)
    print(dict_)
    fen, link = dict_to_fen(dict_, False)
    position_to_png(fen)
    print(link)
    return fen, link

def update_fen_text(fen):
    """Updates the fen_text widget with the given FEN."""
    
    if fen_text is not None:
        fen_text.delete('1.0', tk.END) 
        fen_text.insert(tk.END, fen if fen else "None")

def display_image():
    """Displays the image in the GUI."""
    
    global image_label
    
    digital_chessboard = cv2.imread('output.png')
    digital_chessboard = cv2.cvtColor(digital_chessboard, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(digital_chessboard)
    tk_image = ImageTk.PhotoImage(pil_image)
    image_label = tk.Label(root, image=tk_image)
    image_label.image = tk_image
    image_label.pack(pady=20)

def process_file(file_path, loading_label):
    """Processes the selected file."""
    
    global root, image_label, fen_text

    try:
        fen, link = process_image(file_path)
        update_fen_text(fen)
        display_image()
    except Exception as e:
        tk.messagebox.showerror("Error", f"Failed to process image: {e}")
    finally:
        loading_label.destroy()
    
def main():
    global root, fen_text
    
    root = tk.Tk()
    root.title("RookEye.ph")
    root.geometry("500x650")

    def on_close():
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    menubar = tk.Menu(root)

    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Open", command=select_file)
    file_menu.add_command(label="Clear", command=clear_image)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.destroy)
    menubar.add_cascade(label="File", menu=file_menu)

    about_menu = tk.Menu(menubar, tearoff=0)
    about_menu.add_command(label="About", command=show_about)
    menubar.add_cascade(label="About", menu=about_menu)

    root.config(menu=menubar)

    button_frame = tk.Frame(root)
    button_frame.pack(side=tk.BOTTOM, pady=20)

    fen_text = tk.Text(root, height=2, width=50)
    fen_text.pack(side=tk.BOTTOM, pady=20)
    
    select_file_button = tk.Button(button_frame, text="Select Image", command=select_file)
    select_file_button.pack(side=tk.LEFT, padx=10)

    clear_button = tk.Button(button_frame, text="Clear Image", command=clear_image)
    clear_button.pack(side=tk.LEFT, padx=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()