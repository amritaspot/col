from __future__ import print_function
from tkinter import *
import tkinter as tk
import tkinter.messagebox as messagebox
import sys
import json
import os
import numpy as np
from datetime import datetime
from tinydb import TinyDB, Query, where
from tinydb.operations import add, delete, set, subtract
from tinydb.table import Document
import time
import PIL
from PIL import Image, ImageTk
from time import sleep
from tkinter import ttk
from tkinter import filedialog
#import pyautogui
import psutil
#import pytesseract
import platform
import numpy as np
import matplotlib
import cv2
from picamera import PiCamera
import time
from fpdf import FPDF
from time import sleep
import RPi.GPIO as GPIO
import matplotlib.pyplot as plt
import webbrowser
#from tkPDFViewer import tkPDFViewer as pdf
from tkcalendar import Calendar
#--------------------------------database definitions-------------------------------------------------------------------------------------------------------------
db = TinyDB('/home/pi/COL_0.0.3/results.json')
#db = TinyDB('results.json')
Sample = Query()



#---------------------------------------------------screens------------------------------------------------------------------------------------------------------------
def Splash():
	global splash
	splash = Tk()
	splash.title('Main')
	splash.geometry('480x800')
	splash.config(bg='#ffffff')
	splash.attributes('-fullscreen', True)
	img = ImageTk.PhotoImage(Image.open("/home/pi/COL_0.0.3/logo.jpg"))
	#img = ImageTk.PhotoImage(Image.open("logo.jpg"))
	Label(splash, image=img, background = "white").place(relx=0.5,rely=0.5,anchor=CENTER)
	Label(splash, text="Loading colorcult scanner...", font = "Helvetica 12 bold", background = "white").place(relx=0.5,rely=0.6,anchor=CENTER)
	splash.after(2000, lambda: Homepage())
	
	#--------------------------------image proccessing functions-----------------------------------------------------------------------------------------------------
		
	def camcapture():
		camera = PiCamera()
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(40, GPIO.OUT)
		GPIO.output(40, True)
		GPIO.cleanup
		camera.iso = 800
		camera.vflip = True
		camera.hflip = True
		camera.capture('/home/pi/COL_0.0.3/captured.jpg')
		GPIO.output(40,False)
		input_image = cv2.imread('/home/pi/COL_0.0.3/captured.jpg')
		camera.close()
		return input_image

	def ocrcapture():
		camera = PiCamera()
		#pytesseract.pytesseract.tesseract_cmd = r'sudo /usr/include/tesseract'
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(40, GPIO.OUT)
		GPIO.output(40, True)
		GPIO.cleanup
		camera.iso = 800
		camera.exposure_mode = 'verylong'
		camera.brightness = 80
		camera.vflip = True
		camera.hflip = True
		camera.start_preview()
		barcodes = ''
		i=0
		while ((barcodes=='')and(i<5)):
			camera.capture('/home/pi/COL_0.0.3/ocr.jpg')
			img = cv2.imread('/home/pi/COL_0.0.3/ocr.jpg')
			barcodes = img_corr(img)
			i=i+1
		camera.stop_preview()
		GPIO.output(40,False)
		camera.close()
		return barcodes
	
	def img_corr(image):
		image = image[0:200, 50:400]
		cv2.imwrite('/home/pi/COL_0.0.3/ocr_crop.jpg', image)
		image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
		cv2.imwrite('/home/pi/COL_0.0.3/rotated.jpg', image)

		rgb_planes = cv2.split(image)

		result_planes = []
		result_norm_planes = []
		for plane in rgb_planes:
		    dilated_img = cv2.dilate(plane, np.ones((7,7), np.uint8))
		    bg_img = cv2.medianBlur(dilated_img, 21)
		    diff_img = 255 - cv2.absdiff(plane, bg_img)
		    norm_img = cv2.normalize(diff_img,None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
		    result_norm_planes.append(norm_img)

		result_norm = cv2.merge(result_norm_planes)
		cv2.imwrite('/home/pi/COL_0.0.3/shadows_out_norm.jpg', result_norm)

		# Adding custom options
		custom_config = r'--psm 6 --oem 3 outputbase digits'
		text = pytesseract.image_to_string(result_norm, config=custom_config)
		number = replace_chars(text)
		print(number)
		return number

	def replace_chars(text):
		list_num = re.findall(r'\d+', text)
		num = ''.join(list_num)
		return num
	
	def roi_tube(image):
	    crop = image[320:700, 0:600]
	    cv2.imwrite('/home/pi/COL_0.0.3/crop1.jpg', crop)
	    img = cv2.GaussianBlur(crop, (15,15),0)
	    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	
	    sobelx = cv2.Sobel(img,cv2.CV_64F,0,1,ksize=5)
	    sobely = cv2.Sobel(img,cv2.CV_64F,1,0,ksize=3)
	
	    abs_grad_x = cv2.convertScaleAbs(sobelx)
	    abs_grad_y = cv2.convertScaleAbs(sobely)
	
	    grad = cv2.addWeighted(abs_grad_x, 0.6, abs_grad_y, 0.6, 0)
	    cv2.imwrite('grad.jpg', grad)
	
	    ret, thresh = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
	    cv2.imwrite('/home/pi/COL_0.0.3/thresh.jpg', thresh)
	    thresh = thresh.astype(np.uint8)
	    cnts,_ = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2:]
	    cnts = sorted(cnts, key = cv2.contourArea, reverse = True)
	    cv2.drawContours(img, cnts, -1, (0,255,0), 3)
	    cv2.imwrite('/home/pi/COL_0.0.3/contoured.jpg', img)
	
	    rect = []
	    [img_width, img_height] = img.shape[:2]
	
	    for c in cnts:
	    	epsilon = 0.01*cv2.arcLength(c,True)
	    	approx = cv2.approxPolyDP(c,epsilon,True)
	    	if (len(approx)>=4):
	    		(x, y, w, h) = cv2.boundingRect(approx)
	    		if(x > 8 and x < img_width-8):
	    			#cv2.rectangle(crop, (x, y-40), (x+w, y+h), (255,0,0), 2)
	    			rect.append((x,y,w,h,(h*w)))
	    rect.sort(key=takefourth, reverse=True)
	    cv2.imwrite('/home/pi/COL_0.0.3/rect.jpg', crop)
	    arr=rect[0]
	    x1 = arr[0]
	    y1 = arr[1]
	    w1 = arr[2]
	    h1 = arr[3]
	    #print(y1, h1, x1, w1)
	    roi_image=crop[y1:y1+h1, x1:x1+w1]
	    cv2.imwrite('/home/pi/COL_0.0.3/cropped.jpg', roi_image)
	    return roi_image

	def takefourth(array):
	    return array[4]
	
	def val_sensor(img):
	    #image = Image.open('cropped.jpg')
	    [a1, b1] = img.shape[:2]
	    img = img[0:200, 0:360]
	    b, g, r = cv2.split(img)
	    input = r
	    cv2.imwrite('/home/pi/COL_0.0.3/hue.jpg', input)
	    #[a, b] = input.shape[:2]
	    hist = cv2.calcHist([input],[0],None,[256],[0,256])
	    length = len(hist)
	    i=0
	    hist_array = []
	    while(i<(length-50)):
	    	hist_array = np.append(hist_array, hist[i][0])
	    	i = i+1
	    slist = list(zip(*np.where(hist_array == np.amax(hist_array))))
	    scorea = np.asarray(slist)
	    score1 =scorea[0][0]
	    plt.plot(hist_array)
	    plt.savefig('/home/pi/COL_0.0.3/results/plot.jpg')
	    plt.close()
	    #score1 = np.amax(hist_array)
	    score2 = hist_array[100]
	    print(score1)
	    return score1	
	
	def readtest(sampleid):
		result = ''
		i=sum=0
		while(i<4):
			image = camcapture()
			input_image = roi_tube(image)
			i=i+1
			sum = sum+val_sensor(input_image)
		score = sum/4
		if (score>100): result = "Positive"
		elif (50<score<100): result = "Negative"
		elif (score<17): result = "Negative"
		elif (19<score<45): result = "Positive"
		else: result = "Could not read bottle"
		test_time = str(datetime.now().replace(microsecond=0))
		cv2.imwrite('/home/pi/COL_0.0.3/images/'+str(sampleid)+'.jpg', input_image)
		db.update({'readings':{'result': result, 'test_time': test_time, 'score': score}}, Sample.sample_id == str(sampleid))
		ResultPage(sampleid)
		
		
	#---------------------------------keyboard frame-----------------------------------------------------------------------------------------------------------------

	def drawKeyboard(parent):
	    keyboardFrame = tk.Frame(parent, bg = '#ffffff')
	    keyboardFrame.pack(side=BOTTOM)

	    keys = [
		[ ("Alpha Keys"),
		  [('0', '1', '2', '3', '4', '5', '6', '7', '8', '9','.'),
		   ('q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'),
		    ('a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l','Bksp'),
		    ('#','-', 'z', 'x', 'c', 'v', 'b', 'n', 'm','Space')
		
		  ]
		]
	    ]

	    for key_section in keys:
	    	sect_vals = key_section[1]
	    	sect_frame = tk.Frame(keyboardFrame)
	    	sect_frame.pack(side = 'left', expand = 'yes', fill = 'both', padx = 10, pady = 10, ipadx = 10, ipady = 10)
	    	for key_group in sect_vals:
	    		group_frame = tk.Frame(sect_frame)
	    		group_frame.pack(side = 'top', expand = 'yes', fill = 'both')
	    		for key in key_group:
	    			key = key.capitalize()
	    			if len(key) <= 1: key_button = ttk.Button(group_frame, text = key, width = 4, takefocus=False)
	    			else:key_button = ttk.Button(group_frame, text = key.center(5, ' '), takefocus=False)
	    			key_button['command'] = lambda q=key: key_command(q)
	    			key_button.pack(side = 'left', fill = 'both', expand = 'yes')

	    def key_command(event):
	    	entry = parent.focus_get()
	    	position = entry.index(INSERT)
	    	if event == 'Bksp': entry.delete(position-1)
	    	elif event == 'Space': entry.insert(position, " ")
	    	else: entry.insert(position, event)
	
	#-------------------------------------------------------------hardware check functions----------------------------------------------------
	def get_size(bytes, suffix="B"):
	    """
	    Scale bytes to its proper format
	    e.g:
		1253656 => '1.20MB'
		1253656678 => '1.17GB'
	    """
	    factor = 1024
	    for unit in ["", "K", "M", "G", "T", "P"]:
	    	if (bytes < factor): return f"{bytes:.2f}{unit}{suffix}"
	    	bytes /= factor
	

	def disk_check():
		global disk_list
		disk_list = []
		partitions = psutil.disk_partitions()
		for partition in partitions:
			try:
				partition_usage = psutil.disk_usage(partition.mountpoint)
			except PermissionError:
				# this can be catched due to the disk that
				# isn't ready
				continue
			disk_list.append("Device:" +str({partition.device}))
			disk_list.append("Total Size:"+str({get_size(partition_usage.total)}))
			disk_list.append("Used:" +str({get_size(partition_usage.used)}))
			disk_list.append("Free:" +str({get_size(partition_usage.free)}))
			disk_list.append("Percentage:" +str({partition_usage.percent}))
		return disk_list

	def color_check():
		print('')

	def focus_check():
		print('')
		
	def save_log(date):
		print('')

	#--------------------------------------------os functions-----------------------------------------------------------------------------------------------
	def backup():
		resultview.destroy()
		backup = messagebox.askquestion("Confirm","Do you want to backup all the results?")
		if backup == 'yes':
			ResultView()
		else:
			ResultView()
			exit()
		
	def poweroff():
		homepage.destroy()
		shutdown = messagebox.askquestion("Confirm","Do you want to shutdown?")
		if shutdown == 'no':
			Homepage()
			exit()
		else:
			os.system("sudo shutdown -h now")
		
			
	def restart():
		homepage.destroy()
		restart = messagebox.askquestion("Confirm","Do you want to restart?")
		if restart == 'no':
			Homepage()
			exit()
		else:
			os.system("sudo shutdown -r now")
		
	def browseFiles():
	    resultview.destroy()
	    #result.destroy()
	    filename = filedialog.askopenfile(initialdir = "/home/pi/COL_0.0.3/results", title = "Select a File", filetypes = (("Result files", "*.pdf*"),("all files","*.*")))
	    try:
	    	path = filename.name
	    	webbrowser.open_new(path)
	    except: ResultView()
	
	def get_timedelta(date_string1, date_string2):
		date_time_obj1 = datetime. strptime(date_string1, '%Y-%m-%d %H:%M:%S')
		date_time_obj2 = datetime. strptime(date_string2, '%Y-%m-%d %H:%M:%S')
		delta = date_time_obj2-date_time_obj1
		delta_hrs = (delta.days*24+int((delta.seconds/3600)))
		return delta_hrs

	#-------------------------------------------------module functions---------------------------------------------------------------------------------------------
	def scan_ocr(markupL):
		try:
			sampleid = ocrcapture()
			sampleE.insert(0, sampleid)
		except Exception as e:
			print(e)
			markupL.configure(text="Could not read OCR")
		
	def register_test(sampleid, markupL):
		markupL.configure(text = "Please register the sample")
		RegisterTest(sampleid)
		
	def check_sampleid(sampleid, markupL):
		confirmsample = 'yes'
		if (sampleid.isnumeric() == True):
			time_now = str(datetime.now().replace(microsecond=0))
			db = TinyDB('/home/pi/COL_0.0.3/results.json')
			list = db.search(Sample.sample_id == sampleid)
			if not list: register_test(sampleid, markupL)
			else:
				for l in list: regd_time = l['regd_time']		
				time_delta = get_timedelta(regd_time, time_now)
				readings = l['readings']['result']
				if not readings:
					if (time_delta < 5): markupL.configure(text = "Please read test after 5 hours.")
					if (time_delta > 144):
						markupL.configure(text = "Sample older than 6 days.")
					else:readtest(sampleid)
				else:
					if (readings=="Positive"):
						#result.destroy()
						markupL.configure(text = "Sample already tested positive at: "+l['readings']['test_time'])
					else:
						readtest(sampleid)
		else:
            markupL.configure(text="Please enter a valid numeric sample id")			

	def treeview_sort_column(tv, col, reverse):
	    l = [(tv.set(k, col), k) for k in tv.get_children('')]
	    l.sort(reverse=reverse)

	    # rearrange items in sorted positions
	    for index, (val, k) in enumerate(l): tv.move(k, '', index)

	    # reverse sort next time
	    tv.heading(col, text=col, command=lambda _col=col: treeview_sort_column(tv, _col, not reverse))


