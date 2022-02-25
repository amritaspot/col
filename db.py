from __future__ import print_function
from tkinter import *
import tkinter as tk
import tkinter.messagebox
import sys
import json
import os
import numpy as np
from datetime import datetime
import mysql.connector as mariadb
from tinydb import TinyDB, Query, where
from tinydb.operations import add, delete, set, subtract
from tinydb.table import Document
import time   
import PIL
from PIL import Image, ImageTk
from time import sleep
from tkinter import ttk
from tkinter import filedialog
import pyautogui
import psutil
import platform
import numpy as np
import matplotlib
import cv2
#from picamera import PiCamera
import time
from fpdf import *
from time import sleep
#import RPi.GPIO as GPIO
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, peak_widths, peak_prominences
import webbrowser
#--------------------------------database definitions-------------------------------------------------------------------------------------------------------------
db = TinyDB('/home/pi/COL_0.0.3/results.json')
Sample = Query()

     
#---------------------------------------------------screens------------------------------------------------------------------------------------------------------------
def Splash():
	global splash
	splash = Tk()
	splash.title('Main')
	splash.geometry('480x800')
	splash.config(bg='#ffffff')
	#splash.attributes('-fullscreen', True)
	img = ImageTk.PhotoImage(Image.open("logo.jpg"))
	next = ImageTk.PhotoImage(Image.open("next.png")) 
	Label(splash, image=img, background = "white").place(relx=0.5,rely=0.5,anchor=CENTER)
	Label(splash, text="Loading colorcult scanner...", font = "Helvetica 10 bold", background = "white").place(relx=0.5,rely=0.55,anchor=CENTER)
	splash.after(5000, lambda: Homepage())
	

	def Homepage():
		global homepage
		global sampleid
		homepage = Toplevel()
		homepage.title('Homepage')
		homepage.geometry('480x800')
		homepage.config(bg='#ffffff')
		#homepage.attributes('-fullscreen', True)
		menubar = Menu(homepage)
		
		# keep sampleid definition as 0 so that it is reset everytime homepage is run
		sampleid = 0
		
		#define the menubar with options: results, help, power
		results = Menu(menubar, tearoff = 0)
		menubar.add_cascade(label ='Results', menu = results)
		results.add_command(label="List", command=lambda:ResultsView)
		results.add_command(label="Directory", command=lambda:ResultsFolder)
		
		help = Menu(menubar, tearoff = 0)
		menubar.add_cascade(label ='Help', menu = help)
		help.add_command(label ='Device Info', command = lambda:DeviceInfo)
		help.add_command(label ='Hardware check', command = lambda:Hardwarescan)
		
		shutdown = Menu(menubar, tearoff = 0)
		menubar.add_cascade(label ='Power', menu = shutdown)
		shutdown.add_command(label ='Shutdown', command = lambda:poweroff())
		shutdown.add_command(label ='Restart', command = lambda:restart())
		homepage.config(menu = menubar)
		
		img = ImageTk.PhotoImage(Image.open("scan_ocr.png"))
		
		Button(homepage, image = img, bd=0, background = "white", command=lambda: scan_ocr()).place(relx=0.5,rely=0.3,anchor=CENTER)
		#Button(homepage, text = "Scan OCR on the bottle", bd=0, font = "Helvetica 18", background = "white", command=lambda: scan_ocr()).place(relx=0.5,rely=0.3,anchor=CENTER)
		Label(homepage, text = "Or Enter Sample Id",font = "Helvetica 14", background = "white").place(relx=0.5,rely=0.5,anchor=CENTER)
		
		sampleE = Entry(homepage,font = "Helvetica 14")
		sampleE.place(relx=0.5,rely=0.55,anchor=CENTER)
		
		def get_sampleid(sampleid):
			if (sampleid == 0):
				sampleid = sampleE.get()
				check_sampleid(sampleid)        		
	       
		button = Button(homepage, text='Submit',font = "Helvetica 14", background = "white", command=lambda: get_sampleid(sampleid))
		button.place(relx=0.5,rely=0.6,anchor=CENTER)
		drawKeyboard(homepage)	
		#splash.destroy()
		homepage.mainloop()

	def RegisterTest(sampleid):
		#homepage.destroy()
		global registertest
		global patientE
		registertest = Toplevel()
		registertest.title('Register Test')
		registertest.geometry('480x800')
		registertest.config(bg='#ffffff')
		#registertest.attributes('-fullscreen', True)
		
		Label(registertest, text="Sample ID:"+sampleid,font = "Helvetica 16", background = "white", justify="left").place(relx=0.5,rely=0.1,anchor=CENTER)
		Label(registertest, text="Select Tube Type", font = "Helvetica 14", background = "white", justify="left").place(relx=0.5,rely=0.25,anchor=CENTER)
		
		var = StringVar()  
		Button1 = Radiobutton(registertest, text="Aerobic", variable=var, value="aerobic",font = "Helvetica 12", background = "white", bd=0, width = 10)
		Button2 = Radiobutton(registertest, text="Anaerobic", variable=var, value="anaerobic",font = "Helvetica 12", background = "white", bd=0, width = 10)
		Button3 = Radiobutton(registertest, text="Pediatric", variable=var, value="pediatric",font = "Helvetica 12", background = "white", bd=0, width = 10)
		Button1.place(relx=0.2,rely=0.3,anchor=CENTER)
		Button2.place(relx=0.5,rely=0.3,anchor=CENTER)
		Button3.place(relx=0.8,rely=0.3,anchor=CENTER)
		
		Label(registertest, text="Select sample Type",font = "Helvetica 14", background = "white").place(relx=0.5,rely=0.45,anchor=CENTER)
		
		var1 = StringVar()  
		Button4 = Radiobutton(registertest, text="Whole Blood", variable=var1, value="whole_blood",font = "Helvetica 12", background = "white", bd = 0, width = 10)
		Button5 = Radiobutton(registertest, text="Clear", variable=var1, value="clear",font = "Helvetica 12", background = "white", bd = 0, width = 10)
		Button4.place(relx=0.3,rely=0.5,anchor=CENTER)
		Button5.place(relx=0.7,rely=0.5,anchor=CENTER)
		
		def add_sample(sampleid):
		    tubetype = var.get()
		    sampletype = var1.get()
		    patient_id = patientE.get()
		    reg_date = str(datetime.now().replace(microsecond=0))
		    db.insert({'sample_id': sampleid, 'patient_id': patient_id, 'tube_type': tubetype, 'sample_type': sampletype, 'regd_time':reg_date, 'readings':{}}) 
		    tkinter.messagebox.showinfo(sampleid, "Sample is registered at"+reg_date)
		    PatientPage(patient_id)
		    
		Label(registertest, text = "Enter Patient id",font = "Helvetica 14", background = "white", justify="left").place(relx=0.5,rely=0.6,anchor=CENTER)
		patientE = Entry(registertest,font = "Helvetica 12", background = "white")
		patientE.place(relx=0.5,rely=0.65, anchor=CENTER)
		Button(registertest, text='Submit', font = "Helvetica 12", background = "white", command=lambda: add_sample(sampleid)).place(relx=0.5,rely=0.7,anchor=CENTER)
		drawKeyboard(registertest)
		registertest.mainloop()
		
	def PatientPage(patient_id):
		#registertest.destroy()
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
			Label(patientpage, text = "Sample Id: "+l['sample_id'], font = "Helvetica 12", background = "white", justify="left").place(relx=0.1,rely=0.1)
			Label(patientpage, text = "Patient Id: "+l['patient_id'], font = "Helvetica 12", background = "white", justify="left").place(relx=0.1,rely=0.15)
			Label(patientpage, text = "Bottle Type: "+l['tube_type'], font = "Helvetica 12", background = "white", justify="left").place(relx=0.1,rely=0.2)
			Label(patientpage, text = "Sample collection time: "+l['regd_time'], font = "Helvetica 12", background = "white", justify="left").place(relx=0.1,rely=0.25)
		
		Label(patientpage, text = "Patient Name",font = "Helvetica 12", background = "white", justify="left").place(relx=0.1,rely=0.35)
		nameE = Entry(patientpage,font = "Helvetica 12", background = "white")
		nameE.place(relx=0.5,rely=0.35)
			
		Label(patientpage, text = "Gender",font = "Helvetica 12", background = "white", justify="left").place(relx=0.1,rely=0.4)
		genderE = Entry(patientpage, font = "Helvetica 12", background = "white")
		genderE.place(relx=0.5,rely=0.4)
		
		Label(patientpage, text = "Age",font = "Helvetica 12", background = "white", justify="left").place(relx=0.1,rely=0.45)
		ageE = Entry(patientpage, font = "Helvetica 12", background = "white")
		ageE.place(relx=0.5,rely=0.45)
		
		Button(patientpage, text='Submit', font = "Helvetica 12", background = "white", command=lambda: add_patientdetails(patient_id)).place(relx=0.5,rely=0.6,anchor=CENTER)
		
		def add_patientdetails(patient_id):
			name = nameE.get()
			age = ageE.get()
			gender = genderE.get()
			db.update({'name': name, 'gender': gender, 'age': age}, Sample.patient_id == patient_id)
			tkinter.messagebox.showinfo(patient_id, "Patient details are updated")
			Homepage()
			
		drawKeyboard(patientpage)
		patientpage.mainloop()
		
	def ResultPage(sampleid):
		#homepage.destroy()
		result = Toplevel()
		result.title(sampleid)
		result.geometry('480x800')
		
		resultcanvas = Canvas(result)
		resultcanvas.pack(fill = BOTH, expand=1)
		resultcanvas.config(bg='#ffffff')
		#result.attributes('-fullscreen', True)
		
		list = db.search(Sample.sample_id == sampleid)
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
		
		def genpdf(list):
			pdf = FPDF()
			pdf.add_page()
			pdf.set_font("arial", size = 10)
			pdf.image('colorcult_logo.jpg',10,5,30)
			
			for l in list:
				pdf.cell(200, 10, txt = "Sample Id: "+l['sample_id'], ln=1,align='L')
				pdf.cell(200, 10, txt = "Bottle Type: "+l['tube_type'], ln=2,align='L')
				pdf.cell(200, 10, txt = "Sample Collection Time: "+l['regd_time'], ln=3,align='L')
				pdf.cell(200, 10, txt = "--------------------------------------------------------------------------------------------------", ln=4,align='L')
				pdf.cell(200, 10, txt = "Patient Id: "+l['patient_id'], ln=6,align='L')
				pdf.cell(200, 10, txt = "Patient Name: "+l['name'], ln=7,align='L')
				pdf.cell(200, 10, txt = "Age: "+l['age'], ln=8,align='L')
				pdf.cell(200, 10, txt = "Gender: "+l['gender'], ln=9,align='L')
				pdf.cell(200, 10, txt = "Result: "+l['readings']['result'], ln=10,align='L')
				pdf.cell(200, 10, txt = "Time of test: "+l['readings']['test_time'], ln=11,align='L')
				pdf.cell(200, 10, txt = "--------------------------------------------------------------------------------------------------", ln=12,align='L')
				pdf.cell(200, 10, txt = "", ln=13,align='L')
				pdf.cell(200, 10, txt = "", ln=14,align='L')
				pdf.cell(200, 10, txt = "", ln=15,align='L')
				pdf.cell(200, 10, txt = "Signature: ", ln=16,align='L')
				pdf.set_font("arial", size = 6)
				pdf.cell(200, 10, txt = "Report Generated on Device id: COLS2101; Software version 0.0.3 ",ln=17,align='L')
				
			pdf.output("/home/pi/COL_0.0.3/results"+sampleid+".pdf")
		genpdf(list)	 
		Button(result, text = "View all results", font = "Helvetica 12", justify="left", width =10, command=lambda: ResultView()).place(relx=0.1,rely=0.8)
		Button(result, text = "Homepage", font = "Helvetica 12", justify="left", width =10, command=lambda: Homepage()).place(relx=0.5,rely=0.8)
		result.mainloop()	

	def ResultView():
		#homepage.destroy()
		resultview = Toplevel()
		resultview.title('Main')
		resultview.geometry('480x800')
		resultview.config(bg='#ffffff')
		#resultview.attributes('-fullscreen', True)
		
		columns = ('sample_id','patient_id','tubetype','result', 'days')
		grid_frame = LabelFrame(resultview, text = 'All results', font = "Helvetica 12", background="white")
		grid_frame.pack(fill = BOTH, expand=1)
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
		vsb.place(relx=0.99, rely=0.8, height=300, anchor=CENTER)
		
		def show_pdf(event):
			for selected_item in tree.selection():
				item = tree.item(selected_item)
				sampleid = item['values'][0]
				webbrowser.open_new('/home/amrita/Desktop/colorscan/'+sampleid+'.pdf')
		
		tree.bind('<<TreeviewSelect>>', show_pdf)
		
		tree.configure(yscrollcommand=vsb.set)
		button_frame = LabelFrame(resultview, text = '')
		button_frame.pack(side = TOP, fill = 'x')
		Button(button_frame, text = "Results folder", command = lambda: browseFiles()).pack(side = LEFT)
		Button(button_frame, text = "Homepage").pack(side = LEFT)
		resultview.mainloop()
		
	def DeviceInfo():
		global deviceinfo
		deviceinfo = Toplevel()
		deviceinfo.title('Main')
		deviceinfo.geometry('480x800')
		deviceinfo.config(bg='#ffffff')
		#deviceinfo.attributes('-fullscreen', True)
		
		Label(deviceinfo, text = "--------------This is system info-----------", font = "Helvetica 16", background="white", justify = "center").place(relx=0.1,rely=0.1)
		Label(deviceinfo, text = "Device id: COLS2101", font = "Helvetica 16", background="white", justify = "left").place(relx=0.1,rely=0.3)
		Label(deviceinfo, text = "Software Version: 0.0.3", font = "Helvetica 16", background="white", justify = "left").place(relx=0.1,rely=0.35)
		Label(deviceinfo, text = "Installation date: 12 Dec 2021", font = "Helvetica 16", background="white", justify = "left").place(relx=0.1,rely=0.4)
		Label(deviceinfo, text = "Device state: Active", font = "Helvetica 16", background="white", justify = "left").place(relx=0.1,rely=0.45)
		Button(deviceinfo, text = "Hardware Scan", command = lambda: Hardwarescan()).place(relx=0.1,rely=0.6)
		Button(deviceinfo, text = "Homepage", command = lambda: Homepage()).place(relx=0.5,rely=0.6)
		img = ImageTk.PhotoImage(Image.open("logo.jpg"))
		Label(deviceinfo, image = img, font = "Helvetica 16", background="white", justify = "left").place(relx=0.1,rely=0.45)
		deviceinfo.mainloop()

	def Hardwarescan():
		#deviceinfo.destroy()
		hscan = Toplevel()
		hscan.title('Main')
		hscan.geometry('480x800')
		hscan.config(bg='#ffffff')
		#hscan.attributes('-fullscreen', True)
		disk_list=disk_check()
		
		label_frame = LabelFrame(hscan, text = 'Device Memory')
		label_frame.pack(side = TOP, fill = 'x')
		for i in disk_list:
			Label(label_frame, text = i).pack(side = TOP, fill = 'x')
		hscan.mainloop()

	#--------------------------------image proccessing functions-----------------------------------------------------------------------------------------------------
	def camcapture():
	    camera = PiCamera()
	    GPIO.setwarnings(False)
	    GPIO.setmode(GPIO.BOARD)
	    GPIO.setup(40, GPIO.OUT)
	    GPIO.output(40, True)
	    GPIO.cleanup
	    camera.vflip = True
	    #camera.start_preview()
	    #time.sleep(3)
	    camera.capture('/home/pi/COL_0.0.3/results/captured.jpg')
	    #camera.stop_preview()
	    GPIO.output(40,False)
	    input_image = cv2.imread('/home/pi/COL_0.0.3/results/captured.jpg')
	    camera.close()
	    return input_image

	def val_sensor(img):
	    value=[]
	    for rot in range(1, 5):
		x = 100+rot*30
		h = x+100
		imgcopy = img[320:400, x:h]
		cv2.imwrite('/home/pi/COL_0.0.3/results/cropped_sensor.jpg', imgcopy)
		b, g, r = cv2.split(imgcopy)
		input = b
		[a, b] = input.shape[:2]
		hist = cv2.calcHist([input],[0],None,[256],[0,256])
		np.savetxt('/home/pi/COL_0.0.3/results/hist.csv', hist, delimiter=',')
		plt.plot(hist)
		plt.savefig('/home/pi/COL_0.0.3/results/histogram.jpg')
		plt.close()
		length = len(hist)
		i=0
		hist_array = []
		while(i<length):
		    hist_array = np.append(hist_array, hist[i][0])
		    i = i+1
		index = np.where(hist_array == np.amax(hist_array))
		value = np.append(value, index[0][0])
		print(value)
	    num_reading = np.average(value)
	    print(num_reading)
	    if (num_reading < 40):
		result = "Positive"
	    else:
		result = "Negative"
	    return result
	    
	def readtest(sampleid):
		result = ''
		try:
			image = camcapture()
			result = val_sensor(image)
		except:
			tkinter.messagebox.showinfo(sampleid, "Sample could not be read, please try again")
		test_time = str(datetime.now().replace(microsecond=0))
		db.update({'reading':{'result': result, 'test_time': test_time}}, Sample.patient_id == patient_id)
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
		        if len(key) <= 1:
		            key_button = ttk.Button(group_frame, text = key, width = 4, takefocus=False)
		        else:
		            key_button = ttk.Button(group_frame, text = key.center(5, ' '), takefocus=False)
		        if ' ' in key:
		            key_button['state'] = 'disable'
		        key_button['command'] = lambda q=key: key_command(q)
		        key_button.pack(side = 'left', fill = 'both', expand = 'yes')

	    def key_command(event):
		entry = parent.focus_get()
		if event == 'Bksp':
			entry.delete(len(entry.get())-1, 'end')
		elif event == 'Space':
			entry.insert("end", " ")
		else:
			entry.insert("end", event)
	    
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
		if bytes < factor:
		    return f"{bytes:.2f}{unit}{suffix}"
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
	def poweroff():
		shutdown = input("Do you wish to shutdown your computer ? (yes / no): ")
		if shutdown == 'no':
			exit()
		else:
			os.system("shutdown /s /t 1")
		
	def restart():
		restart = input("Do you wish to restart your computer ? (yes / no): ")
		if restart == 'no':
			exit()
		else:
			os.system("shutdown /r /t 1")
		
	def browseFiles():
	    filename = filedialog.askopenfile(initialdir = "/home/pi/COL_0.0.3/results", title = "Select a File", filetypes = (("Result files", "*.pdf*"),("all files","*.*")))
	    path = filename.name
	    webbrowser.open_new(path)



	def get_timedelta(date_string1, date_string2):
		date_time_obj1 = datetime. strptime(date_string1, '%Y-%m-%d %H:%M:%S')
		date_time_obj2 = datetime. strptime(date_string2, '%Y-%m-%d %H:%M:%S')
		delta = date_time_obj2-date_time_obj1
		delta_hrs = (delta.days*24+int((delta.seconds/3600)))
		return delta_hrs

	#-------------------------------------------------module functions---------------------------------------------------------------------------------------------
	def scan_ocr():

	#..... this function needs to be defined later--------------------
		try:
			sampleid = 0
			check_sampleid(sampleid) 
		except:
			sampleid = 0
			print("couldn't read")
		return sampleid

		
	def check_sampleid(sampleid):
		time_now = str(datetime.now().replace(microsecond=0))
		list = db.search(Sample.sample_id == sampleid)
		if not list:
			tkinter.messagebox.showinfo(sampleid, "Please register the sample")
			RegisterTest(sampleid)
		else:
			for l in list:
				regd_time = l['regd_time']
				result = l['readings']['result']
			time_delta = get_timedelta(regd_time, time_now)
			if (time_delta < 5): 
				tkinter.messagebox.showinfo(sampleid, "Please read test after 5 hours.")
			elif (time_delta > 144):
				tkinter.messagebox.showinfo(sampleid, "Sample older than 6 days.")
				ResultPage(sampleid)
			else:
				if (result=="Positive"):
					tkinter.messagebox.showinfo(sampleid, "Sample already tested positive.")
					ResultPage(sampleid)
				else:
					readtest(sampleid)
					
				

	def treeview_sort_column(tv, col, reverse):
	    l = [(tv.set(k, col), k) for k in tv.get_children('')]
	    l.sort(reverse=reverse)

	    # rearrange items in sorted positions
	    for index, (val, k) in enumerate(l):
		tv.move(k, '', index)

	    # reverse sort next time
	    tv.heading(col, text=col, command=lambda _col=col: \
		         treeview_sort_column(tv, _col, not reverse))


	splash.mainloop()
		
Splash()
	


