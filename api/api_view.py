#!/usr/bin/env python

import gtk
import pygtk
import gobject
import libcloud.security
from libcloud.drivers.slicehost import SlicehostNodeDriver
from libcloud.drivers.rackspace import RackspaceNodeDriver
from libcloud.drivers.rackspace import RackspaceUKNodeDriver
from libcloud.types import NodeState
from functools import wraps

def memonize(func):
	cache = {}
	@wraps(func)
	def wrap(*args):
		if args not in cache:
			cache[args] = func(*args)
		return cache[args]
	return wrap
	
#TODO:decorate this function with the memonize decorator to get cached values
def listSizes(prov):
	if prov == 'slicehost':
		driver = SlicehostNodeDriver(key)
	return driver.sizes()

class app_calls(object):
	def __init__(self):
		self.frame = gtk.Frame(label=None)
		self.nodes_driver_dict={}
		self.slice_id_dict = []
		self.loading = gtk.Image()
		self.loading.set_from_file("loader.gif")
			
	def reboot_call(self, widget, data):
		for node in self.slice_nodes:
			if node.id == data:
				if node.state == NodeState.REBOOTING:
					dialog = gtk.Dialog(title='Slice State',
                     					flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,                       
                     					buttons = (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
 					dialog.vbox.pack_start(gtk.Label('Slice is already in reboot state.'))
 					dialog.show_all()
 					result = dialog.run()
 					if result == gtk.RESPONSE_CLOSE:
 						dialog.destroy()
				elif node.state == NodeState.RUNNING:
					node.reboot()
	
	def delete_call(self, widget, data, model, iters):
		for node in self.slice_nodes:
			if node.id == data:
				try:
					node.destroy()
					model.remove(iters)
				except Exception as detail:
					dialog = gtk.Dialog(title='Not Supported',
                     				flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,                       
                     				buttons = (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
 					dialog.vbox.pack_start(gtk.Label(detail))
 					dialog.show_all()
 					result = dialog.run()
 					if result == gtk.RESPONSE_CLOSE:
 						dialog.destroy()

	
	
	def rename_call(self, widget, data, prov):
		name = self.rename_name.get_text()
		self.rename_dialog.destroy()
		driver = self.nodes_driver_dict[prov]
		
		for node in self.slice_nodes:
			if node.id == data:
				try:
					driver.ex_set_server_name(node, name)
				except Exception as detail:
					dialog = gtk.Dialog(title='Not Supported',
                     				flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,                       
                     				buttons = (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
 					dialog.vbox.pack_start(gtk.Label(detail))
 					dialog.show_all()
 					result = dialog.run()
 					if result == gtk.RESPONSE_CLOSE:
 						dialog.destroy()
		
	def create_call(self, data, **kwargs):
		self.create_window.destroy()
		for args in kwargs:
			if args =='name':
				s_name = kwargs[args]
			elif args =='image':
				s_image = kwargs[args]
			elif args =='size':
				s_size = kwargs[args]
		driver = self.nodes_driver_dict[data]
		images = driver.list_images()
		sizes = driver.list_sizes()
		driver.create_node(name=s_name, image=images[s_image], size=sizes[s_size])
		
		for slices in driver.list_nodes():
			if slices.id not in self.slice_id_dict:		
				ip = ','.join([ip for ip in slices.public_ip])
				self.store.append([slices.name, data, slices.id, slices.state, ip])	
			
	def callback(self, widget, data=None):
		widget.get_active()
		
			
	def delete_event(self, widget, data=None):
		return False
		
	def not_supported(self, widget, data=None):
		dialog = gtk.Dialog(title='Not Supported',
                     		flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,                       
                     		buttons = (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
 		dialog.vbox.pack_start(gtk.Label('This action is not supported yet.'))
 		dialog.show_all()
 		result = dialog.run()
 		if result == gtk.RESPONSE_CLOSE:
 			dialog.destroy()

	
	def rename_slice(self, widget, data=None):
		selected = self.treeView.get_selection()
        	model, row = selected.get_selected_rows()
        	to_rename= model[row[0][0]][2]
        	prov = model[row[0][0]][1]
		self.rename_dialog = gtk.Dialog(title='Rename Slice',
				flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
		button1 = gtk.Button(label='Rename')
		button2 = gtk.Button(label='Cancel')
		label = gtk.Label("Enter New Name")
		self.rename_name = gtk.Entry()
		self.rename_name.set_visibility(True)
  		self.rename_dialog.vbox.pack_start(label, False, False, 5)
  		self.rename_dialog.vbox.pack_start(self.rename_name, False, False, 5)
		self.rename_dialog.action_area.pack_start(button1, False, False, 5)
		self.rename_dialog.action_area.pack_start(button2, False, False, 5)
		button1.connect('pressed', lambda w: self.rename_call(widget, to_rename, prov))
		button2.connect('pressed', lambda w: self.rename_dialog.destroy())
  		self.rename_dialog.show_all()
  				
	def reboot_slice(self, widget, data=None):
		selected = self.treeView.get_selection()
        	model, row = selected.get_selected_rows()
        	to_reboot= model[row[0][0]][2]
		self.reboot_dialog = gtk.Dialog(title='Reboot Slice',
                    					flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,                       
                    					buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
		self.reboot_dialog.vbox.pack_start(gtk.Label('Reboot the slice?'))
 		self.reboot_dialog.show_all()
 		result = self.reboot_dialog.run()
 		if result == gtk.RESPONSE_OK:
 			self.reboot_call(widget, to_reboot)
 			self.reboot_dialog.destroy()
 		elif result == gtk.RESPONSE_CLOSE:
 			self.reboot_dialog.destroy()
				
	def delete_slice(self, widget, data=None):
		selected = self.treeView.get_selection()
        	model, row = selected.get_selected_rows()
        	to_delete= model[row[0][0]][2]
        	iters=model.get_iter(row[0][0])
        		
		self.delete_dialog = gtk.Dialog(title='Delete Slice',
                				flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,                       
                				buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
 		self.delete_dialog.vbox.pack_start(gtk.Label('Delete the slice?\n Once the slice is deleted, there is no turning back.'))
 		self.delete_dialog.show_all()
 		result = self.delete_dialog.run()
 		if result == gtk.RESPONSE_OK:
 			self.delete_call(widget, to_delete, model, iters)
			self.delete_dialog.destroy() 		
 		elif result == gtk.RESPONSE_CLOSE:
 			self.delete_dialog.destroy()
	
	def remove_provider(self, widget, data=None):
		selected = self.treeview.get_selection()
		model, row = selected.get_selected_rows()
		to_remove = model[row[0][0]][0]
		iters=model.get_iter(row[0][0])
		model.remove(iters)
		pathlist = []
		#call foreach with data=to_remove and pathlist to store path
  		self.store.foreach(self.match_value_for_provider, (to_remove, pathlist))
  		pathlist.reverse()
  		for path in pathlist:
    			self.store.remove(self.store.get_iter(path))
			
	def match_value_for_provider(self, model, path, iters, data):
		if self.store.get_value(iters, 1) == data[0]:
      			data[1].append(path)
    		# keep the foreach going, if return is True foreach will stop
    		return False     

  		

	def  create_slice(self, widget, data=None):
		try:
			self.create_window = gtk.Window()
			self.create_window.set_modal(True)
			self.create_window.set_title('Create Slice')
			self.create_window.connect('delete_event', self.delete_event)
			self.create_window.connect('destroy', lambda w: self.create_window.destroy())
			self.create_window.set_border_width(10)
			self.create_window.set_position(gtk.WIN_POS_CENTER)
			self.create_window.set_default_size(350,250)
			self.create_main_vbox = gtk.VBox(False)
			self.create_provider_vbox = gtk.VBox(True)
			self.create_container_vbox = gtk.VBox(True)
			create_size_vbox = gtk.VBox(True)
			create_image_vbox = gtk.VBox(True)
			create_name_vbox = gtk.VBox(True)
			provider_combobox = gtk.combo_box_new_text()
	      		#provider_combobox.append_text('Select Provider:')
			for prov in self.nodes_driver_dict:
				provider_combobox.append_text(prov)
			provider_combobox.connect('changed', self.changed_create_slice_cb, prov)
			provider_combobox.set_active(0)
			self.create_provider_vbox.pack_start(provider_combobox, False, False, 0)
			self.create_main_vbox.pack_start(self.create_provider_vbox, False, False, 2)
			self.create_main_vbox.pack_start(self.create_container_vbox, False, False, 2)
			self.create_window.add(self.create_main_vbox)		
			self.create_window.show_all()
		
		except AttributeError:
			dialog = gtk.Dialog(title='Not Supported',
                     		flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,                       
                     		buttons = (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
 			dialog.vbox.pack_start(gtk.Label('Please add a provider first.'))
 			dialog.show_all()
 			result = dialog.run()
 			if result == gtk.RESPONSE_CLOSE:
 				dialog.destroy()
			
	def slice_apicall(self, data):
		
		if data == 'slicehost':
			key = self.api_key.get_text()
			#libcloud.security.VERIFY_SSL_CERT = True
			try:
				self.slice_driver = SlicehostNodeDriver(key)
				self.slice_nodes = self.slice_driver.list_nodes()
				self.nodes_driver_dict[data] = self.slice_driver
				self.treestore.append(None, [data])
				for slices_id in self.slice_nodes:
					self.slice_id_dict.append(slices_id.id)
			except Exception as detail:
				for widget in self.right_vbox_inside_frame.get_children():
					if widget == self.temp_frame:
						self.right_vbox_inside_frame.remove(widget)
				self.temp_frame_error = gtk.Frame(label = detail)
				self.temp_frame_error.set_shadow_type(gtk.SHADOW_NONE)
				self.right_vbox_inside_frame.pack_start(self.temp_frame_error,False,False,5)
				self.window.show_all()
				
		elif data == 'RackspaceUS':
			key = self.us_api_key.get_text()
			user = self.us_user_entry.get_text()
			#libcloud.security.VERIFY_SSL_CERT = True
			try:
				self.slice_driver = RackspaceNodeDriver(user, key)
				self.slice_nodes = self.slice_driver.list_nodes()
				self.nodes_driver_dict[data] = self.slice_driver
				self.treestore.append(None, [data])
				for slices_id in self.slice_nodes:
					self.slice_id_dict.append(slices_id.id)
			except Exception as detail:
				for widget in self.right_vbox_inside_frame.get_children():
					if widget == self.temp_frame:
						self.right_vbox_inside_frame.remove(widget)
				self.temp_frame_error = gtk.Frame(label = detail)
				self.temp_frame_error.set_shadow_type(gtk.SHADOW_NONE)
				self.right_vbox_inside_frame.pack_start(self.temp_frame_error,False,False,5)
				self.window.show_all()
				
		elif data == 'RackspaceUK':
			key = self.api_key.get_text()
			user = self.user_entry.get_text()
			#libcloud.security.VERIFY_SSL_CERT = True
			try:
				self.slice_driver = RackspaceUKNodeDriver(user, key)
				self.slice_nodes = self.slice_driver.list_nodes()
				self.nodes_driver_dict[data] = self.slice_driver
				self.treestore.append(None, [data])
				for slices_id in self.slice_nodes:
					self.slice_id_dict.append(slices_id.id)
			except Exception as detail:
				for widget in self.right_vbox_inside_frame.get_children():
					if widget == self.temp_frame:
						self.right_vbox_inside_frame.remove(widget)
				self.temp_frame_error = gtk.Frame(label = detail)
				self.temp_frame_error.set_shadow_type(gtk.SHADOW_NONE)
				self.right_vbox_inside_frame.pack_start(self.temp_frame_error,False,False,5)
				self.window.show_all()
				
		try:
			for slices in self.slice_nodes:
				ip = ','.join([ip for ip in slices.public_ip])
				self.store.append([slices.name,data, slices.id, slices.state, ip])
		
			for widget in self.right_vbox_inside_frame.get_children():
				try:
					if widget == self.temp_frame_error:
							self.right_vbox_inside_frame.remove(widget)
				except Exception:
					pass
				try:
					if widget == self.temp_frame:
						self.right_vbox_inside_frame.remove(widget)
				except Exception:
					pass
		except Exception:
			pass
						
	def slice_apicall_tmp(self, widget, data):
		
		try:
			for widget in self.right_vbox_inside_frame.get_children():
				if widget == self.temp_frame_error:
					self.right_vbox_inside_frame.remove(widget)
				if widget == self.temp_frame:
					self.right_vbox_inside_frame.remove(widget)
		except Exception:
			pass
			
		self.temp_frame = gtk.Frame(label = None)
		self.loading = gtk.Image()
		self.loading.set_from_file("loader.gif")
		self.temp_frame.add(self.loading)
		self.temp_frame.set_shadow_type(gtk.SHADOW_NONE)
		self.right_vbox_inside_frame.pack_start(self.temp_frame,False,False,5)
		self.temp_frame.show()
		self.window.show_all()
		gobject.timeout_add_seconds(4, self.slice_apicall, data)		
	
	def changed_cb(self, combobox):
        	model = combobox.get_model()
        	index = combobox.get_active()
        	if index == 1:
        		try:
        			for widget in self.frame.get_children():
					self.frame.remove(widget)
            		except Exception:
            			pass
            	
            		vbox = gtk.VBox(False, 1)
            		frame = gtk.Frame(label='Slicehost API Key')
            		frame.set_shadow_type(gtk.SHADOW_NONE)
            		self.api_key = gtk.Entry()
			self.api_key.set_visibility(True)
			okbutton = gtk.Button('Add')
			frame.add(self.api_key)
			okbutton.connect('pressed', self.slice_apicall_tmp, 'slicehost')
			vbox.pack_start(frame)
			vbox.pack_start(okbutton)
			self.frame.add(vbox)
			self.window.show_all()	
            		            		
            	elif index == 2:
            		try:
        			for widget in self.frame.get_children():
					self.frame.remove(widget)
            		except Exception:
            			pass
            	
            		vbox = gtk.VBox(False, 1)
            		rs_api_frame = gtk.Frame(label='Rackspace US API Key')
            		rs_api_frame.set_shadow_type(gtk.SHADOW_NONE)
            		rs_user_frame = gtk.Frame(label='Rackspace Username')
            		rs_user_frame.set_shadow_type(gtk.SHADOW_NONE)
            		self.us_api_key = gtk.Entry()
			self.us_api_key.set_visibility(True)
			self.us_user_entry = gtk.Entry()
			self.us_user_entry.set_visibility(True)
			rs_api_frame.add(self.us_api_key)
			rs_user_frame.add(self.us_user_entry)
			vbox.pack_start(rs_api_frame)
			vbox.pack_start(rs_user_frame)
			okbutton = gtk.Button('Add')
			okbutton.connect('pressed', self.slice_apicall_tmp, 'RackspaceUS')
			vbox.pack_start(okbutton)
			self.frame.add(vbox)
			self.window.show_all()	
            	
            	elif index == 3:
            		try:
        			for widget in self.frame.get_children():
					self.frame.remove(widget)
            		except Exception:
            			pass
            	
            		vbox = gtk.VBox(False, 1)
            		rs_api_frame = gtk.Frame(label='Rackspace UK API Key')
            		rs_api_frame.set_shadow_type(gtk.SHADOW_NONE)
            		rs_user_frame = gtk.Frame(label='Rackspace Username')
            		rs_user_frame.set_shadow_type(gtk.SHADOW_NONE)
            		self.api_key = gtk.Entry()
			self.api_key.set_visibility(True)
			self.user_entry = gtk.Entry()
			self.user_entry.set_visibility(True)
			rs_api_frame.add(self.api_key)
			rs_user_frame.add(self.user_entry)
			vbox.pack_start(rs_api_frame)
			vbox.pack_start(rs_user_frame)
			okbutton = gtk.Button('Add')
			okbutton.connect('pressed', self.slice_apicall_tmp, 'RackspaceUK')
			vbox.pack_start(okbutton)
			self.frame.add(vbox)
			self.window.show_all()
        	return
        
        def image_index_cb(self, image_combobox):
            	self.image_index = image_combobox.get_active()
            	return self.image_index
        
        def size_index_cb(self, size_combobox):
        	self.size_index = size_combobox.get_active()
        	return self.size_index
            		
        def changed_create_slice_cb(self, provider_combobox, data):
        	
        	model = provider_combobox.get_model()
        	index = provider_combobox.get_active()
        	data = provider_combobox.get_active_text()
        	
        	if data == 'slicehost':
        		try:
        			for widget in self.create_container_vbox.get_children():
					self.create_container_vbox.remove(widget)
            		except Exception:
            			pass
            	
            	elif data == 'RackspaceUS':
        		try:
        			for widget in self.create_container_vbox.get_children():
					self.create_container_vbox.remove(widget)
            		except Exception:
            			pass
            			
            	elif data == 'RackspaceUK':
            		try:
        			for widget in self.create_container_vbox.get_children():
					self.create_container_vbox.remove(widget)
            		except Exception:
            			pass
            	
            	
            	size_frame = gtk.Frame(label='Select Size')
            	size_frame.set_shadow_type(gtk.SHADOW_NONE)
            	size_combobox = gtk.combo_box_new_text()
           	image_frame = gtk.Frame(label='Select Image')
           	image_frame.set_shadow_type(gtk.SHADOW_NONE)
            	image_combobox = gtk.combo_box_new_text()
            	slicehost_driver= self.nodes_driver_dict[data]
            	#size_combobox.append_text('Select Size')
            	for sizes in slicehost_driver.list_sizes():
            		size_combobox.append_text(sizes.name)
            		
            	size_combobox.set_active(0)
            	size_frame.add(size_combobox)
            	#image_combobox.append_text('Select Image')
            	for images in slicehost_driver.list_images():
            		image_combobox.append_text(images.name)
            	image_combobox.set_active(0)
            	image_combobox.connect("changed", self.image_index_cb)
            	
            	image_frame.add(image_combobox)
            	name_frame = gtk.Frame(label='Enter Name')
            	name_frame.set_shadow_type(gtk.SHADOW_NONE)
            	name_text_box = gtk.Entry()
		name_text_box.set_visibility(True)
		name_frame.add(name_text_box)
		buttons_frame = gtk.Frame(label=None)
		create_button = gtk.Button(label='Create')
		create_button_frame = gtk.Frame(label=None)
		create_button_frame.set_shadow_type(gtk.SHADOW_NONE)
		create_button_frame.add(create_button)
		cancel_button = gtk.Button(label='Cancel')
		cancel_button_frame = gtk.Frame(label=None)
		cancel_button_frame.set_shadow_type(gtk.SHADOW_NONE)
		cancel_button_frame.add(cancel_button)
            	
            	cancel_button.connect("clicked", lambda w: self.create_window.destroy())
		create_button.connect("clicked", lambda w: self.create_call(data, name = name_text_box.get_text(),
							image = self.image_index_cb(image_combobox), size = self.size_index_cb(size_combobox)))
		
		buttons_hbox = gtk.HBox(True)
		buttons_hbox.pack_start(create_button_frame, False, False, 1)
		buttons_hbox.pack_start(cancel_button_frame, False, False, 1)
		buttons_frame.add(buttons_hbox)
		
            	self.create_container_vbox.pack_start(size_frame, False, False, 2)
            	self.create_container_vbox.pack_start(image_frame, False, False, 2)
            	self.create_container_vbox.pack_start(name_frame, False, False, 2)
            	self.create_container_vbox.pack_start(buttons_frame, False, False, 2)
            	self.create_container_vbox.show_all()           		
            	
        	return
        	
class ApiCalls(app_calls):
	'''Calls for all api calls'''
	

	def create_model(self):
        	self.store = gtk.ListStore(str, str, str, str, str)
		return self.store


   	def create_columns(self, treeView):
    
        	rendererText = gtk.CellRendererText()
        	column = gtk.TreeViewColumn("Slice Name", rendererText, text=0)
        	column.set_sort_column_id(0)    
        	treeView.append_column(column)
        	
        	rendererText = gtk.CellRendererText()
        	column = gtk.TreeViewColumn("Provider", rendererText, text=1)
        	column.set_sort_column_id(1)    
        	treeView.append_column(column)
        	
        	
        	rendererText = gtk.CellRendererText()
        	column = gtk.TreeViewColumn("Slice ID", rendererText, text=2)
        	column.set_sort_column_id(2)
        	treeView.append_column(column)
	
        	rendererText = gtk.CellRendererText()
        	column = gtk.TreeViewColumn("Status", rendererText, text=3)
        	column.set_sort_column_id(3)
        	treeView.append_column(column)
		
		rendererText = gtk.CellRendererText()
        	column = gtk.TreeViewColumn("IP Adresses", rendererText, text=4)
        	column.set_sort_column_id(4)
        	treeView.append_column(column)

    	def on_activated(self, widget):
		try:    	
        		model, row = widget.get_selected_rows()
        		text = "Slice: " + model[row[0][0]][0] + ",  " + " Provider: " + model[row[0][0]][1] + ",  " \
        		+ "ID: " + model[row[0][0]][2]
        		self.statusbar.push(0, text)
		except Exception:
			self.statusbar.push(0, '')
			
	def apicallmainwindow(self, data=None):
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title('Slice Actions')
		self.window.connect('delete_event', self.delete_event)
		self.window.connect('destroy', lambda w: gtk.main_quit())
		self.window.set_border_width(0)
		self.window.set_position(gtk.WIN_POS_CENTER)
		self.window.set_default_size(850,550)
		self.main = gtk.VBox(False, 5)
		self.hbox_main = gtk.HBox(False, 5)
		self.vbox_top = gtk.VBox(False, 5)
		self.hbox_left = gtk.HBox(False, 5)
		self.hbox_right = gtk.HBox(False, 5)
		
		mb = gtk.MenuBar()
		filemenu = gtk.Menu()
        	filem = gtk.MenuItem("File")
        	filem.set_submenu(filemenu)
       		exit = gtk.MenuItem("Exit")
        	exit.connect("activate", gtk.main_quit)
        	filemenu.append(exit)
		mb.append(filem)
		
        	self.vbox_top.pack_start(mb, False, False, 0)
		
		self.frame_left_hbox = gtk.Frame(label=' Add Slices ')
		self.frame_right_hbox = gtk.Frame(label=None)
		self.frame_right_hbox.set_shadow_type(gtk.SHADOW_NONE)
		self.frame_right_bottom_hbox = gtk.Frame(label=None)
		combobox = gtk.combo_box_new_text()
      		combobox.append_text('Select Provider:')
        	combobox.append_text('Slicehost')
        	combobox.append_text('Rackspace US')
        	combobox.append_text('Rackspace UK')
        	combobox.connect('changed', self.changed_cb)
        	combobox.set_active(0)
        	vbox_combobox = gtk.VBox(False, 1)
        	frame_combobox = gtk.Frame(label=None)
        	frame_combobox.set_shadow_type(gtk.SHADOW_NONE)
		frame_combobox.add(combobox)
		#label if needed for nodes added
		self.frame_left_bottom_hbox = gtk.Frame(label=None)
		self.frame_left_bottom_hbox.set_shadow_type(gtk.SHADOW_NONE)

		# create a TreeStore with one column for providers
		self.treestore = gtk.TreeStore(str)
		self.treeview = gtk.TreeView(self.treestore)
		self.tvcolumn = gtk.TreeViewColumn('Nodes')
		self.treeview.append_column(self.tvcolumn)
		self.cell = gtk.CellRendererText()
		self.tvcolumn.pack_start(self.cell, True)
		self.tvcolumn.add_attribute(self.cell, 'text', 0)
		self.treeview.set_search_column(0)
		self.tvcolumn.set_sort_column_id(0)
		self.treeview.set_reorderable(True)

		self.frame_left_bottom_hbox.add(self.treeview)
		self.remove_button_frame = gtk.Frame(label=None)
		self.remove_button_frame.set_shadow_type(gtk.SHADOW_NONE)
		self.remove_button = gtk.Button(label='Remove')
		self.remove_button.connect("clicked", self.remove_provider)
		self.remove_button_frame.add(self.remove_button)
		
		
		vbox_combobox.pack_start(frame_combobox, False, False, 10)
		vbox_combobox.pack_end(self.remove_button_frame, False, False, 0)
		vbox_combobox.pack_end(self.frame_left_bottom_hbox, True, True, 1)

		self.frame = gtk.Frame(label=None)
		self.frame.set_shadow_type(gtk.SHADOW_NONE)
		vbox_combobox.pack_start(self.frame, False, False, 10)
		self.frame_left_hbox.add(vbox_combobox)
		self.hbox_left.pack_start(self.frame_left_hbox, False, False, 0)
		#vbox on the right hand side
		right_vbox = gtk.VBox(False, 1)
		#second vbox inside the manage slice frame					
		self.right_vbox_inside_frame = gtk.VBox(False,1)

		sw = gtk.ScrolledWindow()
       		sw.set_shadow_type(gtk.SHADOW_NONE)
        	sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        	self.right_vbox_inside_frame.pack_start(sw, True, True, 0)

        	store = self.create_model()
        	self.treeView = gtk.TreeView(store)
        	selection = self.treeView.get_selection()
        	selection.connect("changed", self.on_activated)
        	self.treeView.set_rules_hint(True)
        	sw.add(self.treeView)
	
        	self.create_columns(self.treeView)
        	self.statusbar = gtk.Statusbar()
        
        	self.right_vbox_inside_frame.pack_start(self.statusbar, False, False, 0)
		self.frame_right_hbox.add(self.right_vbox_inside_frame)
		#top frame on the right
		right_vbox.pack_start(self.frame_right_hbox, True, True, 0)	
		button_table = gtk.Table(rows=1, columns = 5)
		reboot_button = gtk.Button(label='Reboot')
		reboot_button.connect("clicked", self.reboot_slice)
		rename_button = gtk.Button(label='Rename')
		rename_button.connect("clicked", self.rename_slice)
		rebuild_button = gtk.Button(label='Rebuild')
		rebuild_button.connect("clicked", self.not_supported)
		create_button = gtk.Button(label='Create')
		create_button.connect("clicked", self.create_slice)
		delete_button = gtk.Button(label='Delete')
		delete_button.connect("clicked", self.delete_slice)
		button_table.attach(reboot_button,0,1,0,1)
		button_table.attach(rename_button,1,2,0,1)
		button_table.attach(rebuild_button,2,3,0,1)
		button_table.attach(create_button,3,4,0,1)
		button_table.attach(delete_button,4,5,0,1)
		self.frame_right_bottom_hbox.add(button_table) 
		#bottom from on the right to have buttons
		right_vbox.pack_end(self.frame_right_bottom_hbox,False,False,2)	
		self.hbox_right.pack_start(right_vbox, True, True, 0)

        	self.hbox_main.pack_start(self.hbox_left,False,False,5)
        	self.hbox_main.pack_start(self.hbox_right,True,True,5)
        	
		self.main.pack_start(self.vbox_top, False, False, 0)
		self.main.pack_start(self.hbox_main, True, True, 0)
        	self.window.add(self.main)
		self.window.show_all()

		gtk.main()




if __name__ == '__main__':
        Api = ApiCalls()
        Api.apicallmainwindow()
        
