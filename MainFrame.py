import tkinter
from tkinter import filedialog
from tkinter.filedialog import asksaveasfile
import cv2
import PIL.Image
import PIL.ImageTk
import time
import os
from fastiecm import fastiecm
import numpy as np


def initialize(window, vid):
    global cameramode
    global canvas
    cameramode = True

    # Create a canvas that can fit the above video source size
    # self.canvas = tkinter.Canvas(window, width=self.vid.width, height=self.vid.height)
    canvas = tkinter.Canvas(window, width=1920, height=1080)
    canvas.pack()

    # Button that lets the user take a snapshot
    btn_snapshot = tkinter.Button(window, text="Photo", width=25, command=lambda: snapshot(vid))
    btn_snapshot.place(x=5, y=5)

    # Button that loads up an image file and switches to Image Processing Mode
    btn_fileexplorer = tkinter.Button(window, text="Open", width=25, command=browse_files)
    btn_fileexplorer.place(x=300, y=5)


def update():
    global canvas
    global photo
    # Get a frame from the video source
    ret, frame = get_frame(vid)

    if ret:
        # This is done every delay (standard: 40ms to get 25 fps)
        if cameramode:
            photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            canvas.create_image(0, 40, image=photo, anchor=tkinter.NW)
    window.after(delay, update)


def get_frame(vid):
    if vid.isOpened():
        ret, frame = vid.read()
        if ret:
            # Return a boolean success flag and the current frame converted to BGR
            return ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            return ret, None
    else:
        return ret, None


def create_canvas(image):
    global photo
    global canvas
    global cameramode
    global glimage
    cameramode = False
    glimage = image

    # Generating the interface in Imae Processing Mode. The panel with the buttons has a height of 40 pixels
    height, width, no_channels = image.shape
    canvas = tkinter.Canvas(window, width=width, height=height + 40)
    canvas.bind("<Key>", key)
    canvas.bind("<Button-1>", callback)
    canvas.pack()

    # Generate the image that was loaded in Camera Mode
    photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(image))
    canvas.create_image(0, 40, image=photo, anchor=tkinter.NW)

    # Switch back to Camera Mode
    btn_cameraon = tkinter.Button(window, text="Camera Mode", width=25, command=cameraon)
    btn_cameraon.place(x=5, y=5)

    # Load aother image with the file browser
    btn_fileexplorer = tkinter.Button(window, text="Open", width=25, command=browse_files)
    btn_fileexplorer.place(x=300, y=5)

    # Save the currently shown image in the canvas with the file browser.
    btn_save = tkinter.Button(window, text="Save", width=25, command=lambda: save_file(image))
    btn_save.place(x=595, y=5)

    # Starts the calculation of the NDVI index
    btn_ndvi = tkinter.Button(window, text="NDVI", width=25, command=lambda: ndvi_pressed(image))
    btn_ndvi.place(x=890, y=5)


def snapshot(vid):
    # Get a frame from the video source
    path = '/home/pi/Photos'
    ret, frame = get_frame(vid)
    # And save it to the Photos directory with the name frame-dmYHMS.jpg
    if ret:
        cv2.imwrite(os.path.join(path, "frame-" + time.strftime("%d-%m-%Y-%H-%M-%S") + ".jpg"), cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))


def browse_files():
    global cv_img

    # Opens a file browser and only allows jpg and png files to load in
    filename = filedialog.askopenfilename(initialdir="/home/pi/Photos",
                                          title="Select an Image",
                                          filetypes=(("Joint Photographic Experts Group (JPEG)", "*.jpg*"),
                                                     ("Portable Network Graphic (PNG)", "*.png*")))
    # insert the line below if you run it on a Windows system
    #filename = filename.replace("/", "\\")
    if filename != () and filename != "":
        print(filename)
        canvas.destroy()

        cv_img = cv2.cvtColor(cv2.imread(filename), cv2.COLOR_BGR2RGB)
        create_canvas(cv_img)


def save_file(cv_img):
    photo = PIL.Image.fromarray(cv_img)
    tk_photo = PIL.ImageTk.PhotoImage(photo)

    # Open the filebrowser to select a path which your currently displayed image is being saved to as a jpg file
    files = (("Joint Photographic Experts Group (JPEG)", "*.jpg*"),
                ("Portable Network Graphic (PNG)", "*.png*"))

    filename = filedialog.asksaveasfile(mode = 'w', filetypes = files, defaultextension ='.jpg')
    print(filename)
    if not filename:
        return
    photo.save(filename)