#----------------------------------------------------------------------------------------------------------------------------------------------------
	def ExitPage():
		global exitpage
		homepage.destroy()
		exitpage = Toplevel()
		exitpage.title('Exit')
		exitpage.geometry('480x800')
		exitpage.config(bg='#ffffff')
		
		Label(exitpage, text="Enter admin password to exit", font = "Helvetica 20", background = "white", justify="center").place(relx=0.5,rely=0.1,anchor=CENTER)
		
		passE = Entry(exitpage,font = "Helvetica 20")
		passE.place(relx=0.5,rely=0.2,anchor=CENTER)
		
		markupL = Label(exitpage, text = "",font = "Helvetica 20", background = "white", justify="center")
		markupL.place(relx=0.5,rely=0.75)
		
		def exit_app():
			password = passE.get()
			if (password=="7983COL003"): splash.destroy()
			else: markupL.configure(text = "Password is incorrect")
		
		Button(exitpage, text='Exit Application', font = "Helvetica 16", width=15, background = "white", command=lambda: exit_app()).place(relx=0.5,rely=0.5,anchor=CENTER)
		Button(exitpage, text='Cancel', font = "Helvetica 16", width = 15, background = "white", command=lambda: Homepage()).place(relx=0.5,rely=0.6,anchor=CENTER)
		drawKeyboard(exitpage)
		exitpage.mainloop()
		
	def AdminPage():
		global exitpage
		homepage.destroy()
		adminpage = Toplevel()
		adminpage.title('Exit')
		adminpage.geometry('480x800')
		adminpage.config(bg='#ffffff')
		
		Label(adminpage, text="Enter admin password for scan", font = "Helvetica 20", background = "white", justify="center").place(relx=0.5,rely=0.1,anchor=CENTER)
		
		passE = Entry(adminpage,font = "Helvetica 20")
		passE.place(relx=0.5,rely=0.2,anchor=CENTER)
		
		markupL = Label(adminpage, text = "",font = "Helvetica 20", background = "white", justify="center")
		markupL.place(relx=0.5,rely=0.75)
		
		def scan_app():
			password = passE.get()
			if (password=="7983COL003"): Hardwarescan()
			else: markupL.configure(text = "Password is incorrect")
		
		Button(adminpage, text='Run Scan', font = "Helvetica 16", width = 15, background = "white", command=lambda: scan_app()).place(relx=0.5,rely=0.5,anchor=CENTER)
		Button(adminpage, text='Cancel', font = "Helvetica 16", width = 15, background = "white", command=lambda: Homepage()).place(relx=0.5,rely=0.6,anchor=CENTER)
		drawKeyboard(adminpage)
		adminpage.mainloop()

	def Homepage():
		global homepage
		global sampleid
		global sampleE
		try:registertest.destroy()
		except: print('')
		try:patientpage.destroy()
		except:print('')
		try:patientdetail.destroy()
		except:print('')
		try: result.destroy()
		except: print('')
		try: resultview.destroy()
		except: print('')
		try: deviceinfo.destroy()
		except: print('')
		try: hscan.destroy()
		except: print('')
		try: sampleE.delete(0,"end")
		except: print('')
		homepage = Toplevel()
		homepage.title('Homepage')
		homepage.geometry('480x800')
		homepage.config(bg='#ffffff')
		#homepage.attributes('-fullscreen', True)
		menubar = Menu(homepage)
		
		# keep sampleid definition as 0 so that it is reset everytime homepage is run
		sampleid = '0'
		
		#define the menubar with options: results, help, power
		results = Menu(menubar, tearoff = 0)
		menubar.add_cascade(label ='Results', menu = results, font = "Helvetica 16")
		results.add_command(label="Show all", font = "Helvetica 16", command=lambda:ResultView())
		#results.add_command(label="Directory", command=lambda:ResultsFolder)
		
		help = Menu(menubar, tearoff = 0)
		menubar.add_cascade(label ='Help', menu = help, font = "Helvetica 16")
		help.add_command(label ='Device Info', font = "Helvetica 16", command = lambda:DeviceInfo())
		help.add_command(label ='Hardware check', font = "Helvetica 16", command = lambda:AdminPage())
		
		shutdown = Menu(menubar, tearoff = 0)
		menubar.add_cascade(label ='Power', menu = shutdown, font = "Helvetica 16")
		shutdown.add_command(label ='Exit', font = "Helvetica 16", command = lambda:ExitPage())
		shutdown.add_command(label ='Shutdown', font = "Helvetica 16", command = lambda:poweroff())
		shutdown.add_command(label ='Restart', font = "Helvetica 16", command = lambda:restart())
		homepage.config(menu = menubar)
		
		img = ImageTk.PhotoImage(Image.open("/home/pi/COL_0.0.3/scan_ocr.png"))
		#img = ImageTk.PhotoImage(Image.open("scan_ocr.png"))
		
		Button(homepage, image = img, bd=0, background = "white", command=lambda: scan_ocr(markupL)).place(relx=0.5,rely=0.3,anchor=CENTER)
		Label(homepage, text = "Or Enter Sample Id",font = "Helvetica 20", background = "white").place(relx=0.5,rely=0.5,anchor=CENTER)
		
		sampleE = Entry(homepage,font = "Helvetica 16")
		sampleE.place(relx=0.5,rely=0.55,anchor=CENTER)
		
		def get_sampleid(markupL):
			markupL.configure(text = "")
			sampleid = str(sampleE.get())
			check_sampleid(sampleid, markupL)
		
		def show_report(markupL):
			sampleid = sampleE.get()
			markupL.configure(text = "")
			list = db.search(Sample.sample_id == sampleid)
			print(list)
			if not list: markupL.configure(text = "Sample report not found")
			else: ResultPage(sampleid)
			
		markupL = Label(homepage, text = "",font = "Helvetica 14", background = "white", justify="center")
		markupL.place(relx=0.1,rely=0.7)
			
		button = Button(homepage, text='Run Test',width=8, font = "Helvetica 16", background = "white", command=lambda: get_sampleid(markupL))
		button.place(relx=0.3,rely=0.65,anchor=CENTER)
		button = Button(homepage, text='See Report',width=8, font = "Helvetica 16", background = "white", command=lambda: show_report(markupL))
		button.place(relx=0.7,rely=0.65,anchor=CENTER)
		drawKeyboard(homepage)	
		homepage.mainloop()

	def RegisterTest(sampleid):
		global registertest
		homepage.destroy()
		registertest = Toplevel()
		registertest.title('Register Test')
		registertest.geometry('480x800')
		registertest.config(bg='#ffffff')
		#registertest.attributes('-fullscreen', True)
		
		Label(registertest, text="Sample ID:"+str(sampleid),font = "Helvetica 16 bold", background = "white", justify="left").place(relx=0.1,rely=0.1,anchor=W)
		Label(registertest, text = "Enter Patient id",font = "Helvetica 16", background = "white", justify="left").place(relx=0.1,rely=0.15,anchor=W)
		patientE = Entry(registertest,font = "Helvetica 14", background = "white")
		patientE.place(relx=0.7,rely=0.15, anchor=CENTER)
		
		
		Label(registertest, text="Select Tube Type", font = "Helvetica 16", background = "white", justify="left").place(relx=0.1,rely=0.25,anchor=W)
		
		var = StringVar()
		Button1 = Radiobutton(registertest, text="Aerobic", variable=var, value="Aerobic",font = "Helvetica 14", background = "white", bd=0, width = 10)
		Button2 = Radiobutton(registertest, text="Anaerobic", variable=var, value="Anaerobic",font = "Helvetica 14", background = "white", bd=0, width = 10)
		Button3 = Radiobutton(registertest, text="Pediatric", variable=var, value="Pediatric",font = "Helvetica 14", background = "white", bd=0, width = 10)
		Button1.place(relx=0.1,rely=0.3,anchor=W)
		Button2.place(relx=0.4,rely=0.3,anchor=W)
		Button3.place(relx=0.7,rely=0.3,anchor=W)
		
		Label(registertest, text="Enter sample collection date",font = "Helvetica 16", background = "white", justify='left').place(relx=0.1,rely=0.4,anchor=W)
		cal = Calendar(registertest, selectmode = 'day', year = 2022, month = 1, day = 1)
		cal.place(relx=0.1,rely=0.55,anchor=W)
		
		def add_sample(sampleid, markupL):
		    tubetype = var.get()
		    sampletype = ''
		    patient_id = patientE.get()
		    col_date = cal.get_date()
		    print(col_date)
		    if ((patient_id=='')or(tubetype=='')or(col_date=='')):
		    	markupL.configure(text= "Please enter all the fields")
		    else:
		    	reg_date = str(datetime.now().replace(microsecond=0))
		    	list = db.search(Sample.patient_id == patient_id)
		    	if not list:
		    		db.insert({'sample_id': sampleid, 'patient_id': patient_id, 'tube_type': tubetype, 'col_date': col_date, 'regd_time':reg_date,'readings':{'result':'', 'test_time':''}})
		    		markupL.configure(text= "Sample is registered")
		    		registertest.after(1000, lambda: PatientPage(patient_id))
		    	else:Patientdetail(patient_id)
		    			
		markupL = Label(registertest, text = "",font = "Helvetica 16", background = "white", justify="left")
		markupL.place(relx=0.1,rely=0.75,anchor=W)
		
		Button(registertest, text='Confirm', font = "Helvetica 16", background = "white", command=lambda: add_sample(sampleid, markupL)).place(relx=0.5,rely=0.7,anchor=CENTER)
				
		drawKeyboard(registertest)
		registertest.mainloop()

	def Patientdetail(patient_id):
		homepage.destroy()
		registertest.destroy()
		global patientdetail
		patientdetail = Toplevel()
		patientdetail.title('Patient Page')
		patientdetail.geometry('480x800')
		patientdetail.config(bg='#ffffff')
		#patientdetail.attributes('-fullscreen', True)

		list = db.search(Sample.patient_id == patient_id)
		
		columns = ('sample_id','col_date','result','test_date')
		grid_frame = LabelFrame(patientdetail, text = "Patient Id: "+patient_id, font = "Helvetica 14", background="white")
		grid_frame.pack(fill = 'x')
		tree = ttk.Treeview(grid_frame, columns=columns, show='headings')
		tree.pack(fill = BOTH, expand=1)
		
		tree.heading('sample_id', text='Id', command=lambda: treeview_sort_column(tree, 'sample_id', False))
		tree.column("sample_id", width=100, stretch=NO)
		
		tree.heading('col_date', text='Collection Date', command=lambda: treeview_sort_column(tree, 'col_date', False))
		tree.column("col_date", width=100, stretch=NO)
		
		tree.heading('result', text='Result', command=lambda: treeview_sort_column(tree, 'result', False))
		tree.column("result", width=100, stretch=NO)
		
		tree.heading('test_date', text='Test time',command=lambda: treeview_sort_column(tree, 'test_date', False))
		tree.column("test_date", width=140, stretch=NO)
		
		readings = []
		for l in list:
			readings.append((l['sample_id'], l['col_date'], l['readings']['result'],l['readings']['test_time']))
		for reading in readings:
			tree.insert('', tk.END, values=reading)
		#tree.grid(row=0, column=0, sticky='nsew')
		
		vsb = ttk.Scrollbar(grid_frame, orient="vertical", command=tree.yview)
		vsb.place(relx=0.95, rely=0.8, height=300, width=30, anchor=CENTER)
		#vsb.pack(side=RIGHT, fill=BOTH)

		tree.configure(yscrollcommand=vsb.set)
		
		def show_pdf(markupL):
			for selected_item in tree.selection():
				item = tree.item(selected_item)
				sampleid = item['values'][0]
				v1 = pdf.ShowPdf()
				try:
					location = "result/"+sampleid+".pdf"
					v2 = v1.pdf_view(patientdetail, pdf_location = location, width = 50, height = 100)
					v2.pack(side=TOP)
				except:
					markupL.configure(text="Could not open report")
		
		button_frame = LabelFrame(patientdetail, text = '',background="white")
		button_frame.pack(side = TOP, fill = 'x')
		Label(button_frame, text = "", font = "Helvetica 12",background="white").pack(side = TOP, fill='x')
		markupL = Label(button_frame, text = "", font = "Helvetica 10",background="white")
		markupL.pack(side = BOTTOM, fill='x')
		Button(button_frame, text = "Results folder", font = "Helvetica 14", background="white", command = lambda: browseFiles()).pack(side = LEFT)
		Button(button_frame, text = "Homepage", font = "Helvetica 14", background="white", command = lambda: Homepage()).pack(side = LEFT)
		Button(button_frame, text = "Run Test", font = "Helvetica 14",background="white", command = lambda: run_test(markupL)).pack(side = LEFT)
		Button(button_frame, text = "See Report", font = "Helvetica 14", background="white",command = lambda: show_pdf(markupL)).pack(side = LEFT)
		Label(button_frame, text = "", font = "Helvetica 12",background="white").pack(side = TOP, fill='x')
		patientdetail.mainloop()

	def PatientPage(patient_id):
		homepage.destroy()
		registertest.destroy()
		global patientpage
		global nameE
		global genderE
		global ageE
		patientpage = Toplevel()
		patientpage.title('Patient Page')
		patientpage.geometry('480x800')
		patientpage.config(bg='#ffffff')
		#patientpage.attributes('-fullscreen', True)
		list = db.search(Sample.patient_id == patient_id)
		for l in list:
			Label(patientpage, text = "Sample Id: "+l['sample_id'], font = "Helvetica 14 bold", background = "white", justify="left").place(relx=0.1,rely=0.1)
			Label(patientpage, text = "Patient Id: "+l['patient_id'], font = "Helvetica 14", background = "white", justify="left").place(relx=0.1,rely=0.15)
			Label(patientpage, text = "Bottle Type: "+l['tube_type'], font = "Helvetica 14", background = "white", justify="left").place(relx=0.1,rely=0.2)
			Label(patientpage, text = "Sample collection date: "+l['col_date'], font = "Helvetica 14", background = "white", justify="left").place(relx=0.1,rely=0.25)
			Label(patientpage, text = "Sample registration time: "+l['regd_time'], font = "Helvetica 14", background = "white", justify="left").place(relx=0.1,rely=0.3)
		
		Label(patientpage, text = "Patient Name",font = "Helvetica 14", background = "white", justify="left").place(relx=0.1,rely=0.35)
		nameE = Entry(patientpage,font = "Helvetica 14", background = "white")
		nameE.place(relx=0.5,rely=0.35)
			
		Label(patientpage, text = "Gender",font = "Helvetica 14", background = "white", justify="left").place(relx=0.1,rely=0.4)
		var = StringVar()
		Button1 = Radiobutton(patientpage, text="Female", variable=var, value="Female",font = "Helvetica 16", background = "white", bd=0, width = 10)
		Button2 = Radiobutton(patientpage, text="Male", variable=var, value="Male",font = "Helvetica 16", background = "white", bd=0, width = 10)
		Button3 = Radiobutton(patientpage, text="Other", variable=var, value="Pediatric",font = "Helvetica 16", background = "white", bd=0, width = 10)
		Button1.place(relx=0.1,rely=0.45,anchor=W)
		Button2.place(relx=0.4,rely=0.45,anchor=W)
		Button3.place(relx=0.7,rely=0.45,anchor=W)


		Label(patientpage, text = "Age",font = "Helvetica 14", background = "white", justify="left").place(relx=0.1,rely=0.5)
		ageE = Entry(patientpage, font = "Helvetica 14", background = "white")
		ageE.place(relx=0.5,rely=0.5)
		
		Label(patientpage, text = "Referred by",font = "Helvetica 14", background = "white", justify="left").place(relx=0.1,rely=0.55)
		referE = Entry(patientpage, font = "Helvetica 14", background = "white")
		referE.place(relx=0.5,rely=0.55)
		
		markupL = Label(patientpage, text = "",font = "Helvetica 14", background = "white", justify="left")
		markupL.place(relx=0.3,rely=0.7)
		
		Button(patientpage, text='Submit', font = "Helvetica 14", background = "white", command=lambda: patientconfirm(patient_id, markupL)).place(relx=0.5,rely=0.65,anchor=CENTER)
		
        def patientconfirm(patient_id, markupL):
            pconfirm = messagebox.askquestion("Confirm","Proceed with patient details?")
    		if pconfirm == 'no':
    			PatientPage()
    			exit()
    		else:
    			add_patientdetails(patient_id, markupL)
         
		def add_patientdetails(patient_id, markupL):
			confirmpatient = 'yes'
			if confirmpatient == 'no':
				patientpage()
				exit()
			else:
				name = nameE.get()
				age = ageE.get()
				gender = var.get()
				refer = referE.get()
				if(name==''): markupL.configure(text = "Please enter patient name")
                    else if: (age.isnumeric==False)or(age>0)or(age>120): markupL.configure(text = "Please enter valid age")
				    else:
					    db.update({'name': name, 'gender': gender, 'age': age, 'refer':refer}, Sample.patient_id == patient_id)
					    markupL.configure(text = "Patient details are updated")
					    patientpage.after(1000, lambda: Homepage())
			
		drawKeyboard(patientpage)
		patientpage.mainloop()
		
	def ResultPage(sampleid):
		try: homepage.destroy()
		except: print('')
		try: resultview.destroy()
		except: print('')
		global result
		result = Toplevel()
		result.title(sampleid)
		result.geometry('480x800')
		
		resultcanvas = Canvas(result)
		resultcanvas.pack(fill = BOTH, expand=1)
		resultcanvas.config(bg='#ffffff')
		result.attributes('-fullscreen', True)
		db = TinyDB('/home/pi/COL_0.0.3/results.json')
		Sample = Query()

		list = db.search(Sample.sample_id == str(sampleid))
		print("db search completed")
		print(list)
		for l in list:
			Label(resultcanvas, text = "Sample Id: "+l['sample_id'], font = "Helvetica 12", background = "white", justify="left").place(relx=0.5,rely=0.1)
			Label(resultcanvas, text = "Bottle Type: "+l['tube_type'], font = "Helvetica 12", background = "white", justify="left").place(relx=0.5,rely=0.15)
			Label(resultcanvas, text = "Sample collection time: ", font = "Helvetica 12", background = "white", justify="left").place(relx=0.5,rely=0.2)
			Label(resultcanvas, text = l['regd_time'], font = "Helvetica 12", background = "white", justify="left").place(relx=0.5,rely=0.25)
		
			Label(resultcanvas, text = "Patient Id: "+l['patient_id'], font = "Helvetica 12", background = "white", justify="left").place(relx=0.1,rely=0.1)
			Label(resultcanvas, text = "Patient Name: "+l['name'], font = "Helvetica 12", background = "white", justify="left").place(relx=0.1,rely=0.15)
			Label(resultcanvas, text = "Patient Gender: "+l['gender'], font = "Helvetica 12", background = "white", justify="left").place(relx=0.1,rely=0.2)
			Label(resultcanvas, text = "Patient Age: "+l['age'], font = "Helvetica 12", background = "white", justify="left").place(relx=0.1,rely=0.25)
			
			#put this data in a table and show all associated results
			Label(resultcanvas, text = "Test Time: "+l['readings']['test_time'], font = "Helvetica 12", background = "white", justify="left").place(relx=0.1,rely=0.4)
			Label(resultcanvas, text = "Result: "+l['readings']['result'], font = "Helvetica 12", background = "white", justify="left").place(relx=0.1,rely=0.45)
		
		Button(result, text = "View all results", font = "Helvetica 12", justify="left", width =10, command=lambda: ResultView()).place(relx=0.1,rely=0.8)
		Button(result, text = "Homepage", font = "Helvetica 12", justify="left", width =10, command=lambda: Homepage()).place(relx=0.5,rely=0.8)
		
		def genpdf(list):
			pdf = FPDF()
			pdf.add_page()
			pdf.set_font("helvetica", size = 12)
			pdf.image('colorcult_logo.jpg',10,5,30)
			
			for l in list:
				pdf.cell(200, 10, txt = "Sample Id: "+l['sample_id'], ln=1,align='L')
				pdf.cell(200, 10, txt = "Bottle Type: "+l['tube_type'], ln=2,align='L')
				pdf.cell(200, 10, txt = "Sample Collection Date: "+l['col_date'], ln=3,align='L')
				pdf.cell(200, 10, txt = "--------------------------------------------------------------------------------------------------", ln=4,align='L')
				pdf.cell(200, 10, txt = "Patient Id: "+l['patient_id'], ln=6,align='L')
				pdf.cell(200, 10, txt = "Patient Name: "+l['name'], ln=7,align='L')
				pdf.cell(200, 10, txt = "Age: "+l['age'], ln=8,align='L')
				pdf.cell(200, 10, txt = "Gender: "+l['gender'], ln=9,align='L')
				pdf.cell(200, 10, txt = "Referred by: "+l['refer'], ln=10,align='L')
				pdf.cell(200, 10, txt = "Result: "+l['readings']['result'], ln=11,align='L')
				pdf.cell(200, 10, txt = "Time of test: "+l['readings']['test_time'], ln=12,align='L')
				pdf.cell(200, 10, txt = "--------------------------------------------------------------------------------------------------", ln=13,align='L')
				pdf.cell(200, 10, txt = "", ln=14,align='L')
				pdf.cell(200, 10, txt = "", ln=15,align='L')
				pdf.cell(200, 10, txt = "", ln=16,align='L')
				pdf.cell(200, 10, txt = "Signature: ", ln=16,align='L')
				pdf.set_font("helvetica", size = 6)
				pdf.cell(200, 10, txt = "Report Generated on Device id: COLS2101; Software version 0.0.3.1 ",ln=17,align='L')
				
			pdf.output("results/"+str(sampleid)+".pdf")
		genpdf(list)	
		print("pdf generation completed")
		result.mainloop()	

	def ResultView():
		try: homepage.destroy()
		except: print('')
		global resultview
		resultview = Toplevel()
		resultview.title('Main')
		resultview.geometry('480x800')
		resultview.config(bg='#ffffff')
		#resultview.attributes('-fullscreen', True)
		
		columns = ('sample_id','patient_id','tubetype','result', 'days')
		grid_frame = LabelFrame(resultview, text = 'All results', font = "Helvetica 12", background="white")
		grid_frame.pack(fill = 'x')
		tree = ttk.Treeview(grid_frame, columns=columns, show='headings')
		tree.pack(fill = BOTH, expand=1)
		
		tree.heading('sample_id', text='Id', command=lambda: treeview_sort_column(tree, 'sample_id', False))
		tree.column("sample_id", width=80, stretch=NO)
		
		tree.heading('patient_id', text='Patientid', command=lambda: treeview_sort_column(tree, 'patient_id', False))
		tree.column("patient_id", width=80, stretch=NO)
		
		tree.heading('tubetype', text='Type', command=lambda: treeview_sort_column(tree, 'tubetype', False))
		tree.column("tubetype", width=80, stretch=NO)
		
		tree.heading('result', text='Result', command=lambda: treeview_sort_column(tree, 'result', False))
		tree.column("result", width=90, stretch=NO)
		
		tree.heading('days', text='Test time',command=lambda: treeview_sort_column(tree, 'days', False))
		tree.column("days", width=140, stretch=NO)
		# generate sample data
		list = db.all()
		readings = []
		for l in list:
			readings.append((l['sample_id'], l['patient_id'], l['tube_type'], l['readings']['result'],l['readings']['test_time']))
		for reading in readings:
			tree.insert('', tk.END, values=reading)
		#tree.grid(row=0, column=0, sticky='nsew')
		
		vsb = ttk.Scrollbar(grid_frame, orient="vertical", command=tree.yview)
		vsb.place(relx=0.95, rely=0.8, height=300, width=30, anchor=CENTER)
		#vsb.pack(side=RIGHT, fill=BOTH)
		
		#add functionality to see pdf within the window
		def show_pdf(markupL):
			for selected_item in tree.selection():
				item = tree.item(selected_item)
				sampleid = item['values'][0]
				try: webbrowser.open_new("results/"+sampleid+".pdf")
				except: markupL.configure(text = "Sample report not found")
		
		def run_test(markupL):
			for selected_item in tree.selection():
				item = tree.item(selected_item)
				sampleid = item['values'][0]
				readtest(sampleid)
		
		#tree.bind('<<TreeviewSelect>>', show_pdf)
		
		tree.configure(yscrollcommand=vsb.set)
		button_frame = LabelFrame(resultview, text = '',background="white")
		button_frame.pack(side = TOP, fill = 'x')
		Label(button_frame, text = "", font = "Helvetica 12",background="white").pack(side = TOP, fill='x')
		markupL = Label(button_frame, text = "", font = "Helvetica 10",background="white")
		markupL.pack(side = BOTTOM, fill='x')
		Button(button_frame, text = "Results folder", font = "Helvetica 14", background="white", command = lambda: browseFiles()).pack(side = LEFT)
		Button(button_frame, text = "Homepage", font = "Helvetica 14", background="white", command = lambda: Homepage()).pack(side = LEFT)
		Button(button_frame, text = "Run Test", font = "Helvetica 14",background="white", command = lambda: run_test(markupL)).pack(side = LEFT)
		Button(button_frame, text = "See Report", font = "Helvetica 14", background="white",command = lambda: show_pdf(markupL)).pack(side = LEFT)
		Label(button_frame, text = "", font = "Helvetica 12",background="white").pack(side = TOP, fill='x')
		resultview.mainloop()
		
	def DeviceInfo():
		global deviceinfo
		homepage.destroy()
		deviceinfo = Toplevel()
		deviceinfo.title('Main')
		deviceinfo.geometry('480x800')
		deviceinfo.config(bg='#ffffff')
		deviceinfo.attributes('-fullscreen', True)
		
		Label(deviceinfo, text = "--------------This is system info-----------", font = "Helvetica 16", background="white", justify = "center").place(relx=0.1,rely=0.1)
		Label(deviceinfo, text = "Device id: COLS2102", font = "Helvetica 16", background="white", justify = "left").place(relx=0.1,rely=0.3)
		Label(deviceinfo, text = "Software Version: 0.0.3", font = "Helvetica 16", background="white", justify = "left").place(relx=0.1,rely=0.35)
		Label(deviceinfo, text = "Installation date: 28 Dec 2021", font = "Helvetica 16", background="white", justify = "left").place(relx=0.1,rely=0.4)
		Label(deviceinfo, text = "Device state: Active", font = "Helvetica 16", background="white", justify = "left").place(relx=0.1,rely=0.45)
		#Button(deviceinfo, text = "Hardware Scan", command = lambda: Hardwarescan()).place(relx=0.1,rely=0.6)
		Button(deviceinfo, text = "Homepage", command = lambda: Homepage()).place(relx=0.5,rely=0.6)
		img = ImageTk.PhotoImage(Image.open("/home/pi/COL_0.0.3/logo.jpg"))
		Label(deviceinfo, image = img, font = "Helvetica 16", background="white", justify = "left").place(relx=0.1,rely=0.45)
		deviceinfo.mainloop()

	def Hardwarescan():
		deviceinfo.destroy()
		try: homepage.destroy()
		except: print('')
		hscan = Toplevel()
		hscan.title('Main')
		hscan.geometry('480x800')
		hscan.config(bg='#ffffff')
		hscan.attributes('-fullscreen', True)
		disk_list=disk_check()
		
		label_frame = LabelFrame(hscan, text = 'Device Memory')
		label_frame.pack(side = TOP, fill = 'x')
		for i in disk_list:
			Label(label_frame, text = i).pack(side = TOP, fill = 'x')
		Button(hscan, text = "Homepage", command = lambda: Homepage()).place(relx=0.4,rely=0.8)
		hscan.mainloop()

	splash.mainloop()


	
Splash()
	