def cameraon():
    # Switch tp Camera Mode. Destroy the current canvas (Imae Processing Mode) and create a new one with the camera stream
    global canvas
    global cameramode
    cameramode = True
    canvas.destroy()
    initialize(window, vid)


def ndvi_pressed(cv_img):
    # The function that is called, when the user starts the NDVI calculation
    # The several display calls in between are for debugging ppurposes to she the various steps of the calculation.

    original = cv_img
    original = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
    #display(original, 'Original')
    # First the contrast of the original image is stretched.
    contrasted = contrast_stretch(original)
    #display(contrasted, 'Contrasted original')
    #cv2.imwrite('contrasted.png', contrasted)

    # This was an idea to invert the colors to see how this looks like.
    # It is not needed for the program, however it was still interesting to see
    #b, g, r = cv2.split(original)m
    #display(b, 'Blau')
    #display(r, 'Rot')
    #original = original[:,:,[2,1,0]]
    #display(original,'inverted')

    # On the contrasted image the NDVI values are being computed and result in numbers between -1 and 1
    ndvi = calc_ndvi(contrasted)
    #display(ndvi, 'NDVI')
    #cv2.imwrite('ndvi.png', ndvi)

    # These values are stretched such that the values lie between 0 and 255
    ndvi_contrasted = contrast_stretch(ndvi)
    #display(ndvi_contrasted, 'NDVI Contrasted')
    #cv2.imwrite('ndvi_contrasted.png', ndvi_contrasted)

    # At last the fastiecm color mapping is applied to the currently grey scaled image
    # The color mapped image is then displayed in the canvas
    color_mapped_prep = ndvi_contrasted.astype(np.uint8)
    color_mapped_image = cv2.applyColorMap(color_mapped_prep, fastiecm)
    #display(color_mapped_image, 'Color mappped')
    #cv2.imwrite('color_mapped_image.png', color_mapped_image)
    canvas.destroy()
    color_mapped_image = cv2.cvtColor(color_mapped_image, cv2.COLOR_BGR2RGB)
    create_canvas(color_mapped_image)


def display(image, image_name):
    #This function displays the current image in a separate window
    image = np.array(image, dtype=float)/float(255)
    shape = image.shape
    height = int(shape[0])
    width = int(shape[1])
    #image = cv2.resize(image, (width, height))
    cv2.namedWindow('Original')
    cv2.imshow('Original', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def calc_ndvi(image):
    # The actual calculation of the NDVI with the formula (NIR - RED) / (NIR + RED)
    # The NIR data is stored in the BLUE channel
    b, g, r = cv2.split(image)
    bottom = (r.astype(float) + b.astype(float))
    bottom[bottom==0] = 0.01
    ndvi = (b.astype(float) - r.astype(float)) / bottom
    return ndvi


def contrast_stretch(im):
    # Linear contrast stretch with 5% percentile
    in_min = np.percentile(im, 5)
    in_max = np.percentile(im, 95)
    out_min = 0.0
    out_max = 255.0

    out = im - in_min
    out *= ((out_min - out_max) / (in_min - in_max))
    out += in_min
    return out


# Generating the Tkinter object
window = tkinter.Tk()
window.title("NDVI Calculator")
video_source = 0

# Open the video source
vid = cv2.VideoCapture(video_source)
if not vid.isOpened():
    raise ValueError("Unable to open video source", video_source)

# The resolution of the camera stream which starts with initialize
vid.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

initialize(window, vid)

# After it is called once, the update method will be automatically called every delay
if cameramode:
    delay = 40
    update()

def key(event):
    if not cameramode:
        print("pressed"), repr(event.char)

def callback(event):
    # Shows the RGB values for the currently loaded image
    if not cameramode:
        # Only works while being in Image Proessing Mode and if the user clicks on the image and not on the bar with the buttons
        if event.y > 40:
            print("clicked at", event.x, event.y - 40)
            text = 'R = ' + str(glimage[event.y-40][event.x][0]) + ' G = ' + str(glimage[event.y-40][event.x][1]) + ' B = ' + str(glimage[event.y-40][event.x][2]) + '      '
            RGB = tkinter.Label(canvas, text=text, font=("Arial", 12))
            RGB.place(x=1185, y=5)
window.mainloop()
